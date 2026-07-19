"""System administration pages for Energy Monitor V2."""

from __future__ import annotations

import ipaddress
import os
import platform
import shutil
import socket
import subprocess
import tempfile
import time
import zipfile
from datetime import datetime
from pathlib import Path

import psutil
import yaml
from flask import Blueprint, current_app, flash, redirect, render_template, request, send_file, url_for
from werkzeug.utils import secure_filename

system_settings = Blueprint("system_settings", __name__, url_prefix="/settings")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
NETPLAN_DIR = Path("/etc/netplan")
SERVICE_NAME = "energy-monitor"
INFLUX_SERVICE = "docker"


def _run(command: list[str], timeout: int = 15) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)


def _service_state(name: str) -> str:
    result = _run(["systemctl", "is-active", name])
    return result.stdout.strip() or "unknown"


def _temperature() -> float | None:
    candidates = [
        Path("/sys/class/thermal/thermal_zone0/temp"),
        Path("/sys/class/hwmon/hwmon0/temp1_input"),
    ]
    for path in candidates:
        try:
            value = float(path.read_text().strip())
            return round(value / 1000.0 if value > 200 else value, 1)
        except (OSError, ValueError):
            continue
    return None


def _uptime() -> str:
    seconds = max(0, int(time.time() - psutil.boot_time()))
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, _ = divmod(seconds, 60)
    return f"{days} d. {hours} val. {minutes} min."


def _default_interface() -> str:
    result = _run(["ip", "route", "show", "default"])
    words = result.stdout.split()
    if "dev" in words:
        try:
            return words[words.index("dev") + 1]
        except (IndexError, ValueError):
            pass
    return "eth0"


def _network_info() -> dict[str, str]:
    interface = _default_interface()
    address = ""
    prefix = "24"
    gateway = ""
    dns = ""

    addr_result = _run(["ip", "-4", "-o", "addr", "show", "dev", interface])
    for line in addr_result.stdout.splitlines():
        parts = line.split()
        if "inet" in parts:
            cidr = parts[parts.index("inet") + 1]
            address, prefix = cidr.split("/", 1)
            break

    route_result = _run(["ip", "route", "show", "default"])
    route_words = route_result.stdout.split()
    if "via" in route_words:
        try:
            gateway = route_words[route_words.index("via") + 1]
        except (IndexError, ValueError):
            pass

    resolv = Path("/etc/resolv.conf")
    try:
        for line in resolv.read_text().splitlines():
            if line.startswith("nameserver "):
                dns = line.split(maxsplit=1)[1].strip()
                break
    except OSError:
        pass

    return {
        "hostname": socket.gethostname(),
        "interface": interface,
        "ip_address": address,
        "prefix": prefix,
        "subnet_mask": str(ipaddress.ip_network(f"0.0.0.0/{prefix}").netmask),
        "gateway": gateway,
        "dns": dns,
    }


def _mask_to_prefix(subnet_mask: str) -> str:
    try:
        network = ipaddress.ip_network(f"0.0.0.0/{subnet_mask}")
    except ValueError as exc:
        raise ValueError("Neteisinga subnet mask. Naudok formatą, pvz. 255.255.255.0.") from exc
    return str(network.prefixlen)


def _validate_network(ip_address: str, subnet_mask: str, gateway: str, dns: str) -> str:
    prefix = _mask_to_prefix(subnet_mask)
    ipaddress.ip_interface(f"{ip_address}/{prefix}")
    ipaddress.ip_address(gateway)
    if dns:
        for server in dns.replace(",", " ").split():
            ipaddress.ip_address(server)
    return prefix


def _write_netplan(interface: str, ip_address: str, prefix: str, gateway: str, dns: str) -> Path:
    nameservers = dns.replace(",", " ").split() if dns else []
    config = {
        "network": {
            "version": 2,
            "renderer": "networkd",
            "ethernets": {
                interface: {
                    "dhcp4": False,
                    "addresses": [f"{ip_address}/{prefix}"],
                    "routes": [{"to": "default", "via": gateway}],
                    "nameservers": {"addresses": nameservers},
                }
            },
        }
    }
    NETPLAN_DIR.mkdir(parents=True, exist_ok=True)
    target = NETPLAN_DIR / "99-energy-monitor.yaml"
    tmp = target.with_suffix(".yaml.tmp")
    tmp.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    os.chmod(tmp, 0o600)
    tmp.replace(target)
    return target


def _deferred_systemctl(action: str, unit: str | None = None) -> None:
    if action not in {"reboot", "poweroff", "restart"}:
        raise ValueError("Unsupported action")
    if action == "restart" and not unit:
        raise ValueError("Unit is required")
    command = ["systemctl", action]
    if unit:
        command.append(unit)
    subprocess.Popen(
        ["bash", "-lc", f"sleep 2; {' '.join(command)}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


@system_settings.route("/", methods=["GET"])
def index():
    disk = psutil.disk_usage("/")
    memory = psutil.virtual_memory()
    diagnostics = {
        "cpu_percent": psutil.cpu_percent(interval=0.15),
        "memory_used_mb": round(memory.used / 1024 / 1024),
        "memory_total_mb": round(memory.total / 1024 / 1024),
        "disk_used_gb": round(disk.used / 1024 / 1024 / 1024, 1),
        "disk_total_gb": round(disk.total / 1024 / 1024 / 1024, 1),
        "temperature": _temperature(),
        "uptime": _uptime(),
        "os": platform.platform(),
        "python": platform.python_version(),
        "energy_monitor": _service_state(SERVICE_NAME),
        "influxdb": _service_state("docker") if shutil.which("docker") else "not installed",
    }
    return render_template("settings.html", network=_network_info(), diagnostics=diagnostics)


@system_settings.route("/network", methods=["POST"])
def save_network():
    hostname = request.form.get("hostname", "").strip()
    interface = request.form.get("interface", "eth0").strip()
    ip_address = request.form.get("ip_address", "").strip()
    subnet_mask = request.form.get("subnet_mask", "255.255.255.0").strip()
    gateway = request.form.get("gateway", "").strip()
    dns = request.form.get("dns", "").strip()

    try:
        if not hostname or len(hostname) > 63 or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-." for c in hostname):
            raise ValueError("Neteisingas hostname.")
        if not interface or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.:-" for c in interface):
            raise ValueError("Neteisinga tinklo sąsaja.")
        prefix = _validate_network(ip_address, subnet_mask, gateway, dns)
        _write_netplan(interface, ip_address, prefix, gateway, dns)
        _run(["hostnamectl", "set-hostname", hostname])
        test = _run(["netplan", "generate"])
        if test.returncode != 0:
            raise RuntimeError(test.stderr.strip() or "netplan generate nepavyko")
        flash(f"Tinklo nustatymai išsaugoti. Perkrauk Orange Pi. Naujas adresas: http://{ip_address}:5000", "success")
    except (ValueError, RuntimeError, OSError) as exc:
        flash(f"Nepavyko išsaugoti tinklo nustatymų: {exc}", "danger")
    return redirect(url_for("system_settings.index"))


@system_settings.route("/action/<action>", methods=["POST"])
def system_action(action: str):
    actions = {
        "restart-app": ("restart", SERVICE_NAME, "Energy Monitor persikrauna."),
        "restart-influx": ("restart", "docker", "Docker / InfluxDB persikrauna."),
        "reboot": ("reboot", None, "Orange Pi persikrauna."),
        "shutdown": ("poweroff", None, "Orange Pi išjungiamas."),
    }
    if action not in actions:
        flash("Nežinomas veiksmas.", "danger")
        return redirect(url_for("system_settings.index"))
    system_action_name, unit, message = actions[action]
    try:
        _deferred_systemctl(system_action_name, unit)
        flash(message, "warning")
    except (OSError, ValueError) as exc:
        flash(f"Veiksmo paleisti nepavyko: {exc}", "danger")
    return redirect(url_for("system_settings.index"))


@system_settings.route("/backup", methods=["GET"])
def backup():
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    temp_dir = Path(tempfile.mkdtemp(prefix="energy-monitor-backup-"))
    archive = temp_dir / f"energy-monitor-backup-{timestamp}.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        if DATA_DIR.exists():
            for path in DATA_DIR.rglob("*"):
                if path.is_file():
                    zf.write(path, Path("data") / path.relative_to(DATA_DIR))
        env_file = PROJECT_ROOT / ".env"
        if env_file.exists():
            zf.write(env_file, ".env")
        uploads = PROJECT_ROOT / "static" / "uploads"
        if uploads.exists():
            for path in uploads.rglob("*"):
                if path.is_file():
                    zf.write(path, Path("static/uploads") / path.relative_to(uploads))
    return send_file(archive, as_attachment=True, download_name=archive.name, mimetype="application/zip")


@system_settings.route("/restore", methods=["POST"])
def restore():
    uploaded = request.files.get("backup_file")
    if uploaded is None or not uploaded.filename:
        flash("Pasirink backup ZIP failą.", "danger")
        return redirect(url_for("system_settings.index"))
    filename = secure_filename(uploaded.filename)
    if not filename.lower().endswith(".zip"):
        flash("Backup turi būti ZIP failas.", "danger")
        return redirect(url_for("system_settings.index"))

    temp_dir = Path(tempfile.mkdtemp(prefix="energy-monitor-restore-"))
    archive = temp_dir / filename
    uploaded.save(archive)
    try:
        with zipfile.ZipFile(archive) as zf:
            for member in zf.infolist():
                member_path = Path(member.filename)
                if member_path.is_absolute() or ".." in member_path.parts:
                    raise ValueError("Nesaugus ZIP turinys")
                if not (member.filename == ".env" or member.filename.startswith("data/") or member.filename.startswith("static/uploads/")):
                    continue
                target = PROJECT_ROOT / member_path
                target.parent.mkdir(parents=True, exist_ok=True)
                if not member.is_dir():
                    with zf.open(member) as src, target.open("wb") as dst:
                        shutil.copyfileobj(src, dst)
        flash("Backup atkurtas. Perkrauk Energy Monitor arba Orange Pi.", "success")
    except (zipfile.BadZipFile, ValueError, OSError) as exc:
        flash(f"Backup atkurti nepavyko: {exc}", "danger")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
    return redirect(url_for("system_settings.index"))

"""
web/mimic.py

Energy Monitor V2

Image based mimic diagrams and live value widgets.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from werkzeug.utils import secure_filename

from database.mimic_models import MimicDiagram, MimicWidget


mimic = Blueprint("mimic", __name__)

ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

MEASUREMENT_CHOICES: tuple[tuple[str, str, str], ...] = (
    ("active_power.total", "Active power total", "kW"),
    ("active_power.l1", "Active power L1", "kW"),
    ("active_power.l2", "Active power L2", "kW"),
    ("active_power.l3", "Active power L3", "kW"),
    ("reactive_power.total", "Reactive power total", "kvar"),
    ("reactive_power.l1", "Reactive power L1", "kvar"),
    ("reactive_power.l2", "Reactive power L2", "kvar"),
    ("reactive_power.l3", "Reactive power L3", "kvar"),
    ("apparent_power.total", "Apparent power total", "kVA"),
    ("current.total", "Current total", "A"),
    ("current.l1", "Current L1", "A"),
    ("current.l2", "Current L2", "A"),
    ("current.l3", "Current L3", "A"),
    ("voltage.average", "Voltage average", "V"),
    ("voltage.l1", "Voltage L1", "V"),
    ("voltage.l2", "Voltage L2", "V"),
    ("voltage.l3", "Voltage L3", "V"),
    ("power_factor.total", "Power factor total", ""),
    ("frequency", "Frequency", "Hz"),
    ("energy.import_active", "Imported active energy", "kWh"),
    ("energy.export_active", "Exported active energy", "kWh"),
)

MEASUREMENT_UNITS = {
    key: unit
    for key, _label, unit in MEASUREMENT_CHOICES
}


def application():
    return current_app.application


def diagram_repository():
    return application().mimic_diagrams


def widget_repository():
    return application().mimic_widgets


def meter_repository():
    return application().meters


def device_manager():
    return application().device_manager


def get_diagram(diagram_id: int) -> MimicDiagram:
    diagram = diagram_repository().get_by_id(diagram_id)
    if diagram is None:
        abort(404)
    return diagram


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _save_background(upload) -> str:
    if upload is None or not upload.filename:
        return ""

    filename = secure_filename(upload.filename)
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError("Supported image formats: PNG, JPG, JPEG and WEBP.")

    upload_dir = Path(current_app.static_folder) / "uploads" / "mimic"
    upload_dir.mkdir(parents=True, exist_ok=True)

    stored_name = f"{uuid4().hex}.{extension}"
    upload.save(upload_dir / stored_name)

    return f"uploads/mimic/{stored_name}"


def _remove_background(relative_path: str) -> None:
    if not relative_path or not relative_path.startswith("uploads/mimic/"):
        return

    path = Path(current_app.static_folder) / relative_path
    try:
        path.unlink(missing_ok=True)
    except OSError:
        current_app.logger.warning("Cannot remove mimic background %s", path)


def _device_by_meter_id(meter_id: int | None):
    if meter_id is None:
        return None

    return device_manager().get(meter_id)


def _resolve_measurement(device, path: str) -> float | None:
    if device is None:
        return None

    value: Any = device.measurements

    for part in path.split("."):
        if value is None or not hasattr(value, part):
            return None
        value = getattr(value, part)

    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _widget_payload(widget: MimicWidget) -> dict[str, Any]:
    device = _device_by_meter_id(widget.meter_id)
    value = _resolve_measurement(device, widget.measurement)
    unit = MEASUREMENT_UNITS.get(widget.measurement, "")

    connected = bool(device and device.connected)
    running = bool(
        connected
        and value is not None
        and value > widget.running_threshold
    )

    percent: float | None = None
    if (
        value is not None
        and widget.nominal_power is not None
        and widget.nominal_power > 0
    ):
        percent = value / widget.nominal_power * 100.0

    return {
        "id": widget.id,
        "title": widget.title,
        "meter_id": widget.meter_id,
        "measurement": widget.measurement,
        "widget_type": widget.widget_type,
        "x": widget.x,
        "y": widget.y,
        "width": widget.width,
        "value": value,
        "unit": unit,
        "connected": connected,
        "running": running,
        "status": (
            "Veikia"
            if running
            else "Neveikia"
            if connected
            else "Nėra ryšio"
        ),
        "percent": percent,
        "nominal_power": widget.nominal_power,
        "running_threshold": widget.running_threshold,
        "decimals": widget.decimals,
        "show_status": widget.show_status,
        "show_percent": widget.show_percent,
    }


@mimic.route("/mimic")
def diagrams():
    return render_template(
        "mimic_list.html",
        diagrams=diagram_repository().get_all(),
    )


@mimic.route("/mimic/add", methods=["GET", "POST"])
def add_diagram():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Diagram name is required.", "danger")
            return render_template("mimic_form.html", diagram=None)

        try:
            background = _save_background(request.files.get("background"))
        except ValueError as ex:
            flash(str(ex), "danger")
            return render_template("mimic_form.html", diagram=None)

        diagram = MimicDiagram(
            name=name,
            description=request.form.get("description", "").strip(),
            background_image=background,
            canvas_width=max(320, _to_int(request.form.get("canvas_width"), 1600)),
            canvas_height=max(200, _to_int(request.form.get("canvas_height"), 900)),
        )
        diagram_repository().add(diagram)
        flash("Mimic diagram created.", "success")
        return redirect(url_for("mimic.diagram", diagram_id=diagram.id, edit=1))

    return render_template("mimic_form.html", diagram=None)


@mimic.route("/mimic/<int:diagram_id>/settings", methods=["GET", "POST"])
def edit_diagram(diagram_id: int):
    diagram = get_diagram(diagram_id)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Diagram name is required.", "danger")
            return render_template("mimic_form.html", diagram=diagram)

        old_background = diagram.background_image

        try:
            new_background = _save_background(request.files.get("background"))
        except ValueError as ex:
            flash(str(ex), "danger")
            return render_template("mimic_form.html", diagram=diagram)

        diagram.name = name
        diagram.description = request.form.get("description", "").strip()
        diagram.canvas_width = max(320, _to_int(request.form.get("canvas_width"), 1600))
        diagram.canvas_height = max(200, _to_int(request.form.get("canvas_height"), 900))

        if new_background:
            diagram.background_image = new_background

        diagram_repository().update(diagram)

        if new_background and old_background != new_background:
            _remove_background(old_background)

        flash("Mimic diagram updated.", "success")
        return redirect(url_for("mimic.diagram", diagram_id=diagram.id, edit=1))

    return render_template("mimic_form.html", diagram=diagram)


@mimic.route("/mimic/<int:diagram_id>/delete", methods=["POST"])
def delete_diagram(diagram_id: int):
    diagram = get_diagram(diagram_id)
    diagram_repository().delete(diagram_id)
    _remove_background(diagram.background_image)
    flash("Mimic diagram deleted.", "success")
    return redirect(url_for("mimic.diagrams"))


@mimic.route("/mimic/<int:diagram_id>")
def diagram(diagram_id: int):
    diagram_model = get_diagram(diagram_id)
    widgets = widget_repository().get_for_diagram(diagram_id)
    meters = meter_repository().get_all()

    return render_template(
        "mimic.html",
        diagram=diagram_model,
        widgets=widgets,
        meters=meters,
        measurement_choices=MEASUREMENT_CHOICES,
        edit_mode=request.args.get("edit") == "1",
    )


@mimic.route("/api/mimic/<int:diagram_id>")
def diagram_api(diagram_id: int):
    get_diagram(diagram_id)
    widgets = widget_repository().get_for_diagram(diagram_id)
    return jsonify(
        {
            "ok": True,
            "widgets": [_widget_payload(widget) for widget in widgets],
        }
    )


@mimic.route("/api/mimic/<int:diagram_id>/widgets", methods=["POST"])
def add_widget(diagram_id: int):
    get_diagram(diagram_id)
    payload = request.get_json(silent=True) or {}

    widget = MimicWidget(
        diagram_id=diagram_id,
        title=str(payload.get("title") or "New widget").strip(),
        meter_id=_to_int(payload.get("meter_id"), 0) or None,
        measurement=str(payload.get("measurement") or "active_power.total"),
        widget_type=str(payload.get("widget_type") or "equipment"),
        x=max(0.0, min(95.0, _to_float(payload.get("x"), 10.0))),
        y=max(0.0, min(95.0, _to_float(payload.get("y"), 10.0))),
        width=max(5.0, min(50.0, _to_float(payload.get("width"), 12.0))),
        nominal_power=(
            _to_float(payload.get("nominal_power"))
            if payload.get("nominal_power") not in (None, "")
            else None
        ),
        running_threshold=_to_float(payload.get("running_threshold"), 1.0),
        decimals=max(0, min(4, _to_int(payload.get("decimals"), 2))),
        show_status=bool(payload.get("show_status", True)),
        show_percent=bool(payload.get("show_percent", True)),
    )
    widget_repository().add(widget)
    return jsonify({"ok": True, "widget": _widget_payload(widget)}), 201


@mimic.route(
    "/api/mimic/<int:diagram_id>/widgets/<int:widget_id>",
    methods=["PUT", "DELETE"],
)
def update_widget(diagram_id: int, widget_id: int):
    get_diagram(diagram_id)
    widget = widget_repository().get_by_id(widget_id)

    if widget is None or widget.diagram_id != diagram_id:
        abort(404)

    if request.method == "DELETE":
        widget_repository().delete(widget_id, diagram_id)
        return jsonify({"ok": True})

    payload = request.get_json(silent=True) or {}

    widget.title = str(payload.get("title", widget.title)).strip() or "Widget"
    widget.meter_id = _to_int(payload.get("meter_id"), 0) or None
    widget.measurement = str(payload.get("measurement", widget.measurement))
    widget.widget_type = str(payload.get("widget_type", widget.widget_type))
    widget.x = max(0.0, min(98.0, _to_float(payload.get("x"), widget.x)))
    widget.y = max(0.0, min(98.0, _to_float(payload.get("y"), widget.y)))
    widget.width = max(5.0, min(50.0, _to_float(payload.get("width"), widget.width)))
    widget.nominal_power = (
        _to_float(payload.get("nominal_power"))
        if payload.get("nominal_power") not in (None, "")
        else None
    )
    widget.running_threshold = _to_float(
        payload.get("running_threshold"), widget.running_threshold
    )
    widget.decimals = max(0, min(4, _to_int(payload.get("decimals"), widget.decimals)))
    widget.show_status = bool(payload.get("show_status", widget.show_status))
    widget.show_percent = bool(payload.get("show_percent", widget.show_percent))

    widget_repository().update(widget)
    return jsonify({"ok": True, "widget": _widget_payload(widget)})

"use strict";

const REFRESH_INTERVAL_MS = 1000;
const SELECTED_METER_STORAGE_KEY = "energy_monitor_selected_meter";

let dashboardDevices = [];
let selectedDeviceId = null;
let refreshTimer = null;
let requestInProgress = false;


/* ------------------------------------------------------------------
 * Helpers
 * ------------------------------------------------------------------ */

function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


function isValidNumber(value) {
    return (
        value !== null &&
        value !== undefined &&
        value !== "" &&
        Number.isFinite(Number(value))
    );
}


function formatNumber(value, decimals = 2) {
    if (!isValidNumber(value)) {
        return "--";
    }

    return Number(value).toFixed(decimals);
}


function formatValue(value, unit = "", decimals = 2) {
    if (!isValidNumber(value)) {
        return `<span class="measurement-empty">--</span>`;
    }

    return `
        <span class="measurement-number">
            ${formatNumber(value, decimals)}
        </span>
        <span class="measurement-unit">
            ${escapeHtml(unit)}
        </span>
    `;
}


function formatResponseTime(value) {
    if (!isValidNumber(value)) {
        return "--";
    }

    return `${formatNumber(value, 1)} ms`;
}


function formatDateTime(value) {
    if (!value) {
        return "--";
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return escapeHtml(value);
    }

    return date.toLocaleString("lt-LT");
}


function getRelativeTime(value) {
    if (!value) {
        return "--";
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return "--";
    }

    const seconds = Math.max(
        0,
        Math.floor((Date.now() - date.getTime()) / 1000)
    );

    if (seconds < 5) {
        return "dabar";
    }

    if (seconds < 60) {
        return `prieš ${seconds} s`;
    }

    const minutes = Math.floor(seconds / 60);

    if (minutes < 60) {
        return `prieš ${minutes} min.`;
    }

    const hours = Math.floor(minutes / 60);

    if (hours < 24) {
        return `prieš ${hours} val.`;
    }

    const days = Math.floor(hours / 24);

    return `prieš ${days} d.`;
}


function getDashboardApiUrl() {
    if (
        typeof dashboardApiUrl !== "undefined" &&
        dashboardApiUrl
    ) {
        return dashboardApiUrl;
    }

    return "/api/dashboard";
}


function getSelectedDevice() {
    return dashboardDevices.find(
        device => Number(device.id) === Number(selectedDeviceId)
    ) || null;
}


/* ------------------------------------------------------------------
 * Summary
 * ------------------------------------------------------------------ */

function renderSummary(data) {
    const onlineElement = document.getElementById("summary-online");
    const offlineElement = document.getElementById("summary-offline");
    const totalElement = document.getElementById("summary-total");

    if (onlineElement) {
        onlineElement.textContent = data.online ?? 0;
    }

    if (offlineElement) {
        offlineElement.textContent = data.offline ?? 0;
    }

    if (totalElement) {
        totalElement.textContent = data.total ?? 0;
    }
}


/* ------------------------------------------------------------------
 * Meter selector
 * ------------------------------------------------------------------ */

function selectDevice(deviceId) {
    selectedDeviceId = Number(deviceId);

    localStorage.setItem(
        SELECTED_METER_STORAGE_KEY,
        String(selectedDeviceId)
    );

    renderMeterTabs();
    renderSelectedDevice();
}


function renderMeterTabs() {
    const root = document.getElementById("meter-tabs");

    if (!root) {
        return;
    }

    root.innerHTML = "";

    for (const device of dashboardDevices) {
        const isSelected =
            Number(device.id) === Number(selectedDeviceId);

        const tab = document.createElement("button");

        tab.type = "button";
        tab.className = `meter-tab${isSelected ? " active" : ""}`;
        tab.dataset.deviceId = String(device.id);

        const statusClass = device.connected
            ? "meter-tab-online"
            : "meter-tab-offline";

        const statusText = device.connected
            ? "Online"
            : "Offline";

        tab.innerHTML = `
            <div class="meter-tab-header">
                <span class="meter-tab-icon">
                    <i class="bi bi-lightning-charge-fill"></i>
                </span>

                <span class="meter-tab-status ${statusClass}">
                    <span class="status-dot"></span>
                    ${statusText}
                </span>
            </div>

            <div class="meter-name">
                ${escapeHtml(device.name || `Meter ${device.id}`)}
            </div>

            <div class="meter-tab-driver">
                ${escapeHtml(device.driver || "")}
            </div>
        `;

        tab.addEventListener("click", () => {
            selectDevice(device.id);
        });

        root.appendChild(tab);
    }
}


/* ------------------------------------------------------------------
 * Dashboard cards
 * ------------------------------------------------------------------ */

function createPhaseTable(title, values, unit, decimals = 2) {
    return `
        <section class="dashboard-panel">
            <div class="dashboard-panel-header">
                <h3>${escapeHtml(title)}</h3>
            </div>

            <div class="phase-grid">
                <div class="phase-item phase-l1">
                    <div class="phase-name">L1</div>
                    <div class="phase-value">
                        ${formatValue(values?.l1, unit, decimals)}
                    </div>
                </div>

                <div class="phase-item phase-l2">
                    <div class="phase-name">L2</div>
                    <div class="phase-value">
                        ${formatValue(values?.l2, unit, decimals)}
                    </div>
                </div>

                <div class="phase-item phase-l3">
                    <div class="phase-name">L3</div>
                    <div class="phase-value">
                        ${formatValue(values?.l3, unit, decimals)}
                    </div>
                </div>
            </div>
        </section>
    `;
}


function createPowerCard(
    title,
    icon,
    value,
    unit,
    cssClass = "",
    decimals = 2
) {
    return `
        <div class="power-card ${cssClass}">
            <div class="power-card-icon">
                <i class="bi ${escapeHtml(icon)}"></i>
            </div>

            <div class="power-card-content">
                <div class="power-card-title">
                    ${escapeHtml(title)}
                </div>

                <div class="power-card-value">
                    ${formatValue(value, unit, decimals)}
                </div>
            </div>
        </div>
    `;
}


function createEnergyRow(title, value, unit) {
    return `
        <div class="energy-row">
            <span class="energy-label">
                ${escapeHtml(title)}
            </span>

            <span class="energy-value">
                ${formatValue(value, unit, 2)}
            </span>
        </div>
    `;
}


function renderSelectedDevice() {
    const root = document.getElementById("device");

    if (!root) {
        return;
    }

    const device = getSelectedDevice();

    if (!device) {
        root.innerHTML = `
            <div class="dashboard-message">
                Skaitiklis nepasirinktas.
            </div>
        `;
        return;
    }

    const connectedClass = device.connected
        ? "device-online"
        : "device-offline";

    const connectedText = device.connected
        ? "ONLINE"
        : "OFFLINE";

    const statusIcon = device.connected
        ? "bi-check-circle-fill"
        : "bi-x-circle-fill";

    const errorHtml = device.last_error
        ? `
            <div class="device-error">
                <i class="bi bi-exclamation-triangle-fill"></i>
                ${escapeHtml(device.last_error)}
            </div>
        `
        : "";

    root.innerHTML = `
        <section class="selected-device">

            <div class="selected-device-header">

                <div class="selected-device-title">

                    <div class="selected-device-icon">
                        <i class="bi bi-lightning-charge-fill"></i>
                    </div>

                    <div>
                        <h2>
                            ${escapeHtml(device.name || `Meter ${device.id}`)}
                        </h2>

                        <div class="selected-device-meta">
                            <span>
                                ${escapeHtml(device.driver || "--")}
                            </span>

                            <span class="meta-separator">•</span>

                            <span>
                                ${escapeHtml(device.protocol || "--")}
                            </span>

                            <span class="meta-separator">•</span>

                            <span>
                                ID ${escapeHtml(device.id)}
                            </span>
                        </div>
                    </div>

                </div>

                <div class="selected-device-status ${connectedClass}">
                    <i class="bi ${statusIcon}"></i>
                    ${connectedText}
                </div>

            </div>

            ${errorHtml}

            <div class="device-diagnostics">

                <div class="diagnostic-item">
                    <span class="diagnostic-label">
                        Atsako laikas
                    </span>

                    <span class="diagnostic-value">
                        ${formatResponseTime(device.response_time_ms)}
                    </span>
                </div>

                <div class="diagnostic-item">
                    <span class="diagnostic-label">
                        Paskutinis atnaujinimas
                    </span>

                    <span
                        class="diagnostic-value"
                        title="${formatDateTime(device.last_update)}"
                    >
                        ${getRelativeTime(device.last_update)}
                    </span>
                </div>

                <div class="diagnostic-item">
                    <span class="diagnostic-label">
                        Busena
                    </span>

                    <span class="diagnostic-value">
                        ${escapeHtml(device.state || "--")}
                    </span>
                </div>

            </div>

            <div class="dashboard-main-grid">

                ${createPhaseTable(
                    "Itampa",
                    device.voltage,
                    "V",
                    1
                )}

                ${createPhaseTable(
                    "Srove",
                    device.current,
                    "A",
                    2
                )}

            </div>

            <section class="dashboard-panel">

                <div class="dashboard-panel-header">
                    <h3>Galia</h3>
                </div>

                <div class="power-grid">

                    ${createPowerCard(
                        "Aktyvioji galia",
                        "bi-lightning-fill",
                        device.active_power?.total,
                        "kW",
                        "active-power"
                    )}

                    ${createPowerCard(
                        "Reaktyvioji galia",
                        "bi-activity",
                        device.reactive_power?.total,
                        "kvar",
                        "reactive-power"
                    )}

                    ${createPowerCard(
                        "Pilnutine galia",
                        "bi-bounding-box",
                        device.apparent_power?.total,
                        "kVA",
                        "apparent-power"
                    )}

                    ${createPowerCard(
                        "Galios koeficientas",
                        "bi-speedometer",
                        device.power_factor?.total,
                        "",
                        "power-factor",
                        3
                    )}

                    ${createPowerCard(
                        "Dažnis",
                        "bi-soundwave",
                        device.frequency,
                        "Hz",
                        "frequency",
                        2
                    )}

                </div>

            </section>

            <section class="dashboard-panel">

                <div class="dashboard-panel-header">
                    <h3>Energija</h3>
                </div>

                <div class="energy-grid">

                    <div class="energy-card">
                        <div class="energy-card-title">
                            Aktyvioji energija
                        </div>

                        ${createEnergyRow(
                            "Importas",
                            device.energy?.import_active,
                            "kWh"
                        )}

                        ${createEnergyRow(
                            "Eksportas",
                            device.energy?.export_active,
                            "kWh"
                        )}
                    </div>

                    <div class="energy-card">
                        <div class="energy-card-title">
                            Reaktyvioji energija
                        </div>

                        ${createEnergyRow(
                            "Importas",
                            device.energy?.import_reactive,
                            "kvarh"
                        )}

                        ${createEnergyRow(
                            "Eksportas",
                            device.energy?.export_reactive,
                            "kvarh"
                        )}
                    </div>

                </div>

            </section>

        </section>
    `;
}


/* ------------------------------------------------------------------
 * Error and empty states
 * ------------------------------------------------------------------ */

function renderEmptyDashboard() {
    const tabs = document.getElementById("meter-tabs");
    const device = document.getElementById("device");

    if (tabs) {
        tabs.innerHTML = "";
    }

    if (device) {
        device.innerHTML = `
            <div class="dashboard-message">
                <i class="bi bi-cpu"></i>

                <h3>Nera sukonfiguruotu skaitikliu</h3>

                <p>
                    Pridekite pirma skaitikli per Meters puslapi.
                </p>
            </div>
        `;
    }
}


function renderConnectionError(error) {
    const device = document.getElementById("device");

    if (!device) {
        return;
    }

    device.innerHTML = `
        <div class="dashboard-message dashboard-message-error">
            <i class="bi bi-wifi-off"></i>

            <h3>Nepavyko gauti dashboard duomenu</h3>

            <p>
                ${escapeHtml(error?.message || "Nežinoma serverio klaida")}
            </p>
        </div>
    `;
}


/* ------------------------------------------------------------------
 * Data loading
 * ------------------------------------------------------------------ */

function restoreSelectedDevice() {
    const storedValue = localStorage.getItem(
        SELECTED_METER_STORAGE_KEY
    );

    if (storedValue !== null && storedValue !== "") {
        selectedDeviceId = Number(storedValue);
    }
}


function validateSelectedDevice() {
    if (dashboardDevices.length === 0) {
        selectedDeviceId = null;
        return;
    }

    const exists = dashboardDevices.some(
        device => Number(device.id) === Number(selectedDeviceId)
    );

    if (!exists) {
        selectedDeviceId = Number(dashboardDevices[0].id);

        localStorage.setItem(
            SELECTED_METER_STORAGE_KEY,
            String(selectedDeviceId)
        );
    }
}


async function refreshDashboard() {
    if (requestInProgress) {
        return;
    }

    requestInProgress = true;

    try {
        const response = await fetch(
            getDashboardApiUrl(),
            {
                method: "GET",
                headers: {
                    "Accept": "application/json"
                },
                cache: "no-store"
            }
        );

        if (!response.ok) {
            throw new Error(
                `Serverio klaida: HTTP ${response.status}`
            );
        }

        const data = await response.json();

        dashboardDevices = Array.isArray(data.devices)
            ? data.devices
            : [];

        renderSummary(data);

        if (dashboardDevices.length === 0) {
            renderEmptyDashboard();
            return;
        }

        validateSelectedDevice();
        renderMeterTabs();
        renderSelectedDevice();

    } catch (error) {
        console.error(
            "Dashboard refresh failed:",
            error
        );

        renderConnectionError(error);

    } finally {
        requestInProgress = false;
    }
}


/* ------------------------------------------------------------------
 * Start
 * ------------------------------------------------------------------ */

document.addEventListener("DOMContentLoaded", () => {
    restoreSelectedDevice();

    refreshDashboard();

    refreshTimer = window.setInterval(
        refreshDashboard,
        REFRESH_INTERVAL_MS
    );
});


window.addEventListener("beforeunload", () => {
    if (refreshTimer !== null) {
        window.clearInterval(refreshTimer);
        refreshTimer = null;
    }
});
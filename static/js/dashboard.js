const REFRESH_INTERVAL = 1000;

let devices = [];
let selectedDeviceId = null;

async function refreshDashboard() {
    try {

        const response = await fetch(dashboardApiUrl);
        const data = await response.json();

        devices = data.devices || [];

        updateSummary(data);

        if (!devices.length) {
            document.getElementById("meter-tabs").innerHTML = "";
            document.getElementById("device").innerHTML =
                "<div class='alert alert-warning'>No meters configured.</div>";
            return;
        }

        if (selectedDeviceId === null) {
            selectedDeviceId =
                Number(localStorage.getItem("selected_meter")) || devices[0].id;
        }

        let device = devices.find(d => d.id === selectedDeviceId);

        if (!device) {
            device = devices[0];
            selectedDeviceId = device.id;
        }

        localStorage.setItem("selected_meter", selectedDeviceId);

        renderTabs(devices);
        renderDevice(device);

    } catch (error) {

        console.error(error);

        document.getElementById("device").innerHTML =
            "<div class='alert alert-danger'>Unable to connect to server.</div>";
    }
}

function updateSummary(data) {

    const online = document.getElementById("summary-online");
    const offline = document.getElementById("summary-offline");
    const total = document.getElementById("summary-total");

    if (online) online.textContent = data.online;
    if (offline) offline.textContent = data.offline;
    if (total) total.textContent = data.total;
}

function renderTabs(devices) {

    const root = document.getElementById("meter-tabs");

    if (!root) return;

    root.innerHTML = "";

    devices.forEach(device => {

        const div = document.createElement("div");

        div.className =
            "meter-tab" +
            (device.id === selectedDeviceId ? " active" : "");

        div.innerHTML = `
            <div class="meter-name">${device.name}</div>
            <div class="meter-status">
                ${device.connected ? "🟢 Online" : "🔴 Offline"}
            </div>
        `;

        div.onclick = () => {

            selectedDeviceId = device.id;

            localStorage.setItem(
                "selected_meter",
                selectedDeviceId
            );

            renderTabs(devices);

            renderDevice(device);
        };

        root.appendChild(div);
    });
}

function value(v, unit = "") {

    if (v === null || v === undefined)
        return "--";

    return Number(v).toFixed(2) + " " + unit;
}

function renderDevice(device) {

    const root = document.getElementById("device");

    if (!root) return;

    root.innerHTML = `

<div class="measurements">

<div class="measurement-card">
<div class="measurement-title">Voltage L1</div>
<div class="measurement-value">${value(device.voltage.l1,"V")}</div>
</div>

<div class="measurement-card">
<div class="measurement-title">Voltage L2</div>
<div class="measurement-value">${value(device.voltage.l2,"V")}</div>
</div>

<div class="measurement-card">
<div class="measurement-title">Voltage L3</div>
<div class="measurement-value">${value(device.voltage.l3,"V")}</div>
</div>

<div class="measurement-card">
<div class="measurement-title">Current</div>
<div class="measurement-value">${value(device.current.total,"A")}</div>
</div>

<div class="measurement-card">
<div class="measurement-title">Active Power</div>
<div class="measurement-value">${value(device.active_power.total,"kW")}</div>
</div>

<div class="measurement-card">
<div class="measurement-title">Reactive Power</div>
<div class="measurement-value">${value(device.reactive_power.total,"kvar")}</div>
</div>

<div class="measurement-card">
<div class="measurement-title">Power Factor</div>
<div class="measurement-value">${value(device.power_factor.total)}</div>
</div>

<div class="measurement-card">
<div class="measurement-title">Frequency</div>
<div class="measurement-value">${value(device.frequency,"Hz")}</div>
</div>

<div class="measurement-card">
<div class="measurement-title">Energy Import</div>
<div class="measurement-value">${value(device.energy.import_active,"kWh")}</div>
</div>

</div>

`;
}

document.addEventListener("DOMContentLoaded", () => {

    refreshDashboard();

    setInterval(refreshDashboard, REFRESH_INTERVAL);

});
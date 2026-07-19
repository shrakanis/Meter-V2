/*
 * static/js/device.js
 *
 * Energy Monitor V2
 *
 * Live single-device page and Chart.js graph.
 */

"use strict";


const DEVICE_REFRESH_INTERVAL_MS = 1000;
const LIVE_CHART_MAX_POINTS = 300;

let deviceRefreshTimer = null;
let deviceRequestInProgress = false;

let liveChart = null;
let selectedChartType = "voltage";

const chartHistory = {
    labels: [],

    voltageL1: [],
    voltageL2: [],
    voltageL3: [],

    currentL1: [],
    currentL2: [],
    currentL3: [],

    activePowerL1: [],
    activePowerL2: [],
    activePowerL3: [],

    reactivePowerL1: [],
    reactivePowerL2: [],
    reactivePowerL3: [],
};


/* ==========================================================
 * Helpers
 * ========================================================== */


function isValidNumber(value) {
    return (
        value !== null &&
        value !== undefined &&
        value !== "" &&
        Number.isFinite(Number(value))
    );
}


function numberOrNull(value) {
    if (!isValidNumber(value)) {
        return null;
    }

    return Number(value);
}


function formatNumber(
    value,
    decimals = 2
) {
    if (!isValidNumber(value)) {
        return "--";
    }

    return Number(value).toFixed(decimals);
}


function setText(
    elementId,
    value,
    decimals = null
) {
    const element = document.getElementById(
        elementId
    );

    if (!element) {
        return;
    }

    if (
        decimals !== null &&
        isValidNumber(value)
    ) {
        element.textContent = formatNumber(
            value,
            decimals
        );

        return;
    }

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {
        element.textContent = "--";
        return;
    }

    element.textContent = String(value);
}


function formatDateTime(value) {
    if (!value) {
        return "--";
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return String(value);
    }

    return date.toLocaleString("lt-LT");
}


function currentTimeLabel() {
    return new Date().toLocaleTimeString(
        "lt-LT",
        {
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
        }
    );
}


/* ==========================================================
 * Status
 * ========================================================== */


function updateStatus(connected) {
    const badge = document.getElementById(
        "device-status"
    );

    if (!badge) {
        return;
    }

    badge.classList.remove(
        "bg-success",
        "bg-danger"
    );

    if (connected) {
        badge.classList.add("bg-success");
        badge.textContent = "ONLINE";
    } else {
        badge.classList.add("bg-danger");
        badge.textContent = "OFFLINE";
    }
}


function updateError(message) {
    const errorBox = document.getElementById(
        "device-error"
    );

    const errorText = document.getElementById(
        "device-error-text"
    );

    if (!errorBox || !errorText) {
        return;
    }

    if (message) {
        errorText.textContent = message;

        errorBox.classList.remove(
            "d-none"
        );
    } else {
        errorText.textContent = "";

        errorBox.classList.add(
            "d-none"
        );
    }
}


/* ==========================================================
 * Measurements
 * ========================================================== */


function updateMeasurements(data) {
    const voltage = data.voltage || {};
    const current = data.current || {};
    const active = data.active_power || {};
    const reactive = data.reactive_power || {};
    const powerFactor = data.power_factor || {};
    const energy = data.energy || {};

    setText(
        "voltage-l1",
        voltage.l1,
        1
    );

    setText(
        "voltage-l2",
        voltage.l2,
        1
    );

    setText(
        "voltage-l3",
        voltage.l3,
        1
    );


    setText(
        "current-l1",
        current.l1,
        2
    );

    setText(
        "current-l2",
        current.l2,
        2
    );

    setText(
        "current-l3",
        current.l3,
        2
    );


    setText(
        "active-l1",
        active.l1,
        2
    );

    setText(
        "active-l2",
        active.l2,
        2
    );

    setText(
        "active-l3",
        active.l3,
        2
    );


    setText(
        "reactive-l1",
        reactive.l1,
        2
    );

    setText(
        "reactive-l2",
        reactive.l2,
        2
    );

    setText(
        "reactive-l3",
        reactive.l3,
        2
    );


    setText(
        "pf-l1",
        powerFactor.l1,
        3
    );

    setText(
        "pf-l2",
        powerFactor.l2,
        3
    );

    setText(
        "pf-l3",
        powerFactor.l3,
        3
    );


    setText(
        "total-active",
        active.total,
        2
    );

    setText(
        "total-reactive",
        reactive.total,
        2
    );

    setText(
        "frequency",
        data.frequency,
        2
    );

    setText(
        "pf-total",
        powerFactor.total,
        3
    );


    setText(
        "energy-import",
        energy.import_active,
        2
    );

    setText(
        "energy-export",
        energy.export_active,
        2
    );
}


/* ==========================================================
 * Device diagnostics
 * ========================================================== */


function updateDiagnostics(data) {
    updateStatus(
        Boolean(data.connected)
    );

    setText(
        "response-time",
        data.response_time_ms,
        1
    );

    setText(
        "device-state",
        data.state
    );

    setText(
        "last-update",
        formatDateTime(
            data.last_update
        )
    );

    updateError(
        data.last_error
    );
}


/* ==========================================================
 * Live chart data
 * ========================================================== */


function appendChartData(data) {
    const voltage = data.voltage || {};
    const current = data.current || {};
    const activePower = data.active_power || {};
    const reactivePower = data.reactive_power || {};

    chartHistory.labels.push(
        currentTimeLabel()
    );

    chartHistory.voltageL1.push(
        numberOrNull(voltage.l1)
    );

    chartHistory.voltageL2.push(
        numberOrNull(voltage.l2)
    );

    chartHistory.voltageL3.push(
        numberOrNull(voltage.l3)
    );

    chartHistory.currentL1.push(
        numberOrNull(current.l1)
    );

    chartHistory.currentL2.push(
        numberOrNull(current.l2)
    );

    chartHistory.currentL3.push(
        numberOrNull(current.l3)
    );

    chartHistory.activePowerL1.push(
        numberOrNull(activePower.l1)
    );

    chartHistory.activePowerL2.push(
        numberOrNull(activePower.l2)
    );

    chartHistory.activePowerL3.push(
        numberOrNull(activePower.l3)
    );

    chartHistory.reactivePowerL1.push(
        numberOrNull(reactivePower.l1)
    );

    chartHistory.reactivePowerL2.push(
        numberOrNull(reactivePower.l2)
    );

    chartHistory.reactivePowerL3.push(
        numberOrNull(reactivePower.l3)
    );

    trimChartHistory();
}


function trimArray(array) {
    while (
        array.length >
        LIVE_CHART_MAX_POINTS
    ) {
        array.shift();
    }
}


function trimChartHistory() {
    trimArray(chartHistory.labels);

    trimArray(chartHistory.voltageL1);
    trimArray(chartHistory.voltageL2);
    trimArray(chartHistory.voltageL3);

    trimArray(chartHistory.currentL1);
    trimArray(chartHistory.currentL2);
    trimArray(chartHistory.currentL3);

    trimArray(chartHistory.activePowerL1);
    trimArray(chartHistory.activePowerL2);
    trimArray(chartHistory.activePowerL3);

    trimArray(chartHistory.reactivePowerL1);
    trimArray(chartHistory.reactivePowerL2);
    trimArray(chartHistory.reactivePowerL3);
}


/* ==========================================================
 * Live chart configuration
 * ========================================================== */


function phaseDatasets(l1, l2, l3) {
    return [
        {
            label: "L1",
            data: l1,
            borderColor: "#e53935",
            backgroundColor: "#e53935",
            borderWidth: 2,
            pointRadius: 0,
            tension: 0.15,
            spanGaps: true,
        },
        {
            label: "L2",
            data: l2,
            borderColor: "#fbc02d",
            backgroundColor: "#fbc02d",
            borderWidth: 2,
            pointRadius: 0,
            tension: 0.15,
            spanGaps: true,
        },
        {
            label: "L3",
            data: l3,
            borderColor: "#1e88e5",
            backgroundColor: "#1e88e5",
            borderWidth: 2,
            pointRadius: 0,
            tension: 0.15,
            spanGaps: true,
        },
    ];
}


function chartDatasets() {
    if (selectedChartType === "current") {
        return phaseDatasets(
            chartHistory.currentL1,
            chartHistory.currentL2,
            chartHistory.currentL3
        );
    }

    if (selectedChartType === "active-power") {
        return phaseDatasets(
            chartHistory.activePowerL1,
            chartHistory.activePowerL2,
            chartHistory.activePowerL3
        );
    }

    if (selectedChartType === "reactive-power") {
        return phaseDatasets(
            chartHistory.reactivePowerL1,
            chartHistory.reactivePowerL2,
            chartHistory.reactivePowerL3
        );
    }

    return phaseDatasets(
        chartHistory.voltageL1,
        chartHistory.voltageL2,
        chartHistory.voltageL3
    );
}


function chartUnit() {
    if (selectedChartType === "current") {
        return "A";
    }

    if (selectedChartType === "active-power") {
        return "kW";
    }

    if (selectedChartType === "reactive-power") {
        return "kvar";
    }

    return "V";
}


function chartTitle() {
    if (selectedChartType === "current") {
        return "Live current";
    }

    if (selectedChartType === "active-power") {
        return "Live active power";
    }

    if (selectedChartType === "reactive-power") {
        return "Live reactive power";
    }

    return "Live voltage";
}


function initializeChart() {
    const canvas = document.getElementById(
        "live-device-chart"
    );

    if (!canvas) {
        return;
    }

    if (typeof Chart === "undefined") {
        console.error(
            "Chart.js is not loaded."
        );

        return;
    }

    liveChart = new Chart(
        canvas,
        {
            type: "line",

            data: {
                labels: chartHistory.labels,
                datasets: chartDatasets(),
            },

            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: false,
                normalized: true,

                interaction: {
                    mode: "index",
                    intersect: false,
                },

                plugins: {
                    legend: {
                        display: true,

                        labels: {
                            color: "#dddddd",
                            usePointStyle: true,
                            boxWidth: 8,
                        },
                    },

                    title: {
                        display: true,
                        text: chartTitle(),
                        color: "#ffffff",
                        font: {
                            size: 16,
                        },
                    },

                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                const value =
                                    context.parsed.y;

                                if (
                                    value === null ||
                                    value === undefined
                                ) {
                                    return (
                                        context.dataset.label +
                                        ": --"
                                    );
                                }

                                return (
                                    context.dataset.label +
                                    ": " +
                                    value.toFixed(2) +
                                    " " +
                                    chartUnit()
                                );
                            },
                        },
                    },
                },

                scales: {
                    x: {
                        grid: {
                            color: "rgba(255,255,255,0.05)",
                        },

                        ticks: {
                            color: "#999999",
                            maxTicksLimit: 10,
                        },
                    },

                    y: {
                        grid: {
                            color: "rgba(255,255,255,0.08)",
                        },

                        ticks: {
                            color: "#999999",

                            callback: function (value) {
                                return (
                                    value +
                                    " " +
                                    chartUnit()
                                );
                            },
                        },
                    },
                },
            },
        }
    );
}


function updateChart() {
    if (!liveChart) {
        return;
    }

    liveChart.data.labels =
        chartHistory.labels;

    liveChart.data.datasets =
        chartDatasets();

    liveChart.options.plugins.title.text =
        chartTitle();

    liveChart.update("none");
}


/* ==========================================================
 * Chart buttons
 * ========================================================== */


function selectChartType(type) {
    selectedChartType = type;

    document
        .querySelectorAll(
            "[data-chart-type]"
        )
        .forEach(
            function (button) {
                button.classList.toggle(
                    "btn-primary",
                    button.dataset.chartType === type
                );

                button.classList.toggle(
                    "btn-outline-secondary",
                    button.dataset.chartType !== type
                );
            }
        );

    updateChart();
}


function initializeChartButtons() {
    document
        .querySelectorAll(
            "[data-chart-type]"
        )
        .forEach(
            function (button) {
                button.addEventListener(
                    "click",
                    function () {
                        selectChartType(
                            button.dataset.chartType
                        );
                    }
                );
            }
        );

    selectChartType(
        selectedChartType
    );
}


/* ==========================================================
 * API
 * ========================================================== */


async function refreshDevice() {
    if (deviceRequestInProgress) {
        return;
    }

    deviceRequestInProgress = true;

    try {
        const response = await fetch(
            deviceApiUrl,
            {
                method: "GET",

                headers: {
                    "Accept": "application/json",
                },

                cache: "no-store",
            }
        );

        if (!response.ok) {
            throw new Error(
                `HTTP ${response.status}`
            );
        }

        const data = await response.json();

        updateDiagnostics(data);
        updateMeasurements(data);

        appendChartData(data);
        updateChart();

    } catch (error) {
        console.error(
            "Device refresh failed:",
            error
        );

        updateStatus(false);

        updateError(
            `API connection error: ${error.message}`
        );

    } finally {
        deviceRequestInProgress = false;
    }
}


/* ==========================================================
 * Start and stop
 * ========================================================== */


document.addEventListener(
    "DOMContentLoaded",
    function () {
        initializeChart();
        initializeChartButtons();

        refreshDevice();

        deviceRefreshTimer =
            window.setInterval(
                refreshDevice,
                DEVICE_REFRESH_INTERVAL_MS
            );
    }
);


window.addEventListener(
    "beforeunload",
    function () {
        if (
            deviceRefreshTimer !== null
        ) {
            window.clearInterval(
                deviceRefreshTimer
            );

            deviceRefreshTimer = null;
        }

        if (liveChart) {
            liveChart.destroy();
            liveChart = null;
        }
    }
);
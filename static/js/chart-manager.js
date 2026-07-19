/*
 * static/js/chart-manager.js
 *
 * Energy Monitor V2
 *
 * Reusable Chart.js manager with single and multi-dataset support.
 */

"use strict";


class ChartManager {

    constructor(options = {}) {
        this.canvasId = options.canvasId || "history-chart";
        this.emptyElementId = options.emptyElementId || null;
        this.loadingElementId = options.loadingElementId || null;

        this.title = options.title || "";
        this.unit = options.unit || "";
        this.lineLabel = options.lineLabel || "Value";
        this.lineColor = options.lineColor || "#0d6efd";
        this.backgroundColor = options.backgroundColor || "rgba(13, 110, 253, 0.10)";

        this.enableZoom = options.enableZoom !== false;
        this.enablePan = options.enablePan !== false;
        this.fill = options.fill === true;
        this.decimals = Number.isInteger(options.decimals) ? options.decimals : 2;
        this.maxTicks = Number.isInteger(options.maxTicks) ? options.maxTicks : 12;

        this.chart = null;
        this.labels = [];
        this.datasets = [];
        this.values = []; // Backward-compatible alias for the first dataset.
        this.initialized = false;
        this.firstRender = true;

        this.palette = [
            "#e53935", // L1
            "#fbc02d", // L2
            "#1e88e5", // L3
            "#8e24aa",
            "#00897b",
            "#fb8c00",
            "#6d4c41",
            "#546e7a",
        ];
    }

    getCanvas() {
        return document.getElementById(this.canvasId);
    }

    getEmptyElement() {
        return this.emptyElementId
            ? document.getElementById(this.emptyElementId)
            : null;
    }

    getLoadingElement() {
        return this.loadingElementId
            ? document.getElementById(this.loadingElementId)
            : null;
    }

    initialize() {
        if (this.initialized) {
            return true;
        }

        if (typeof Chart === "undefined") {
            console.error("Chart.js is not loaded.");
            return false;
        }

        const canvas = this.getCanvas();
        if (!canvas) {
            console.error(`Canvas element '${this.canvasId}' was not found.`);
            return false;
        }

        this.destroy();

        const context = canvas.getContext("2d");
        if (!context) {
            console.error("Cannot create 2D chart context.");
            return false;
        }

        this.chart = new Chart(context, this.createConfiguration());
        this.initialized = true;
        return true;
    }

    createConfiguration() {
        return {
            type: "line",
            data: {
                labels: this.labels,
                datasets: this.chartDatasets(),
            },
            options: this.createOptions(),
        };
    }

    normalizeValues(values) {
        const normalized = Array.isArray(values)
            ? values.map((value) => {
                if (value === null || value === undefined || value === "") {
                    return null;
                }
                const number = Number(value);
                return Number.isFinite(number) ? number : null;
            })
            : [];

        while (normalized.length < this.labels.length) {
            normalized.push(null);
        }

        return normalized.slice(0, this.labels.length);
    }

    normalizeDatasets(datasets) {
        if (!Array.isArray(datasets)) {
            return [];
        }

        return datasets.map((dataset, index) => ({
            field: dataset.field || `dataset_${index + 1}`,
            label: dataset.label || dataset.field || `Series ${index + 1}`,
            values: this.normalizeValues(dataset.values ?? dataset.data),
            color: dataset.color || this.palette[index % this.palette.length],
            backgroundColor: dataset.backgroundColor || null,
            fill: dataset.fill === true,
        }));
    }

    createDataset(dataset, index) {
        const color = dataset.color || this.palette[index % this.palette.length];

        return {
            label: dataset.label,
            data: dataset.values,
            borderColor: color,
            backgroundColor: dataset.backgroundColor || color,
            borderWidth: 2,
            pointRadius: 0,
            pointHoverRadius: 4,
            pointHitRadius: 12,
            tension: 0.15,
            fill: dataset.fill === true,
            spanGaps: true,
            normalized: true,
        };
    }

    chartDatasets() {
        const source = this.datasets.length > 0
            ? this.datasets
            : [{
                field: "value",
                label: this.lineLabel,
                values: this.values,
                color: this.lineColor,
                backgroundColor: this.backgroundColor,
                fill: this.fill,
            }];

        return source.map((dataset, index) => this.createDataset(dataset, index));
    }

    createOptions() {
        return {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: this.firstRender ? 300 : 0 },
            interaction: { mode: "index", intersect: false },
            parsing: true,
            normalized: true,
            plugins: {
                legend: {
                    display: true,
                    labels: {
                        usePointStyle: true,
                        pointStyle: "line",
                        boxWidth: 20,
                        color: "#495057",
                        font: { size: 12, weight: "500" },
                    },
                },
                title: {
                    display: Boolean(this.title),
                    text: this.title,
                    color: "#212529",
                    padding: { top: 4, bottom: 18 },
                    font: { size: 16, weight: "600" },
                },
                tooltip: {
                    enabled: true,
                    displayColors: true,
                    callbacks: {
                        title: (items) => {
                            if (!items || items.length === 0) {
                                return "";
                            }
                            return this.formatTooltipTitle(items[0].label);
                        },
                        label: (context) => (
                            `${context.dataset.label}: ${this.formatValue(context.parsed.y)}`
                        ),
                    },
                },
                decimation: {
                    enabled: true,
                    algorithm: "lttb",
                    samples: 1000,
                    threshold: 1500,
                },
                zoom: this.createZoomOptions(),
            },
            scales: {
                x: {
                    type: "category",
                    offset: false,
                    grid: { display: true, color: "rgba(0, 0, 0, 0.05)" },
                    border: { color: "rgba(0, 0, 0, 0.15)" },
                    ticks: {
                        color: "#6c757d",
                        maxTicksLimit: this.maxTicks,
                        maxRotation: 0,
                        autoSkip: true,
                        callback: (value) => this.formatAxisLabel(this.labels[value]),
                    },
                    title: {
                        display: true,
                        text: "Time",
                        color: "#6c757d",
                        font: { weight: "500" },
                    },
                },
                y: {
                    beginAtZero: false,
                    grace: "5%",
                    grid: { color: "rgba(0, 0, 0, 0.06)" },
                    border: { color: "rgba(0, 0, 0, 0.15)" },
                    ticks: {
                        color: "#6c757d",
                        callback: (value) => this.formatValue(value),
                    },
                    title: {
                        display: Boolean(this.unit),
                        text: this.unit,
                        color: "#6c757d",
                        font: { weight: "500" },
                    },
                },
            },
        };
    }

    createZoomOptions() {
        return {
            limits: { x: { min: "original", max: "original", minRange: 5 } },
            pan: {
                enabled: this.enablePan,
                mode: "x",
                modifierKey: null,
                threshold: 5,
            },
            zoom: {
                wheel: { enabled: this.enableZoom, speed: 0.08 },
                pinch: { enabled: this.enableZoom },
                drag: { enabled: false },
                mode: "x",
            },
        };
    }

    formatValue(value) {
        if (value === null || value === undefined || !Number.isFinite(Number(value))) {
            return "--";
        }

        const formatted = Number(value).toFixed(this.decimals);
        return this.unit ? `${formatted} ${this.unit}` : formatted;
    }

    formatAxisLabel(value) {
        if (!value) {
            return "";
        }

        const date = new Date(value);
        if (Number.isNaN(date.getTime())) {
            return String(value);
        }

        return date.toLocaleTimeString("lt-LT", {
            hour: "2-digit",
            minute: "2-digit",
        });
    }

    formatTooltipTitle(value) {
        if (!value) {
            return "";
        }

        const date = new Date(value);
        return Number.isNaN(date.getTime())
            ? String(value)
            : date.toLocaleString("lt-LT");
    }

    applyData() {
        this.updateEmptyState();

        if (!this.initialized) {
            this.initialize();
        }

        if (!this.chart) {
            return;
        }

        this.chart.data.labels = this.labels;
        this.chart.data.datasets = this.chartDatasets();
        this.chart.update(this.firstRender ? undefined : "none");
        this.firstRender = false;
    }

    setData(labels, values) {
        this.labels = Array.isArray(labels) ? [...labels] : [];
        this.values = this.normalizeValues(values);
        this.datasets = [{
            field: "value",
            label: this.lineLabel,
            values: this.values,
            color: this.lineColor,
            backgroundColor: this.backgroundColor,
            fill: this.fill,
        }];
        this.applyData();
    }

    setDatasets(labels, datasets) {
        this.labels = Array.isArray(labels) ? [...labels] : [];
        this.datasets = this.normalizeDatasets(datasets);
        this.values = this.datasets.length > 0 ? this.datasets[0].values : [];
        this.applyData();
    }

    clear() {
        this.labels = [];
        this.values = [];
        this.datasets = [];

        if (this.chart) {
            this.chart.data.labels = [];
            this.chart.data.datasets = [];
            this.chart.update("none");
        }

        this.updateEmptyState();
    }

    hasData() {
        return this.datasets.some((dataset) => dataset.values.some(
            (value) => value !== null && value !== undefined && Number.isFinite(Number(value))
        ));
    }

    setTitle(title) {
        this.title = title || "";
        if (this.chart) {
            this.chart.options.plugins.title.display = Boolean(this.title);
            this.chart.options.plugins.title.text = this.title;
            this.chart.update("none");
        }
    }

    setUnit(unit) {
        this.unit = unit || "";
        if (this.chart) {
            this.chart.options.scales.y.title.display = Boolean(this.unit);
            this.chart.options.scales.y.title.text = this.unit;
            this.chart.update("none");
        }
    }

    setLineLabel(label) {
        this.lineLabel = label || "Value";
        if (this.datasets.length === 1) {
            this.datasets[0].label = this.lineLabel;
        }
        if (this.chart && this.chart.data.datasets[0]) {
            this.chart.data.datasets[0].label = this.lineLabel;
            this.chart.update("none");
        }
    }

    setDecimals(decimals) {
        if (!Number.isInteger(decimals) || decimals < 0 || decimals > 8) {
            return;
        }
        this.decimals = decimals;
        if (this.chart) {
            this.chart.update("none");
        }
    }

    setLineColor(lineColor, backgroundColor = null) {
        if (lineColor) {
            this.lineColor = lineColor;
        }
        if (backgroundColor) {
            this.backgroundColor = backgroundColor;
        }
        if (this.datasets.length === 1) {
            this.datasets[0].color = this.lineColor;
            this.datasets[0].backgroundColor = this.backgroundColor;
        }
        this.applyData();
    }

    setFill(fill) {
        this.fill = Boolean(fill);
        if (this.datasets.length === 1) {
            this.datasets[0].fill = this.fill;
        }
        this.applyData();
    }

    showLoading() {
        const element = this.getLoadingElement();
        if (element) {
            element.classList.remove("d-none");
        }
    }

    hideLoading() {
        const element = this.getLoadingElement();
        if (element) {
            element.classList.add("d-none");
        }
    }

    showEmpty() {
        const element = this.getEmptyElement();
        if (element) {
            element.classList.remove("d-none");
        }
        const canvas = this.getCanvas();
        if (canvas) {
            canvas.style.visibility = "hidden";
        }
    }

    hideEmpty() {
        const element = this.getEmptyElement();
        if (element) {
            element.classList.add("d-none");
        }
        const canvas = this.getCanvas();
        if (canvas) {
            canvas.style.visibility = "visible";
        }
    }

    updateEmptyState() {
        if (this.hasData()) {
            this.hideEmpty();
        } else {
            this.showEmpty();
        }
    }

    resetZoom() {
        if (this.chart && typeof this.chart.resetZoom === "function") {
            this.chart.resetZoom();
        }
    }

    zoomIn() {
        if (this.chart && typeof this.chart.zoom === "function") {
            this.chart.zoom(1.2);
        }
    }

    zoomOut() {
        if (this.chart && typeof this.chart.zoom === "function") {
            this.chart.zoom(0.8);
        }
    }

    panLeft() {
        if (this.chart && typeof this.chart.pan === "function") {
            this.chart.pan({ x: 100, y: 0 });
        }
    }

    panRight() {
        if (this.chart && typeof this.chart.pan === "function") {
            this.chart.pan({ x: -100, y: 0 });
        }
    }

    numericValues() {
        return this.datasets.flatMap((dataset) => dataset.values).filter(
            (value) => value !== null && value !== undefined && Number.isFinite(Number(value))
        ).map(Number);
    }

    statistics() {
        const values = this.numericValues();
        if (values.length === 0) {
            return {
                count: 0,
                minimum: null,
                maximum: null,
                average: null,
                latest: null,
            };
        }

        let minimum = values[0];
        let maximum = values[0];
        let total = 0;

        for (const value of values) {
            minimum = Math.min(minimum, value);
            maximum = Math.max(maximum, value);
            total += value;
        }

        let latest = null;
        for (let index = this.labels.length - 1; index >= 0 && latest === null; index -= 1) {
            for (const dataset of this.datasets) {
                const value = dataset.values[index];
                if (value !== null && value !== undefined && Number.isFinite(Number(value))) {
                    latest = Number(value);
                    break;
                }
            }
        }

        return {
            count: values.length,
            minimum,
            maximum,
            average: total / values.length,
            latest,
        };
    }

    datasetStatistics() {
        return this.datasets.map((dataset) => {
            const values = dataset.values.filter(
                (value) => value !== null && value !== undefined && Number.isFinite(Number(value))
            ).map(Number);

            if (values.length === 0) {
                return {
                    field: dataset.field,
                    label: dataset.label,
                    count: 0,
                    minimum: null,
                    maximum: null,
                    average: null,
                    latest: null,
                };
            }

            return {
                field: dataset.field,
                label: dataset.label,
                count: values.length,
                minimum: Math.min(...values),
                maximum: Math.max(...values),
                average: values.reduce((sum, value) => sum + value, 0) / values.length,
                latest: values[values.length - 1],
            };
        });
    }

    firstLabel() {
        return this.labels.length > 0 ? this.labels[0] : null;
    }

    lastLabel() {
        return this.labels.length > 0 ? this.labels[this.labels.length - 1] : null;
    }

    toRows() {
        return this.labels.map((timestamp, index) => {
            const row = { timestamp };
            for (const dataset of this.datasets) {
                row[dataset.field] = dataset.values[index] ?? null;
            }
            return row;
        });
    }

    escapeCsvValue(value) {
        if (value === null || value === undefined) {
            return "";
        }
        const text = String(value);
        if (text.includes(",") || text.includes("\"") || text.includes("\n")) {
            return `"${text.replaceAll("\"", "\"\"")}"`;
        }
        return text;
    }

    toCsv(timestampHeader = "Timestamp", valueHeader = null) {
        const datasets = this.datasets.length > 0
            ? this.datasets
            : [{ field: "value", label: valueHeader || this.lineLabel, values: this.values }];

        const headers = [
            timestampHeader,
            ...datasets.map((dataset) => dataset.label || dataset.field),
        ];

        const lines = [headers.map((value) => this.escapeCsvValue(value)).join(",")];

        for (let index = 0; index < this.labels.length; index += 1) {
            lines.push([
                this.labels[index],
                ...datasets.map((dataset) => dataset.values[index] ?? null),
            ].map((value) => this.escapeCsvValue(value)).join(","));
        }

        return lines.join("\n");
    }

    downloadCsv(filename = "history.csv") {
        const blob = new Blob([this.toCsv()], { type: "text/csv;charset=utf-8" });
        const url = URL.createObjectURL(blob);
        const anchor = document.createElement("a");
        anchor.href = url;
        anchor.download = filename;
        document.body.appendChild(anchor);
        anchor.click();
        anchor.remove();
        URL.revokeObjectURL(url);
    }

    toBase64Image() {
        return this.chart ? this.chart.toBase64Image("image/png", 1) : null;
    }

    downloadImage(filename = "chart.png") {
        const image = this.toBase64Image();
        if (!image) {
            return;
        }
        const anchor = document.createElement("a");
        anchor.href = image;
        anchor.download = filename;
        document.body.appendChild(anchor);
        anchor.click();
        anchor.remove();
    }

    resize() {
        if (this.chart) {
            this.chart.resize();
        }
    }

    destroy() {
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }
        this.initialized = false;
    }
}

window.ChartManager = ChartManager;

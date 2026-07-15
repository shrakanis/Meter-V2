/*
 * static/js/chart-manager.js
 *
 * Energy Monitor V2
 *
 * Reusable Chart.js manager.
 *
 * Part 1 of 2
 */

"use strict";


class ChartManager {

    constructor(options = {}) {

        this.canvasId =
            options.canvasId || "history-chart";

        this.emptyElementId =
            options.emptyElementId || null;

        this.loadingElementId =
            options.loadingElementId || null;

        this.title =
            options.title || "";

        this.unit =
            options.unit || "";

        this.lineLabel =
            options.lineLabel || "Value";

        this.lineColor =
            options.lineColor || "#0d6efd";

        this.backgroundColor =
            options.backgroundColor ||
            "rgba(13, 110, 253, 0.10)";

        this.enableZoom =
            options.enableZoom !== false;

        this.enablePan =
            options.enablePan !== false;

        this.fill =
            options.fill === true;

        this.decimals =
            Number.isInteger(options.decimals)
                ? options.decimals
                : 2;

        this.maxTicks =
            Number.isInteger(options.maxTicks)
                ? options.maxTicks
                : 12;

        this.chart = null;

        this.labels = [];

        this.values = [];

        this.initialized = false;

        this.firstRender = true;
    }


    /* ======================================================
     * DOM helpers
     * ====================================================== */


    getCanvas() {

        return document.getElementById(
            this.canvasId
        );
    }


    getEmptyElement() {

        if (!this.emptyElementId) {
            return null;
        }

        return document.getElementById(
            this.emptyElementId
        );
    }


    getLoadingElement() {

        if (!this.loadingElementId) {
            return null;
        }

        return document.getElementById(
            this.loadingElementId
        );
    }


    /* ======================================================
     * Initialization
     * ====================================================== */


    initialize() {

        if (this.initialized) {
            return true;
        }

        if (typeof Chart === "undefined") {

            console.error(
                "Chart.js is not loaded."
            );

            return false;
        }

        const canvas = this.getCanvas();

        if (!canvas) {

            console.error(
                `Canvas element '${this.canvasId}' was not found.`
            );

            return false;
        }

        this.destroy();

        const context =
            canvas.getContext("2d");

        if (!context) {

            console.error(
                "Cannot create 2D chart context."
            );

            return false;
        }

        this.chart = new Chart(
            context,
            this.createConfiguration()
        );

        this.initialized = true;

        return true;
    }


    /* ======================================================
     * Configuration
     * ====================================================== */


    createConfiguration() {

        return {

            type: "line",

            data: {

                labels: this.labels,

                datasets: [
                    this.createDataset()
                ],
            },

            options: this.createOptions(),
        };
    }


    createDataset() {

        return {

            label: this.lineLabel,

            data: this.values,

            borderColor:
                this.lineColor,

            backgroundColor:
                this.backgroundColor,

            borderWidth: 2,

            pointRadius: 0,

            pointHoverRadius: 4,

            pointHitRadius: 12,

            tension: 0.15,

            fill: this.fill,

            spanGaps: true,

            normalized: true,
        };
    }


    createOptions() {

        return {

            responsive: true,

            maintainAspectRatio: false,

            animation: {

                duration:
                    this.firstRender
                        ? 300
                        : 0,
            },

            interaction: {

                mode: "index",

                intersect: false,
            },

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

                        font: {

                            size: 12,

                            weight: "500",
                        },
                    },
                },

                title: {

                    display:
                        Boolean(this.title),

                    text: this.title,

                    color: "#212529",

                    padding: {

                        top: 4,

                        bottom: 18,
                    },

                    font: {

                        size: 16,

                        weight: "600",
                    },
                },

                tooltip: {

                    enabled: true,

                    displayColors: true,

                    callbacks: {

                        title: (
                            tooltipItems
                        ) => {

                            if (
                                !tooltipItems ||
                                tooltipItems.length === 0
                            ) {
                                return "";
                            }

                            return this.formatTooltipTitle(
                                tooltipItems[0].label
                            );
                        },

                        label: (
                            context
                        ) => {

                            const value =
                                context.parsed.y;

                            return (
                                `${context.dataset.label}: ` +
                                this.formatValue(value)
                            );
                        },
                    },
                },

                decimation: {

                    enabled: true,

                    algorithm: "lttb",

                    samples: 1000,

                    threshold: 1500,
                },

                zoom:
                    this.createZoomOptions(),
            },

            scales: {

                x: {

                    type: "category",

                    offset: false,

                    grid: {

                        display: true,

                        color:
                            "rgba(0, 0, 0, 0.05)",
                    },

                    border: {

                        color:
                            "rgba(0, 0, 0, 0.15)",
                    },

                    ticks: {

                        color: "#6c757d",

                        maxTicksLimit:
                            this.maxTicks,

                        maxRotation: 0,

                        autoSkip: true,

                        callback: (
                            value
                        ) => {

                            const label =
                                this.labels[value];

                            return this.formatAxisLabel(
                                label
                            );
                        },
                    },

                    title: {

                        display: true,

                        text: "Time",

                        color: "#6c757d",

                        font: {

                            weight: "500",
                        },
                    },
                },

                y: {

                    beginAtZero: false,

                    grace: "5%",

                    grid: {

                        color:
                            "rgba(0, 0, 0, 0.06)",
                    },

                    border: {

                        color:
                            "rgba(0, 0, 0, 0.15)",
                    },

                    ticks: {

                        color: "#6c757d",

                        callback: (
                            value
                        ) => {

                            return this.formatValue(
                                value
                            );
                        },
                    },

                    title: {

                        display:
                            Boolean(this.unit),

                        text: this.unit,

                        color: "#6c757d",

                        font: {

                            weight: "500",
                        },
                    },
                },
            },
        };
    }


    createZoomOptions() {

        return {

            limits: {

                x: {

                    min: "original",

                    max: "original",

                    minRange: 5,
                },
            },

            pan: {

                enabled:
                    this.enablePan,

                mode: "x",

                modifierKey: null,

                threshold: 5,
            },

            zoom: {

                wheel: {

                    enabled:
                        this.enableZoom,

                    speed: 0.08,
                },

                pinch: {

                    enabled:
                        this.enableZoom,
                },

                drag: {

                    enabled: false,
                },

                mode: "x",
            },
        };
    }


    /* ======================================================
     * Formatting
     * ====================================================== */


    formatValue(value) {

        if (
            value === null ||
            value === undefined ||
            !Number.isFinite(
                Number(value)
            )
        ) {
            return "--";
        }

        const formatted =
            Number(value).toFixed(
                this.decimals
            );

        if (!this.unit) {
            return formatted;
        }

        return `${formatted} ${this.unit}`;
    }


    formatAxisLabel(value) {

        if (!value) {
            return "";
        }

        const date =
            new Date(value);

        if (
            Number.isNaN(
                date.getTime()
            )
        ) {
            return String(value);
        }

        return date.toLocaleTimeString(
            "lt-LT",
            {

                hour: "2-digit",

                minute: "2-digit",
            }
        );
    }


    formatTooltipTitle(value) {

        if (!value) {
            return "";
        }

        const date =
            new Date(value);

        if (
            Number.isNaN(
                date.getTime()
            )
        ) {
            return String(value);
        }

        return date.toLocaleString(
            "lt-LT"
        );
    }
    /* ======================================================
     * Data
     * ====================================================== */


    setData(
        labels,
        values
    ) {

        this.labels = Array.isArray(labels)
            ? [...labels]
            : [];

        this.values = Array.isArray(values)
            ? values.map(
                (value) => {

                    if (
                        value === null ||
                        value === undefined
                    ) {
                        return null;
                    }

                    const number =
                        Number(value);

                    return Number.isFinite(number)
                        ? number
                        : null;
                }
            )
            : [];

        if (
            this.values.length <
            this.labels.length
        ) {

            while (
                this.values.length <
                this.labels.length
            ) {
                this.values.push(null);
            }
        }

        if (
            this.labels.length <
            this.values.length
        ) {

            this.values =
                this.values.slice(
                    0,
                    this.labels.length
                );
        }

        this.updateEmptyState();

        if (!this.initialized) {

            this.initialize();
        }

        if (!this.chart) {
            return;
        }

        this.chart.data.labels =
            this.labels;

        this.chart.data.datasets[0].data =
            this.values;

        this.chart.update(
            this.firstRender
                ? undefined
                : "none"
        );

        this.firstRender = false;
    }


    clear() {

        this.labels = [];
        this.values = [];

        if (this.chart) {

            this.chart.data.labels = [];

            this.chart.data.datasets[0].data = [];

            this.chart.update("none");
        }

        this.updateEmptyState();
    }


    hasData() {

        return this.values.some(
            (value) => (
                value !== null &&
                value !== undefined &&
                Number.isFinite(
                    Number(value)
                )
            )
        );
    }


    /* ======================================================
     * Appearance
     * ====================================================== */


    setTitle(title) {

        this.title =
            title || "";

        if (!this.chart) {
            return;
        }

        this.chart.options.plugins.title.display =
            Boolean(this.title);

        this.chart.options.plugins.title.text =
            this.title;

        this.chart.update("none");
    }


    setUnit(unit) {

        this.unit =
            unit || "";

        if (!this.chart) {
            return;
        }

        this.chart.options.scales.y.title.display =
            Boolean(this.unit);

        this.chart.options.scales.y.title.text =
            this.unit;

        this.chart.update("none");
    }


    setLineLabel(label) {

        this.lineLabel =
            label || "Value";

        if (!this.chart) {
            return;
        }

        const dataset =
            this.chart.data.datasets[0];

        if (!dataset) {
            return;
        }

        dataset.label =
            this.lineLabel;

        this.chart.update("none");
    }


    setDecimals(decimals) {

        if (
            !Number.isInteger(decimals) ||
            decimals < 0 ||
            decimals > 8
        ) {
            return;
        }

        this.decimals =
            decimals;

        if (this.chart) {
            this.chart.update("none");
        }
    }


    setLineColor(
        lineColor,
        backgroundColor = null
    ) {

        if (lineColor) {
            this.lineColor =
                lineColor;
        }

        if (backgroundColor) {

            this.backgroundColor =
                backgroundColor;
        }

        if (!this.chart) {
            return;
        }

        const dataset =
            this.chart.data.datasets[0];

        if (!dataset) {
            return;
        }

        dataset.borderColor =
            this.lineColor;

        dataset.backgroundColor =
            this.backgroundColor;

        this.chart.update("none");
    }


    setFill(fill) {

        this.fill =
            Boolean(fill);

        if (!this.chart) {
            return;
        }

        const dataset =
            this.chart.data.datasets[0];

        if (!dataset) {
            return;
        }

        dataset.fill =
            this.fill;

        this.chart.update("none");
    }


    /* ======================================================
     * Loading
     * ====================================================== */


    showLoading() {

        const element =
            this.getLoadingElement();

        if (!element) {
            return;
        }

        element.classList.remove(
            "d-none"
        );
    }


    hideLoading() {

        const element =
            this.getLoadingElement();

        if (!element) {
            return;
        }

        element.classList.add(
            "d-none"
        );
    }


    /* ======================================================
     * Empty state
     * ====================================================== */


    showEmpty() {

        const element =
            this.getEmptyElement();

        if (!element) {
            return;
        }

        element.classList.remove(
            "d-none"
        );

        const canvas =
            this.getCanvas();

        if (canvas) {

            canvas.style.visibility =
                "hidden";
        }
    }


    hideEmpty() {

        const element =
            this.getEmptyElement();

        if (element) {

            element.classList.add(
                "d-none"
            );
        }

        const canvas =
            this.getCanvas();

        if (canvas) {

            canvas.style.visibility =
                "visible";
        }
    }


    updateEmptyState() {

        if (this.hasData()) {

            this.hideEmpty();

        } else {

            this.showEmpty();
        }
    }


    /* ======================================================
     * Zoom and pan
     * ====================================================== */


    resetZoom() {

        if (!this.chart) {
            return;
        }

        if (
            typeof this.chart.resetZoom ===
            "function"
        ) {

            this.chart.resetZoom();
        }
    }


    zoomIn() {

        if (!this.chart) {
            return;
        }

        if (
            typeof this.chart.zoom ===
            "function"
        ) {

            this.chart.zoom(
                1.2
            );
        }
    }


    zoomOut() {

        if (!this.chart) {
            return;
        }

        if (
            typeof this.chart.zoom ===
            "function"
        ) {

            this.chart.zoom(
                0.8
            );
        }
    }


    panLeft() {

        if (!this.chart) {
            return;
        }

        if (
            typeof this.chart.pan ===
            "function"
        ) {

            this.chart.pan(
                {
                    x: 100,
                    y: 0,
                }
            );
        }
    }


    panRight() {

        if (!this.chart) {
            return;
        }

        if (
            typeof this.chart.pan ===
            "function"
        ) {

            this.chart.pan(
                {
                    x: -100,
                    y: 0,
                }
            );
        }
    }


    /* ======================================================
     * Statistics
     * ====================================================== */


    numericValues() {

        return this.values.filter(
            (value) => (
                value !== null &&
                value !== undefined &&
                Number.isFinite(
                    Number(value)
                )
            )
        );
    }


    statistics() {

        const values =
            this.numericValues();

        if (values.length === 0) {

            return {
                count: 0,
                minimum: null,
                maximum: null,
                average: null,
                latest: null,
            };
        }

        let minimum =
            values[0];

        let maximum =
            values[0];

        let total = 0;

        for (const value of values) {

            if (value < minimum) {
                minimum = value;
            }

            if (value > maximum) {
                maximum = value;
            }

            total += value;
        }

        return {
            count: values.length,
            minimum: minimum,
            maximum: maximum,
            average:
                total / values.length,
            latest:
                values[values.length - 1],
        };
    }


    firstLabel() {

        if (this.labels.length === 0) {
            return null;
        }

        return this.labels[0];
    }


    lastLabel() {

        if (this.labels.length === 0) {
            return null;
        }

        return this.labels[
            this.labels.length - 1
        ];
    }


    /* ======================================================
     * Export helpers
     * ====================================================== */


    toRows() {

        const rows = [];

        for (
            let index = 0;
            index < this.labels.length;
            index += 1
        ) {

            rows.push(
                {
                    timestamp:
                        this.labels[index],

                    value:
                        this.values[index] ??
                        null,
                }
            );
        }

        return rows;
    }


    toCsv(
        timestampHeader = "Timestamp",
        valueHeader = null
    ) {

        const header =
            valueHeader ||
            this.lineLabel ||
            "Value";

        const escapeCsvValue =
            (value) => {

                if (
                    value === null ||
                    value === undefined
                ) {
                    return "";
                }

                const text =
                    String(value);

                if (
                    text.includes(",") ||
                    text.includes("\"") ||
                    text.includes("\n")
                ) {

                    return (
                        "\"" +
                        text.replaceAll(
                            "\"",
                            "\"\""
                        ) +
                        "\""
                    );
                }

                return text;
            };

        const lines = [
            [
                escapeCsvValue(
                    timestampHeader
                ),
                escapeCsvValue(
                    header
                ),
            ].join(","),
        ];

        for (
            let index = 0;
            index < this.labels.length;
            index += 1
        ) {

            lines.push(
                [
                    escapeCsvValue(
                        this.labels[index]
                    ),
                    escapeCsvValue(
                        this.values[index]
                    ),
                ].join(",")
            );
        }

        return lines.join("\n");
    }


    downloadCsv(
        filename = "history.csv"
    ) {

        const csv =
            this.toCsv();

        const blob =
            new Blob(
                [csv],
                {
                    type:
                        "text/csv;charset=utf-8",
                }
            );

        const url =
            URL.createObjectURL(
                blob
            );

        const anchor =
            document.createElement(
                "a"
            );

        anchor.href = url;

        anchor.download =
            filename;

        document.body.appendChild(
            anchor
        );

        anchor.click();

        anchor.remove();

        URL.revokeObjectURL(
            url
        );
    }


    /* ======================================================
     * Image export
     * ====================================================== */


    toBase64Image() {

        if (!this.chart) {
            return null;
        }

        return this.chart.toBase64Image(
            "image/png",
            1
        );
    }


    downloadImage(
        filename = "chart.png"
    ) {

        const image =
            this.toBase64Image();

        if (!image) {
            return;
        }

        const anchor =
            document.createElement(
                "a"
            );

        anchor.href =
            image;

        anchor.download =
            filename;

        document.body.appendChild(
            anchor
        );

        anchor.click();

        anchor.remove();
    }


    /* ======================================================
     * Resize
     * ====================================================== */


    resize() {

        if (!this.chart) {
            return;
        }

        this.chart.resize();
    }


    /* ======================================================
     * Destroy
     * ====================================================== */


    destroy() {

        if (this.chart) {

            this.chart.destroy();

            this.chart = null;
        }

        this.initialized = false;
    }

}


/* ==========================================================
 * Global export
 * ========================================================== */


window.ChartManager =
    ChartManager;
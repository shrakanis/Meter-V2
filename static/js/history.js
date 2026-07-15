/*
 * static/js/history.js
 *
 * Energy Monitor V2
 *
 * History page.
 */

"use strict";


class HistoryPage {

    constructor() {

        this.chart = new ChartManager({

            canvasId: "history-chart",

            emptyElementId: "history-empty",

            loadingElementId: "history-loading",

            lineColor: "#0d6efd",

            backgroundColor:
                "rgba(13,110,253,0.12)",

            fill: true,

            decimals: 2,

        });

        this.field =
            historyDefaultField;

        this.range =
            historyDefaultRange;

        this.start = null;

        this.stop = null;

        this.abortController = null;

        this.initialize();
    }


    /* ------------------------------------------------------- */

    initialize() {

        this.cacheElements();

        this.bindEvents();

        this.load();
    }


    /* ------------------------------------------------------- */

    cacheElements() {

        this.fieldSelect =
            document.getElementById(
                "history-field"
            );

        this.refreshButton =
            document.getElementById(
                "history-refresh"
            );

        this.resetZoomButton =
            document.getElementById(
                "history-reset-zoom"
            );

        this.customContainer =
            document.getElementById(
                "history-custom-range"
            );

        this.customStart =
            document.getElementById(
                "history-start"
            );

        this.customStop =
            document.getElementById(
                "history-stop"
            );

        this.customLoadButton =
            document.getElementById(
                "history-load-custom"
            );

        this.rangeButtons =
            document.querySelectorAll(
                ".history-range-button"
            );
    }


    /* ------------------------------------------------------- */

    bindEvents() {

        this.fieldSelect.addEventListener(

            "change",

            () => {

                this.field =
                    this.fieldSelect.value;

                this.load();
            }
        );


        this.refreshButton.addEventListener(

            "click",

            () => {

                this.load();
            }
        );


        this.resetZoomButton.addEventListener(

            "click",

            () => {

                this.chart.resetZoom();
            }
        );


        this.customLoadButton.addEventListener(

            "click",

            () => {

                this.loadCustom();
            }
        );


        this.rangeButtons.forEach(

            button => {

                button.addEventListener(

                    "click",

                    () => {

                        this.changeRange(
                            button.dataset.range
                        );
                    }
                );

            }

        );

    }


    /* ------------------------------------------------------- */

    async load() {

        this.chart.showLoading();

        this.hideError();

        if (this.abortController) {

            this.abortController.abort();
        }

        this.abortController =
            new AbortController();

        try {

            const url =
                this.buildUrl();

            const response =
                await fetch(

                    url,

                    {
                        signal:
                            this.abortController.signal,
                    }

                );

            if (!response.ok) {

                throw new Error(
                    "HTTP " +
                    response.status
                );
            }

            const json =
                await response.json();

            this.updateChart(
                json
            );

            this.updateStatistics(
                json
            );

        }

        catch (error) {

            if (

                error.name ===
                "AbortError"

            ) {

                return;
            }

            console.error(
                error
            );

            this.showError(
                error.message
            );

        }

        finally {

            this.chart.hideLoading();
        }

    }


    /* ------------------------------------------------------- */

    buildUrl() {

        const url =
            new URL(
                historyApiUrl,
                window.location.origin
            );

        url.searchParams.set(

            "field",

            this.field

        );

        if (

            this.range ===
            "custom"

        ) {

            url.searchParams.set(

                "start",

                this.start

            );

            url.searchParams.set(

                "stop",

                this.stop

            );

        }

        else {

            url.searchParams.set(

                "range",

                this.range

            );

        }

        return url;
    }


    /* ------------------------------------------------------- */

    updateChart(data) {
        const title =
            document.getElementById(
                "history-chart-title"
            );

        if (title) {

            title.textContent =
                data.title;
        }

        const period =
            document.getElementById(
                "history-chart-period"
            );

        if (period) {

            period.textContent =
                this.rangeLabel();
        }
        this.chart.setTitle(
            data.title
        );

        this.chart.setUnit(
            data.unit
        );

        this.chart.setLineLabel(
            data.title
        );

        this.chart.setDecimals(
            data.decimals
        );

        this.chart.setData(

            data.labels,

            data.values

        );
        this.chart.resetZoom();

    }
    /* ------------------------------------------------------- */

    updateStatistics(data) {

        const stats =
            this.chart.statistics();

        this.setStat(
            "history-min",
            stats.minimum,
            data.unit,
            data.decimals
        );

        this.setStat(
            "history-max",
            stats.maximum,
            data.unit,
            data.decimals
        );

        this.setStat(
            "history-average",
            stats.average,
            data.unit,
            data.decimals
        );

        this.setStat(
            "history-latest",
            stats.latest,
            data.unit,
            data.decimals
        );

        const samples =
            document.getElementById(
                "history-samples"
            );

        if (samples) {
            samples.textContent =
                String(stats.count);
        }

        const firstSample =
            document.getElementById(
                "history-first-sample"
            );

        if (firstSample) {

            firstSample.textContent =
                this.formatDateTime(
                    this.chart.firstLabel()
                );
        }

        const lastSample =
            document.getElementById(
                "history-last-sample"
            );

        if (lastSample) {

            lastSample.textContent =
                this.formatDateTime(
                    this.chart.lastLabel()
                );
        }

        const chartPeriod =
            document.getElementById(
                "history-chart-period"
            );

        if (chartPeriod) {

            chartPeriod.textContent =
                this.rangeLabel();
        }
    }


    /* ------------------------------------------------------- */

    setStat(
        valueElementId,
        value,
        unit,
        decimals = 2
    ) {

        const valueElement =
            document.getElementById(
                valueElementId
            );

        const unitElement =
            document.getElementById(
                `${valueElementId}-unit`
            );

        if (valueElement) {

            if (
                value === null ||
                value === undefined ||
                !Number.isFinite(
                    Number(value)
                )
            ) {

                valueElement.textContent =
                    "--";

            } else {

                const precision =
                    Number.isInteger(decimals)
                        ? decimals
                        : 2;

                valueElement.textContent =
                    Number(value).toFixed(
                        precision
                    );
            }
        }

        if (unitElement) {

            unitElement.textContent =
                unit || "";
        }
    }


    /* ------------------------------------------------------- */

    changeRange(range) {

        if (!range) {
            return;
        }

        this.range = range;

        this.rangeButtons.forEach(

            button => {

                button.classList.toggle(

                    "active",

                    button.dataset.range ===
                    range

                );
            }
        );

        if (
            range ===
            "custom"
        ) {

            this.customContainer.classList.remove(
                "d-none"
            );

            this.prepareCustomRange();

            return;
        }

        this.customContainer.classList.add(
            "d-none"
        );

        this.start = null;
        this.stop = null;

        this.load();
    }


    /* ------------------------------------------------------- */

    prepareCustomRange() {

        const stop =
            new Date();

        const start =
            new Date(
                stop.getTime() -
                60 * 60 * 1000
            );

        if (
            !this.customStart.value
        ) {

            this.customStart.value =
                this.toDateTimeLocal(
                    start
                );
        }

        if (
            !this.customStop.value
        ) {

            this.customStop.value =
                this.toDateTimeLocal(
                    stop
                );
        }
    }


    /* ------------------------------------------------------- */

    loadCustom() {

        const start =
            this.customStart.value;

        const stop =
            this.customStop.value;

        if (!start || !stop) {

            this.showError(
                "Select both start and stop time."
            );

            return;
        }

        const startDate =
            new Date(start);

        const stopDate =
            new Date(stop);

        if (
            Number.isNaN(
                startDate.getTime()
            ) ||
            Number.isNaN(
                stopDate.getTime()
            )
        ) {

            this.showError(
                "Invalid custom time range."
            );

            return;
        }

        if (
            stopDate <= startDate
        ) {

            this.showError(
                "Stop time must be later than start time."
            );

            return;
        }

        this.start =
            startDate.toISOString();

        this.stop =
            stopDate.toISOString();

        this.range =
            "custom";

        this.load();
    }


    /* ------------------------------------------------------- */

    toDateTimeLocal(date) {

        const pad =
            value =>
                String(value).padStart(
                    2,
                    "0"
                );

        return (
            date.getFullYear() +
            "-" +
            pad(date.getMonth() + 1) +
            "-" +
            pad(date.getDate()) +
            "T" +
            pad(date.getHours()) +
            ":" +
            pad(date.getMinutes())
        );
    }


    /* ------------------------------------------------------- */

    formatDateTime(value) {

        if (!value) {
            return "--";
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


    /* ------------------------------------------------------- */

    rangeLabel() {

        const labels = {

            "1h":
                "Last hour",

            "24h":
                "Last 24 hours",

            "7d":
                "Last 7 days",

            "30d":
                "Last 30 days",

            "custom":
                "Custom range",

        };

        return (
            labels[this.range] ||
            this.range
        );
    }


    /* ------------------------------------------------------- */

    showError(message) {

        const container =
            document.getElementById(
                "history-error"
            );

        const text =
            document.getElementById(
                "history-error-text"
            );

        if (!container || !text) {
            return;
        }

        text.textContent =
            message || "Unknown error.";

        container.classList.remove(
            "d-none"
        );
    }


    /* ------------------------------------------------------- */

    hideError() {

        const container =
            document.getElementById(
                "history-error"
            );

        const text =
            document.getElementById(
                "history-error-text"
            );

        if (text) {
            text.textContent = "";
        }

        if (container) {

            container.classList.add(
                "d-none"
            );
        }
    }


    /* ------------------------------------------------------- */

    destroy() {

        if (this.abortController) {

            this.abortController.abort();

            this.abortController = null;
        }

        if (this.chart) {

            this.chart.destroy();
        }
    }

}


/* ==========================================================
 * Start
 * ========================================================== */


let historyPage = null;


document.addEventListener(

    "DOMContentLoaded",

    () => {

        historyPage =
            new HistoryPage();
    }

);


window.addEventListener(

    "beforeunload",

    () => {

        if (historyPage) {

            historyPage.destroy();

            historyPage = null;
        }
    }

);
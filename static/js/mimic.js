/*
 * static/js/mimic.js
 *
 * Energy Monitor V2
 *
 * Live mimic diagram and layout editor.
 */

"use strict";


class MimicPage {

    constructor(root) {
        this.root = root;
        this.diagramId = Number(root.dataset.diagramId);
        this.apiUrl = root.dataset.apiUrl;
        this.widgetUrl = root.dataset.widgetUrl;
        this.editMode = root.dataset.editMode === "1";
        this.backUrl = root.dataset.backUrl || "/";
        this.canvasWidth = Number(root.dataset.canvasWidth) || 1600;
        this.canvasHeight = Number(root.dataset.canvasHeight) || 900;
        this.stage = document.getElementById("mimic-stage");
        this.stageColumn = this.stage ? this.stage.closest(".mimic-stage-column") : null;
        this.toolbar = document.getElementById("mimic-toolbar");
        this.backButton = document.getElementById("mimic-back");
        this.fullscreenButton = document.getElementById("mimic-fullscreen");
        this.selectedWidget = null;
        this.dragState = null;
        this.refreshTimer = null;

        this.cacheEditor();
        this.bindEvents();
        this.refresh();

        this.refreshTimer = window.setInterval(
            () => this.refresh(),
            1000
        );
    }


    goBack() {
        window.location.href = this.backUrl;
    }


    async toggleFullscreen() {
        try {
            if (document.fullscreenElement === this.root) {
                await document.exitFullscreen();
                return;
            }

            if (this.root.requestFullscreen) {
                await this.root.requestFullscreen();
                return;
            }

            this.root.classList.toggle("mimic-pseudo-fullscreen");
            document.body.classList.toggle(
                "mimic-fullscreen-body",
                this.root.classList.contains("mimic-pseudo-fullscreen")
            );
            this.onFullscreenChange();

        } catch (error) {
            console.error("Cannot enter fullscreen:", error);
        }
    }


    isFullscreen() {
        return (
            document.fullscreenElement === this.root ||
            this.root.classList.contains("mimic-pseudo-fullscreen")
        );
    }


    onFullscreenChange() {
        const active = this.isFullscreen();

        this.root.classList.toggle("is-fullscreen", active);
        document.body.classList.toggle("mimic-fullscreen-body", active);

        if (this.fullscreenButton) {
            const icon = this.fullscreenButton.querySelector(
                '[data-role="fullscreen-icon"]'
            );
            const text = this.fullscreenButton.querySelector(
                '[data-role="fullscreen-text"]'
            );

            if (icon) {
                icon.classList.toggle("bi-arrows-fullscreen", !active);
                icon.classList.toggle("bi-fullscreen-exit", active);
            }

            if (text) {
                text.textContent = active ? "Exit fullscreen" : "Fullscreen";
            }
        }

        if (active) {
            window.requestAnimationFrame(() => this.fitFullscreenStage());
        } else {
            this.restoreStageSize();
        }
    }


    fitFullscreenStage() {
        if (!this.isFullscreen() || !this.stage || !this.stageColumn) {
            return;
        }

        const columnRect = this.stageColumn.getBoundingClientRect();
        const availableWidth = Math.max(100, columnRect.width);
        const availableHeight = Math.max(100, window.innerHeight - columnRect.top - 12);
        const ratio = this.canvasWidth / this.canvasHeight;

        let width = availableWidth;
        let height = width / ratio;

        if (height > availableHeight) {
            height = availableHeight;
            width = height * ratio;
        }

        this.stage.style.width = `${Math.floor(width)}px`;
        this.stage.style.height = `${Math.floor(height)}px`;
        this.stage.style.aspectRatio = "auto";
    }


    restoreStageSize() {
        if (!this.stage) {
            return;
        }

        this.stage.style.width = "100%";
        this.stage.style.height = "";
        this.stage.style.aspectRatio = `${this.canvasWidth} / ${this.canvasHeight}`;
    }


    cacheEditor() {
        this.editorEmpty = document.getElementById("mimic-editor-empty");
        this.editorFields = document.getElementById("mimic-editor-fields");
        this.titleInput = document.getElementById("widget-title");
        this.typeInput = document.getElementById("widget-type");
        this.meterInput = document.getElementById("widget-meter");
        this.measurementInput = document.getElementById("widget-measurement");
        this.widthInput = document.getElementById("widget-width");
        this.decimalsInput = document.getElementById("widget-decimals");
        this.thresholdInput = document.getElementById("widget-threshold");
        this.nominalInput = document.getElementById("widget-nominal");
        this.showStatusInput = document.getElementById("widget-show-status");
        this.showPercentInput = document.getElementById("widget-show-percent");
        this.saveButton = document.getElementById("widget-save");
        this.deleteButton = document.getElementById("widget-delete");
        this.addButton = document.getElementById("mimic-add-widget");
    }


    bindEvents() {
        if (this.backButton) {
            this.backButton.addEventListener("click", () => this.goBack());
        }

        if (this.fullscreenButton) {
            this.fullscreenButton.addEventListener("click", () => this.toggleFullscreen());
        }

        document.addEventListener("fullscreenchange", () => this.onFullscreenChange());
        window.addEventListener("resize", () => this.fitFullscreenStage());

        if (!this.editMode) {
            return;
        }

        this.stage.querySelectorAll(".mimic-widget").forEach(
            (widget) => this.bindWidget(widget)
        );

        if (this.addButton) {
            this.addButton.addEventListener("click", () => this.addWidget());
        }

        if (this.saveButton) {
            this.saveButton.addEventListener("click", () => this.saveSelected());
        }

        if (this.deleteButton) {
            this.deleteButton.addEventListener("click", () => this.deleteSelected());
        }

        window.addEventListener("pointermove", (event) => this.onPointerMove(event));
        window.addEventListener("pointerup", () => this.onPointerUp());
    }


    bindWidget(widget) {
        widget.addEventListener("pointerdown", (event) => {
            if (!this.editMode) {
                return;
            }

            event.preventDefault();
            this.selectWidget(widget);

            const stageRect = this.stage.getBoundingClientRect();
            this.dragState = {
                widget: widget,
                stageRect: stageRect,
            };
        });

        widget.addEventListener("click", (event) => {
            event.preventDefault();
            this.selectWidget(widget);
        });
    }


    selectWidget(widget) {
        this.stage.querySelectorAll(".mimic-widget").forEach(
            (item) => item.classList.remove("is-selected")
        );

        this.selectedWidget = widget;
        widget.classList.add("is-selected");

        if (!this.editorFields) {
            return;
        }

        this.editorEmpty.classList.add("d-none");
        this.editorFields.classList.remove("d-none");

        this.titleInput.value = widget.dataset.title || "";
        this.typeInput.value = widget.dataset.widgetType || "equipment";
        this.meterInput.value = widget.dataset.meterId || "";
        this.measurementInput.value = widget.dataset.measurement || "active_power.total";
        this.widthInput.value = widget.dataset.width || "12";
        this.decimalsInput.value = widget.dataset.decimals || "2";
        this.thresholdInput.value = widget.dataset.runningThreshold || "1";
        this.nominalInput.value = widget.dataset.nominalPower || "";
        this.showStatusInput.checked = widget.dataset.showStatus !== "0";
        this.showPercentInput.checked = widget.dataset.showPercent !== "0";
    }


    onPointerMove(event) {
        if (!this.dragState) {
            return;
        }

        const rect = this.dragState.stageRect;
        let x = (event.clientX - rect.left) / rect.width * 100;
        let y = (event.clientY - rect.top) / rect.height * 100;

        x = Math.max(0, Math.min(100, x));
        y = Math.max(0, Math.min(100, y));

        const widget = this.dragState.widget;
        widget.dataset.x = x.toFixed(3);
        widget.dataset.y = y.toFixed(3);
        widget.style.left = `${x}%`;
        widget.style.top = `${y}%`;
    }


    onPointerUp() {
        this.dragState = null;
    }


    async refresh() {
        try {
            const response = await fetch(this.apiUrl, {
                headers: {"Accept": "application/json"},
                cache: "no-store",
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const payload = await response.json();

            for (const data of payload.widgets || []) {
                const widget = this.stage.querySelector(
                    `.mimic-widget[data-widget-id="${data.id}"]`
                );

                if (widget) {
                    this.updateWidgetDisplay(widget, data);
                }
            }
        } catch (error) {
            console.error("Mimic refresh failed:", error);
        }
    }


    updateWidgetDisplay(widget, data) {
        const valueElement = widget.querySelector('[data-role="value"]');
        const unitElement = widget.querySelector('[data-role="unit"]');
        const statusElement = widget.querySelector('[data-role="status"]');
        const percentElement = widget.querySelector('[data-role="percent"]');
        const decimals = Number.isInteger(data.decimals) ? data.decimals : 2;

        if (data.value === null || data.value === undefined) {
            valueElement.textContent = "--";
            valueElement.parentElement.classList.add("missing");
        } else {
            valueElement.textContent = Number(data.value).toFixed(decimals);
            valueElement.parentElement.classList.remove("missing");
        }

        unitElement.textContent = data.unit ? ` ${data.unit}` : "";

        statusElement.textContent = data.status || "--";
        statusElement.classList.remove("is-running", "is-stopped", "is-offline");
        statusElement.classList.add(
            !data.connected
                ? "is-offline"
                : data.running
                ? "is-running"
                : "is-stopped"
        );
        statusElement.style.display = data.show_status ? "block" : "none";

        percentElement.textContent = (
            data.percent === null || data.percent === undefined
                ? "--"
                : `${Number(data.percent).toFixed(1)}%`
        );
        percentElement.style.display = data.show_percent ? "block" : "none";

        widget.classList.toggle("mimic-widget-value-only", data.widget_type === "value");
    }


    editorPayload(widget) {
        return {
            title: this.titleInput.value.trim() || "Widget",
            widget_type: this.typeInput.value,
            meter_id: this.meterInput.value || null,
            measurement: this.measurementInput.value,
            x: Number(widget.dataset.x || 10),
            y: Number(widget.dataset.y || 10),
            width: Number(this.widthInput.value || 12),
            decimals: Number(this.decimalsInput.value || 2),
            running_threshold: Number(this.thresholdInput.value || 0),
            nominal_power: this.nominalInput.value === ""
                ? null
                : Number(this.nominalInput.value),
            show_status: this.showStatusInput.checked,
            show_percent: this.showPercentInput.checked,
        };
    }


    async addWidget() {
        const payload = {
            title: "New widget",
            widget_type: "equipment",
            measurement: "active_power.total",
            x: 50,
            y: 50,
            width: 12,
            decimals: 2,
            running_threshold: 1,
            show_status: true,
            show_percent: true,
        };

        const response = await fetch(this.widgetUrl, {
            method: "POST",
            headers: {
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            body: JSON.stringify(payload),
        });

        if (!response.ok) {
            alert(`Cannot add widget: HTTP ${response.status}`);
            return;
        }

        window.location.reload();
    }


    async saveSelected() {
        if (!this.selectedWidget) {
            return;
        }

        const widget = this.selectedWidget;
        const widgetId = widget.dataset.widgetId;
        const payload = this.editorPayload(widget);

        const response = await fetch(`${this.widgetUrl}/${widgetId}`, {
            method: "PUT",
            headers: {
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            body: JSON.stringify(payload),
        });

        if (!response.ok) {
            alert(`Cannot save widget: HTTP ${response.status}`);
            return;
        }

        widget.dataset.title = payload.title;
        widget.dataset.widgetType = payload.widget_type;
        widget.dataset.meterId = payload.meter_id || "";
        widget.dataset.measurement = payload.measurement;
        widget.dataset.width = String(payload.width);
        widget.dataset.decimals = String(payload.decimals);
        widget.dataset.runningThreshold = String(payload.running_threshold);
        widget.dataset.nominalPower = payload.nominal_power ?? "";
        widget.dataset.showStatus = payload.show_status ? "1" : "0";
        widget.dataset.showPercent = payload.show_percent ? "1" : "0";
        widget.style.width = `${payload.width}%`;
        widget.querySelector(".mimic-widget-title").textContent = payload.title;

        await this.refresh();
    }


    async deleteSelected() {
        if (!this.selectedWidget) {
            return;
        }

        if (!window.confirm("Delete this widget?")) {
            return;
        }

        const widgetId = this.selectedWidget.dataset.widgetId;
        const response = await fetch(`${this.widgetUrl}/${widgetId}`, {
            method: "DELETE",
            headers: {"Accept": "application/json"},
        });

        if (!response.ok) {
            alert(`Cannot delete widget: HTTP ${response.status}`);
            return;
        }

        this.selectedWidget.remove();
        this.selectedWidget = null;
        this.editorFields.classList.add("d-none");
        this.editorEmpty.classList.remove("d-none");
    }


    destroy() {
        if (document.fullscreenElement === this.root && document.exitFullscreen) {
            document.exitFullscreen().catch(() => {});
        }

        this.root.classList.remove("mimic-pseudo-fullscreen", "is-fullscreen");
        document.body.classList.remove("mimic-fullscreen-body");

        if (this.refreshTimer !== null) {
            window.clearInterval(this.refreshTimer);
            this.refreshTimer = null;
        }
    }
}


let mimicPage = null;

document.addEventListener("DOMContentLoaded", () => {
    const root = document.getElementById("mimic-page");
    if (root) {
        mimicPage = new MimicPage(root);
    }
});

window.addEventListener("beforeunload", () => {
    if (mimicPage) {
        mimicPage.destroy();
        mimicPage = null;
    }
});

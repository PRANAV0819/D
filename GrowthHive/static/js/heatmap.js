/**
 * static/js/heatmap.js
 * GitHub-style contribution heatmap.
 *
 * Reads window.HEATMAP_DATA — an object of { "YYYY-MM-DD": count } pairs
 * injected by the Django template. Renders a 52-week grid into #heatmap.
 *
 * No external dependencies. Vanilla JS ES2020.
 */

(function () {
    "use strict";

    // ── Config ──────────────────────────────────────────────────────────
    const WEEKS = 52;
    const DAYS = 7;       // rows (Sun=0 … Sat=6)
    const CELL_SIZE = 11;      // px — keep in sync with CSS .heatmap-cell
    const CELL_GAP = 2;       // px

    // Thresholds for the 5 heat levels (inclusive upper bounds)
    const THRESHOLDS = [0, 1, 3, 6, Infinity];

    // ── Data ────────────────────────────────────────────────────────────
    const rawData = window.HEATMAP_DATA || {};

    // ── DOM ─────────────────────────────────────────────────────────────
    const container = document.getElementById("heatmap");
    if (!container) return;

    // ── Helpers ─────────────────────────────────────────────────────────
    function isoDate(d) {
        return d.toISOString().slice(0, 10);
    }

    function heatLevel(count) {
        for (let i = 0; i < THRESHOLDS.length; i++) {
            if (count <= THRESHOLDS[i]) return i;
        }
        return THRESHOLDS.length - 1;
    }

    function pluralise(n, word) {
        return `${n} ${word}${n === 1 ? "" : "s"}`;
    }

    // ── Build date range ─────────────────────────────────────────────────
    // Start from the Sunday of the week containing (today – 52 weeks)
    const today = new Date();
    const startDate = new Date(today);
    startDate.setDate(today.getDate() - WEEKS * DAYS + 1);
    // Rewind to the nearest Sunday
    startDate.setDate(startDate.getDate() - startDate.getDay());

    // ── Build grid ───────────────────────────────────────────────────────
    // The CSS grid is set to 7 rows (days) and auto columns (weeks).
    // We iterate week-by-week, day-by-day to fill column-first.

    const fragment = document.createDocumentFragment();
    const tooltip = createTooltip();
    document.body.appendChild(tooltip);

    const current = new Date(startDate);

    while (current <= today) {
        const key = isoDate(current);
        const count = rawData[key] || 0;
        const level = heatLevel(count);

        const cell = document.createElement("div");
        cell.className = `heatmap-cell heatmap-cell--${level}`;
        cell.dataset.date = key;
        cell.dataset.count = count;
        cell.setAttribute("role", "gridcell");
        cell.setAttribute("aria-label", `${key}: ${pluralise(count, "contribution")}`);

        cell.addEventListener("mouseenter", onCellEnter);
        cell.addEventListener("mouseleave", onCellLeave);

        fragment.appendChild(cell);
        current.setDate(current.getDate() + 1);
    }

    container.appendChild(fragment);

    // ── Tooltip ──────────────────────────────────────────────────────────
    function createTooltip() {
        const el = document.createElement("div");
        el.className = "heatmap-tooltip";
        el.style.display = "none";
        return el;
    }

    function onCellEnter(e) {
        const cell = e.currentTarget;
        const count = parseInt(cell.dataset.count, 10);
        const date = cell.dataset.date;

        const label = count === 0
            ? `No contributions on ${date}`
            : `${pluralise(count, "contribution")} on ${date}`;

        tooltip.textContent = label;
        tooltip.style.display = "block";
        positionTooltip(e);
    }

    function onCellLeave() {
        tooltip.style.display = "none";
    }

    function positionTooltip(e) {
        const rect = e.currentTarget.getBoundingClientRect();
        tooltip.style.left = `${rect.left + window.scrollX + CELL_SIZE / 2}px`;
        tooltip.style.top = `${rect.top + window.scrollY}px`;
    }

    // Reposition on scroll (keeps tooltip from drifting)
    document.addEventListener("scroll", () => {
        tooltip.style.display = "none";
    }, { passive: true });

})();
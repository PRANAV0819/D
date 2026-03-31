/**
 * static/js/edit_profile.js
 *
 * Handles three interactive features on the edit profile page:
 *   1. Skill tag-input widget  — add/remove skill chips
 *   2. Avatar image preview    — instant preview on file select
 *   3. Bio character counter   — live remaining-chars display
 *
 * No external dependencies. Written as self-contained IIFEs so each
 * feature can be extracted independently.
 */

"use strict";

/* ── 1. Skill tag-input widget ─────────────────────────────────────────
 *
 * Reads window.INITIAL_SKILLS (array injected by template).
 * Syncs the chip list to a hidden <input id="skills-raw-input">
 * which the Django form reads on submit.
 *
 * UX:  Enter or comma → add tag
 *      Backspace on empty input → remove last tag
 *      Click × on chip → remove that tag
 */
(function tagInput() {
    const container = document.getElementById("tag-input-container");
    const tagList = document.getElementById("tag-list");
    const textInput = document.getElementById("tag-text-input");
    const hiddenInput = document.getElementById("skills-raw-input");

    if (!container || !tagList || !textInput || !hiddenInput) return;

    let skills = Array.isArray(window.INITIAL_SKILLS) ? [...window.INITIAL_SKILLS] : [];

    // ── Render ────────────────────────────────────────────────────────
    function render() {
        tagList.innerHTML = "";
        skills.forEach((skill, idx) => {
            const chip = document.createElement("span");
            chip.className = "tag-chip";
            chip.innerHTML = `${escapeHtml(skill)}<button type="button" class="tag-chip__remove" data-idx="${idx}" aria-label="Remove ${escapeHtml(skill)}">×</button>`;
            tagList.appendChild(chip);
        });
        // Sync hidden field
        hiddenInput.value = skills.join(",");
    }

    // ── Add skill ─────────────────────────────────────────────────────
    function addSkill(raw) {
        const skill = titleCase(raw.trim().replace(/,/g, ""));
        if (!skill || skills.includes(skill) || skills.length >= 20) return;
        skills.push(skill);
        render();
    }

    // ── Remove skill by index ─────────────────────────────────────────
    function removeSkill(idx) {
        skills.splice(idx, 1);
        render();
    }

    // ── Events ────────────────────────────────────────────────────────
    textInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === ",") {
            e.preventDefault();
            addSkill(textInput.value);
            textInput.value = "";
        } else if (e.key === "Backspace" && textInput.value === "" && skills.length) {
            removeSkill(skills.length - 1);
        }
    });

    textInput.addEventListener("blur", () => {
        if (textInput.value.trim()) {
            addSkill(textInput.value);
            textInput.value = "";
        }
    });

    // Delegate chip remove clicks to the container
    container.addEventListener("click", (e) => {
        const btn = e.target.closest(".tag-chip__remove");
        if (btn) removeSkill(parseInt(btn.dataset.idx, 10));
    });

    // Click on the container focuses the text input
    container.addEventListener("click", (e) => {
        if (!e.target.closest(".tag-chip")) textInput.focus();
    });

    // ── Utils ─────────────────────────────────────────────────────────
    function escapeHtml(str) {
        const map = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" };
        return str.replace(/[&<>"']/g, (c) => map[c]);
    }

    function titleCase(str) {
        return str.replace(/\w\S*/g, (w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase());
    }

    render();
})();


/* ── 2. Avatar image preview ───────────────────────────────────────────
 *
 * Shows a live preview of the selected file before upload.
 */
(function avatarPreview() {
    const fileInput = document.querySelector(".form-file-input");
    const preview = document.getElementById("avatar-preview");

    if (!fileInput || !preview) return;

    fileInput.addEventListener("change", () => {
        const file = fileInput.files?.[0];
        if (!file || !file.type.startsWith("image/")) return;

        // Validate size client-side (2 MB)
        if (file.size > 2 * 1024 * 1024) {
            alert("Image must be smaller than 2 MB.");
            fileInput.value = "";
            return;
        }

        const reader = new FileReader();
        reader.onload = (e) => { preview.src = e.target.result; };
        reader.readAsDataURL(file);
    });
})();


/* ── 3. Bio character counter ──────────────────────────────────────────
 *
 * Any element with [data-target] and [data-max] will show live count.
 */
(function charCounters() {
    document.querySelectorAll(".char-counter[data-target][data-max]").forEach((counter) => {
        const targetId = counter.dataset.target;
        const max = parseInt(counter.dataset.max, 10);
        const input = document.getElementById(targetId);

        if (!input) return;

        function update() {
            const len = input.value.length;
            counter.textContent = `${len} / ${max}`;
            counter.style.color = len > max * 0.9
                ? (len >= max ? "#dc2626" : "#d97706")
                : "";
        }

        input.addEventListener("input", update);
        update(); // initial count
    });
})();
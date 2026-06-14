/**
 * mdd-ui dashboard client — binds wireframe components to /api/v1/ contracts.
 */
(function () {
  "use strict";

  const API = "/api/v1";

  const ui = {
    connectionBadge: document.getElementById("connection-badge"),
    healthIndicator: document.getElementById("health-indicator"),
    ollamaBanner: document.getElementById("ollama-status-banner"),
    modelPicker: document.getElementById("model-picker"),
    modelHint: document.getElementById("model-picker-hint"),
    refreshModels: document.getElementById("refresh-models"),
    pathInput: document.getElementById("path-input"),
    pathHint: document.getElementById("path-validation-hint"),
    previewMessage: document.getElementById("preview-message"),
    previewMeta: document.getElementById("preview-meta"),
    previewList: document.getElementById("preview-item-list"),
    previewWarnings: document.getElementById("preview-warnings"),
    previewButton: document.getElementById("preview-button"),
    runScanButton: document.getElementById("run-scan-button"),
    scanStatusBar: document.getElementById("scan-status-bar"),
    scanStatusText: document.getElementById("scan-status-text"),
    reportEmpty: document.getElementById("report-empty"),
    reportStale: document.getElementById("report-stale"),
    reportContent: document.getElementById("report-content"),
    riskGaugeFill: document.getElementById("risk-gauge-fill"),
    riskGaugeValue: document.getElementById("risk-gauge-value"),
    riskLevelLabel: document.getElementById("risk-level-label"),
    severityCards: document.getElementById("severity-cards"),
    scanMetadata: document.getElementById("scan-metadata"),
    findingsBody: document.getElementById("findings-body"),
    inventoryBody: document.getElementById("inventory-body"),
    modelMetadataSection: document.getElementById("model-metadata-section"),
    filterSeverity: document.getElementById("filter-severity"),
    filterScanner: document.getElementById("filter-scanner"),
    exportMarkdown: document.getElementById("export-markdown"),
    exportJson: document.getElementById("export-json"),
    exportSarif: document.getElementById("export-sarif"),
    tabOllama: document.getElementById("tab-ollama"),
    tabPath: document.getElementById("tab-path"),
    panelOllama: document.getElementById("panel-ollama"),
    panelPath: document.getElementById("panel-path"),
    optSkipExternal: document.getElementById("opt-skip-external"),
    optSkipSemgrep: document.getElementById("opt-skip-semgrep"),
    optSkipBandit: document.getElementById("opt-skip-bandit"),
    optTimeout: document.getElementById("opt-timeout"),
    optFailOn: document.getElementById("opt-fail-on"),
  };

  const state = {
    activeTab: "ollama",
    scanRunning: false,
    scanId: null,
    lastReport: null,
    lastFindings: [],
    lastScanTarget: null,
    scanStartedAt: null,
  };

  function setBadge(el, text, interactionState) {
    if (!el) return;
    el.textContent = text;
    el.className = "badge badge--" + (interactionState || "idle");
  }

  function setBanner(el, text, interactionState) {
    if (!el) return;
    el.textContent = text;
    el.className = "status-banner status-banner--" + (interactionState || "loading");
  }

  function setScanStatus(text, interactionState) {
    ui.scanStatusText.textContent = text;
    ui.scanStatusBar.className = "scan-status scan-status--" + (interactionState || "idle");
  }

  function formatBytes(bytes) {
    if (bytes == null || Number.isNaN(bytes)) return "—";
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + " MB";
    return (bytes / (1024 * 1024 * 1024)).toFixed(2) + " GB";
  }

  function truncate(text, max) {
    if (!text) return "";
    return text.length <= max ? text : text.slice(0, max) + "…";
  }

  async function apiFetch(path, options) {
    const response = await fetch(API + path, options);
    const contentType = response.headers.get("content-type") || "";
    let payload = null;
    if (contentType.includes("application/json")) {
      payload = await response.json();
    }
    if (!response.ok) {
      const message =
        payload && typeof payload === "object"
          ? payload.detail || payload.error || response.statusText
          : response.statusText;
      throw new Error(String(message));
    }
    return payload;
  }

  function scanOptionsPayload() {
    return {
      skip_external: ui.optSkipExternal.checked,
      skip_semgrep: ui.optSkipSemgrep.checked,
      skip_bandit: ui.optSkipBandit.checked,
      skip_pip_audit: false,
      skip_detect_secrets: false,
      skip_modelscan: false,
      timeout_seconds: Number(ui.optTimeout.value) || 300,
      fail_on: ui.optFailOn.value,
    };
  }

  function currentTarget() {
    if (state.activeTab === "ollama") {
      const name = ui.modelPicker.value;
      if (!name) throw new Error("Select an Ollama model first.");
      return { target_type: "ollama", target: name };
    }
    const path = ui.pathInput.value.trim();
    if (!path) throw new Error("Enter a file or directory path.");
    return { target_type: "path", target: path };
  }

  async function loadHealth() {
    setBadge(ui.healthIndicator, "API: checking…", "loading");
    try {
      const data = await apiFetch("/health");
      const label = "API v" + data.version + " (" + data.status + ")";
      setBadge(ui.healthIndicator, label, data.status === "ok" ? "success" : "warning");
    } catch (err) {
      setBadge(ui.healthIndicator, "API: unreachable", "error");
    }
  }

  async function loadOllamaStatus() {
    setBadge(ui.connectionBadge, "Ollama: checking…", "loading");
    setBanner(ui.ollamaBanner, "Checking Ollama connectivity…", "loading");
    try {
      const data = await apiFetch("/ollama/status");
      const short = data.connected ? "connected" : data.source === "filesystem" ? "offline (local store)" : "unavailable";
      setBadge(ui.connectionBadge, "Ollama: " + short, data.state);
      setBanner(ui.ollamaBanner, data.message, data.state);
    } catch (err) {
      setBadge(ui.connectionBadge, "Ollama: error", "error");
      setBanner(ui.ollamaBanner, String(err.message || err), "error");
    }
  }

  async function loadModels() {
    ui.modelPicker.disabled = true;
    ui.modelPicker.innerHTML = '<option value="">Loading models…</option>';
    ui.modelHint.textContent = "Fetching installed models…";
    try {
      const data = await apiFetch("/ollama/models");
      ui.modelPicker.innerHTML = "";
      if (!data.models || data.models.length === 0) {
        ui.modelPicker.innerHTML = '<option value="">No models found</option>';
        ui.modelHint.textContent = data.message;
        return;
      }
      const placeholder = document.createElement("option");
      placeholder.value = "";
      placeholder.textContent = "Select a model…";
      ui.modelPicker.appendChild(placeholder);
      data.models.forEach(function (model) {
        const opt = document.createElement("option");
        opt.value = model.name;
        const size = model.size_bytes != null ? " — " + formatBytes(model.size_bytes) : "";
        const family = model.family ? " [" + model.family + "]" : "";
        opt.textContent = model.name + family + size;
        ui.modelPicker.appendChild(opt);
      });
      ui.modelPicker.disabled = false;
      ui.modelHint.textContent = data.message;
    } catch (err) {
      ui.modelPicker.innerHTML = '<option value="">Failed to load models</option>';
      ui.modelHint.textContent = String(err.message || err);
    }
  }

  function targetFingerprint() {
    try {
      return JSON.stringify(currentTarget());
    } catch (_err) {
      return null;
    }
  }

  function markReportStaleIfNeeded() {
    if (!state.lastScanTarget || !ui.reportStale) return;
    const current = targetFingerprint();
    const stale = current !== null && current !== state.lastScanTarget;
    ui.reportStale.hidden = !stale;
  }

  function renderPreview(data) {
    const itemCount = (data.items || []).length;
    if (ui.previewMeta) {
      if (data.resolved_path || itemCount) {
        ui.previewMeta.hidden = false;
        ui.previewMeta.textContent =
          (data.resolved_path ? "Resolved: " + data.resolved_path + " · " : "") +
          itemCount +
          " artefact" +
          (itemCount === 1 ? "" : "s") +
          " listed";
      } else {
        ui.previewMeta.hidden = true;
      }
    }
    ui.previewMessage.textContent = data.message || "Preview ready.";
    ui.previewList.innerHTML = "";
    (data.items || []).forEach(function (item) {
      const li = document.createElement("li");
      li.textContent = item.label + " (" + item.kind + ")" + (item.size_bytes != null ? " — " + formatBytes(item.size_bytes) : "");
      ui.previewList.appendChild(li);
    });
    ui.previewWarnings.innerHTML = "";
    (data.warnings || []).forEach(function (warning) {
      const li = document.createElement("li");
      li.textContent = warning;
      ui.previewWarnings.appendChild(li);
    });
  }

  function severityCounts(summary) {
    return [
      { key: "CRITICAL", count: summary.critical_findings || 0 },
      { key: "HIGH", count: summary.high_findings || 0 },
      { key: "MEDIUM", count: summary.medium_findings || 0 },
      { key: "LOW", count: summary.low_findings || 0 },
      { key: "INFO", count: summary.info_findings || 0 },
    ];
  }

  function renderSeverityCards(summary) {
    ui.severityCards.innerHTML = "";
    severityCounts(summary).forEach(function (item) {
      const card = document.createElement("div");
      card.className = "severity-card severity-card--" + item.key;
      card.innerHTML = "<strong>" + item.count + "</strong><span>" + item.key + "</span>";
      ui.severityCards.appendChild(card);
    });
  }

  function renderFindings(findings) {
    const severityFilter = ui.filterSeverity.value;
    const scannerFilter = (ui.filterScanner.value || "").toLowerCase();
    ui.findingsBody.innerHTML = "";
    const filtered = (findings || []).filter(function (f) {
      const sev = (f.severity || "").toUpperCase();
      if (severityFilter && sev !== severityFilter) return false;
      if (scannerFilter && !(f.scanner || "").toLowerCase().includes(scannerFilter)) return false;
      return true;
    });
    if (filtered.length === 0) {
      const row = document.createElement("tr");
      row.innerHTML = '<td colspan="4">No findings match the current filters.</td>';
      ui.findingsBody.appendChild(row);
      return;
    }
    filtered.forEach(function (finding, index) {
      const row = document.createElement("tr");
      const sev = (finding.severity || "INFO").toUpperCase();
      let evidenceHtml = "";
      if (finding.evidence || finding.recommendation) {
        const body =
          (finding.evidence ? "Evidence:\n" + escapeHtml(finding.evidence) + "\n" : "") +
          (finding.recommendation ? "Recommendation:\n" + escapeHtml(finding.recommendation) : "");
        evidenceHtml =
          '<details class="finding-details"><summary>View evidence (' +
          (index + 1) +
          ')</summary><div class="evidence-panel">' +
          body +
          "</div></details>";
      }
      row.innerHTML =
        '<td><span class="sev-pill sev-pill--' +
        sev +
        '">' +
        sev +
        "</span></td>" +
        "<td>" +
        escapeHtml(finding.category || "") +
        "</td>" +
        "<td>" +
        escapeHtml(truncate(finding.file || "", 48)) +
        "</td>" +
        "<td>" +
        escapeHtml(finding.message || "") +
        evidenceHtml +
        "</td>";
      ui.findingsBody.appendChild(row);
    });
  }

  function escapeHtml(text) {
    return String(text)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function renderInventory(files) {
    ui.inventoryBody.innerHTML = "";
    (files || []).slice(0, 100).forEach(function (file) {
      const row = document.createElement("tr");
      row.innerHTML =
        "<td>" +
        escapeHtml(truncate(file.path || file.absolute_path || "", 40)) +
        "</td>" +
        "<td>" +
        escapeHtml(String(file.category || "")) +
        "</td>" +
        "<td>" +
        formatBytes(file.size_bytes) +
        "</td>" +
        "<td>" +
        escapeHtml(truncate(file.sha256 || "", 16)) +
        "</td>";
      ui.inventoryBody.appendChild(row);
    });
  }

  function renderMetadata(metadata) {
    ui.modelMetadataSection.innerHTML = "";
    if (!metadata || metadata.length === 0) {
      ui.modelMetadataSection.innerHTML = '<p class="empty-inline">No model metadata extracted.</p>';
      return;
    }
    metadata.forEach(function (entry) {
      const card = document.createElement("div");
      card.className = "metadata-card";
      card.innerHTML =
        "<strong>" +
        escapeHtml(entry.file || entry.kind || "metadata") +
        "</strong><pre>" +
        escapeHtml(JSON.stringify(entry.metadata || {}, null, 2)) +
        "</pre>";
      ui.modelMetadataSection.appendChild(card);
    });
  }

  function setExportLinks(scanId) {
    const base = API + "/scan/" + scanId + "/export/";
    const links = [ui.exportMarkdown, ui.exportJson, ui.exportSarif];
    const formats = ["markdown", "json", "sarif"];
    links.forEach(function (link, idx) {
      if (!link) return;
      link.href = base + formats[idx];
      link.setAttribute("download", "");
      link.classList.remove("btn--disabled");
      link.setAttribute("aria-disabled", "false");
      link.tabIndex = 0;
    });
  }

  function disableExportLinks() {
    [ui.exportMarkdown, ui.exportJson, ui.exportSarif].forEach(function (link) {
      if (!link) return;
      link.href = "#";
      link.removeAttribute("download");
      link.classList.add("btn--disabled");
      link.setAttribute("aria-disabled", "true");
      link.tabIndex = -1;
    });
  }

  function renderReport(scanResponse) {
    const report = scanResponse.report || {};
    const summary = report.summary || {};
    state.scanId = scanResponse.report_paths && scanResponse.report_paths.scan_id;
    state.lastReport = report;
    state.lastFindings = report.findings || [];

    ui.reportEmpty.hidden = true;
    ui.reportContent.hidden = false;
    if (ui.reportStale) ui.reportStale.hidden = true;

    state.lastScanTarget = targetFingerprint();

    const score = report.risk_score != null ? report.risk_score : 0;
    ui.riskGaugeFill.style.width = Math.min(100, Math.max(0, score)) + "%";
    ui.riskGaugeValue.textContent = score + " / 100";
    ui.riskLevelLabel.textContent = (report.risk_level || "—") + " risk";

    renderSeverityCards(summary);
    ui.scanMetadata.textContent =
      "Target: " +
      (scanResponse.scanned_path || scanResponse.target) +
      " · Files: " +
      (summary.files_scanned != null ? summary.files_scanned : "—") +
      " · Findings: " +
      (summary.findings != null ? summary.findings : "—");

    renderFindings(state.lastFindings);
    renderInventory(report.files || []);
    renderMetadata(report.metadata || []);

    if (state.scanId) setExportLinks(state.scanId);

    const statusState = scanResponse.state || "success";
    let statusText = scanResponse.message || "Scan completed.";
    if ((scanResponse.warnings || []).length) {
      statusText += " " + scanResponse.warnings.join(" ");
    }
    setScanStatus(statusText, statusState);
  }

  async function runPreview() {
    ui.previewButton.disabled = true;
    ui.previewMessage.textContent = "Building scan plan…";
    try {
      const target = currentTarget();
      const data = await apiFetch("/scan/preview", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...target, options: scanOptionsPayload() }),
      });
      renderPreview(data);
      if (state.activeTab === "path") {
        ui.pathHint.textContent = "Path validated for preview.";
        ui.pathHint.className = "field-hint";
      }
    } catch (err) {
      ui.previewMessage.textContent = "Preview failed: " + (err.message || err);
      if (state.activeTab === "path") {
        ui.pathHint.textContent = String(err.message || err);
      }
    } finally {
      ui.previewButton.disabled = state.scanRunning;
    }
  }

  async function runScan() {
    if (state.scanRunning) return;
    state.scanRunning = true;
    ui.runScanButton.disabled = true;
    ui.previewButton.disabled = true;
    state.scanStartedAt = Date.now();
    setScanStatus("Running static scan…", "running");
    const timer = window.setInterval(function () {
      if (!state.scanRunning || !state.scanStartedAt) return;
      const seconds = Math.floor((Date.now() - state.scanStartedAt) / 1000);
      setScanStatus("Running static scan… (" + seconds + "s)", "running");
    }, 1000);
    try {
      const target = currentTarget();
      const data = await apiFetch("/scan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...target, options: scanOptionsPayload() }),
      });
      renderReport(data);
    } catch (err) {
      setScanStatus("Scan failed: " + (err.message || err), "error");
    } finally {
      window.clearInterval(timer);
      state.scanRunning = false;
      state.scanStartedAt = null;
      ui.runScanButton.disabled = false;
      ui.previewButton.disabled = false;
    }
  }

  function switchTab(tab) {
    state.activeTab = tab;
    const isOllama = tab === "ollama";
    ui.tabOllama.classList.toggle("tab--active", isOllama);
    ui.tabPath.classList.toggle("tab--active", !isOllama);
    ui.tabOllama.setAttribute("aria-selected", String(isOllama));
    ui.tabPath.setAttribute("aria-selected", String(!isOllama));
    ui.panelOllama.hidden = !isOllama;
    ui.panelPath.hidden = isOllama;
    ui.panelOllama.classList.toggle("tab-panel--hidden", !isOllama);
    ui.panelPath.classList.toggle("tab-panel--hidden", isOllama);
  }

  function bindEvents() {
    ui.tabOllama.addEventListener("click", function () {
      switchTab("ollama");
      markReportStaleIfNeeded();
    });
    ui.tabPath.addEventListener("click", function () {
      switchTab("path");
      markReportStaleIfNeeded();
    });
    ui.refreshModels.addEventListener("click", loadModels);
    ui.previewButton.addEventListener("click", runPreview);
    ui.runScanButton.addEventListener("click", runScan);
    ui.modelPicker.addEventListener("change", markReportStaleIfNeeded);
    ui.filterSeverity.addEventListener("change", function () {
      renderFindings(state.lastFindings);
    });
    ui.filterScanner.addEventListener("input", function () {
      renderFindings(state.lastFindings);
    });
    ui.pathInput.addEventListener("input", function () {
      ui.pathHint.textContent = "Enter a local GGUF, safetensors, file, or directory path.";
      markReportStaleIfNeeded();
    });
    document.addEventListener("keydown", function (event) {
      if (event.target === ui.pathInput && event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        runPreview();
      }
      if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
        event.preventDefault();
        runScan();
      }
    });
  }

  async function init() {
    bindEvents();
    disableExportLinks();
    await Promise.all([loadHealth(), loadOllamaStatus(), loadModels()]);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();

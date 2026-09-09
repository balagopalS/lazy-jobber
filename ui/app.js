// Lazy-Jobber Web UI Client Logic
document.addEventListener("DOMContentLoaded", () => {
  const connectionBadge = document.getElementById("connectionStatusBadge");
  const connectionText = document.getElementById("connectionText");
  const btnCheckCdp = document.getElementById("btnCheckCdp");

  const btnStartAgent = document.getElementById("btnStartAgent");
  const btnStopAgent = document.getElementById("btnStopAgent");
  const agentStateBadge = document.getElementById("agentStateBadge");
  const agentActionText = document.getElementById("agentActionText");

  const aiProviderSelect = document.getElementById("aiProviderSelect");
  const ollamaFields = document.getElementById("ollamaFields");
  const openrouterFields = document.getElementById("openrouterFields");
  const ollamaUrlInput = document.getElementById("ollamaUrlInput");
  const ollamaModelInput = document.getElementById("ollamaModelInput");
  const openrouterApiKey = document.getElementById("openrouterApiKey");
  const openrouterModelInput = document.getElementById("openrouterModelInput");
  const btnSaveAiConfig = document.getElementById("btnSaveAiConfig");

  const btnStartScan = document.getElementById("btnStartScan");
  const btnStartJobber = document.getElementById("btnStartJobber");
  const btnClearTerminal = document.getElementById("btnClearTerminal");
  const terminalBody = document.getElementById("terminalBody");

  const candidateName = document.getElementById("candidateName");
  const candidateEmail = document.getElementById("candidateEmail");
  const candidateLocation = document.getElementById("candidateLocation");
  const skillsPills = document.getElementById("skillsPills");

  const metricTarget = document.getElementById("metricTarget");
  const metricApplied = document.getElementById("metricApplied");
  const metricAvgMatch = document.getElementById("metricAvgMatch");
  const metricStatus = document.getElementById("metricStatus");
  const metricStatusSub = document.getElementById("metricStatusSub");

  const appLimitInput = document.getElementById("appLimitInput");
  const minScoreInput = document.getElementById("minScoreInput");
  const jobsTableBody = document.getElementById("jobsTableBody");

  let isConnected = false;
  let seenLogCount = 0;

  // 1. Toggle AI Provider Fields
  aiProviderSelect.addEventListener("change", () => {
    const val = aiProviderSelect.value;
    if (val === "openrouter") {
      ollamaFields.style.display = "none";
      openrouterFields.style.display = "block";
    } else {
      ollamaFields.style.display = "block";
      openrouterFields.style.display = "none";
    }
  });

  // Save AI Config
  btnSaveAiConfig.addEventListener("click", async () => {
    const provider = aiProviderSelect.value;
    const body = {
      provider: provider,
      ollama: {
        base_url: ollamaUrlInput.value.trim() || "http://localhost:11434",
        model: ollamaModelInput.value.trim() || "llama3"
      },
      openrouter: {
        api_key: openrouterApiKey.value.trim(),
        model: openrouterModelInput.value.trim() || "meta-llama/llama-3.1-8b-instruct:free"
      }
    };

    btnSaveAiConfig.disabled = true;
    btnSaveAiConfig.textContent = "Saving...";
    try {
      const res = await fetch("/api/config/ai", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
      });
      const data = await res.json();
      if (data.success) {
        alert("✅ AI Provider settings saved successfully!");
      } else {
        alert("❌ Failed to save AI config: " + data.error);
      }
    } catch (e) {
      alert("Error saving AI config: " + e.message);
    } finally {
      btnSaveAiConfig.disabled = false;
      btnSaveAiConfig.textContent = "💾 Save AI Provider Config";
    }
  });

  // 2. Autonomous Agent Controls
  btnStartAgent.addEventListener("click", async () => {
    btnStartAgent.disabled = true;
    try {
      const res = await fetch("/api/agent/start", { method: "GET" });
      const data = await res.json();
      if (data.success) {
        btnStartAgent.style.display = "none";
        btnStopAgent.style.display = "inline-flex";
      } else {
        alert("Agent start error: " + data.message);
      }
    } catch (e) {
      alert("Agent trigger failed: " + e.message);
    } finally {
      btnStartAgent.disabled = false;
    }
  });

  btnStopAgent.addEventListener("click", async () => {
    btnStopAgent.disabled = true;
    try {
      const res = await fetch("/api/agent/stop", { method: "GET" });
      const data = await res.json();
      if (data.success) {
        btnStopAgent.style.display = "none";
        btnStartAgent.style.display = "inline-flex";
      }
    } catch (e) {
      alert("Agent stop failed: " + e.message);
    } finally {
      btnStopAgent.disabled = false;
    }
  });

  async function pollAgentStatus() {
    try {
      const res = await fetch("/api/agent/status");
      if (!res.ok) return;
      const data = await res.json();

      agentStateBadge.textContent = data.state || "IDLE";
      if (data.state === "RUNNING") {
        agentStateBadge.className = "badge badge-success";
        btnStartAgent.style.display = "none";
        btnStopAgent.style.display = "inline-flex";
        metricStatus.textContent = "Running";
        metricStatus.className = "metric-value status-running";
      } else {
        agentStateBadge.className = "badge badge-warning";
        btnStopAgent.style.display = "none";
        btnStartAgent.style.display = "inline-flex";
        metricStatus.textContent = "Idle";
        metricStatus.className = "metric-value status-idle";
      }

      agentActionText.textContent = data.current_action || "Agent Idle";
      if (data.stats) {
        metricApplied.textContent = data.stats.total_applied || 0;
      }
    } catch (e) {
      // Ignore transient errors
    }
  }

  // 3. Terminal Logs Stream Polling
  async function pollTerminalLogs() {
    try {
      const res = await fetch("/api/logs?limit=100");
      if (!res.ok) return;
      const data = await res.json();
      if (!data.logs || data.logs.length === 0) return;

      if (data.logs.length !== seenLogCount) {
        seenLogCount = data.logs.length;
        terminalBody.innerHTML = "";
        data.logs.forEach(log => {
          const div = document.createElement("div");
          let levelClass = "log-line-info";
          if (log.level === "WARNING") levelClass = "log-line-warning";
          else if (log.level === "ERROR") levelClass = "log-line-error";

          div.className = levelClass;
          div.textContent = `[${log.asctime || 'LOG'}] [${log.level}] ${log.message}`;
          terminalBody.appendChild(div);
        });
        terminalBody.scrollTop = terminalBody.scrollHeight;
      }
    } catch (e) {
      // Ignore
    }
  }

  btnClearTerminal.addEventListener("click", () => {
    terminalBody.innerHTML = '<div class="log-line-info">[SYSTEM] Terminal logs cleared.</div>';
    seenLogCount = 0;
  });

  // 4. Fetch Candidate Profile & Config
  async function loadProfileAndConfig() {
    try {
      const res = await fetch("/api/profile");
      if (!res.ok) return;
      const data = await res.json();

      const info = data.personal_info || {};
      candidateName.textContent = info.full_name || "Balagopal S";
      candidateEmail.textContent = `📧 ${info.email || "balagopalsasidharan@gmail.com"}`;
      candidateLocation.textContent = `📍 ${info.location || "Bengaluru, India"}`;

      skillsPills.innerHTML = "";
      const skills = data.skills || [];
      skills.forEach(skill => {
        const pill = document.createElement("span");
        pill.className = "pill";
        pill.textContent = skill;
        skillsPills.appendChild(pill);
      });

      if (data.config) {
        appLimitInput.value = data.config.application_limit || 40;
        metricTarget.textContent = data.config.application_limit || 40;
        if (data.config.search_criteria && data.config.search_criteria.matching_score_threshold) {
          minScoreInput.value = Math.round(data.config.search_criteria.matching_score_threshold * 100);
        }

        if (data.config.ai_config) {
          const aiCfg = data.config.ai_config;
          aiProviderSelect.value = aiCfg.provider || "ollama";
          aiProviderSelect.dispatchEvent(new Event("change"));

          if (aiCfg.ollama) {
            ollamaUrlInput.value = aiCfg.ollama.base_url || "http://localhost:11434";
            ollamaModelInput.value = aiCfg.ollama.model || "llama3";
          }
          if (aiCfg.openrouter) {
            openrouterApiKey.value = aiCfg.openrouter.api_key || "";
            openrouterModelInput.value = aiCfg.openrouter.model || "meta-llama/llama-3.1-8b-instruct:free";
          }
        }
      }
    } catch (e) {
      console.error("Error loading profile:", e);
    }
  }

  // 5. Check Chrome CDP Status
  async function checkCdpStatus() {
    connectionBadge.className = "badge badge-warning";
    connectionText.textContent = "Probing Port 9222...";
    try {
      const res = await fetch("/api/cdp/status");
      const data = await res.json();
      if (data.connected) {
        isConnected = true;
        connectionBadge.className = "badge badge-success";
        connectionText.textContent = `Chrome Active (Tab: ${data.title ? data.title.substring(0, 20) + '...' : 'Connected'})`;
        btnStartScan.disabled = false;
        btnStartJobber.disabled = false;
      } else {
        isConnected = false;
        connectionBadge.className = "badge badge-danger";
        connectionText.textContent = "Chrome Port 9222 Disconnected";
        btnStartScan.disabled = true;
        btnStartJobber.disabled = true;
      }
    } catch (e) {
      isConnected = false;
      connectionBadge.className = "badge badge-danger";
      connectionText.textContent = "Backend Unreachable";
      btnStartScan.disabled = true;
      btnStartJobber.disabled = true;
    }
  }

  // 6. Manual Scan Current Page
  async function scanPage() {
    btnStartScan.disabled = true;
    btnStartScan.textContent = "Scanning...";
    try {
      const minScore = parseInt(minScoreInput.value, 10) || 65;
      const res = await fetch(`/api/cdp/scan?min_score=${minScore}`);
      const data = await res.json();

      if (data.success && data.jobs) {
        renderJobs(data.jobs);
        updateMetrics(data.jobs);
      } else {
        alert("Could not scan page: " + (data.error || "No active jobs found on page."));
      }
    } catch (e) {
      alert("Scan failed: " + e.message);
    } finally {
      btnStartScan.disabled = false;
      btnStartScan.textContent = "🔎 Manual Scan Current Page";
    }
  }

  // 7. 1-Click Batch Auto Apply
  async function runBatchApply() {
    const minScore = parseInt(minScoreInput.value, 10) || 65;
    if (!confirm(`Launch 1-Click Batch Apply on Naukri for jobs with >= ${minScore}% match?`)) return;

    btnStartJobber.disabled = true;
    btnStartJobber.textContent = "Applying Batch...";
    try {
      const res = await fetch(`/api/cdp/apply_batch?min_score=${minScore}`);
      const data = await res.json();

      if (data.success) {
        if (data.applied_count > 0) {
          alert(`🎉 ${data.message}`);
          scanPage();
        } else {
          alert(data.message || "No eligible jobs found to apply on this screen.");
        }
      } else {
        alert("Batch apply failed: " + (data.error || "Unknown error"));
      }
    } catch (e) {
      alert("Application error: " + e.message);
    } finally {
      btnStartJobber.disabled = false;
      btnStartJobber.textContent = "🚀 1-Click Batch Apply";
    }
  }

  // 8. Render Jobs Table
  function renderJobs(jobs) {
    if (!jobs || jobs.length === 0) {
      jobsTableBody.innerHTML = `
        <tr class="empty-row">
          <td colspan="5">
            <div class="empty-state">
              <div class="empty-icon">⚠️</div>
              <p>No job postings found on the current tab. Ensure you are on a Naukri search results page.</p>
            </div>
          </td>
        </tr>
      `;
      return;
    }

    jobsTableBody.innerHTML = "";
    jobs.forEach(job => {
      const tr = document.createElement("tr");

      const score = Math.round(job.match_score || 0);
      let scoreClass = "score-low";
      if (score >= 70) scoreClass = "score-high";
      else if (score >= 50) scoreClass = "score-med";

      const statusTag = job.applied ?
        `<span class="badge badge-success">Applied</span>` :
        `<span class="badge badge-warning">Scored</span>`;

      tr.innerHTML = `
        <td>
          <a href="${job.url || '#'}" target="_blank" style="color: #93c5fd; text-decoration: none; font-weight: 600;">
            ${escapeHtml(job.title)}
          </a>
          <div style="font-size: 0.75rem; color: #6b7280;">${escapeHtml(job.experience || 'Exp not specified')} • ${escapeHtml(job.location || 'India')}</div>
        </td>
        <td style="font-weight: 500;">${escapeHtml(job.company)}</td>
        <td><span class="score-badge ${scoreClass}">${score}%</span></td>
        <td style="font-size: 0.75rem; color: #9ca3af; max-width: 260px;">${escapeHtml(job.matched_skills ? job.matched_skills.join(', ') : job.tech_skills || '-')}</td>
        <td>${statusTag}</td>
      `;
      jobsTableBody.appendChild(tr);
    });
  }

  function updateMetrics(jobs) {
    if (!jobs || jobs.length === 0) return;
    const totalScore = jobs.reduce((acc, j) => acc + (j.match_score || 0), 0);
    const avg = Math.round(totalScore / jobs.length);
    metricAvgMatch.textContent = `${avg}%`;

    const appliedCount = jobs.filter(j => j.applied).length;
    metricApplied.textContent = appliedCount;
  }

  function escapeHtml(text) {
    if (!text) return "";
    return text.replace(/[&<>"']/g, m => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
    }[m]));
  }

  // Event Listeners
  btnCheckCdp.addEventListener("click", checkCdpStatus);
  btnStartScan.addEventListener("click", scanPage);
  btnStartJobber.addEventListener("click", runBatchApply);

  // Init & Periodic Polling
  loadProfileAndConfig();
  checkCdpStatus();

  setInterval(checkCdpStatus, 10000);
  setInterval(pollAgentStatus, 2000);
  setInterval(pollTerminalLogs, 1500);
});

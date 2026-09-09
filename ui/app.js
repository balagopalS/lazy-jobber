// Lazy-Jobber Web UI Client Logic
document.addEventListener("DOMContentLoaded", () => {
  const connectionBadge = document.getElementById("connectionStatusBadge");
  const connectionText = document.getElementById("connectionText");
  const btnCheckCdp = document.getElementById("btnCheckCdp");
  const btnStartScan = document.getElementById("btnStartScan");
  const btnStartJobber = document.getElementById("btnStartJobber");
  const btnStopJobber = document.getElementById("btnStopJobber");
  const btnClearLog = document.getElementById("btnClearLog");

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
  let isRunning = false;
  let pollInterval = null;

  // 1. Fetch Candidate Profile & Config
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
      }
    } catch (e) {
      console.error("Error loading profile:", e);
    }
  }

  // 2. Check Chrome CDP Status
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

  // 3. Scan Current Naukri Page
  async function scanPage() {
    btnStartScan.disabled = true;
    btnStartScan.textContent = "Scanning...";
    metricStatus.textContent = "Scanning";
    metricStatus.className = "metric-value status-running";
    metricStatusSub.textContent = "Reading active tab";

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
      btnStartScan.textContent = "🔎 Scan Current Page";
      metricStatus.textContent = "Ready";
      metricStatus.className = "metric-value status-idle";
      metricStatusSub.textContent = "Awaiting command";
    }
  }

  // 4. Batch 1-Click Auto Apply (Up to 5 at a time)
  async function runBatchApply() {
    const minScore = parseInt(minScoreInput.value, 10) || 65;
    if (!confirm(`Launch 1-Click Batch Apply on Naukri for jobs with >= ${minScore}% match?`)) return;

    btnStartJobber.disabled = true;
    btnStartJobber.textContent = "Applying Batch...";
    metricStatus.textContent = "Applying";
    metricStatus.className = "metric-value status-running";
    metricStatusSub.textContent = "Checking boxes & applying";

    try {
      const res = await fetch(`/api/cdp/apply_batch?min_score=${minScore}`);
      const data = await res.json();

      if (data.success) {
        if (data.applied_count > 0) {
          alert(`🎉 ${data.message}`);
          // Refresh list to update state
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
      btnStartJobber.textContent = "🚀 Launch Auto-Apply";
      metricStatus.textContent = "Ready";
      metricStatus.className = "metric-value status-idle";
      metricStatusSub.textContent = "Idle";
    }
  }

  // 5. Render Jobs in Table
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
  btnClearLog.addEventListener("click", () => {
    renderJobs([]);
    metricApplied.textContent = "0";
    metricAvgMatch.textContent = "0%";
  });

  const btnRestartAll = document.getElementById("btnRestartAll");
  if (btnRestartAll) {
    btnRestartAll.addEventListener("click", async () => {
      if (!confirm("Are you sure you want to kill lingering background tasks and reboot the server?")) return;
      btnRestartAll.disabled = true;
      btnRestartAll.textContent = "Rebooting...";
      try {
        await fetch("/api/system/restart");
      } catch (e) {
        // Expected if server kills itself immediately
      }
      setTimeout(() => {
        window.location.reload();
      }, 2500);
    });
  }

  // Init
  loadProfileAndConfig();
  checkCdpStatus();
});

/**
 * AI Resume Analyzer - Dashboard Page Logic
 */

document.addEventListener("DOMContentLoaded", async () => {
  if (!Auth.requireAuth()) return;

  await loadSystemHealth();
  await loadDashboardData();
});

async function loadSystemHealth() {
  const healthBadge = document.getElementById("systemHealthBadge");
  if (!healthBadge) return;

  try {
    const health = await API.getHealth();
    healthBadge.innerHTML = `
      <span class="system-tag online">● Core Online</span>
      <span class="system-tag">AI Provider: <strong>${health.active_ai_provider}</strong></span>
      <span class="system-tag">RAG Docs: <strong>${health.rag_documents_count}</strong></span>
    `;
  } catch (err) {
    healthBadge.innerHTML = `<span class="system-tag" style="color:var(--danger)">● Offline</span>`;
  }
}

async function loadDashboardData() {
  const resumeContainer = document.getElementById("dashboardResumeSection");
  const recsContainer = document.getElementById("dashboardRecsSection");
  const statsResumes = document.getElementById("statResumesCount");
  const statsJobs = document.getElementById("statJobsCount");
  const statsSkills = document.getElementById("statSkillsCount");
  const statsWeaknesses = document.getElementById("statWeaknessesCount");

  try {
    // 1. Fetch user resumes
    const resumeRes = await API.getResumes();
    const resumes = resumeRes.resumes || [];
    if (statsResumes) statsResumes.textContent = resumes.length;

    // 2. Fetch jobs count
    const jobsRes = await API.listJobs(0, 1);
    if (statsJobs) statsJobs.textContent = jobsRes.total || 0;

    if (resumes.length === 0) {
      if (resumeContainer) {
        resumeContainer.innerHTML = `
          <div class="card" style="text-align: center; padding: 48px 24px;">
            <div style="font-size: 3rem; margin-bottom: 16px;">📄</div>
            <h3>No Resumes Uploaded Yet</h3>
            <p style="margin: 8px auto 24px;">Upload your first resume in PDF or DOCX format to trigger the AI Analyzer Agent and unlock job matching.</p>
            <div>
              <a href="resume.html" class="btn btn-primary">Upload Resume Now</a>
            </div>
          </div>
        `;
      }
      if (recsContainer) {
        recsContainer.innerHTML = `
          <p style="color:var(--ink-muted); text-align:center; padding: 24px;">
            Job recommendations will appear here after you upload and analyze a resume.
          </p>
        `;
      }
      return;
    }

    // Active resume (most recent)
    const activeResume = resumes[0];

    // Try fetching analysis for active resume
    let analysis = null;
    try {
      analysis = await API.getResumeAnalysis(activeResume.id);
    } catch (e) {
      // Not analyzed yet
    }

    if (analysis) {
      if (statsSkills) statsSkills.textContent = (analysis.technical_skills || []).length;
      if (statsWeaknesses) statsWeaknesses.textContent = (analysis.weaknesses || []).length;

      const skillsHtml = (analysis.technical_skills || []).slice(0, 8).map(s => 
        `<span class="badge badge-indigo">${Utils.escapeHtml(s)}</span>`
      ).join(" ");

      if (resumeContainer) {
        resumeContainer.innerHTML = `
          <div class="card">
            <div class="card-header">
              <div>
                <span class="badge badge-cyan" style="margin-bottom:6px;">Active Resume Profile</span>
                <h3 class="card-title">${Utils.escapeHtml(analysis.candidate_name || activeResume.filename)}</h3>
                <div class="card-description">Analyzed via <strong>${Utils.escapeHtml(analysis.ai_provider_used)}</strong> • ${Utils.formatDate(analysis.created_at)}</div>
              </div>
              <a href="resume.html?id=${activeResume.id}" class="btn btn-outline btn-sm">Full Analysis & Edit</a>
            </div>
            
            <p style="margin-bottom: 16px;">${Utils.escapeHtml(analysis.professional_summary || 'Professional profile extracted.')}</p>
            
            <div style="margin-bottom: 16px;">
              <div style="font-size:0.8125rem; color:var(--ink-muted); margin-bottom: 6px; text-transform:uppercase; font-weight:600;">Key Technical Competencies</div>
              <div class="skills-cloud">${skillsHtml}</div>
            </div>

            <div style="display:flex; gap: 12px; flex-wrap:wrap; padding-top: 12px; border-top:1px solid var(--border-subtle);">
              <a href="resume.html?id=${activeResume.id}&tab=recommendations" class="btn btn-primary btn-sm">View Job Matches</a>
              <a href="career.html?resume_id=${activeResume.id}" class="btn btn-secondary btn-sm">Ask Career Advisor</a>
            </div>
          </div>
        `;
      }

      // Fetch or generate recommendations
      loadActiveResumeRecommendations(activeResume.id, recsContainer);

    } else {
      // Resume exists but not analyzed
      if (resumeContainer) {
        resumeContainer.innerHTML = `
          <div class="card">
            <div class="card-header">
              <div>
                <h3 class="card-title">${Utils.escapeHtml(activeResume.filename)}</h3>
                <div class="card-description">Uploaded ${Utils.formatDate(activeResume.created_at)} (${Utils.formatFileSize(activeResume.file_size_bytes)})</div>
              </div>
              <button id="triggerAnalyzeBtn" class="btn btn-primary btn-sm">Run AI Analyzer</button>
            </div>
            <p>Your resume is uploaded. Click the button above to run the Resume Analyzer Agent (Agent 1) to extract structured skills and insights.</p>
          </div>
        `;

        document.getElementById("triggerAnalyzeBtn")?.addEventListener("click", async () => {
          const btn = document.getElementById("triggerAnalyzeBtn");
          btn.disabled = true;
          btn.innerHTML = `<span class="spinner"></span> Analyzing...`;
          try {
            await API.analyzeResume(activeResume.id);
            window.location.reload();
          } catch (err) {
            Utils.showToast(err.message, "error");
            btn.disabled = false;
            btn.textContent = "Run AI Analyzer";
          }
        });
      }
    }

  } catch (err) {
    console.error("Dashboard error:", err);
    Utils.showToast(err.message || "Failed to load dashboard data.", "error");
  }
}

async function loadActiveResumeRecommendations(resumeId, container) {
  if (!container) return;

  try {
    container.innerHTML = `<div class="skeleton" style="height: 120px; border-radius: 12px;"></div>`;
    
    // Check if recommendations already exist
    let recsRes = await API.getRecommendations(resumeId);
    if (!recsRes.recommendations || recsRes.recommendations.length === 0) {
      // Auto-trigger calculation
      recsRes = await API.generateRecommendations(resumeId);
    }

    const recs = recsRes.recommendations || [];
    if (recs.length === 0) {
      container.innerHTML = `<p style="color:var(--ink-muted);">No job listings match this resume yet.</p>`;
      return;
    }

    const top3 = recs.slice(0, 3);
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap: 16px;">
        ${top3.map(r => `
          <div class="card" style="padding: 16px 20px;">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom: 8px;">
              <div>
                <h4 style="font-size: 1rem; color: var(--ink-primary);">${Utils.escapeHtml(r.job ? r.job.title : 'Target Job')}</h4>
                <div style="font-size: 0.8125rem; color: var(--ink-muted);">${Utils.escapeHtml(r.job ? r.job.company : 'Company')} • ${Utils.escapeHtml(r.job ? r.job.location : 'Remote')}</div>
              </div>
              ${Utils.renderScoreBadge(r.match_score)}
            </div>
            
            <p style="font-size: 0.875rem; margin-bottom: 12px;">${Utils.escapeHtml(r.match_explanation)}</p>

            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
              <div style="display:flex; gap: 6px; flex-wrap:wrap;">
                ${(r.matching_skills || []).slice(0, 3).map(s => `<span class="badge badge-matched">✓ ${Utils.escapeHtml(s)}</span>`).join(" ")}
                ${(r.missing_skills || []).slice(0, 2).map(s => `<span class="badge badge-missing">Missing: ${Utils.escapeHtml(s)}</span>`).join(" ")}
              </div>
              <a href="job-details.html?id=${r.job_id}&resume_id=${resumeId}" class="btn btn-outline btn-sm">Inspect Breakdown →</a>
            </div>
          </div>
        `).join("")}
      </div>
    `;

  } catch (err) {
    console.error("Recs error:", err);
    container.innerHTML = `<p style="color:var(--ink-muted);">Click 'View Job Matches' to inspect recommendation rankings.</p>`;
  }
}

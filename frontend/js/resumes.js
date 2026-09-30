/**
 * AI Resume Analyzer - Resumes & Analysis Page Logic
 */

let currentResumeId = null;
let currentAnalysis = null;

document.addEventListener("DOMContentLoaded", async () => {
  if (!Auth.requireAuth()) return;

  setupUploadZone();
  setupTabNavigation();

  // Check URL query param for resume_id
  const urlParams = new URLSearchParams(window.location.search);
  const paramId = urlParams.get("id");
  const paramTab = urlParams.get("tab");

  await loadResumesList(paramId);

  if (paramTab) {
    switchTab(paramTab);
  }
});

function setupUploadZone() {
  const dropZone = document.getElementById("resumeDropZone");
  const fileInput = document.getElementById("resumeFileInput");

  if (!dropZone || !fileInput) return;

  dropZone.addEventListener("click", () => fileInput.click());

  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("dragover");
  });

  dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("dragover");
  });

  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("dragover");
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener("change", () => {
    if (fileInput.files && fileInput.files.length > 0) {
      handleFileUpload(fileInput.files[0]);
    }
  });
}

async function handleFileUpload(file) {
  // Validate extension
  const ext = file.name.split(".").pop().toLowerCase();
  if (!["pdf", "docx"].includes(ext)) {
    Utils.showToast("Unsupported file type. Please upload a PDF or DOCX resume.", "error");
    return;
  }

  // Validate size (10 MB)
  if (file.size > 10 * 1024 * 1024) {
    Utils.showToast("File exceeds 10MB limit.", "error");
    return;
  }

  const dropZone = document.getElementById("resumeDropZone");
  const originalHtml = dropZone.innerHTML;
  dropZone.innerHTML = `
    <div class="spinner" style="width: 36px; height: 36px;"></div>
    <p style="margin-top: 12px; font-weight: 500;">Uploading and parsing ${Utils.escapeHtml(file.name)}...</p>
  `;

  try {
    const formData = new FormData();
    formData.append("file", file);

    const res = await API.uploadResume(formData);
    Utils.showToast("Resume uploaded successfully! Initializing analysis...", "success");

    // Auto-trigger Agent 1 analysis
    await API.analyzeResume(res.id);
    Utils.showToast("AI Resume Analyzer Agent finished structured extraction!", "success");

    await loadResumesList(res.id);
  } catch (err) {
    Utils.showToast(err.message || "Failed to process resume.", "error");
  } finally {
    dropZone.innerHTML = originalHtml;
  }
}

async function loadResumesList(selectId = null) {
  const listContainer = document.getElementById("resumesList");
  if (!listContainer) return;

  try {
    const data = await API.getResumes();
    const resumes = data.resumes || [];

    if (resumes.length === 0) {
      listContainer.innerHTML = `<p style="color:var(--ink-muted); font-size:0.875rem;">No resumes uploaded yet.</p>`;
      document.getElementById("analysisContainer").style.display = "none";
      return;
    }

    listContainer.innerHTML = resumes.map(r => `
      <div class="resume-item-card ${r.id === Number(selectId) ? 'selected' : ''}" data-id="${r.id}" style="
        display: flex; justify-content: space-between; align-items: center; padding: 12px 16px;
        background: var(--surface-2); border: 1px solid var(--border-default); border-radius: 8px; margin-bottom: 8px; cursor: pointer;">
        <div>
          <div style="font-weight: 600; font-size: 0.9375rem; color: var(--ink-primary);">${Utils.escapeHtml(r.filename)}</div>
          <div style="font-size: 0.8125rem; color: var(--ink-muted);">${Utils.formatDate(r.created_at)} • ${Utils.formatFileSize(r.file_size_bytes)}</div>
        </div>
        <div style="display: flex; gap: 8px;">
          <button class="btn btn-outline btn-sm delete-resume-btn" data-id="${r.id}" title="Delete Resume">🗑</button>
        </div>
      </div>
    `).join("");

    // Attach click listeners
    document.querySelectorAll(".resume-item-card").forEach(el => {
      el.addEventListener("click", (e) => {
        if (e.target.closest(".delete-resume-btn")) return;
        const id = Number(el.getAttribute("data-id"));
        selectResume(id);
      });
    });

    document.querySelectorAll(".delete-resume-btn").forEach(btn => {
      btn.addEventListener("click", async (e) => {
        e.stopPropagation();
        const id = Number(btn.getAttribute("data-id"));
        if (confirm("Are you sure you want to delete this resume?")) {
          try {
            await API.deleteResume(id);
            Utils.showToast("Resume deleted.", "info");
            await loadResumesList();
          } catch (err) {
            Utils.showToast(err.message, "error");
          }
        }
      });
    });

    // Determine which resume to select
    const targetId = selectId ? Number(selectId) : resumes[0].id;
    selectResume(targetId);

  } catch (err) {
    console.error("Failed to load resumes:", err);
    Utils.showToast(err.message, "error");
  }
}

async function selectResume(resumeId) {
  currentResumeId = resumeId;
  const analysisContainer = document.getElementById("analysisContainer");
  if (!analysisContainer) return;

  analysisContainer.style.display = "block";

  // Highlight selected in list
  document.querySelectorAll(".resume-item-card").forEach(el => {
    if (Number(el.getAttribute("data-id")) === resumeId) {
      el.style.borderColor = "var(--border-focus)";
      el.style.backgroundColor = "var(--surface-3)";
    } else {
      el.style.borderColor = "var(--border-default)";
      el.style.backgroundColor = "var(--surface-2)";
    }
  });

  // Fetch or trigger analysis
  try {
    currentAnalysis = await API.getResumeAnalysis(resumeId);
    renderAnalysisData(currentAnalysis);
  } catch (e) {
    // Needs analysis
    renderUnanalyzedState(resumeId);
  }
}

function renderUnanalyzedState(resumeId) {
  const container = document.getElementById("tabOverview");
  if (!container) return;

  container.innerHTML = `
    <div style="text-align: center; padding: 48px 16px;">
      <h3>Ready for AI Analysis</h3>
      <p style="margin: 12px auto 24px;">Trigger Agent 1 to extract structured competencies, experience, strengths, and weaknesses from this resume.</p>
      <button id="runAnalyzeBtn" class="btn btn-primary btn-lg">Run Resume Analyzer Agent</button>
    </div>
  `;

  document.getElementById("runAnalyzeBtn")?.addEventListener("click", async () => {
    const btn = document.getElementById("runAnalyzeBtn");
    btn.disabled = true;
    btn.innerHTML = `<span class="spinner"></span> Analyzing with Agent 1...`;
    try {
      currentAnalysis = await API.analyzeResume(resumeId);
      Utils.showToast("Analysis complete!", "success");
      renderAnalysisData(currentAnalysis);
    } catch (err) {
      Utils.showToast(err.message, "error");
      btn.disabled = false;
      btn.textContent = "Run Resume Analyzer Agent";
    }
  });
}

function renderAnalysisData(analysis) {
  // Update Candidate Header
  const candName = document.getElementById("candidateName");
  const candContact = document.getElementById("candidateContact");
  const providerBadge = document.getElementById("analysisProviderBadge");

  if (candName) candName.textContent = analysis.candidate_name || "Applicant Profile";
  if (candContact) {
    const parts = [
      analysis.email ? `📧 ${analysis.email}` : null,
      analysis.phone ? `📞 ${analysis.phone}` : null,
      analysis.location ? `📍 ${analysis.location}` : null
    ].filter(Boolean);
    candContact.textContent = parts.join(" • ") || "Contact information extracted";
  }
  if (providerBadge) {
    providerBadge.textContent = `Analyzed by: ${analysis.ai_provider_used}`;
  }

  // 1. Tab Overview
  const tabOverview = document.getElementById("tabOverview");
  if (tabOverview) {
    tabOverview.innerHTML = `
      <div style="margin-bottom: 24px;">
        <h4 style="margin-bottom: 8px;">Professional Summary</h4>
        <p style="font-size: 1rem; line-height: 1.6;">${Utils.escapeHtml(analysis.professional_summary || 'No summary extracted.')}</p>
      </div>

      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px;">
        <div class="card" style="padding: 16px;">
          <h4 style="font-size: 0.9375rem; margin-bottom: 8px;">Certifications</h4>
          ${(analysis.certifications || []).length > 0
            ? analysis.certifications.map(c => `<div style="font-size:0.875rem; margin-bottom:4px;">🎖 ${Utils.escapeHtml(c)}</div>`).join("")
            : '<p style="font-size:0.8125rem; color:var(--ink-muted);">None listed in resume.</p>'
          }
        </div>
        <div class="card" style="padding: 16px;">
          <h4 style="font-size: 0.9375rem; margin-bottom: 8px;">Languages</h4>
          ${(analysis.languages || []).length > 0
            ? analysis.languages.map(l => `<span class="badge badge-indigo" style="margin-right:4px;">${Utils.escapeHtml(l)}</span>`).join("")
            : '<p style="font-size:0.8125rem; color:var(--ink-muted);">English</p>'
          }
        </div>
      </div>
    `;
  }

  // 2. Tab Skills
  const tabSkills = document.getElementById("tabSkills");
  if (tabSkills) {
    const techSkills = (analysis.technical_skills || []).map(s => `<span class="badge badge-indigo" style="font-size:0.875rem; padding: 6px 12px;">${Utils.escapeHtml(s)}</span>`).join(" ");
    const softSkills = (analysis.soft_skills || []).map(s => `<span class="badge badge-cyan" style="font-size:0.875rem; padding: 6px 12px;">${Utils.escapeHtml(s)}</span>`).join(" ");

    tabSkills.innerHTML = `
      <div style="margin-bottom: 28px;">
        <h4 style="margin-bottom: 12px;">Technical Skills & Tools (${(analysis.technical_skills || []).length})</h4>
        <div class="skills-cloud">${techSkills || '<p style="color:var(--ink-muted);">No technical skills extracted.</p>'}</div>
      </div>
      <div>
        <h4 style="margin-bottom: 12px;">Soft & Leadership Skills (${(analysis.soft_skills || []).length})</h4>
        <div class="skills-cloud">${softSkills || '<p style="color:var(--ink-muted);">No soft skills extracted.</p>'}</div>
      </div>
    `;
  }

  // 3. Tab Experience & Education
  const tabExperience = document.getElementById("tabExperience");
  if (tabExperience) {
    const expItems = (analysis.experience || []).map(exp => `
      <div class="timeline-item">
        <div class="timeline-title">${Utils.escapeHtml(exp.title || 'Role')} <span style="font-weight:400; color:var(--ink-secondary);">at ${Utils.escapeHtml(exp.company || 'Organization')}</span></div>
        <div class="timeline-meta">${Utils.escapeHtml(exp.duration || 'Duration not specified')}</div>
        <p style="font-size: 0.875rem;">${Utils.escapeHtml(exp.description || '')}</p>
      </div>
    `).join("");

    const eduItems = (analysis.education || []).map(edu => `
      <div class="timeline-item">
        <div class="timeline-title">${Utils.escapeHtml(edu.degree || 'Degree')}</div>
        <div class="timeline-meta">${Utils.escapeHtml(edu.institution || 'University')} • ${Utils.escapeHtml(edu.year || 'Completed')}</div>
        ${edu.field ? `<p style="font-size: 0.8125rem; color:var(--accent-cyan);">Major / Field: ${Utils.escapeHtml(edu.field)}</p>` : ''}
      </div>
    `).join("");

    tabExperience.innerHTML = `
      <div style="margin-bottom: 32px;">
        <h4 style="margin-bottom: 16px;">Work Experience</h4>
        <div class="timeline-list">${expItems || '<p style="color:var(--ink-muted);">No experience entries extracted.</p>'}</div>
      </div>
      <div>
        <h4 style="margin-bottom: 16px;">Education & Qualifications</h4>
        <div class="timeline-list">${eduItems || '<p style="color:var(--ink-muted);">No education entries extracted.</p>'}</div>
      </div>
    `;
  }

  // 4. Tab Insights (Strengths, Weaknesses, Improvements)
  const tabInsights = document.getElementById("tabInsights");
  if (tabInsights) {
    const strengthsHtml = (analysis.strengths || []).map(s => `<li>${Utils.escapeHtml(s)}</li>`).join("");
    const weaknessesHtml = (analysis.weaknesses || []).map(w => `<li>${Utils.escapeHtml(w)}</li>`).join("");
    const improvementsHtml = (analysis.recommended_improvements || []).map(imp => `
      <div style="padding: 10px 14px; background:var(--surface-2); border-left:3px solid var(--accent-cyan); border-radius:6px; margin-bottom:8px; font-size:0.875rem;">
        💡 ${Utils.escapeHtml(imp)}
      </div>
    `).join("");

    tabInsights.innerHTML = `
      <div class="insights-grid" style="margin-bottom: 24px;">
        <div class="insight-card strengths">
          <h4>Candidate Strengths</h4>
          <ul class="bullet-list strengths">${strengthsHtml}</ul>
        </div>
        <div class="insight-card weaknesses">
          <h4>Identified Weaknesses & Missing Details</h4>
          <ul class="bullet-list weaknesses">${weaknessesHtml}</ul>
        </div>
      </div>

      <div class="card">
        <h4 style="margin-bottom: 12px;">Recommended Resume Improvements</h4>
        <div>${improvementsHtml || '<p style="color:var(--ink-muted);">No improvement actions listed.</p>'}</div>
      </div>
    `;
  }

  // 5. Tab Recommendations
  loadRecommendationsTab(analysis.resume_id);
}

async function loadRecommendationsTab(resumeId) {
  const container = document.getElementById("tabRecommendations");
  if (!container) return;

  container.innerHTML = `<div class="skeleton" style="height: 160px; border-radius: 12px;"></div>`;

  try {
    let recsRes = await API.getRecommendations(resumeId);
    if (!recsRes.recommendations || recsRes.recommendations.length === 0) {
      recsRes = await API.generateRecommendations(resumeId);
    }

    const recs = recsRes.recommendations || [];
    if (recs.length === 0) {
      container.innerHTML = `<p style="color:var(--ink-muted); text-align:center; padding: 32px;">No matching jobs found in database. You can add jobs in the Job Directory.</p>`;
      return;
    }

    container.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 16px;">
        <h4>Ranked Job Recommendations (${recs.length})</h4>
        <button id="recalculateMatchesBtn" class="btn btn-outline btn-sm">🔄 Recalculate Matches</button>
      </div>

      <div style="display:flex; flex-direction:column; gap: 16px;">
        ${recs.map(r => `
          <div class="card">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom: 10px;">
              <div>
                <h3 style="font-size: 1.125rem; color: var(--ink-primary);">${Utils.escapeHtml(r.job ? r.job.title : 'Target Position')}</h3>
                <div style="font-size: 0.8125rem; color: var(--ink-muted);">${Utils.escapeHtml(r.job ? r.job.company : 'Company')} • ${Utils.escapeHtml(r.job ? r.job.location : 'Remote')} • ${Utils.escapeHtml(r.job ? r.job.employment_type : 'Full-time')}</div>
              </div>
              ${Utils.renderScoreBadge(r.match_score)}
            </div>

            <div class="breakdown-grid">
              <div class="breakdown-item">
                <div class="breakdown-title">Skill (40%)</div>
                <div class="breakdown-score">${Math.round(r.skill_score)}%</div>
              </div>
              <div class="breakdown-item">
                <div class="breakdown-title">Experience (25%)</div>
                <div class="breakdown-score">${Math.round(r.experience_score)}%</div>
              </div>
              <div class="breakdown-item">
                <div class="breakdown-title">Education (15%)</div>
                <div class="breakdown-score">${Math.round(r.education_score)}%</div>
              </div>
              <div class="breakdown-item">
                <div class="breakdown-title">Semantic (20%)</div>
                <div class="breakdown-score">${Math.round(r.semantic_score)}%</div>
              </div>
            </div>

            <p style="font-size: 0.9375rem; line-height: 1.5; margin-bottom: 14px;"><strong>AI Match Explanation:</strong> ${Utils.escapeHtml(r.match_explanation)}</p>

            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap: 12px;">
              <div style="display:flex; gap: 8px; flex-wrap:wrap;">
                ${(r.matching_skills || []).map(s => `<span class="badge badge-matched">✓ ${Utils.escapeHtml(s)}</span>`).join(" ")}
                ${(r.missing_skills || []).map(s => `<span class="badge badge-missing">Missing: ${Utils.escapeHtml(s)}</span>`).join(" ")}
              </div>
              <a href="job-details.html?id=${r.job_id}&resume_id=${resumeId}" class="btn btn-secondary btn-sm">Full Job Match Analysis →</a>
            </div>
          </div>
        `).join("")}
      </div>
    `;

    document.getElementById("recalculateMatchesBtn")?.addEventListener("click", async () => {
      container.innerHTML = `<div class="skeleton" style="height: 160px; border-radius: 12px;"></div>`;
      try {
        await API.generateRecommendations(resumeId);
        Utils.showToast("Recalculated recommendations with Agent 2!", "success");
        loadRecommendationsTab(resumeId);
      } catch (err) {
        Utils.showToast(err.message, "error");
      }
    });

  } catch (err) {
    console.error("Recommendations error:", err);
    container.innerHTML = `<p style="color:var(--danger);">Failed to load recommendations: ${Utils.escapeHtml(err.message)}</p>`;
  }
}

function setupTabNavigation() {
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const tabTarget = btn.getAttribute("data-tab");
      switchTab(tabTarget);
    });
  });
}

function switchTab(tabId) {
  document.querySelectorAll(".tab-btn").forEach(b => {
    b.classList.toggle("active", b.getAttribute("data-tab") === tabId);
  });
  document.querySelectorAll(".tab-pane").forEach(p => {
    p.classList.toggle("active", p.id === tabId);
  });
}

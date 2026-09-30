let currentJob = null;
let currentJobId = null;
let currentResumeId = null;
let isEditModalInitialized = false;

document.addEventListener("DOMContentLoaded", async () => {
  const urlParams = new URLSearchParams(window.location.search);
  const jobId = urlParams.get("id");
  let resumeId = urlParams.get("resume_id");

  if (!jobId) {
    Utils.showToast("No job ID provided.", "error");
    setTimeout(() => window.location.href = "jobs.html", 500);
    return;
  }

  currentJobId = jobId;

  // If resume_id wasn't in URL, check if logged in user has resumes
  if (!resumeId && API.getToken()) {
    try {
      const resData = await API.getResumes();
      if (resData.resumes && resData.resumes.length > 0) {
        resumeId = resData.resumes[0].id;
      }
    } catch (e) {
      // Ignore
    }
  }

  currentResumeId = resumeId;
  setupEditModalEvents();
  await loadJobAndMatch(jobId, resumeId);
});

function setupEditModalEvents() {
  if (isEditModalInitialized) return;
  isEditModalInitialized = true;

  const closeBtn = document.getElementById("closeEditJobModalBtn");
  const cancelBtn = document.getElementById("cancelEditJobBtn");
  const editForm = document.getElementById("editJobForm");

  closeBtn?.addEventListener("click", () => Utils.closeModal("editJobModal"));
  cancelBtn?.addEventListener("click", () => Utils.closeModal("editJobModal"));

  editForm?.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!currentJob) return;

    const title = document.getElementById("editJobTitle").value.trim();
    const company = document.getElementById("editJobCompany").value.trim();
    const description = document.getElementById("editJobDesc").value.trim();
    const skillsRaw = document.getElementById("editJobSkills").value.trim();
    const prefSkillsRaw = document.getElementById("editJobPrefSkills").value.trim();
    const expYears = parseFloat(document.getElementById("editJobExp").value) || 0.0;
    const eduLevel = document.getElementById("editJobEdu").value.trim();
    const location = document.getElementById("editJobLocation").value.trim() || "Remote";
    const empType = document.getElementById("editJobType").value;
    const salary = document.getElementById("editJobSalary").value.trim() || null;
    const contactEmail = document.getElementById("editJobContactEmail").value.trim() || null;

    const required_skills = skillsRaw
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);

    const preferred_skills = prefSkillsRaw
      ? prefSkillsRaw
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean)
      : [];

    const saveBtn = document.getElementById("saveEditJobBtn");
    const originalText = saveBtn ? saveBtn.textContent : "Save Changes";
    if (saveBtn) {
      saveBtn.disabled = true;
      saveBtn.textContent = "Saving...";
    }

    try {
      await API.updateJob(currentJob.id, {
        title,
        company,
        description,
        required_skills,
        preferred_skills,
        experience_years: expYears,
        education_level: eduLevel,
        location,
        employment_type: empType,
        salary_range: salary,
        contact_email: contactEmail,
      });

      Utils.showToast("Job posting updated successfully!", "success");
      Utils.closeModal("editJobModal");
      await loadJobAndMatch(currentJobId, currentResumeId);
    } catch (err) {
      Utils.showToast(err.message || "Failed to update job posting.", "error");
    } finally {
      if (saveBtn) {
        saveBtn.disabled = false;
        saveBtn.textContent = originalText;
      }
    }
  });
}

function openEditModal(job) {
  document.getElementById("editJobTitle").value = job.title || "";
  document.getElementById("editJobCompany").value = job.company || "";
  document.getElementById("editJobDesc").value = job.description || "";
  document.getElementById("editJobSkills").value = (job.required_skills || []).join(", ");
  document.getElementById("editJobPrefSkills").value = (job.preferred_skills || []).join(", ");
  document.getElementById("editJobExp").value = job.experience_years ?? 0;
  document.getElementById("editJobEdu").value = job.education_level || "Bachelor's";
  document.getElementById("editJobLocation").value = job.location || "Remote";
  document.getElementById("editJobType").value = job.employment_type || "Full-time";
  document.getElementById("editJobSalary").value = job.salary_range || "";
  document.getElementById("editJobContactEmail").value = job.contact_email || "";

  Utils.openModal("editJobModal");
}

async function loadJobAndMatch(jobId, resumeId) {
  const jobContainer = document.getElementById("jobDetailCard");
  const matchContainer = document.getElementById("jobMatchPanel");

  try {
    const job = await API.getJob(jobId);
    currentJob = job;

    const breadcrumb = document.getElementById("breadcrumbJobTitle");
    if (breadcrumb) breadcrumb.textContent = job.title;

    // Render Job Details Card
    jobContainer.innerHTML = `
      <div class="card-header">
        <div>
          <span class="badge badge-indigo" style="margin-bottom:6px;">${Utils.escapeHtml(job.employment_type)}</span>
          <h2 class="card-title">${Utils.escapeHtml(job.title)}</h2>
          <div class="card-description" style="font-size:1rem; color:var(--accent-cyan); font-weight:600;">
            ${Utils.escapeHtml(job.company)} • 📍 ${Utils.escapeHtml(job.location)}
          </div>
        </div>
        <div style="text-align:right;">
          ${job.salary_range ? `<div style="font-size:1.125rem; font-weight:700; color:var(--success); font-family:var(--font-mono);">${Utils.escapeHtml(job.salary_range)}</div>` : ''}
          <div style="font-size:0.8125rem; color:var(--ink-muted);">Posted ${Utils.formatDate(job.created_at)}</div>
        </div>
      </div>

      <div style="display:flex; gap:16px; margin: 16px 0; flex-wrap:wrap; font-size:0.875rem; color:var(--ink-secondary);">
        <div><strong>Experience Required:</strong> ${job.experience_years} Years</div>
        <div><strong>Education:</strong> ${Utils.escapeHtml(job.education_level)}</div>
      </div>

      <div style="margin: 24px 0;">
        <h4 style="margin-bottom: 8px;">Job Description</h4>
        <div style="font-size: 0.9375rem; line-height: 1.6; white-space: pre-line; color: var(--ink-secondary);">
          ${Utils.escapeHtml(job.description)}
        </div>
      </div>

      <div style="margin: 24px 0;">
        <h4 style="margin-bottom: 10px;">Mandatory Technical Requirements</h4>
        <div class="skills-cloud">
          ${(job.required_skills || []).map(s => `<span class="badge badge-indigo" style="font-size:0.875rem; padding:6px 12px;">${Utils.escapeHtml(s)}</span>`).join(" ")}
        </div>
      </div>

      ${(job.preferred_skills || []).length > 0 ? `
        <div style="margin: 20px 0;">
          <h4 style="margin-bottom: 10px;">Preferred / Nice-to-Have Skills</h4>
          <div class="skills-cloud">
            ${job.preferred_skills.map(s => `<span class="badge badge-cyan" style="font-size:0.875rem; padding:6px 12px;">${Utils.escapeHtml(s)}</span>`).join(" ")}
          </div>
        </div>
      ` : ''}

      ${job.contact_email ? `
        <div style="margin: 24px 0; padding: 20px; background: linear-gradient(135deg, rgba(99, 102, 241, 0.08), rgba(6, 182, 212, 0.08)); border-radius: 12px; border: 1px solid var(--border-subtle);">
          <h4 style="margin-bottom: 8px; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 1.25rem;">📧</span> Apply for This Position
          </h4>
          <p style="font-size: 0.875rem; color: var(--ink-secondary); margin-bottom: 12px;">
            Interested in this role? Send your application to the contact below:
          </p>
          <a href="mailto:${Utils.escapeHtml(job.contact_email)}?subject=${encodeURIComponent('Application for: ' + job.title)}"
             class="btn btn-primary" style="display: inline-flex; align-items: center; gap: 8px;">
            ✉️ ${Utils.escapeHtml(job.contact_email)}
          </a>
        </div>
      ` : ''}

      <div style="margin-top: 32px; border-top: 1px solid var(--border-subtle); padding-top: 16px; display:flex; justify-content:space-between; align-items:center;">
        <a href="jobs.html" class="btn btn-outline btn-sm">← Back to Job Directory</a>
        <div style="display:flex; gap:8px;">
          <button id="editJobActionBtn" class="btn btn-outline btn-sm" style="display:none;">✏️ Edit Job</button>
          <button id="deleteJobActionBtn" class="btn btn-danger btn-sm" style="display:none;">Delete Job Posting</button>
        </div>
      </div>
    `;

    // Check if user is admin or creator
    const user = API.getUser();
    if (user && (user.role === "admin" || user.id === job.created_by_user_id)) {
      const editBtn = document.getElementById("editJobActionBtn");
      const delBtn = document.getElementById("deleteJobActionBtn");

      if (editBtn) {
        editBtn.style.display = "inline-flex";
        editBtn.addEventListener("click", () => openEditModal(job));
      }

      if (delBtn) {
        delBtn.style.display = "inline-flex";
        delBtn.addEventListener("click", async () => {
          if (confirm("Are you sure you want to delete this job posting?")) {
            try {
              await API.deleteJob(job.id);
              Utils.showToast("Job posting deleted.", "info");
              setTimeout(() => window.location.href = "jobs.html", 500);
            } catch (err) {
              Utils.showToast(err.message, "error");
            }
          }
        });
      }
    }

    // Match Evaluation Panel
    if (!resumeId) {
      matchContainer.innerHTML = `
        <div class="card" style="text-align:center; padding: 32px 16px;">
          <div style="font-size:2rem; margin-bottom:12px;">🎯</div>
          <h3>Benchmark Your Resume</h3>
          <p style="margin:8px auto 20px;">Log in and upload a resume to calculate transparent multi-factor compatibility scores and missing skills.</p>
          <a href="resume.html" class="btn btn-primary btn-sm">Upload Resume</a>
        </div>
      `;
      return;
    }

    matchContainer.innerHTML = `<div class="skeleton" style="height: 240px; border-radius:12px;"></div>`;

    // Fetch Live Match
    const match = await API.getLiveJobMatch(resumeId, jobId);

    matchContainer.innerHTML = `
      <div class="card" style="border-color: var(--border-focus);">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom: 16px;">
          <div>
            <span class="badge badge-cyan" style="margin-bottom:6px;">Multi-Factor Match Score</span>
            <h3 style="font-size:1.25rem;">Candidate Alignment</h3>
          </div>
          ${Utils.renderScoreBadge(match.match_score)}
        </div>

        <div class="progress-track" style="margin-bottom: 20px;">
          <div class="progress-bar" style="width: ${match.match_score}%;"></div>
        </div>

        <div style="font-size:0.75rem; text-transform:uppercase; color:var(--ink-muted); font-weight:600; margin-bottom:8px;">
          Transparent Formula Breakdown:
        </div>
        <div class="breakdown-grid">
          <div class="breakdown-item">
            <div class="breakdown-title">Skill Match (40%)</div>
            <div class="breakdown-score">${Math.round(match.skill_score)}%</div>
          </div>
          <div class="breakdown-item">
            <div class="breakdown-title">Experience (25%)</div>
            <div class="breakdown-score">${Math.round(match.experience_score)}%</div>
          </div>
          <div class="breakdown-item">
            <div class="breakdown-title">Education (15%)</div>
            <div class="breakdown-score">${Math.round(match.education_score)}%</div>
          </div>
          <div class="breakdown-item">
            <div class="breakdown-title">Semantic (20%)</div>
            <div class="breakdown-score">${Math.round(match.semantic_score)}%</div>
          </div>
        </div>

        <div style="margin: 20px 0;">
          <h4 style="font-size:0.9375rem; margin-bottom:8px;">Job Matching Agent Explanation</h4>
          <p style="font-size:0.875rem; line-height:1.5;">${Utils.escapeHtml(match.match_explanation)}</p>
        </div>

        <div style="margin-bottom: 16px;">
          <div style="font-size:0.8125rem; font-weight:600; color:var(--success); margin-bottom:6px;">Matching Skills Found:</div>
          <div class="skills-cloud">
            ${(match.matching_skills || []).length > 0
              ? match.matching_skills.map(s => `<span class="badge badge-matched">✓ ${Utils.escapeHtml(s)}</span>`).join(" ")
              : '<span style="font-size:0.8125rem; color:var(--ink-muted);">None directly matched</span>'
            }
          </div>
        </div>

        <div style="margin-bottom: 24px;">
          <div style="font-size:0.8125rem; font-weight:600; color:var(--warning); margin-bottom:6px;">Skill Gaps to Bridge:</div>
          <div class="skills-cloud">
            ${(match.missing_skills || []).length > 0
              ? match.missing_skills.map(s => `<span class="badge badge-missing">Missing: ${Utils.escapeHtml(s)}</span>`).join(" ")
              : '<span style="font-size:0.8125rem; color:var(--success);">All mandatory skills covered!</span>'
            }
          </div>
        </div>

        <div style="border-top:1px solid var(--border-subtle); padding-top:16px;">
          <a href="career.html?target_role=${encodeURIComponent(job.title)}&resume_id=${resumeId}" class="btn btn-primary" style="width:100%;">
            Ask Career Advisor How to Land This Role →
          </a>
        </div>
      </div>
    `;

  } catch (err) {
    console.error("Job details load error:", err);
    jobContainer.innerHTML = `<p style="color:var(--danger);">Error: ${Utils.escapeHtml(err.message)}</p>`;
  }
}

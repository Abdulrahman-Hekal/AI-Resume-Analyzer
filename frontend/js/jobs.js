/**
 * AI Resume Analyzer - Job Directory & Search Logic
 */

let activeUserResumes = [];

document.addEventListener("DOMContentLoaded", async () => {
  setupFilters();
  setupJobModal();
  await checkActiveUserResumes();
  await loadJobs();
});

async function checkActiveUserResumes() {
  if (!API.getToken()) return;
  try {
    const res = await API.getResumes();
    activeUserResumes = res.resumes || [];
  } catch (e) {
    // Ignore if not logged in
  }
}

function setupFilters() {
  const searchInput = document.getElementById("jobSearchInput");
  const skillInput = document.getElementById("jobSkillFilter");
  const expSelect = document.getElementById("jobExpFilter");
  const typeSelect = document.getElementById("jobTypeFilter");

  let debounceTimer = null;
  const triggerSearch = () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      loadJobs();
    }, 300);
  };

  searchInput?.addEventListener("input", triggerSearch);
  skillInput?.addEventListener("input", triggerSearch);
  expSelect?.addEventListener("change", triggerSearch);
  typeSelect?.addEventListener("change", triggerSearch);

  document.getElementById("clearFiltersBtn")?.addEventListener("click", () => {
    if (searchInput) searchInput.value = "";
    if (skillInput) skillInput.value = "";
    if (expSelect) expSelect.value = "";
    if (typeSelect) typeSelect.value = "";
    loadJobs();
  });
}

async function loadJobs() {
  const container = document.getElementById("jobsListContainer");
  const countBadge = document.getElementById("jobsCountBadge");
  if (!container) return;

  container.innerHTML = `<div class="skeleton" style="height: 180px; border-radius: 12px;"></div>`;

  const params = { limit: 50 };
  const q = document.getElementById("jobSearchInput")?.value.trim();
  if (q) params.q = q;

  const skill = document.getElementById("jobSkillFilter")?.value.trim();
  if (skill) params.skill = skill;

  const expVal = document.getElementById("jobExpFilter")?.value;
  if (expVal && !isNaN(parseFloat(expVal))) {
    params.max_exp = parseFloat(expVal);
  }

  const empType = document.getElementById("jobTypeFilter")?.value;
  if (empType) params.employment_type = empType;

  try {
    const data = await API.searchJobs(params);

    const jobs = data.jobs || [];
    if (countBadge) countBadge.textContent = `${data.total} Jobs`;

    if (jobs.length === 0) {
      container.innerHTML = `
        <div class="card" style="text-align: center; padding: 48px 24px; grid-column: 1 / -1;">
          <h3>No Jobs Found Matching Criteria</h3>
          <p style="margin-top: 8px;max-width:100%;">Try clearing filters or search for another keyword.</p>
        </div>
      `;
      return;
    }

    const defaultResumeId =
      activeUserResumes.length > 0 ? activeUserResumes[0].id : null;

    container.innerHTML = jobs
      .map((j) => {
        const detailUrl = defaultResumeId
          ? `job-details.html?id=${j.id}&resume_id=${defaultResumeId}`
          : `job-details.html?id=${j.id}`;

        return `
        <div class="job-card">
          <div>
            <div class="job-card-header">
              <div>
                <h3 style="font-size: 1.125rem; color: var(--ink-primary); margin-bottom: 2px;">
                  <a href="${detailUrl}">${Utils.escapeHtml(j.title)}</a>
                </h3>
                <div style="font-size: 0.875rem; color: var(--accent-cyan); font-weight: 500;">
                  ${Utils.escapeHtml(j.company)}
                </div>
              </div>
              <span class="badge badge-indigo">${Utils.escapeHtml(j.employment_type)}</span>
            </div>

            <div class="job-meta-row" style="margin: 8px 0 12px;">
              <span>📍 ${Utils.escapeHtml(j.location)}</span>
              <span>🎓 ${Utils.escapeHtml(j.education_level)}</span>
              <span>⏱ ${j.experience_years} yrs exp</span>
              ${j.salary_range ? `<span>💰 ${Utils.escapeHtml(j.salary_range)}</span>` : ""}
              ${j.contact_email ? `<span>📧 <a href="mailto:${Utils.escapeHtml(j.contact_email)}" style="color:var(--accent-cyan); text-decoration:none;">${Utils.escapeHtml(j.contact_email)}</a></span>` : ""}
            </div>

            <p style="font-size: 0.875rem; line-height: 1.4; margin-bottom: 14px;">
              ${Utils.escapeHtml(j.description.length > 180 ? j.description.substring(0, 180) + "..." : j.description)}
            </p>

            <div class="skills-cloud" style="margin-bottom: 12px;">
              ${(j.required_skills || [])
                .slice(0, 5)
                .map(
                  (s) =>
                    `<span class="badge badge-indigo">${Utils.escapeHtml(s)}</span>`,
                )
                .join(" ")}
              ${(j.required_skills || []).length > 5 ? `<span class="badge" style="background:var(--surface-3);">+${j.required_skills.length - 5}</span>` : ""}
            </div>
          </div>

          <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid var(--border-subtle); padding-top: 12px;">
            <span style="font-size: 0.75rem; color: var(--ink-muted);">Posted ${Utils.formatDate(j.created_at)}</span>
            <a href="${detailUrl}" class="btn btn-outline btn-sm">View Details & Match →</a>
          </div>
        </div>
      `;
      })
      .join("");
  } catch (err) {
    console.error("Failed to load jobs:", err);
    container.innerHTML = `<p style="color:var(--danger);">Error loading jobs: ${Utils.escapeHtml(err.message)}</p>`;
  }
}

function setupJobModal() {
  const addBtn = document.getElementById("openAddJobModalBtn");
  const modal = document.getElementById("jobModal");
  const closeBtn = document.getElementById("closeJobModalBtn");
  const form = document.getElementById("jobForm");

  if (!addBtn) return;

  // Show button only if user is logged in
  if (API.getToken()) {
    addBtn.style.display = "inline-flex";
  } else {
    addBtn.style.display = "none";
    return;
  }

  if (!modal) return;

  addBtn.addEventListener("click", () => {
    form.reset();
    Utils.openModal("jobModal");
  });

  closeBtn?.addEventListener("click", () => Utils.closeModal("jobModal"));

  const demoBtn = document.getElementById("fillDemoJobBtn");
  demoBtn?.addEventListener("click", () => {
    document.getElementById("modalJobTitle").value = "Senior AI Platform Engineer";
    document.getElementById("modalJobCompany").value = "Nexus AI Labs";
    document.getElementById("modalJobDesc").value =
`We are seeking a Senior AI Platform Engineer to design, scale, and optimize our distributed LLM inference pipelines, RAG systems, and microservices architecture.

Key Responsibilities:
- Build and maintain high-throughput asynchronous API microservices using FastAPI and Docker.
- Orchestrate vector databases (ChromaDB / Pinecone) for retrieval-augmented generation.
- Collaborate with ML research and engineering teams to deploy and monitor generative models in production.
- Ensure end-to-end security, observability, and sub-100ms inference latency.`;
    document.getElementById("modalJobSkills").value = "Python, FastAPI, Docker, PostgreSQL, PyTorch, LangChain, REST, Redis";
    document.getElementById("modalJobExp").value = "4.0";
    document.getElementById("modalJobEdu").value = "Bachelor's";
    document.getElementById("modalJobLocation").value = "San Francisco, CA (Hybrid)";
    document.getElementById("modalJobType").value = "Full-time";
    document.getElementById("modalJobSalary").value = "$145,000 - $185,000";
    document.getElementById("modalJobContactEmail").value = "careers@nexusailabs.com";

    Utils.showToast("Demo job details filled into form!", "info");
  });

  form?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const title = document.getElementById("modalJobTitle").value.trim();
    const company = document.getElementById("modalJobCompany").value.trim();
    const description = document.getElementById("modalJobDesc").value.trim();
    const skillsRaw = document.getElementById("modalJobSkills").value.trim();
    const expYears =
      parseFloat(document.getElementById("modalJobExp").value) || 0.0;
    const eduLevel = document.getElementById("modalJobEdu").value.trim();
    const location =
      document.getElementById("modalJobLocation").value.trim() || "Remote";
    const empType = document.getElementById("modalJobType").value;
    const salary =
      document.getElementById("modalJobSalary").value.trim() || undefined;
    const contactEmail =
      document.getElementById("modalJobContactEmail").value.trim() || undefined;

    const required_skills = skillsRaw
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);

    try {
      await API.createJob({
        title,
        company,
        description,
        required_skills,
        preferred_skills: [],
        experience_years: expYears,
        education_level: eduLevel,
        location,
        employment_type: empType,
        salary_range: salary,
        contact_email: contactEmail,
      });

      Utils.showToast("Job posting created successfully!", "success");
      Utils.closeModal("jobModal");
      await loadJobs();
    } catch (err) {
      Utils.showToast(err.message || "Failed to create job.", "error");
    }
  });
}

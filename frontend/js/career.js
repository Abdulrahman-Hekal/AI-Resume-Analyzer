/**
 * AI Resume Analyzer - Career Advisor & RAG Pipeline Logic
 */

let activeResumeId = null;
let activeTargetRole = null;

document.addEventListener("DOMContentLoaded", async () => {
  const urlParams = new URLSearchParams(window.location.search);
  activeResumeId = urlParams.get("resume_id");
  activeTargetRole = urlParams.get("target_role");

  if (!activeResumeId && API.getToken()) {
    try {
      const res = await API.getResumes();
      if (res.resumes && res.resumes.length > 0) {
        activeResumeId = res.resumes[0].id;
      }
    } catch (e) {
      // Ignore
    }
  }

  setupChat();
  setupSuggestedChips();
  await loadKnowledgeDocsOverview();

  // If user arrived with a target role, automatically trigger an initial recommendation
  if (activeTargetRole) {
    const prompt = `What is the optimal preparation and skill roadmap to qualify for '${activeTargetRole}'?`;
    document.getElementById("careerQuestionInput").value = prompt;
    handleQuestionSubmit();
  }
});

function setupSuggestedChips() {
  document.querySelectorAll(".chip-btn").forEach(chip => {
    chip.addEventListener("click", () => {
      const question = chip.textContent.trim();
      document.getElementById("careerQuestionInput").value = question;
      handleQuestionSubmit();
    });
  });
}

function setupChat() {
  const form = document.getElementById("careerChatForm");
  form?.addEventListener("submit", (e) => {
    e.preventDefault();
    handleQuestionSubmit();
  });
}

async function handleQuestionSubmit() {
  const input = document.getElementById("careerQuestionInput");
  const sendBtn = document.getElementById("careerSendBtn");
  const messagesBox = document.getElementById("careerChatMessages");
  const question = input.value.trim();

  if (!question) return;

  // Append user bubble
  appendMessage("user", question);
  input.value = "";
  sendBtn.disabled = true;
  sendBtn.innerHTML = `<span class="spinner"></span>`;

  // Append loading bubble
  const loadingId = "advisorLoading_" + Date.now();
  appendLoadingMessage(loadingId);

  try {
    const response = await API.askCareerAdvisor({
      question,
      resume_id: activeResumeId ? Number(activeResumeId) : undefined,
      target_role: activeTargetRole || undefined
    });

    // Remove loading bubble
    document.getElementById(loadingId)?.remove();

    // Render Advisor response with RAG citations and Roadmaps
    appendAdvisorResponse(response);

  } catch (err) {
    document.getElementById(loadingId)?.remove();
    appendMessage("advisor", `⚠ Error retrieving career guidance: ${err.message || 'Please check system connectivity.'}`);
  } finally {
    sendBtn.disabled = false;
    sendBtn.textContent = "Ask Advisor";
  }
}

function appendMessage(role, text) {
  const box = document.getElementById("careerChatMessages");
  if (!box) return;

  const bubble = document.createElement("div");
  bubble.className = `chat-bubble ${role}`;
  bubble.innerHTML = `<p>${Utils.escapeHtml(text)}</p>`;
  box.appendChild(bubble);
  box.scrollTop = box.scrollHeight;
}

function appendLoadingMessage(id) {
  const box = document.getElementById("careerChatMessages");
  if (!box) return;

  const bubble = document.createElement("div");
  bubble.id = id;
  bubble.className = "chat-bubble advisor";
  bubble.innerHTML = `
    <div style="display:flex; align-items:center; gap:8px;">
      <span class="spinner" style="border-top-color:var(--accent-primary);"></span>
      <span style="font-size:0.875rem; color:var(--ink-secondary);">Searching Knowledge Base & Generating Grounded Advice...</span>
    </div>
  `;
  box.appendChild(bubble);
  box.scrollTop = box.scrollHeight;
}

function appendAdvisorResponse(res) {
  const box = document.getElementById("careerChatMessages");
  if (!box) return;

  const bubble = document.createElement("div");
  bubble.className = "chat-bubble advisor";

  // RAG Grounding Badges
  let citationsHtml = "";
  if (res.grounded_by_rag && res.retrieved_sources && res.retrieved_sources.length > 0) {
    citationsHtml = `
      <div class="rag-citation-box">
        <div class="rag-badge">🔍 RAG Verified • Retrieved from Knowledge Base</div>
        <div style="margin-top:6px; display:flex; flex-direction:column; gap:6px;">
          ${res.retrieved_sources.map(src => `
            <div style="font-size:0.75rem; background:var(--surface-1); padding:6px 10px; border-radius:4px; border:1px solid var(--border-subtle);">
              <strong>${Utils.escapeHtml(src.document_title)}</strong> (${src.similarity_score}% match)
              <div style="color:var(--ink-muted); margin-top:2px;">"${Utils.escapeHtml(src.snippet)}"</div>
            </div>
          `).join("")}
        </div>
      </div>
    `;
  }

  // Roadmap Steps if returned
  let roadmapHtml = "";
  if (res.career_roadmap && res.career_roadmap.length > 0) {
    roadmapHtml = `
      <div style="margin-top: 16px; border-top:1px solid var(--border-default); padding-top:12px;">
        <h4 style="font-size:0.9375rem; margin-bottom:8px; color:var(--accent-cyan);">Suggested Career Progression Roadmap:</h4>
        <div style="display:flex; flex-direction:column; gap:8px;">
          ${res.career_roadmap.map(step => `
            <div style="background:var(--surface-1); border:1px solid var(--border-subtle); border-radius:6px; padding:10px 12px; font-size:0.8125rem;">
              <div style="font-weight:600; color:var(--ink-primary); margin-bottom:2px;">${Utils.escapeHtml(step.phase)}</div>
              <p style="font-size:0.8125rem; margin-bottom:6px;">${Utils.escapeHtml(step.description)}</p>
              <div style="display:flex; gap:4px; flex-wrap:wrap;">
                ${(step.focus_skills || []).map(s => `<span class="badge badge-indigo">${Utils.escapeHtml(s)}</span>`).join(" ")}
              </div>
            </div>
          `).join("")}
        </div>
      </div>
    `;
  }

  // Certifications & Resources
  let extrasHtml = "";
  if (res.suggested_certifications && res.suggested_certifications.length > 0) {
    extrasHtml += `
      <div style="margin-top:12px; font-size:0.8125rem;">
        <strong>Recommended Certifications:</strong>
        <div style="display:flex; gap:4px; flex-wrap:wrap; margin-top:4px;">
          ${res.suggested_certifications.map(c => `<span class="badge badge-cyan">🎖 ${Utils.escapeHtml(c)}</span>`).join(" ")}
        </div>
      </div>
    `;
  }

  bubble.innerHTML = `
    <div style="font-size: 0.9375rem; line-height:1.6; white-space: pre-line;">
      ${Utils.escapeHtml(res.answer)}
    </div>
    ${citationsHtml}
    ${roadmapHtml}
    ${extrasHtml}
    <div style="font-size:0.7rem; color:var(--ink-muted); margin-top:10px; text-align:right;">
      Agent: Career Advisor • Provider: ${Utils.escapeHtml(res.ai_provider_used)}
    </div>
  `;

  box.appendChild(bubble);
  box.scrollTop = box.scrollHeight;
}

async function loadKnowledgeDocsOverview() {
  const container = document.getElementById("knowledgeBaseList");
  if (!container) return;

  const isLoggedIn = !!API.getToken();

  // Show "Add Doc" button for authenticated users
  const addBtn = document.getElementById("openAddKnowledgeDocBtn");
  if (addBtn) {
    addBtn.style.display = isLoggedIn ? "inline-flex" : "none";
  }

  // Setup modal if not already done
  setupKnowledgeDocModal();

  try {
    const docs = await API.getKnowledgeDocs();
    if (docs.length === 0) {
      container.innerHTML = `<p style="font-size:0.8125rem; color:var(--ink-muted); text-align:center; padding:16px 0;">No knowledge documents found. Add one to power the RAG pipeline.</p>`;
      return;
    }

    container.innerHTML = docs.map(d => `
      <div style="padding: 10px 12px; background:var(--surface-2); border:1px solid var(--border-default); border-radius:6px; font-size:0.8125rem;">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:8px;">
          <div style="flex:1; min-width:0;">
            <div style="font-weight:600; color:var(--ink-primary); margin-bottom:2px;">${Utils.escapeHtml(d.title)}</div>
            <div style="color:var(--accent-cyan); font-size:0.75rem;">Category: ${Utils.escapeHtml(d.category)} • ${d.chunks_count} Vector Chunks</div>
            <div style="color:var(--ink-muted); font-size:0.6875rem; margin-top:2px;">Source: ${Utils.escapeHtml(d.source || 'curated')}</div>
          </div>
          ${isLoggedIn ? `
            <button class="btn btn-outline btn-sm" style="font-size:0.6875rem; padding:2px 8px; color:var(--danger); border-color:var(--danger);"
                    onclick="deleteKnowledgeDoc(${d.id}, '${Utils.escapeHtml(d.title).replace(/'/g, "\\'")}')">
              ✕
            </button>
          ` : ''}
        </div>
      </div>
    `).join("");
  } catch (err) {
    container.innerHTML = `<p style="font-size:0.75rem; color:var(--ink-muted);">Knowledge base loaded.</p>`;
  }
}

let knowledgeDocModalSetup = false;

function setupKnowledgeDocModal() {
  if (knowledgeDocModalSetup) return;
  knowledgeDocModalSetup = true;

  const addBtn = document.getElementById("openAddKnowledgeDocBtn");
  const modal = document.getElementById("knowledgeDocModal");
  const closeBtn = document.getElementById("closeKnowledgeDocModalBtn");
  const form = document.getElementById("knowledgeDocForm");

  if (!addBtn || !modal) return;

  addBtn.addEventListener("click", () => {
    form?.reset();
    Utils.openModal("knowledgeDocModal");
  });

  closeBtn?.addEventListener("click", () => Utils.closeModal("knowledgeDocModal"));

  form?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const title = document.getElementById("modalKnowledgeTitle").value.trim();
    const category = document.getElementById("modalKnowledgeCategory").value;
    const source = document.getElementById("modalKnowledgeSource").value.trim() || "user_contributed";
    const content = document.getElementById("modalKnowledgeContent").value.trim();

    if (!title || !content) {
      Utils.showToast("Title and content are required.", "error");
      return;
    }

    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;
    submitBtn.disabled = true;
    submitBtn.innerHTML = `<span class="spinner"></span> Embedding...`;

    try {
      await API.createKnowledgeDoc({ title, category, source, content });
      Utils.showToast("Knowledge document ingested and indexed successfully!", "success");
      Utils.closeModal("knowledgeDocModal");
      await loadKnowledgeDocsOverview();
    } catch (err) {
      Utils.showToast(err.message || "Failed to add knowledge document.", "error");
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = originalText;
    }
  });
}

async function deleteKnowledgeDoc(docId, docTitle) {
  if (!confirm(`Delete knowledge document "${docTitle}"?\n\nThis will remove the document and all its vector chunks from the RAG knowledge base.`)) {
    return;
  }

  try {
    await API.deleteKnowledgeDoc(docId);
    Utils.showToast(`Document "${docTitle}" deleted successfully.`, "info");
    await loadKnowledgeDocsOverview();
  } catch (err) {
    Utils.showToast(err.message || "Failed to delete document.", "error");
  }
}


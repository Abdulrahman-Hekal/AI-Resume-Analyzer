/**
 * AI Resume Analyzer - REST API Client
 * Modular fetch wrapper with JWT bearer token injection and error handling.
 */

const API_BASE_URL = window.location.origin;

class APIClient {
  static getToken() {
    return localStorage.getItem("resume_ai_token");
  }

  static setToken(token) {
    localStorage.setItem("resume_ai_token", token);
  }

  static clearToken() {
    localStorage.removeItem("resume_ai_token");
    localStorage.removeItem("resume_ai_user");
  }

  static getUser() {
    const raw = localStorage.getItem("resume_ai_user");
    try {
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  }

  static setUser(user) {
    localStorage.setItem("resume_ai_user", JSON.stringify(user));
  }

  static async request(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const token = APIClient.getToken();

    const headers = {
      ...(options.headers || {})
    };

    if (token && !headers["Authorization"]) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    if (!(options.body instanceof FormData) && !headers["Content-Type"]) {
      headers["Content-Type"] = "application/json";
    }

    const config = {
      ...options,
      headers
    };

    try {
      const response = await fetch(url, config);
      
      // Auto-handle 401 Unauthorized
      if (response.status === 401 && !endpoint.includes("/auth/login") && !endpoint.includes("/auth/register")) {
        APIClient.clearToken();
        if (!window.location.pathname.includes("login.html") && !window.location.pathname.includes("register.html") && window.location.pathname !== "/") {
          window.location.href = "login.html";
        }
      }

      const contentType = response.headers.get("content-type");
      const isJson = contentType && contentType.includes("application/json");
      const data = isJson ? await response.json() : await response.text();

      if (!response.ok) {
        const errorMsg = data && data.detail ? data.detail : `Request failed with status ${response.status}`;
        throw new Error(errorMsg);
      }

      return data;
    } catch (err) {
      console.error(`API Error [${endpoint}]:`, err);
      throw err;
    }
  }

  /* Auth Endpoints */
  static register(data) {
    return APIClient.request("/api/auth/register", {
      method: "POST",
      body: JSON.stringify(data)
    });
  }

  static login(data) {
    return APIClient.request("/api/auth/login", {
      method: "POST",
      body: JSON.stringify(data)
    });
  }

  static logout() {
    return APIClient.request("/api/auth/logout", { method: "POST" });
  }

  static getMe() {
    return APIClient.request("/api/auth/me");
  }

  /* Resume Endpoints */
  static uploadResume(formData) {
    return APIClient.request("/api/resumes", {
      method: "POST",
      body: formData
    });
  }

  static getResumes() {
    return APIClient.request("/api/resumes");
  }

  static getResume(id) {
    return APIClient.request(`/api/resumes/${id}`);
  }

  static deleteResume(id) {
    return APIClient.request(`/api/resumes/${id}`, { method: "DELETE" });
  }

  /* Analysis Endpoints */
  static analyzeResume(id) {
    return APIClient.request(`/api/resumes/${id}/analyze`, { method: "POST" });
  }

  static getResumeAnalysis(id) {
    return APIClient.request(`/api/resumes/${id}/analysis`);
  }

  /* Job Recommendations Endpoints */
  static generateRecommendations(resumeId) {
    return APIClient.request(`/api/resumes/${resumeId}/recommendations`, { method: "POST" });
  }

  static getRecommendations(resumeId) {
    return APIClient.request(`/api/resumes/${resumeId}/recommendations`);
  }

  static getLiveJobMatch(resumeId, jobId) {
    return APIClient.request(`/api/resumes/${resumeId}/match/${jobId}`);
  }

  /* Jobs Management & Search Endpoints */
  static listJobs(skip = 0, limit = 50) {
    return APIClient.request(`/api/jobs?skip=${skip}&limit=${limit}`);
  }

  static searchJobs(params = {}) {
    const cleanParams = {};
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== null && value !== "" && value !== "undefined" && value !== "null") {
        cleanParams[key] = value;
      }
    }
    const query = new URLSearchParams(cleanParams).toString();
    return APIClient.request(`/api/jobs/search${query ? '?' + query : ''}`);
  }

  static getJob(id) {
    return APIClient.request(`/api/jobs/${id}`);
  }

  static createJob(data) {
    return APIClient.request("/api/jobs", {
      method: "POST",
      body: JSON.stringify(data)
    });
  }

  static updateJob(id, data) {
    return APIClient.request(`/api/jobs/${id}`, {
      method: "PUT",
      body: JSON.stringify(data)
    });
  }

  static deleteJob(id) {
    return APIClient.request(`/api/jobs/${id}`, { method: "DELETE" });
  }

  /* Career Advisor & RAG Endpoints */
  static askCareerAdvisor(data) {
    return APIClient.request("/api/career/questions", {
      method: "POST",
      body: JSON.stringify(data)
    });
  }

  static getCareerGuidance(resumeId) {
    return APIClient.request(`/api/career/guidance/${resumeId}`);
  }

  static getKnowledgeDocs() {
    return APIClient.request("/api/career/knowledge-docs");
  }

  static getKnowledgeDoc(id) {
    return APIClient.request(`/api/career/knowledge-docs/${id}`);
  }

  static createKnowledgeDoc(data) {
    return APIClient.request("/api/career/knowledge-docs", {
      method: "POST",
      body: JSON.stringify(data)
    });
  }

  static deleteKnowledgeDoc(id) {
    return APIClient.request(`/api/career/knowledge-docs/${id}`, { method: "DELETE" });
  }

  /* Health & System */
  static getHealth() {
    return APIClient.request("/api/health");
  }
}

window.API = APIClient;

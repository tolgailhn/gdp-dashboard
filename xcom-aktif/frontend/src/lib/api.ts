const API_BASE = "http://localhost:8000";

function getToken(): string | null {
  return localStorage.getItem("xcom_token");
}

async function apiFetch(path: string, options: RequestInit = {}) {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `API hatasi: ${res.status}`);
  }

  return res.json();
}

// Dashboard
export function getDashboardStats() {
  return apiFetch("/api/dashboard/stats");
}

// Scanner
export function scanTopics(params: {
  time_range: string;
  category?: string;
  max_results?: number;
  custom_query?: string;
  min_likes?: number;
  min_retweets?: number;
  min_followers?: number;
  engine?: string;
}) {
  return apiFetch("/api/scanner/scan", {
    method: "POST",
    body: JSON.stringify(params),
  });
}

export function discoverTopics(params: {
  time_range: string;
  max_results?: number;
  engine?: string;
}) {
  return apiFetch("/api/scanner/discover", {
    method: "POST",
    body: JSON.stringify(params),
  });
}

export function getCategories() {
  return apiFetch("/api/scanner/categories");
}

// Generator
export function generateTweet(params: {
  topic: string;
  style?: string;
  length?: string;
  thread?: boolean;
  research_context?: string;
}) {
  return apiFetch("/api/generator/tweet", {
    method: "POST",
    body: JSON.stringify(params),
  });
}

// Research
export function researchTopic(topic: string, depth: string = "normal") {
  return apiFetch("/api/generator/research", {
    method: "POST",
    body: JSON.stringify({ topic, depth }),
  });
}

// Publish
export function publishTweet(params: {
  text: string;
  thread_parts?: string[];
}) {
  return apiFetch("/api/publish/tweet", {
    method: "POST",
    body: JSON.stringify(params),
  });
}

// Drafts
export function listDrafts() {
  return apiFetch("/api/drafts/list");
}

export function addDraft(params: {
  text: string;
  topic?: string;
  style?: string;
}) {
  return apiFetch("/api/drafts/add", {
    method: "POST",
    body: JSON.stringify(params),
  });
}

export function deleteDraft(index: number) {
  return apiFetch("/api/drafts/delete", {
    method: "POST",
    body: JSON.stringify({ index }),
  });
}

// Analytics
export function analyzeAccount(username: string, tweetCount: number) {
  return apiFetch("/api/analytics/analyze", {
    method: "POST",
    body: JSON.stringify({ username, tweet_count: tweetCount }),
  });
}

// Calendar
export function getTodaySchedule() {
  return apiFetch("/api/calendar/today");
}

// ── Settings ───────────────────────────────────────────

export function getAPIStatus() {
  return apiFetch("/api/settings/status");
}

export function updateAPIKey(key: string, value: string) {
  return apiFetch("/api/settings/update-key", {
    method: "POST",
    body: JSON.stringify({ key, value }),
  });
}

// Connection Tests
export function testTwitter() {
  return apiFetch("/api/settings/test-twitter", { method: "POST" });
}

export function testAI() {
  return apiFetch("/api/settings/test-ai", { method: "POST" });
}

export function testGrok() {
  return apiFetch("/api/settings/test-grok", { method: "POST" });
}

export function testTelegram() {
  return apiFetch("/api/settings/test-telegram", { method: "POST" });
}

export function testTwikit() {
  return apiFetch("/api/settings/test-twikit", { method: "POST" });
}

// Twikit / Cookies
export function getTwikitStatus() {
  return apiFetch("/api/settings/twikit-status");
}

export function saveTwikitCookies(auth_token: string, ct0: string) {
  return apiFetch("/api/settings/twikit-cookies", {
    method: "POST",
    body: JSON.stringify({ auth_token, ct0 }),
  });
}

export function deleteTwikitCookies() {
  return apiFetch("/api/settings/twikit-cookies", { method: "DELETE" });
}

// X Account Info
export function getAccountInfo() {
  return apiFetch("/api/settings/account-info");
}

// Monitored Accounts
export function getMonitoredAccounts() {
  return apiFetch("/api/settings/monitored-accounts");
}

export function addMonitoredAccount(username: string) {
  return apiFetch("/api/settings/monitored-accounts", {
    method: "POST",
    body: JSON.stringify({ username }),
  });
}

export function removeMonitoredAccount(username: string) {
  return apiFetch(`/api/settings/monitored-accounts/${encodeURIComponent(username)}`, {
    method: "DELETE",
  });
}

// User Samples (Writing Style)
export function getUserSamples() {
  return apiFetch("/api/settings/user-samples");
}

export function addUserSample(text: string) {
  return apiFetch("/api/settings/user-samples", {
    method: "POST",
    body: JSON.stringify({ text }),
  });
}

export function addBulkSamples(texts: string[]) {
  return apiFetch("/api/settings/user-samples/bulk", {
    method: "POST",
    body: JSON.stringify({ texts }),
  });
}

export function deleteUserSample(index: number) {
  return apiFetch(`/api/settings/user-samples/${index}`, { method: "DELETE" });
}

// Persona
export function getPersona() {
  return apiFetch("/api/settings/persona");
}

export function savePersona(persona: string) {
  return apiFetch("/api/settings/persona", {
    method: "POST",
    body: JSON.stringify({ persona }),
  });
}

export function analyzeStyle() {
  return apiFetch("/api/settings/analyze-style", { method: "POST" });
}

// Post History
export function getPostHistory() {
  return apiFetch("/api/settings/post-history");
}

export function clearPostHistory() {
  return apiFetch("/api/settings/post-history", { method: "DELETE" });
}

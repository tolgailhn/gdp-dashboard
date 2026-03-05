/**
 * API client for communicating with the FastAPI backend.
 * All requests go through Next.js rewrite to http://localhost:8000
 */

const API_BASE = "/api";

function getAuthHeaders(): Record<string, string> {
  if (typeof window === "undefined") return {};
  const token = localStorage.getItem("xcom_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function fetchAPI<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders(),
      ...options?.headers,
    },
  });

  if (res.status === 401) {
    // Token expired or invalid — clear and redirect
    if (typeof window !== "undefined") {
      localStorage.removeItem("xcom_token");
      localStorage.removeItem("xcom_token_expiry");
      window.location.href = "/login";
    }
    throw new Error("Oturum suresi doldu. Tekrar giris yapin.");
  }

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `API error: ${res.status}`);
  }

  return res.json();
}

// Dashboard
export async function getDashboardStats() {
  return fetchAPI("/dashboard/stats");
}

// Scanner
export async function scanTopics(timeRange: string, category: string) {
  return fetchAPI("/scanner/scan", {
    method: "POST",
    body: JSON.stringify({ time_range: timeRange, category }),
  });
}

// Generator
export async function generateTweet(params: {
  topic: string;
  style?: string;
  length?: string;
  thread?: boolean;
  research_context?: string;
  media_urls?: string[];
}) {
  return fetchAPI("/generator/tweet", {
    method: "POST",
    body: JSON.stringify(params),
  });
}

export async function generateLongContent(params: {
  topic: string;
  style?: string;
  length?: string;
  research_context?: string;
}) {
  return fetchAPI("/generator/long-content", {
    method: "POST",
    body: JSON.stringify(params),
  });
}

export async function researchTopic(topic: string, depth?: string) {
  return fetchAPI("/generator/research", {
    method: "POST",
    body: JSON.stringify({ topic, depth }),
  });
}

// Publish
export async function publishTweet(params: {
  text: string;
  thread_parts?: string[];
  quote_tweet_id?: string;
}) {
  return fetchAPI("/publish/tweet", {
    method: "POST",
    body: JSON.stringify(params),
  });
}

// Settings
export async function getAPIStatus() {
  return fetchAPI("/settings/status");
}

export async function updateAPIKey(key: string, value: string) {
  return fetchAPI("/settings/update-key", {
    method: "POST",
    body: JSON.stringify({ key, value }),
  });
}

// Analytics
export async function analyzeAccount(username: string, tweetCount?: number) {
  return fetchAPI("/analytics/analyze", {
    method: "POST",
    body: JSON.stringify({ username, tweet_count: tweetCount || 50 }),
  });
}

// Calendar
export async function getTodaySchedule() {
  return fetchAPI("/calendar/today");
}

export async function logPost(entry: {
  slot_time: string;
  post_type?: string;
  has_media?: boolean;
  has_self_reply?: boolean;
  url?: string;
  content?: string;
}) {
  return fetchAPI("/calendar/log", {
    method: "POST",
    body: JSON.stringify(entry),
  });
}

// Health
export async function healthCheck() {
  return fetchAPI("/health");
}

export const CATEGORIES = [
  "Password Reset",
  "Hardware Issue",
  "Software Issue",
  "Network/Connectivity",
  "Access Request",
  "General Inquiry",
] as const;

export const URGENCY_LEVELS = ["Low", "Medium", "High", "Critical"] as const;

// Confidence thresholds — pulled out as config instead of hardcoded numbers
// so they're easy to tune without touching node logic.
export const CONFIDENCE_THRESHOLDS = {
  AUTO_RESOLVE_MIN: 0.8, // category == Password Reset AND confidence >= this -> auto_resolve
  FALLBACK_MAX: 0.6,     // confidence < this -> fallback
};

// Maps each category to the human team that should handle it.
export const ASSIGNMENT_GROUPS: Record<string, string> = {
  "Password Reset": "Identity & Access Team",
  "Hardware Issue": "Desktop Support",
  "Software Issue": "Application Support",
  "Network/Connectivity": "Network Operations",
  "Access Request": "Identity & Access Team",
  "General Inquiry": "Service Desk",
};

// OpenRouter model + endpoint settings
export const LLM_CONFIG = {
  model: "openai/gpt-oss-20b:free",
  baseURL: "https://openrouter.ai/api/v1",
};
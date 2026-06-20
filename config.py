"""Configuration for the triage agent.

Everything that a reviewer or operator might reasonably want to tune lives here
rather than being scattered through the node logic: confidence thresholds, the
category->team routing table, and LLM connection settings.
"""

import os

# --------------------------------------------------------------------------- #
# Classification vocabulary
# --------------------------------------------------------------------------- #
CATEGORIES = [
    "Password Reset",
    "Hardware Issue",
    "Software Issue",
    "Network/Connectivity",
    "Access Request",
    "General Inquiry",
]

URGENCIES = ["Low", "Medium", "High", "Critical"]

# --------------------------------------------------------------------------- #
# Routing thresholds  (kept as config values, not hardcoded in node logic)
# --------------------------------------------------------------------------- #
# A Password Reset at or above this confidence is safe to auto-resolve.
AUTO_RESOLVE_MIN_CONFIDENCE = 0.8

# Anything below this confidence is too uncertain to act on -> human review.
FALLBACK_MAX_CONFIDENCE = 0.6

# --------------------------------------------------------------------------- #
# Category -> assignment group mapping
# --------------------------------------------------------------------------- #
ASSIGNMENT_GROUPS = {
    "Password Reset": "Identity & Access Team",
    "Hardware Issue": "Desktop Support",
    "Software Issue": "Application Support",
    "Network/Connectivity": "Network Operations",
    "Access Request": "Identity & Access Team",
    "General Inquiry": "Service Desk",
}

# Where tickets go when classification is too uncertain to route confidently.
FALLBACK_GROUP = "AI Review Queue"

# --------------------------------------------------------------------------- #
# LLM settings (OpenRouter, OpenAI-compatible API)
# --------------------------------------------------------------------------- #
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
MODEL = os.getenv("TRIAGE_MODEL", "openai/gpt-oss-20b")
LLM_TEMPERATURE = 0.0  # deterministic classification

# If no API key is present, the agent transparently uses a keyword-based mock
# classifier so the repo still runs end-to-end. Set USE_MOCK_LLM=1 to force it.
API_KEY = os.getenv("OPENROUTER_API_KEY", "")
USE_MOCK_LLM = os.getenv("USE_MOCK_LLM", "").lower() in {"1", "true", "yes"} or not API_KEY

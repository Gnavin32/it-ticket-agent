"""Node functions for the triage graph.

Each public ``*_node`` function takes the current ``TicketState`` and returns a
partial-state dict that LangGraph merges back in. The two ``route_*`` functions
are conditional-edge selectors: they read state and return the name of the next
node (they never mutate state).

The LLM helpers (real OpenRouter call + keyword mock + email generation) live
here too, so the whole agent stays within the file layout the assignment asks
for.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

import config
from state import TicketState

logger = logging.getLogger("triage")


def _now() -> str:
    """ISO-8601 UTC timestamp, e.g. 2026-06-19T10:30:00Z."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _log_action(state: TicketState, message: str) -> list[str]:
    """Return a new actions_log with a timestamped entry appended."""
    entry = f"[{_now()}] {message}"
    logger.info(entry)
    return [*state.get("actions_log", []), entry]


# =========================================================================== #
# LLM access: real (OpenRouter) + mock (keyword) classifiers
# =========================================================================== #

# Lazily-built OpenAI client so importing this module never requires a key.
_client = None


def _get_client():
    global _client
    if _client is None:
        from openai import OpenAI

        _client = OpenAI(base_url=config.OPENROUTER_BASE_URL, api_key=config.API_KEY)
    return _client


CLASSIFY_SYSTEM_PROMPT = f"""You are an IT service-desk triage assistant. \
Classify a single support ticket and respond with ONLY a JSON object — no prose, \
no code fences.

The JSON must have exactly these keys:
  "category":   one of {config.CATEGORIES}
  "urgency":    one of {config.URGENCIES}
  "confidence": a float between 0.0 and 1.0
  "reasoning":  one short sentence explaining the choice

Guidelines:
- Choose the single best-fitting category.
- "confidence" reflects how clearly the ticket maps to a category. If the ticket \
is vague, gibberish, empty, contains random characters (e.g. "asdfghjkl"), or \
has an extremely generic/uninformative description (e.g. "computer broken thing not work"), \
you MUST classify it as "General Inquiry" and set "confidence" below 0.5.
- A clearly described, well-understood issue should score 0.85 or higher.
- "urgency" reflects business impact: a locked-out user or an outage is High/Critical; \
a minor annoyance is Low.
"""


def _classify_with_llm(state: TicketState) -> dict:
    """Call the LLM and parse its JSON classification. Raises on any failure."""
    user_msg = (
        f"Subject: {state['subject']}\n"
        f"Description: {state['description']}"
    )
    response = _get_client().chat.completions.create(
        model=config.MODEL,
        temperature=config.LLM_TEMPERATURE,
        messages=[
            {"role": "system", "content": CLASSIFY_SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
    )
    raw = response.choices[0].message.content or ""
    return _parse_classification(raw)


def _parse_classification(raw: str) -> dict:
    """Extract and validate a classification dict from raw model text."""
    text = raw.strip()
    # Tolerate models that wrap JSON in ```json fences.
    if text.startswith("```"):
        text = text.strip("`")
        text = text[text.find("{"):]
    # Grab the outermost JSON object.
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"No JSON object found in model output: {raw!r}")
    data = json.loads(text[start : end + 1])

    category = data["category"]
    urgency = data["urgency"]
    confidence = float(data["confidence"])
    if category not in config.CATEGORIES:
        raise ValueError(f"Unknown category: {category!r}")
    if urgency not in config.URGENCIES:
        raise ValueError(f"Unknown urgency: {urgency!r}")
    if not 0.0 <= confidence <= 1.0:
        raise ValueError(f"Confidence out of range: {confidence}")

    return {
        "category": category,
        "urgency": urgency,
        "confidence": confidence,
        "reasoning": str(data.get("reasoning", "")).strip(),
    }


# --- Mock classifier (used when no API key is configured) ------------------ #

# Specific, high-signal keywords per category.
_CATEGORY_KEYWORDS = {
    "Password Reset": ["password", "reset", "locked out", "locked", "forgot",
                       "log in", "login", "active directory", "credentials", "sign in"],
    "Hardware Issue": ["laptop", "screen", "monitor", "keyboard", "mouse", "flicker",
                       "dell", "battery", "printer", "docking", "hardware"],
    "Software Issue": ["software", "application", "install", "crash", "license",
                       "excel", "outlook", "program", "app "],
    "Network/Connectivity": ["vpn", "wifi", "wi-fi", "network", "internet", "connect",
                             "disconnect", "globalprotect", "ethernet", "dns"],
    "Access Request": ["access", "sharepoint", "permission", "provision", "onboard",
                       "teams channel", "joined", "grant", "role", "shared drive"],
}

# Generic words that signal a problem but reveal nothing specific.
_VAGUE_WORDS = ["help", "broken", "thing", "computer", "not work", "issue", "problem"]


def _classify_mock(state: TicketState) -> dict:
    """Deterministic keyword classifier mirroring the real LLM's output shape."""
    text = f"{state['subject']} {state['description']}".lower()

    scores = {
        cat: sum(1 for kw in kws if kw in text)
        for cat, kws in _CATEGORY_KEYWORDS.items()
    }
    best_category = max(scores, key=scores.get)
    best_hits = scores[best_category]

    if best_hits >= 3:
        confidence = 0.95
    elif best_hits == 2:
        confidence = 0.88
    elif best_hits == 1:
        confidence = 0.75
    else:
        # Nothing specific matched -> treat as an unclear general inquiry.
        best_category = "General Inquiry"
        vague_hits = sum(1 for w in _VAGUE_WORDS if w in text)
        confidence = 0.35 if vague_hits else 0.25

    # Simple urgency heuristic.
    if any(w in text for w in ["asap", "urgent", "critical", "locked out", "outage", "down"]):
        urgency = "High"
    elif any(w in text for w in ["every", "intermittent", "persists", "slow", "keeps", "hard to work"]):
        urgency = "Medium"
    else:
        urgency = "Low"

    return {
        "category": best_category,
        "urgency": urgency,
        "confidence": confidence,
        "reasoning": f"Keyword match (mock): {best_hits} signal(s) for '{best_category}'.",
    }


# =========================================================================== #
# Nodes
# =========================================================================== #

REQUIRED_FIELDS = ("subject", "description", "user_email")


def ticket_intake_node(state: TicketState) -> dict:
    """Validate and normalize the incoming ticket into graph state."""
    missing = [f for f in REQUIRED_FIELDS if not str(state.get(f, "")).strip()]
    if missing:
        note = f"Missing required field(s): {', '.join(missing)}"
        return {
            "error": note,
            "actions_log": _log_action(state, f"Intake failed — {note}"),
        }

    # Normalize whitespace / derive a display name if none provided.
    user_email = state["user_email"].strip().lower()
    user_name = state.get("user_name") or user_email.split("@")[0].replace(".", " ").title()
    return {
        "subject": state["subject"].strip(),
        "description": state["description"].strip(),
        "user_email": user_email,
        "user_name": user_name,
        "actions_log": _log_action(state, f"Ticket {state.get('ticket_id', '?')} intake OK"),
    }


def classify_node(state: TicketState) -> dict:
    """Classify the ticket (LLM or mock). On any failure, set error -> fallback."""
    try:
        result = _classify_mock(state) if config.USE_MOCK_LLM else _classify_with_llm(state)
    except Exception as exc:  # noqa: BLE001 — any failure should degrade to review
        note = f"Classification failed: {exc}"
        logger.warning(note)
        return {"error": note, "actions_log": _log_action(state, note)}

    msg = (f"Classified as {result['category']} / {result['urgency']} "
           f"(confidence {result['confidence']:.2f})")
    return {**result, "actions_log": _log_action(state, msg)}


def auto_resolve_node(state: TicketState) -> dict:
    """Simulate an automated password reset."""
    # Mock action — in production this would call the IAM provider's reset API.
    msg = f"Auto-reset password for {state['user_email']} (simulated)"
    return {
        "resolution_status": "Auto-Resolved",
        "assignment_group": config.ASSIGNMENT_GROUPS["Password Reset"],
        "resolution_notes": "Temporary password issued; user prompted to set a new one at next login.",
        "actions_log": _log_action(state, msg),
    }


def assign_to_team_node(state: TicketState) -> dict:
    """Route the ticket to the correct support group based on category."""
    group = config.ASSIGNMENT_GROUPS.get(state["category"], config.FALLBACK_GROUP)
    return {
        "resolution_status": "Assigned",
        "assignment_group": group,
        "resolution_notes": f"Assigned to {group} for {state['category']} ({state['urgency']} urgency).",
        "actions_log": _log_action(state, f"Assigned to {group}"),
    }


def notify_user_node(state: TicketState) -> dict:
    """Generate a context-aware email to the user (LLM, with template fallback)."""
    email = _generate_email(state)
    return {
        "email_body": email,
        "actions_log": _log_action(state, f"Notification email generated for {state['user_email']}"),
    }


def update_ticket_node(state: TicketState) -> dict:
    """Finalize the record — timestamp the resolution and log closure."""
    return {
        "actions_log": _log_action(
            state,
            f"Ticket finalized — status={state.get('resolution_status')} "
            f"group={state.get('assignment_group')}",
        ),
    }


def fallback_node(state: TicketState) -> dict:
    """Send tickets we can't confidently handle to the human review queue."""
    reason = state.get("error") or (
        f"confidence {state.get('confidence', 0.0):.2f} below threshold "
        f"{config.FALLBACK_MAX_CONFIDENCE}"
    )
    return {
        "resolution_status": "Fallback",
        "assignment_group": config.FALLBACK_GROUP,
        "resolution_notes": f"Low confidence classification — requires manual review. {reason}",
        "actions_log": _log_action(state, f"Fallback to {config.FALLBACK_GROUP}: {reason}"),
    }


# =========================================================================== #
# Email generation (LLM with deterministic template fallback)
# =========================================================================== #

def _generate_email(state: TicketState) -> str:
    ref = state.get("ticket_id", "N/A")
    if state.get("resolution_status") == "Auto-Resolved":
        action = "We have automatically reset your password."
        next_steps = ("Use the temporary password we issued to sign in, then set a new "
                      "password when prompted. Reply to this ticket if you still can't access your account.")
    else:
        group = state.get("assignment_group", "the relevant team")
        action = f"Your request has been assigned to our {group}."
        next_steps = "A specialist will follow up shortly. No action is needed from you right now."

    if config.USE_MOCK_LLM:
        return _email_template(state, ref, action, next_steps)

    try:
        prompt = (
            "Write a brief, friendly IT support email to the user. Plain text only.\n"
            f"User name: {state.get('user_name')}\n"
            f"Ticket reference: {ref}\n"
            f"Original subject: {state.get('subject')}\n"
            f"Action taken: {action}\n"
            f"Next steps: {next_steps}\n"
            "Include the ticket reference, the action taken, and the next steps. "
            "Keep it under 120 words."
        )
        response = _get_client().chat.completions.create(
            model=config.MODEL,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}],
        )
        body = (response.choices[0].message.content or "").strip()
        return body or _email_template(state, ref, action, next_steps)
    except Exception as exc:  # noqa: BLE001 — never let email generation break the flow
        logger.warning("Email LLM failed, using template: %s", exc)
        return _email_template(state, ref, action, next_steps)


def _email_template(state: TicketState, ref: str, action: str, next_steps: str) -> str:
    return (
        f"Hi {state.get('user_name', 'there')},\n\n"
        f"Thank you for contacting the IT Service Desk regarding \"{state.get('subject')}\" "
        f"(Ticket {ref}).\n\n"
        f"{action}\n\n"
        f"Next steps: {next_steps}\n\n"
        f"Best regards,\nIT Service Desk"
    )


# =========================================================================== #
# Conditional-edge routers (read-only: return the next node's name)
# =========================================================================== #

def route_after_intake(state: TicketState) -> str:
    """After intake: bad data -> fallback, otherwise classify."""
    return "fallback" if state.get("error") else "classify"


def route_decision(state: TicketState) -> str:
    """Core routing logic, driven by config thresholds.

    Precedence:
      1. classification failed            -> fallback
      2. Password Reset & high confidence -> auto_resolve
      3. confidence below floor           -> fallback
      4. everything else                  -> assign_to_team
    """
    if state.get("error"):
        return "fallback"

    confidence = state.get("confidence", 0.0)
    if state.get("category") == "Password Reset" and confidence >= config.AUTO_RESOLVE_MIN_CONFIDENCE:
        return "auto_resolve"
    if confidence < config.FALLBACK_MAX_CONFIDENCE:
        return "fallback"
    return "assign_to_team"

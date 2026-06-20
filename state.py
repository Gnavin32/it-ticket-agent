"""Graph state schema for the IT ticket triage agent.

A single ``TicketState`` dict flows through every node in the graph. Each node
reads the fields it needs and returns a partial update, which LangGraph merges
back into the shared state.
"""

from typing import TypedDict


class TicketState(TypedDict, total=False):
    """Shared state passed between graph nodes.

    ``total=False`` lets early nodes populate fields incrementally — e.g.
    ``category`` does not exist until ``classify`` runs — without every node
    having to supply every key.
    """

    # --- Populated by ticket_intake (from the raw incoming ticket) ---
    ticket_id: str
    subject: str
    description: str
    user_email: str
    user_name: str

    # --- Populated by classify ---
    category: str          # one of config.CATEGORIES
    urgency: str           # one of config.URGENCIES
    confidence: float      # 0.0 - 1.0
    reasoning: str         # brief explanation from the classifier

    # --- Populated by routing / action nodes ---
    assignment_group: str
    resolution_status: str  # "Auto-Resolved" | "Assigned" | "Fallback"
    resolution_notes: str
    email_body: str
    actions_log: list[str]  # append-only audit trail of what each node did

    # --- Set only when something goes wrong (drives routing to fallback) ---
    error: str

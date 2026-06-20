"""Assembles the LangGraph triage agent.

Flow:

    START
      -> ticket_intake
           -> (valid)   classify
           -> (invalid) fallback
      -> classify
           -> (Password Reset & high conf) auto_resolve
           -> (low confidence / failed)    fallback
           -> (otherwise)                  assign_to_team
      -> auto_resolve / assign_to_team -> notify_user -> update_ticket -> END
      -> fallback -> END
"""

from langgraph.graph import StateGraph, START, END

import nodes
from state import TicketState


def build_agent():
    """Build and compile the triage graph into a runnable agent."""
    graph = StateGraph(TicketState)

    # --- Register nodes ---
    graph.add_node("ticket_intake", nodes.ticket_intake_node)
    graph.add_node("classify", nodes.classify_node)
    graph.add_node("auto_resolve", nodes.auto_resolve_node)
    graph.add_node("assign_to_team", nodes.assign_to_team_node)
    graph.add_node("notify_user", nodes.notify_user_node)
    graph.add_node("update_ticket", nodes.update_ticket_node)
    graph.add_node("fallback", nodes.fallback_node)

    # --- Edges ---
    graph.add_edge(START, "ticket_intake")

    # Intake validates; bad input skips classification entirely.
    graph.add_conditional_edges(
        "ticket_intake",
        nodes.route_after_intake,
        {"classify": "classify", "fallback": "fallback"},
    )

    # Core routing decision after classification.
    graph.add_conditional_edges(
        "classify",
        nodes.route_decision,
        {
            "auto_resolve": "auto_resolve",
            "assign_to_team": "assign_to_team",
            "fallback": "fallback",
        },
    )

    # Both action paths converge on notification, then the final update.
    graph.add_edge("auto_resolve", "notify_user")
    graph.add_edge("assign_to_team", "notify_user")
    graph.add_edge("notify_user", "update_ticket")
    graph.add_edge("update_ticket", END)

    # Fallback terminates without notifying (input may lack a usable email).
    graph.add_edge("fallback", END)

    return graph.compile()


# Build once at import so callers can `from agent import agent`.
agent = build_agent()

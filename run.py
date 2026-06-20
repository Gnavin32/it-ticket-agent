"""Entry point — runs the triage agent over the 5 sample tickets.

For each ticket it prints a short summary to the console and writes the full
final state to output/<TICKET_ID>.json.

Usage:
    python run.py            # process all sample tickets
"""

import json
import logging
import os

from dotenv import load_dotenv

load_dotenv()  # pick up OPENROUTER_API_KEY / TRIAGE_MODEL from a .env file if present

import config  # noqa: E402  (import after load_dotenv so env vars are read)
from agent import agent  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(message)s")

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")

# --------------------------------------------------------------------------- #
# Sample tickets from the assignment
# --------------------------------------------------------------------------- #
SAMPLE_TICKETS = [
    {
        "ticket_id": "INC001",
        "subject": "Cannot login to my account",
        "description": "I forgot my password and I'm locked out of my Active Directory "
                       "account. Please reset ASAP.",
        "user_email": "john.smith@company.com",
    },
    {
        "ticket_id": "INC002",
        "subject": "Laptop screen flickering",
        "description": "My Dell laptop screen has been flickering intermittently since "
                       "yesterday. It's making it hard to work.",
        "user_email": "jane.doe@company.com",
    },
    {
        "ticket_id": "INC003",
        "subject": "Need access to SharePoint site",
        "description": "I recently joined the marketing team and need access to the "
                       "Marketing SharePoint site and Teams channel.",
        "user_email": "bob.wilson@company.com",
    },
    {
        "ticket_id": "INC004",
        "subject": "asdfghjkl",
        "description": "help computer broken thing not work",
        "user_email": "alice.brown@company.com",
    },
    {
        "ticket_id": "INC005",
        "subject": "VPN disconnects every 10 minutes",
        "description": "Since the last update, my VPN drops every 10 minutes. I'm on "
                       "Windows 11 using GlobalProtect. I've tried reinstalling but the "
                       "issue persists.",
        "user_email": "charlie.davis@company.com",
    },
]


def process_ticket(ticket: dict) -> dict:
    """Run one ticket through the agent and return its final state."""
    initial_state = {**ticket, "actions_log": []}
    return agent.invoke(initial_state)


def main() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    mode = "MOCK keyword classifier" if config.USE_MOCK_LLM else f"LLM ({config.MODEL})"
    print(f"\n=== IT Ticket Triage Agent — using {mode} ===\n")

    for ticket in SAMPLE_TICKETS:
        result = process_ticket(ticket)

        out_path = os.path.join(OUTPUT_DIR, f"{ticket['ticket_id']}.json")
        with open(out_path, "w") as f:
            json.dump(result, f, indent=2)

        print(f"--- {result['ticket_id']} ---")
        print(f"  Category   : {result.get('category', '-')} "
              f"(confidence {result.get('confidence', 0.0):.2f})")
        print(f"  Urgency    : {result.get('urgency', '-')}")
        print(f"  Status     : {result.get('resolution_status', '-')}")
        print(f"  Group      : {result.get('assignment_group', '-')}")
        print(f"  Saved      : output/{result['ticket_id']}.json\n")


if __name__ == "__main__":
    main()

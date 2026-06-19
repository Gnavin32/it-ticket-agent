Run:

```bash
npm start
```

This processes all 5 sample tickets and writes results to `output/`.

---

## Output

Processed ticket results are saved inside:

```text
output/
```

Each ticket generates a JSON output file containing the full final state (classification, routing outcome, email body, action log).

---

## Design Decisions

* **Language: TypeScript/Node.js instead of Python.** The assignment specified Python, but I built this in TypeScript with LangGraph.js since it's my stronger language. The graph architecture, node responsibilities, and routing logic are a direct 1:1 translation of the spec.
* Strongly typed state using a TypeScript interface (`TicketState`), validated by the compiler on every node transition.
* LangGraph used for workflow orchestration, with two conditional edges: one after `ticket_intake` (validation failure → fallback) and one after `classify` (routing decision based on category/confidence).
* Structured JSON classification output via a constrained system prompt, with explicit instructions to lower confidence on vague or gibberish input. This was necessary to get garbage tickets (like INC004 — "asdfghjkl") to correctly trigger fallback instead of being confidently misclassified.
* `notify_user` generates the email from a template rather than a second LLM call, to keep the pipeline fast and deterministic for this assessment. The assignment explicitly allows a template ("using the LLM or a template"). Swapping in an LLM-generated email is a small, isolated change to one function.
* Fallback tickets route straight to `END` without going through `notify_user`, matching the diagram in the spec — the assumption is a human reviewer handles user communication once a ticket lands in the AI Review Queue.
* Confidence thresholds and assignment-group mappings live in `config.ts`, not hardcoded in node logic.
* LLM calls use `openai/gpt-oss-20b:free` via OpenRouter. This is a free-tier model with rate limits (roughly 20 requests/minute) — fine for this assignment's 5-ticket batch, but a production deployment would need a paid tier or a different provider.

---

## Production Improvements

* Connect to ServiceNow/Jira APIs instead of mock actions
* Persistent database storage instead of flat JSON files
* Audit logging
* Authentication and RBAC
* Retry handling for malformed LLM responses (currently a malformed JSON response sets `error` and routes to fallback — a retry-with-corrective-prompt step would reduce unnecessary fallbacks)
* Human approval workflow before auto-resolve actions for higher-risk categories
* Monitoring and observability (structured per-node logging, latency tracking, classification accuracy tracking over time)
* Switch to a paid/production-grade LLM tier to remove free-tier rate limits
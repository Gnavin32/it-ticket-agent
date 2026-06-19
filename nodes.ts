import type { TicketState } from "./state.js";
import { llm } from "./llm.js";
import {
  CATEGORIES,
  URGENCY_LEVELS,
  CONFIDENCE_THRESHOLDS,
  ASSIGNMENT_GROUPS,
} from "./config.js";

// ----------------------
// ticket_intake
// ----------------------
export function ticketIntake(raw: any): TicketState {
  const missing: string[] = [];

  if (!raw.subject) missing.push("subject");
  if (!raw.description) missing.push("description");
  if (!raw.user_email) missing.push("user_email");

  return {
    ticket_id: raw.ticket_id,
    subject: raw.subject ?? "",
    description: raw.description ?? "",
    user_email: raw.user_email ?? "",
    user_name: raw.user_name ?? "",

    category: "",
    urgency: "",
    confidence: 0,
    reasoning: "",

    assignment_group: "",
    resolution_status: "",
    resolution_notes: "",
    email_body: "",

    actions_log: [
      `[${new Date().toISOString()}] Ticket intake processed`,
    ],

    error:
      missing.length > 0
        ? `Missing required fields: ${missing.join(", ")}`
        : "",
  };
}

// ----------------------
// classify
// ----------------------
export async function classify(
  state: TicketState
): Promise<TicketState> {
  if (state.error) return state;

  const systemPrompt = `
You are an IT Service Desk Ticket Classifier.

Allowed Categories:
${CATEGORIES.join(", ")}

Allowed Urgency:
${URGENCY_LEVELS.join(", ")}

Be honest about uncertainty. If the subject or description is vague, generic,
contains gibberish, or lacks enough specific detail to confidently pick a
category, you MUST give a LOW confidence score (below 0.5), regardless of
which category you pick. Only give a high confidence score (0.8+) when the
ticket clearly and specifically describes a problem that matches one category
well.

Return ONLY valid JSON.

Example:
{
  "category":"Password Reset",
  "urgency":"High",
  "confidence":0.95,
  "reasoning":"User forgot password"
}
`;

  const userPrompt = `
Subject: ${state.subject}

Description:
${state.description}
`;

  try {
    const response = await llm.invoke([
      {
        role: "system",
        content: systemPrompt,
      },
      {
        role: "user",
        content: userPrompt,
      },
    ]);

    const parsed = JSON.parse(response.content.toString());

    return {
      ...state,
      category: parsed.category,
      urgency: parsed.urgency,
      confidence: parsed.confidence,
      reasoning: parsed.reasoning,

      actions_log: [
        ...state.actions_log,
        `[${new Date().toISOString()}] Classified as ${parsed.category}`,
      ],
    };
  } catch (err) {
    return {
      ...state,
      error: "Classification failed",
    };
  }
}

// ----------------------
// route_decision
// ----------------------
export function routeDecision(
  state: TicketState
): "auto_resolve" | "assign_to_team" | "fallback" {
  if (state.error) return "fallback";

  const isPasswordReset = state.category === "Password Reset";
  const meetsAutoResolveBar = state.confidence >= CONFIDENCE_THRESHOLDS.AUTO_RESOLVE_MIN;
  const belowFallbackBar = state.confidence < CONFIDENCE_THRESHOLDS.FALLBACK_MAX;

  if (isPasswordReset && meetsAutoResolveBar) {
    return "auto_resolve";
  }

  if (belowFallbackBar) {
    return "fallback";
  }

  return "assign_to_team";
}

// ----------------------
// auto_resolve
// ----------------------
export function autoResolve(
  state: TicketState
): TicketState {
  return {
    ...state,
    resolution_status: "Auto-Resolved",
    resolution_notes:
      "Password reset completed successfully.",

    actions_log: [
      ...state.actions_log,
      `[${new Date().toISOString()}] Password reset executed`,
    ],
  };
}

// ----------------------
// assign_to_team
// ----------------------
export function assignToTeam(
  state: TicketState
): TicketState {
  const group =
    ASSIGNMENT_GROUPS[state.category] ??
    "Service Desk";

  return {
    ...state,
    assignment_group: group,
    resolution_status: "Assigned",

    resolution_notes: `Assigned to ${group}`,

    actions_log: [
      ...state.actions_log,
      `[${new Date().toISOString()}] Assigned to ${group}`,
    ],
  };
}

// ----------------------
// notify_user
// ----------------------
export async function notifyUser(
  state: TicketState
): Promise<TicketState> {
  const email = `
Hello,

Ticket Reference: ${state.ticket_id}

Category: ${state.category}
Status: ${state.resolution_status}

${state.resolution_notes}

Thank you,
IT Service Desk
`;

  return {
    ...state,
    email_body: email,

    actions_log: [
      ...state.actions_log,
      `[${new Date().toISOString()}] Email generated`,
    ],
  };
}

// ----------------------
// update_ticket
// ----------------------
export function updateTicket(
  state: TicketState
): TicketState {
  return {
    ...state,

    actions_log: [
      ...state.actions_log,
      `[${new Date().toISOString()}] Ticket updated`,
    ],
  };
}

// ----------------------
// fallback
// ----------------------
export function fallback(
  state: TicketState
): TicketState {
  return {
    ...state,

    assignment_group: "AI Review Queue",

    resolution_status: "Fallback",

    resolution_notes:
      "Low confidence classification — requires manual review",

    actions_log: [
      ...state.actions_log,
      `[${new Date().toISOString()}] Sent to AI Review Queue`,
    ],
  };
}
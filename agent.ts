import { StateGraph, START, END, Annotation } from "@langchain/langgraph";
import {
  ticketIntake,
  classify,
  routeDecision,
  autoResolve,
  assignToTeam,
  notifyUser,
  updateTicket,
  fallback,
} from "./nodes.js";

// LangGraph needs the state shape declared as "Annotations" so it knows
// how to merge updates returned by each node. Since every one of our
// node functions already returns a FULL, merged state object (using
// `...state` spreads), we don't need custom merge logic — each field
// just gets overwritten with whatever the node returns.
const GraphState = Annotation.Root({
  ticket_id: Annotation<string>(),
  subject: Annotation<string>(),
  description: Annotation<string>(),
  user_email: Annotation<string>(),
  user_name: Annotation<string>(),
  category: Annotation<string>(),
  urgency: Annotation<string>(),
  confidence: Annotation<number>(),
  reasoning: Annotation<string>(),
  assignment_group: Annotation<string>(),
  resolution_status: Annotation<string>(),
  resolution_notes: Annotation<string>(),
  email_body: Annotation<string>(),
  actions_log: Annotation<string[]>(),
  error: Annotation<string>(),
});

// Build the graph: nodes first, then edges (including the two
// conditional branch points from the assignment spec).
const workflow = new StateGraph(GraphState)
  .addNode("ticket_intake", (state) => ticketIntake(state))
  .addNode("classify", classify)
  .addNode("auto_resolve", autoResolve)
  .addNode("assign_to_team", assignToTeam)
  .addNode("notify_user", notifyUser)
  .addNode("update_ticket", updateTicket)
  .addNode("fallback", fallback)

  .addEdge(START, "ticket_intake")

  // Branch 1: did intake validation fail (missing required fields)?
  .addConditionalEdges(
    "ticket_intake",
    (state) => (state.error ? "fallback" : "classify"),
    { fallback: "fallback", classify: "classify" }
  )

  // Branch 2: based on classification result, decide the path.
  .addConditionalEdges("classify", routeDecision, {
    auto_resolve: "auto_resolve",
    assign_to_team: "assign_to_team",
    fallback: "fallback",
  })

  .addEdge("auto_resolve", "notify_user")
  .addEdge("assign_to_team", "notify_user")
  .addEdge("notify_user", "update_ticket")
  .addEdge("update_ticket", END)
  .addEdge("fallback", END);

export const agent = workflow.compile();
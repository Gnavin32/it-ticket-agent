export interface TicketState {
  ticket_id: string;
  subject: string;
  description: string;
  user_email: string;
  user_name: string;

  category: string;
  urgency: string;
  confidence: number;
  reasoning: string;

  assignment_group: string;
  resolution_status: string; // "Auto-Resolved" | "Assigned" | "Fallback"
  resolution_notes: string;
  email_body: string;

  actions_log: string[];
  error: string;
}
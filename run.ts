import fs from "fs";
import { agent } from "./agent.js";

const tickets = [
  {
    ticket_id: "INC001",
    subject: "Cannot login to my account",
    description:
      "I forgot my password and I'm locked out of my Active Directory account. Please reset ASAP.",
    user_email: "john.smith@company.com",
    user_name: "John Smith",
  },

  {
    ticket_id: "INC002",
    subject: "Laptop screen flickering",
    description:
      "My Dell laptop screen has been flickering intermittently since yesterday. It's making it hard to work.",
    user_email: "jane.doe@company.com",
    user_name: "Jane Doe",
  },

  {
    ticket_id: "INC003",
    subject: "Need access to SharePoint site",
    description:
      "I recently joined the marketing team and need access to the Marketing SharePoint site and Teams channel.",
    user_email: "bob.wilson@company.com",
    user_name: "Bob Wilson",
  },

  {
    ticket_id: "INC004",
    subject: "asdfghjkl",
    description: "help computer broken thing not work",
    user_email: "alice.brown@company.com",
    user_name: "Alice Brown",
  },

  {
    ticket_id: "INC005",
    subject: "VPN disconnects every 10 minutes",
    description:
      "Since the last update, my VPN drops every 10 minutes. I'm on Windows 11 using GlobalProtect. I've tried reinstalling but the issue persists.",
    user_email: "charlie.davis@company.com",
    user_name: "Charlie Davis",
  },
];

// Create output folder if it doesn't exist
if (!fs.existsSync("output")) {
  fs.mkdirSync("output");
}

for (const ticket of tickets) {
  const result = await agent.invoke(ticket);

  console.log("\n==================================");
  console.log(`Ticket: ${ticket.ticket_id}`);
  console.log("==================================");

  console.log(JSON.stringify(result, null, 2));

  fs.writeFileSync(
    `output/${ticket.ticket_id}.json`,
    JSON.stringify(result, null, 2)
  );
}

console.log("\n✅ All ticket outputs saved to output/ folder");
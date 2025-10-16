import os
import re
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain.agents import initialize_agent, AgentType, Tool
from langchain_tavily import TavilySearch
from raghugging import get_answer
import re
from categorization import categorize_ticket
from langchain.memory import ConversationBufferMemory


load_dotenv()

# -----------------------------
# Google Sheets setup
# -----------------------------
SHEET_NAME = "MyDatabaseSheet"
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
gspread_client = gspread.authorize(creds)
sheet = gspread_client.open(SHEET_NAME)
ticket_sheet = sheet.sheet1

# -----------------------------
# Ticket Lookup (run once per session)
# -----------------------------
lookup_cache = {}

def ticket_lookup(input_str):
    """Extract a ticket ID from any string and lookup in Google Sheets."""
    match = re.search(r"\bTIC\d+\b", input_str.upper())
    if not match:
        return f"Could not find a valid ticket ID in: {input_str}"
    
    ticket_id = match.group(0)
    
    # Check cache first
    if ticket_id in lookup_cache:
        info = lookup_cache[ticket_id]
        return f"Ticket {info['ticket_id']} ({info['ticket_category']}) was created by {info['ticket_by']} on {info['ticket_timestamp']}. Status: {info['ticket_status']}. Content: {info['ticket_content']}"
    
    # Lookup in sheet
    all_tickets = ticket_sheet.get_all_records()
    for row in all_tickets:
        if row.get("ticket_id") == ticket_id:
            ticket_info = {
                "ticket_id": row.get("ticket_id"),
                "ticket_content": row.get("ticket_content", "N/A"),
                "ticket_category": row.get("ticket_category", "N/A"),
                "ticket_timestamp": row.get("ticket_timestamp", "N/A"),
                "ticket_by": row.get("ticket_by", "N/A"),
                "ticket_status": row.get("ticket_status", "N/A")
            }
            lookup_cache[ticket_id] = ticket_info
            return f"Ticket {ticket_info['ticket_id']} ({ticket_info['ticket_category']}) was created by {ticket_info['ticket_by']} on {ticket_info['ticket_timestamp']}. Status: {ticket_info['ticket_status']}. Content: {ticket_info['ticket_content']}"
    
    return f"Ticket ID {ticket_id} not found in the sheet."
# -----------------------------
# Tools
# -----------------------------
rag_tool = Tool(
    name="RAGKnowledgeBase",
    func=get_answer,
    description="Answer ticket-related queries using internal knowledge base (Train.pdf)."
)

google_sheet_lookup_tool = Tool(
    name="GoogleSheetsLookup",
    func=ticket_lookup,
    description="Look up ticket information by ticket ID in Google Sheets."
)

tavily = TavilySearch(max_results=3, tavily_api_key=os.getenv("TAVILY_API_KEY"))

def tavily_search_fn(query: str) -> str:
    result = tavily.invoke({"query": query})
    return str(result)

tavily_tool = Tool(
    name="TavilySearch",
    func=tavily_search_fn,
    description="Search the web using Tavily. Input should be a search query string."
)
from datetime import datetime

# -----------------------------
# Ticket Tools
# -----------------------------

def save_ticket_tool(ticket: dict):
    """
    Save or update a ticket in Google Sheets.
    ticket: dict with keys - ticket_id, content, user_email
            optionally - category
    """
    ticket_id = ticket.get("ticket_id")
    content = ticket.get("content")
    user_email = ticket.get("user_email")
    category = ticket.get("category")

    if not ticket_id or not content or not user_email:
        return "❌ Missing required ticket information."

    # Auto-categorize if category not provided
    if not category:
        try:
            category = categorize_ticket(content)
        except Exception:
            category = "uncategorized"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        all_tickets = ticket_sheet.get_all_records()
        existing_ids = [row["ticket_id"] for row in all_tickets]

        row_data = [ticket_id, content, category, timestamp, user_email, "pending"]

        if ticket_id in existing_ids:
            # Direct update if ticket exists
            row_index = existing_ids.index(ticket_id) + 2
            ticket_sheet.update(f"A{row_index}:F{row_index}", [row_data])
            lookup_cache[ticket_id] = {
                "ticket_id": ticket_id,
                "ticket_content": content,
                "ticket_category": category,
                "ticket_timestamp": timestamp,
                "ticket_by": user_email,
                "ticket_status": lookup_cache.get(ticket_id, {}).get("ticket_status", "pending")
            }
            return f"✅ Ticket '{ticket_id}' updated successfully (category: {category})."
        else:
            ticket_sheet.append_row(row_data)
            lookup_cache[ticket_id] = {
                "ticket_id": ticket_id,
                "ticket_content": content,
                "ticket_category": category,
                "ticket_timestamp": timestamp,
                "ticket_by": user_email,
                "ticket_status": "pending"
            }
            return f"✅ Ticket '{ticket_id}' saved successfully (category: {category})."
    except Exception as e:
        return f"⚠️ Error saving ticket: {str(e)}"


def update_ticket_status_tool(input_str: str):
    """
    Update ticket status in Google Sheets.
    Input examples:
        "TIC123, closed" -> sets ticket TIC123 to closed
        "TIC123" -> defaults status to 'pending'
    """
    try:
        # Split ticket ID and optional status
        parts = [p.strip() for p in input_str.split(",")]
        ticket_id = parts[0].upper()
        status = parts[1].lower() if len(parts) > 1 else "pending"

        all_tickets = ticket_sheet.get_all_records()
        existing_ids = [row["ticket_id"] for row in all_tickets]

        if ticket_id not in existing_ids:
            return f"⚠️ Ticket ID '{ticket_id}' not found."

        row_index = existing_ids.index(ticket_id) + 2
        status_col_index = ticket_sheet.row_values(1).index("ticket_status") + 1

        ticket_sheet.update_cell(row_index, status_col_index, status)

        # Update cache
        lookup_cache[ticket_id]["ticket_status"] = status
        return f"✅ Ticket '{ticket_id}' status updated to '{status}'."

    except Exception as e:
        return f"⚠️ Error updating ticket status: {str(e)}"

# -----------------------------
# Tool Wrappers for LangChain
# -----------------------------
save_ticket_tool_wrapper = Tool(
    name="SaveTicket",
    func=save_ticket_tool,
    description="Save or update a ticket. Input must be a dict with keys: ticket_id, content, category, user_email."
)

update_ticket_status_tool_wrapper = Tool(
    name="UpdateTicketStatus",
    func=update_ticket_status_tool,
    description="Update the status of a ticket. Input: 'TIC123, closed' or 'TIC123'."
)

memory = ConversationBufferMemory(
    memory_key="chat_history",   # must match your agent input
    return_messages=True          # keeps messages as structured chat
)
# -----------------------------
# LLM
# -----------------------------
llm = ChatGroq(model="llama-3.1-8b-instant")

# -----------------------------
# Prompt (for final reasoning)
# -----------------------------
prompt = PromptTemplate(
    input_variables=["question", "agent_scratchpad"],
    template=(
        "You are a helpful ticket assistant.\n"
        "User question: {question}\n"
        "Information gathered from tools so far:\n{agent_scratchpad}\n"
        "Now provide a final answer."
    )
)

# -----------------------------
# Agent
# -----------------------------
tools = [rag_tool, google_sheet_lookup_tool, tavily_tool,save_ticket_tool_wrapper]

agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
    verbose=True,
    memory=memory,
    handle_parsing_errors=True,
    max_iterations=5,         
    max_execution_time=100
)


# -----------------------------
# Run
# -----------------------------
if __name__ == "__main__":
    print("🛠️ Welcome to the AI Ticket Assistant!")
    print("Type 'exit' or 'quit' to end the session.\n")

    while True:
        try:
            user_input = input("Enter your question: ").strip()
            
            if user_input.lower() in ["exit", "quit","bye"]:
                print("👋 Goodbye!")
                break

            # Agent now automatically handles memory
            response = agent.invoke({"input": user_input})
            
            # Print the final answer
            print("\nFinal Answer:\n", response.get("output", "No response from agent.\n"))

        except KeyboardInterrupt:
            print("\n👋 Session interrupted. Exiting...")
            break
        except Exception as e:
            print(f"⚠️ Error: {e}\n")

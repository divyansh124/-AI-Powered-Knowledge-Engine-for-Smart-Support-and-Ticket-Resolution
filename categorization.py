import os
from groq import Groq

# Load Groq API key from environment
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Categories list
CATEGORIES = [
    "maintenance", "product_support", "refund", "high_priority_product", "technical_issue",
    "new_booking", "cancellation", "reschedule", "seat_change", "payment_issue",
    "discount_coupon_issue", "booking_confirmation", "waitlist_enquiry", "tatkal_booking",
    "special_assistance", "baggage_luggage", "travel_passes", "group_booking",
    "general_enquiry", "high_priority_escalation"
]

def categorize_ticket(content: str, model: str = "llama-3.1-8b-instant") -> str:
    """
    Use Groq LLM to categorize a ticket.
    Returns the most appropriate category from CATEGORIES.
    """
    try:
        response = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": f"""
                You are an expert support ticket categorizer.
                Analyze the SEMANTIC MEANING of the ticket.
                Choose the most appropriate category from:
                {CATEGORIES}.
                Return ONLY the category name.
                """},
                {"role": "user", "content": f"Ticket content: {content}"}
            ],
            model=model,
            temperature=0.0,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("⚠️ Error in categorization:", e)
        return "general_enquiry"

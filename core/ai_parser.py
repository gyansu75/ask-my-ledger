import json
import os
import pandas as pd
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def process_natural_query(query: str, transactions: list) -> dict:
  """Parses natural language queries using Groq with detailed terminal logging."""
  df = pd.DataFrame(transactions)

  system_prompt = """
    You are AskMyLedger AI, an expert financial analyst assistant for merchants using PayPal.
    Analyze the user's natural language query against the available transaction data properties.
    Return a valid JSON object with EXACTLY these three keys:
    1. "filter_status": string ("Completed", "Refunded", "Pending", or "All")
    2. "filter_type": string ("Subscription", "Service", "One-time", or "All")
    3. "message": string (A professional, concise financial analyst response summarizing what is being shown)
    
    Do not include any markdown formatting blocks like ```json in your response, just return the raw JSON string.
    """

  user_prompt = f"User Query: '{query}'\nAvailable Transactions Summary: {df.to_dict(orient='records')}"

  try:
    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        model="openai/gpt-oss-20b",
        temperature=0.1,
        response_format={"type": "json_object"},
    )

    ai_response_content = chat_completion.choices[0].message.content
    print(f"\n[DEBUG] Raw Groq Response: {ai_response_content}")

    parsed_intent = json.loads(ai_response_content)

    f_status = parsed_intent.get("filter_status", "All")
    f_type = parsed_intent.get("filter_type", "All")
    msg = parsed_intent.get(
        "message", "Here are your filtered merchant transactions:"
    )

    print(f"[DEBUG] Extracted Filters -> Status: {f_status} | Type: {f_type}")

    # Apply filters using Pandas
    filtered_df = df.copy()
    if f_status and f_status.lower() != "all":
      filtered_df = filtered_df[
          filtered_df["status"].str.lower() == f_status.lower()
      ]
    if f_type and f_type.lower() != "all":
      filtered_df = filtered_df[
          filtered_df["type"].str.lower() == f_type.lower()
      ]

    return {"message": msg, "data": filtered_df.to_dict(orient="records")}

  except Exception as e:
    print(f"\n[ERROR] Groq AI Parsing Failed: {e}")
    return {
        "message": (
            "Showing all transactions (AI query processed via fallback mode due"
            " to error)."
        ),
        "data": transactions,
    }
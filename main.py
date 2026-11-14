from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from core.paypal import fetch_sandbox_transactions
from core.ai_parser import process_natural_query

app = FastAPI(
    title="AskMyLedger",
    description="AI Financial Analyst & Interactive Dashboard powered by PayPal",
)

# Serve frontend static files
app.mount("/static", StaticFiles(directory="static"), name="static")


class QueryRequest(BaseModel):
  prompt: str


@app.get("/api/transactions")
def get_transactions():
  """Fetch all PayPal sandbox transactions for the merchant ledger."""
  try:
    txns = fetch_sandbox_transactions()
    return {"status": "success", "transactions": txns}
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ask")
def ask_ledger(payload: QueryRequest):
  """Accepts plain English prompts, queries ledger data, and returns results."""
  try:
    txns = fetch_sandbox_transactions()
    result = process_natural_query(payload.prompt, txns)
    return {"status": "success", "query": payload.prompt, "result": result}
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
def read_root():
  return {
      "message": "Welcome to AskMyLedger API! Access the UI at /static/index.html"
  }
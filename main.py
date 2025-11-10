from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from typing import Optional, List

app = FastAPI(title="NayaPay Tracker API")

# MongoDB connection
client = AsyncIOMotorClient(
    "mongodb+srv://zaimkhan2003_db_user:VHMT9UIU3eFSnmtk@expense.mnaci9g.mongodb.net/expenseTracker?retryWrites=true&w=majority"
)
db = client.expenseTracker
collection = db.transactions

# Transaction model
class Transaction(BaseModel):
    date: str           # e.g., "Sun, Nov 9, 2025, 23:27"
    type: str           # "sent" or "received"
    amount: float
    merchant: str
    balance: Optional[float] = 0

# Add a new transaction
@app.post("/transactions")
async def add_transaction(tx: Transaction):
    try:
        # Convert string date to datetime
        if "T" in tx.date:
            date_obj = datetime.fromisoformat(tx.date)
        else:
            date_obj = datetime.strptime(tx.date, "%a, %b %d, %Y, %H:%M")
        tx_dict = tx.dict()
        tx_dict["date"] = date_obj
        result = await collection.insert_one(tx_dict)
        return {"id": str(result.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get all transactions
@app.get("/transactions")
async def get_transactions():
    transactions = await collection.find().sort("date", -1).to_list(length=None)
    for t in transactions:
        t["_id"] = str(t["_id"])
    return transactions

# Get monthly summary
@app.get("/transactions/summary/{month}")
async def monthly_summary(month: str):
    """
    month format: "2025-11"
    Returns total amount grouped by type (sent/received) for the month
    """
    try:
        start = datetime.strptime(f"{month}-01", "%Y-%m-%d")
        end_month = start.month % 12 + 1
        end_year = start.year if end_month != 1 else start.year + 1
        end = datetime(end_year, end_month, 1)
        pipeline = [
            {"$match": {"date": {"$gte": start, "$lt": end}}},
            {"$group": {"_id": "$type", "total": {"$sum": "$amount"}}}
        ]
        summary = await collection.aggregate(pipeline).to_list(length=None)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

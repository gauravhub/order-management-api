"""FastAPI REST API for order management database queries."""

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

from src.config import Configuration
from src.services.database import DatabaseService

# Initialize configuration and database service
config = Configuration()
db_service = DatabaseService(config)

app = FastAPI(
    title="Order Management API",
    description="REST API for querying order management database",
    version="0.1.0"
)


@app.on_event("startup")
async def startup_event():
    """Initialize database on application startup."""
    try:
        print("Initializing database from JSON files...")
        results = db_service.initialize()
        print(f"Database initialization complete: {results}")
    except Exception as e:
        print(f"ERROR: Failed to initialize database: {str(e)}")
        raise


@app.get("/api/customer")
async def find_customer(
    email: str = Query(default="", description="Customer email address"),
    customer_id: str = Query(default="", description="Customer ID")
) -> dict:
    """Find a customer by email or customer ID.
    
    Args:
        email: Customer's email address (optional)
        customer_id: Customer ID (optional)
    
    Returns:
        Dictionary with customer information if found, empty dict if not found.
        Contains: customer_id, name, email
    """
    if not email and not customer_id:
        return {}
    
    try:
        customer = db_service.find_customer(email=email if email else None, customer_id=customer_id if customer_id else None)
        if customer:
            return customer
        return {}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        return {"error": f"Could not find customer: {str(e)}"}


@app.get("/api/order")
async def find_order(
    order_no: str = Query(..., description="Order number (e.g., ORD00009998)")
) -> dict:
    """Find an order by order number.
    
    Args:
        order_no: Order number (e.g., "ORD00009998")
    
    Returns:
        Dictionary with order information if found, empty dict if not found.
        Contains: order_no, customer_id, order_status, order_date_time, etc.
    """
    if not order_no:
        return {}
    
    try:
        order = db_service.find_order(order_no)
        if order:
            return order
        return {}
    except Exception as e:
        return {"error": f"Could not find order: {str(e)}"}


@app.get("/api/transaction")
async def find_transaction(
    transaction_id: str = Query(..., description="Transaction ID to search for")
) -> dict:
    """Find a transaction by transaction ID.
    
    Args:
        transaction_id: Transaction ID to search for
    
    Returns:
        Dictionary with transaction information if found, empty dict if not found.
        Contains: transaction_id, order_no, customer_id, transaction_status, amount, etc.
    """
    if not transaction_id:
        return {}
    
    try:
        transaction = db_service.find_transaction(transaction_id)
        if transaction:
            return transaction
        return {}
    except Exception as e:
        return {"error": f"Could not find transaction: {str(e)}"}


@app.get("/api/transaction/order/{order_no}")
async def get_transaction_for_order(order_no: str) -> dict:
    """Get transaction information for an order.
    
    Args:
        order_no: Order number (e.g., "ORD00009998")
    
    Returns:
        Dictionary with transaction information if found, empty dict if not found.
        Contains: transaction_id, order_no, customer_id, transaction_status, amount, etc.
    """
    if not order_no:
        return {}
    
    try:
        transaction = db_service.get_transaction_for_order(order_no)
        if transaction:
            return transaction
        return {}
    except Exception as e:
        return {"error": f"Could not find transaction for order: {str(e)}"}


@app.get("/api/refund/order/{order_no}")
async def get_refund_for_order(order_no: str) -> dict:
    """Get refund information for an order.
    
    Args:
        order_no: Order number (e.g., "ORD00009998")
    
    Returns:
        Dictionary with refund information if found, empty dict if not found.
        Contains: refund_id, order_no, transaction_id, refund_status, refund_amount, etc.
    """
    if not order_no:
        return {}
    
    try:
        refund = db_service.get_refund_for_order(order_no)
        if refund:
            return refund
        return {}
    except Exception as e:
        return {"error": f"Could not find refund for order: {str(e)}"}


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Order Management API",
        "version": "0.1.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

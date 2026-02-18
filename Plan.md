## Feature: Database Health Check Endpoint

### Description
Implement a new API endpoint to check the health of the database connection. This will help in monitoring the status of the database and detect connectivity issues early.

### Files to Create or Modify
- Modify: `backend/app/routers/__init__.py`
- Modify: `backend/app/routers/features.py`
- Create: `backend/app/tests/test_features.py`

### Step-by-Step Implementation Instructions

1. **Modify `backend/app/routers/__init__.py`:**
   - Import the new database health check route from `features.py`.
   - Ensure the route is added to the router so that it becomes part of the application.

2. **Modify `backend/app/routers/features.py`:**
   - Import necessary database connection utilities.
   - Define a new function `check_database_health` that:
     - Attempts to execute a simple query, such as `SELECT 1`.
     - Returns a JSON response with a 200 status code if the query is successful.
     - Returns an error message and a non-200 status code if there is a database connectivity issue.
   - Add a route decorator to expose this function as an API endpoint, e.g., `/health/database`.

3. **Create `backend/app/tests/test_features.py`:**
   - Write a test case to check that the endpoint returns a 200 status code for a healthy database connection.
   - Write a test to simulate a database downtime (mock database connection failure) and verify that the endpoint returns an error status code and message.
   - Write a performance test to measure response time of the endpoint under normal and stressed conditions.

### Constraints
- Do not modify `.env`, CI configurations, or deployment configurations.
- Limit changes to a maximum of 25 files.

### Example Code Snippet for `features.py`
```python
from fastapi import APIRouter, HTTPException
from sqlalchemy.exc import OperationalError
from database import get_db

router = APIRouter()

@router.get("/health/database")
def check_database_health():
    try:
        db = next(get_db())
        db.execute("SELECT 1")
        return {"status": "healthy"}
    except OperationalError:
        raise HTTPException(status_code=503, detail="Database connection failed")
```


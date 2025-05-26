from fastapi import FastAPI
from database import run_query

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hola món! Benvingut a LoveLink 💘"}

@app.get("/test-neo4j")
def test_connection():
    query = "MATCH (n) RETURN n LIMIT 5"
    try:
        results = run_query(query)
        return {"success": True, "data": results}
    except Exception as e:
        return {"success": False, "error": str(e)}
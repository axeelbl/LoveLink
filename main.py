from fastapi import FastAPI
from neo4j import GraphDatabase
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from models import PersonCreate, RelationshipCreate
from database import get_recommendations_for

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

app = FastAPI()



# --- Endpoint para obtener todas las personas en la base de datos.  ---
@app.get("/persons/")
async def list_persons():
    query = "MATCH (p:Person) RETURN p"
    with driver.session() as session:
        result = session.run(query)
        people = [record["p"] for record in result]
    return people

# --- Endpoint para para ver las relaciones de una persona específica.  ---
@app.get("/person/{name}/relationships")
async def get_relationships(name: str):
    query = """
    MATCH (p:Person {name: $name})-[r]->(other)
    RETURN type(r) AS type, r, other.name AS other_name
    """
    with driver.session() as session:
        result = session.run(query, name=name)
        relationships = []
        for record in result:
            relationships.append({
                "type": record["type"],
                "details": dict(record["r"]),
                "with": record["other_name"]
            })
    return relationships


# --- Endpoint para crear una persona ---
@app.post("/person/")
async def create_person(person: PersonCreate):
    query = """
    CREATE (:Person {name: $name, age: $age, gender: $gender, interests: $interests})
    """
    with driver.session() as session:
        session.run(query, 
            name=person.name, 
            age=person.age, 
            gender=person.gender, 
            interests=person.interests
        )
    return {"message": f"Persona {person.name} creada."}

# --- Endpoint para crear una relación ---
@app.post("/relationship/")
async def create_relationship(rel: RelationshipCreate):
    if rel.type == "INTERACTED_WITH" and (rel.interaction_type is None or rel.timestamp is None):
        raise HTTPException(status_code=400, detail="INTERACTED_WITH requiere interaction_type y timestamp.")

    match_query = """
    MATCH (a:Person {name: $from_name}), (b:Person {name: $to_name})
    """

    if rel.type == "FRIEND":
        relation_query = "CREATE (a)-[:FRIEND]->(b)"
    elif rel.type == "DATED":
        relation_query = "CREATE (a)-[:DATED]->(b)"
    elif rel.type == "INTERACTED_WITH":
        relation_query = """
        CREATE (a)-[:INTERACTED_WITH {type: $interaction_type, timestamp: $timestamp}]->(b)
        """
    else:
        raise HTTPException(status_code=400, detail="Tipo de relación no soportado.")

    with driver.session() as session:
        session.run(match_query + relation_query,
            from_name=rel.from_person,
            to_name=rel.to_person,
            interaction_type=rel.interaction_type,
            timestamp=rel.timestamp
        )

    return {"message": f"Relación {rel.type} creada entre {rel.from_person} y {rel.to_person}"}


# --- Endpoint para obtener la recomendación ---
@app.get("/recommendations/{name}")
def get_recommendations(name: str):
    try:
        recommendations = get_recommendations_for(name)
        return {"recommendations": recommendations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
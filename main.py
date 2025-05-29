from fastapi import FastAPI, HTTPException
from neo4j import GraphDatabase
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from models import PersonCreate, RelationshipCreate,InterestCreate
from database import get_recommendations_for,path_to_person

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
    
# --- Endpoint para marcar interés ---
@app.post("/interest/")
async def express_interest(interest: InterestCreate):
    query = """
    MATCH (a:Person {name: $from_name}), (b:Person {name: $to_name})
    MERGE (a)-[r:INTERESTED_IN]->(b)
    RETURN a, b
    """
    with driver.session() as session:
        session.run(query, from_name=interest.from_person, to_name=interest.to_person)

    # Ahora chequeamos si hay interés mutuo para marcar un "match"
    match_check_query = """
    MATCH (a:Person {name: $from_name})-[:INTERESTED_IN]->(b:Person {name: $to_name}),
          (b)-[:INTERESTED_IN]->(a)
    RETURN a, b
    """
    with driver.session() as session:
        result = session.run(match_check_query, from_name=interest.from_person, to_name=interest.to_person)
        if result.single():
            return {"message": f"¡Es un match entre {interest.from_person} y {interest.to_person}!"}

    return {"message": f"{interest.from_person} ha mostrado interés en {interest.to_person}."}


# --- Endpoint para mostrar matches ---
@app.get("/matches/{name}")
async def get_matches(name: str):
    query = """
    MATCH (a:Person {name: $name})-[:INTERESTED_IN]->(b:Person),
          (b)-[:INTERESTED_IN]->(a)
    RETURN b.name AS name, b.age AS age, b.gender AS gender, b.interests AS interests
    """
    with driver.session() as session:
        result = session.run(query, name=name)
        return [record.data() for record in result]
    

# --- Endpoint para mostrar el camino más corto hacia la persona que te interesa. ---
@app.get("/path-to/{from_name}/{to_name}")
def get_path_to_person(from_name: str, to_name: str):  
    try:
        path = path_to_person(from_name, to_name) 
        return path
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
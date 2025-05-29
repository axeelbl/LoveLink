from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

# Cargar variables del archivo .env
load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# Crear el driver de conexión
driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
)

# Función de utilidad para ejecutar consultas
def run_query(query, parameters=None):
    with driver.session() as session:
        result = session.run(query, parameters or {})
        return [record.data() for record in result]


# Función de utilidad para buscar recomendaciones
def get_recommendations_for(name: str):
    query = """
    MATCH (me:Person {name: $name})
    MATCH (me)-[:FRIEND|DATED|INTERACTED_WITH*1..2]-(candidate:Person)
    WHERE me <> candidate
      AND NOT (me)-[:FRIEND|DATED|INTERACTED_WITH]-(candidate)
    RETURN DISTINCT candidate.name AS name,
                    candidate.age AS age,
                    candidate.gender AS gender,
                    candidate.interests AS interests
    LIMIT 10
    """
    with driver.session() as session:
        result = session.run(query, name=name)
        return [record.data() for record in result]
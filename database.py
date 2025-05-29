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

    // Buscar candidatos cercanos (máximo 2 saltos de relaciones sociales)
    MATCH path = (me)-[:FRIEND|DATED|INTERACTED_WITH*1..2]-(candidate:Person)

    WHERE me <> candidate
      AND NOT (me)-[:FRIEND|DATED|INTERACTED_WITH]-(candidate) // No recomendados si ya hay relación

    // Obtener intereses en común
    WITH me, candidate,
         [i IN me.interests WHERE i IN candidate.interests] AS common_interests,
         length(path) AS degree

    RETURN DISTINCT
           candidate.name AS name,
           candidate.age AS age,
           candidate.gender AS gender,
           candidate.interests AS interests,
           size(common_interests) AS common_count,
           degree,
           'Coincidís en ' + toString(size(common_interests)) + ' intereses' AS reason

    ORDER BY common_count DESC, degree ASC
    LIMIT 10
    """
    with driver.session() as session:
        result = session.run(query, name=name)
        return [record.data() for record in result]


# Función que te da el camino más corto hacía la persona que te interesa.
def path_to_person(from_name: str, to_name: str):
    query = """
    MATCH path = shortestPath(
        (from:Person {name: $from_name})-[:FRIEND|DATED|INTERACTED_WITH*..5]-(to:Person {name: $to_name})
    )
    RETURN [n IN nodes(path) | n.name] AS path_names,
           [rel IN relationships(path) | type(rel)] AS relationship_types
    """
    with driver.session() as session:
        result = session.run(query, from_name=from_name, to_name=to_name)
        record = result.single()
        if not record:
            return {"path": [], "types": []}
        return {
            "path": record["path_names"],
            "types": record["relationship_types"]
        }
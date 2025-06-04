from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
)

def delete_specific_lowercase_emails():
    emails_to_delete = [
        "laura2@gmail.com",
    ]
    query = """
    MATCH (p:Person)
    WHERE p.email IN $emails
    DETACH DELETE p
    """
    with driver.session() as session:
        session.run(query, emails=emails_to_delete)
    print("Usuarios duplicados con emails en minúscula borrados.")

if __name__ == "__main__":
    delete_specific_lowercase_emails()

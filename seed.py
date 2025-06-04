from neo4j import GraphDatabase
from dotenv import load_dotenv
import os
import random
from passlib.context import CryptContext

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

names = [
    ("Lucía", "Mujer"), ("David", "Hombre"), ("Elena", "Mujer"), ("Pablo", "Hombre"),
    ("Sofía", "Mujer"), ("Daniel", "Hombre"), ("Noa", "Mujer"), ("Hugo", "Hombre")
]
interests_pool = ["Música", "Deporte", "Cine", "Lectura", "Moda", "Tecnología", "Viajes", "Animales", "Arte", "Idiomas", "Videojuegos", "Cocina", "Naturaleza", "Fitness", "Fotografía"]

def create_seed_users():
    with driver.session() as session:
        for i, (name, gender) in enumerate(names):
            email = f"{name.lower()}@gmail.com"
            password = pwd_context.hash("1234")
            age = random.randint(20, 30)
            interests = random.sample(interests_pool, k=random.randint(3, 5))
            profile_picture = f"/static/uploads/{name.lower()}.jpg"
            
            # Evita duplicados con MERGE
            session.run("""
                MERGE (p:Person {email: $email})
                SET p.name = $name,
                    p.password = $password,
                    p.gender = $gender,
                    p.age = $age,
                    p.interests = $interests,
                    p.profile_picture = $profile_picture
            """, {
                "email": email,
                "name": name,
                "password": password,
                "gender": gender,
                "age": age,
                "interests": interests,
                "profile_picture": profile_picture
            })

def create_random_relationships():
    rel_types = ["FRIEND", "DATED", "INTERACTED_WITH", "INTERESTED_IN"]
    with driver.session() as session:
        for _ in range(15):
            p1, p2 = random.sample(names, 2)
            if p1 == p2:
                continue
            name1 = p1[0]
            name2 = p2[0]
            rel = random.choice(rel_types)

            # Evita duplicados
            session.run(f"""
                MATCH (a:Person {{name: $name1}}), (b:Person {{name: $name2}})
                MERGE (a)-[r:{rel}]->(b)
            """, {"name1": name1, "name2": name2})

if __name__ == "__main__":
    create_seed_users()
    create_random_relationships()
    print("✅ Seed completada: usuarios y relaciones creadas.")

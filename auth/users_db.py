# auth/users_db.py
from passlib.context import CryptContext
from neo4j import Driver

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_user(driver: Driver, email: str, password: str, name: str, age: int, gender: str, interests: list, profile_picture: str = ""):
    hashed_password = pwd_context.hash(password)

    with driver.session() as session:
        # Verificar si ya existe
        check = session.run("MATCH (p:Person {email: $email}) RETURN p", email=email).single()
        if check:
            raise ValueError("El usuario ya existe")

        # Crear el nodo persona 
        session.run("""
            CREATE (p:Person {
                email: $email,
                password: $password,
                name: $name,
                age: $age,
                gender: $gender,
                interests: $interests,
                profile_picture: $profile_picture
            })
        """, {
            "email": email,
            "password": hashed_password,
            "name": name,
            "age": age,
            "gender": gender,
            "interests": interests,
            "profile_picture": profile_picture  
        })

# 🔐 Obtener usuario por email
def get_user_by_email(driver: Driver, email: str):
    with driver.session() as session:
        result = session.run("MATCH (p:Person {email: $email}) RETURN p", email=email)
        record = result.single()
        if record:
            return record["p"]
        return None

# 🔐 Verificar contraseña (plain vs hashed)
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# 🔐 Obtener usuario por nombre
def get_user_by_name(driver: Driver, name: str):
    with driver.session() as session:
        result = session.run("MATCH (p:Person {name: $name}) RETURN p", name=name)
        record = result.single()
        if record:
            return record["p"]
        return None
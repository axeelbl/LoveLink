from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from neo4j import GraphDatabase
from pydantic import BaseModel, EmailStr
import os
from dotenv import load_dotenv
from models import RelationshipCreate, InterestCreate,UserCreate
from database import get_recommendations_for, path_to_person
from auth.users_db import create_user
from auth.login import login_user
from fastapi.security import OAuth2PasswordRequestForm
from auth.jwt_handler import decode_access_token
from starlette.middleware.base import BaseHTTPMiddleware


load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

app = FastAPI()

#FRONTEND

# Middleware para proteger el acceso a /
class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/":
            token = request.cookies.get("access_token")
            if not token:
                return RedirectResponse("/login-page")
            try:
                decode_access_token(token)
            except Exception:
                return RedirectResponse("/login-page")
        return await call_next(request)

app.add_middleware(AuthMiddleware)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login-page", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register-page", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})



#FUNCIONES API-BACKEND

# --- Endpoint para obtener todas las personas en la base de datos. ---
@app.get("/persons/")
async def list_persons():
    query = "MATCH (p:Person) RETURN p"
    with driver.session() as session:
        result = session.run(query)
        people = [record["p"] for record in result]
    return people


# --- Endpoint para para ver las relaciones de una persona específica. ---
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


# --- Endpoint para obtener recomendaciones ---
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


# --- Endpoint para mostrar el camino más corto hacia otra persona ---
@app.get("/path-to/{from_name}/{to_name}")
def get_path_to_person(from_name: str, to_name: str):
    try:
        path = path_to_person(from_name, to_name)
        return path
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Endpoint para registrarnos ---
@app.post("/register")
def register(user: UserCreate):
    try:
        create_user(driver, user.email, user.password, user.name, user.age, user.gender, user.interests)
        return {"message": "Usuario creado correctamente"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")
    
# --- Endpoint para iniciar sesión ---
@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    return login_user(form_data, driver)

# --- Endpoint para obtener la información del usuario que ha iniciado sesión ---
@app.get("/me")
def get_current_user(token_data: dict = Depends(decode_access_token)):
    return {"email": token_data["sub"], "name": token_data.get("name")}

# --- Endpoint para cerrar sesión ---
@app.get("/logout")
def logout():
    response = RedirectResponse(url="/login-page", status_code=303)
    response.delete_cookie("access_token")
    return response
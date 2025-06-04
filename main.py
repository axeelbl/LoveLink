#main.py

import json
import shutil
from typing import List, Optional
import uuid
from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, Response, UploadFile,status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from neo4j import Driver, GraphDatabase
from pydantic import BaseModel, EmailStr
import os
from dotenv import load_dotenv
from models import RelationshipCreate, InterestCreate,UserCreate
from database import get_recommendations_for, path_to_person
from auth.users_db import create_user,get_user_by_name
from auth.login import login_user
from fastapi.security import OAuth2PasswordRequestForm,OAuth2PasswordBearer
from auth.jwt_handler import decode_access_token
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from auth.jwt_handler import create_access_token, decode_access_token
from fastapi import Request


load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


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
app.mount("/static", StaticFiles(directory="static"), name="static")

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
        create_user(driver, user.email, user.password, user.name, user.age, user.gender, user.interests, user.profile_picture or "")
        return {"message": "Usuario creado correctamente"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")
    
# --- Endpoint para iniciar sesión ---
@app.post("/login")
def login(response: Response, form_data: OAuth2PasswordRequestForm = Depends()):
    user_data = login_user(form_data, driver)

    token = user_data["access_token"]

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="Lax",
        secure=False  # Cambia a True si usas HTTPS
    )

    return {"message": "login_success"}


# --- Endpoint para obtener la información del usuario que ha iniciado sesión ---
def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se encontró token en las cookies"
        )
    return decode_access_token(token)
@app.get("/me")
def get_current_user_info(user_data: dict = Depends(get_current_user)):
    return {"email": user_data["sub"], "name": user_data.get("name")}



# --- Endpoint para cerrar sesión ---
@app.get("/logout")
def logout():
    response = RedirectResponse(url="/login-page", status_code=303)
    response.delete_cookie("access_token")
    return response



# --- Endpoint para coger las recomendaciones del usuario logeado ---
@app.get("/user-logged-recommendations")
def get_my_recommendations(user_node: dict = Depends(get_current_user)):
    name = user_node.get("name", "").strip()
    recommendations = get_recommendations_for(name)

    enriched_recommendations = []
    for person in recommendations:
        full_user = get_user_by_name(driver, person["name"])
        profile_picture = full_user.get("profile_picture", "") if full_user else ""
        
        person["profile_picture"] = profile_picture if profile_picture else "/static/default.jpg"
        enriched_recommendations.append(person)

    return {"recommendations": enriched_recommendations}

# --- Endpoint nuevo con from_name desde usuario logeado y to_name como parámetro ---
@app.get("/path-to-user/{to_name}")
def get_path_from_logged_user(to_name: str, user_data: dict = Depends(get_current_user)):
    from_name = user_data.get("name")
    if not from_name:
        raise HTTPException(status_code=400, detail="Usuario sin nombre válido en token")
    try:
        path = path_to_person(from_name, to_name)
        return path
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# --- Endpoint para saber quien soy (Cogiendo todos los datos reales de la database) ---
def get_user_by_email(driver: Driver, email: str):
    with driver.session() as session:
        result = session.run("MATCH (p:Person {email: $email}) RETURN p", email=email)
        record = result.single()
        if record:
            return record["p"]
        return None
@app.get("/whoami")
def whoami(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="No token provided")

    try:
        payload = decode_access_token(token)
        email = payload.get("sub")
        user_node = get_user_by_email(driver, email)
        if not user_node:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "name": user_node.get("name"),
            "email": email,
            "age": user_node.get("age"),
            "gender": user_node.get("gender"),
            "interests": user_node.get("interests", []),
            "profile_picture": user_node.get("profile_picture", "")
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token or internal error")


# --- Endpoint para ir al profile ---
@app.get("/profile", response_class=HTMLResponse)
def profile(request: Request):
    return templates.TemplateResponse("profile.html", {"request": request})


# --- Endpoint para editar los datos del user ---
class UserUpdate(BaseModel):
    name: str
    age: int
    gender: str
    interests: List[str]
    profile_picture: Optional[str] = None

@app.put("/update-profile")
async def update_profile(
    request: Request,
    name: str = Form(...),
    age: int = Form(...),
    gender: str = Form(...),
    interests: str = Form(...),  # Viene como stringified JSON
    profile_picture: Optional[UploadFile] = File(None),
    user_data: dict = Depends(get_current_user)
):
    email = user_data.get("sub")
    if not email:
        raise HTTPException(status_code=401, detail="Token inválido")

    interests_list = json.loads(interests)

    # Guardar la imagen si existe
    picture_url = ""
    if profile_picture:
        ext = os.path.splitext(profile_picture.filename)[1]
        filename = f"{uuid.uuid4().hex}{ext}"
        filepath = os.path.join("static/uploads", filename)

        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(profile_picture.file, buffer)

        picture_url = f"/static/uploads/{filename}"

    with driver.session() as session:
        result = session.run("""
            MATCH (p:Person {email: $email})
            SET p.name = $name,
                p.age = $age,
                p.gender = $gender,
                p.interests = $interests,
                p.profile_picture = CASE WHEN $picture <> '' THEN $picture ELSE p.profile_picture END
            RETURN p
        """, {
            "email": email,
            "name": name,
            "age": age,
            "gender": gender,
            "interests": interests_list,
            "picture": picture_url
        })
        updated = result.single()
        if not updated:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Crear nuevo token
    new_token = create_access_token({"sub": email, "name": name})

    response = JSONResponse({"message": "Perfil actualizado correctamente"})
    response.set_cookie(key="access_token", value=new_token, httponly=True, samesite="lax", secure=False)
    return response


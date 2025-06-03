# auth/login.py Este archivo maneja el proceso de login.

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from auth.users_db import get_user_by_email, verify_password
from auth.jwt_handler import create_access_token
from neo4j import Driver
from fastapi.responses import JSONResponse

def login_user(form_data: OAuth2PasswordRequestForm, driver: Driver):
    user = get_user_by_email(driver, form_data.username)
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas"
        )

    token = create_access_token({"sub": user["email"], "name": user["name"]})

    # Guardar el token como cookie segura
    response = JSONResponse(content={"message": "Login correcto"})
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,  # Evita acceso vía JS
        secure=False,   
        samesite="lax"
    )
    return response



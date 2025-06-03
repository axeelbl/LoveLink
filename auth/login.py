# auth/login.py Este archivo maneja el proceso de login.

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from auth.users_db import get_user_by_email, verify_password
from auth.jwt_handler import create_access_token
from neo4j import Driver

def login_user(form_data: OAuth2PasswordRequestForm, driver: Driver):
    user = get_user_by_email(driver, form_data.username)
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas"
        )
    token = create_access_token({"sub": user["email"], "name": user["name"]})
    return {"access_token": token, "token_type": "bearer"}



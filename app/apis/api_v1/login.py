# -*- coding: utf-8 -*-
# FileName: login.py
# Time : 2024/6/17 11:45
# Author: zzy
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from app.core import config
from app.crud.user import user_crud
from app.schemas.user import Token
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils import security

router = APIRouter()


@router.post("/login/access-token")
async def login_access_token(
        async_session: AsyncSession,
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
    user = user_crud.authenticate(async_session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="错误的用户名或密码")
    access_token_expires = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    return Token(
        access_token=security
    )
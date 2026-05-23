from pydantic import BaseModel
from datetime import datetime


class UserRegister(BaseModel):
    email: str
    username: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: str
    email: str
    username: str
    role_id: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class RoleCreate(BaseModel):
    name: str
    permission: str


class RoleOut(BaseModel):
    id: str
    name: str
    permission: str

    class Config:
        from_attributes = True


class AssignRole(BaseModel):
    user_id: str
    role_id: str


class DocumentOut(BaseModel):
    id: str
    title: str
    company_name: str
    document_type: str
    uploaded_by: str
    created_at: datetime

    class Config:
        from_attributes = True


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5

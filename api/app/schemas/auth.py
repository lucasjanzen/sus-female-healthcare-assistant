from datetime import datetime

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: str
    nome: str
    email: str
    role: str
    ativo: bool
    criado_em: datetime

    model_config = {"from_attributes": True}

import uuid

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.enums import Role


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: Role = Role.employee
    team_id: uuid.UUID | None = None


class UserUpdate(BaseModel):
    name: str | None = None
    role: Role | None = None
    team_id: uuid.UUID | None = None
    is_active: bool | None = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: EmailStr
    role: Role
    team_id: uuid.UUID | None
    is_active: bool

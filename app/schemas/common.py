import datetime as dt
import uuid

from pydantic import BaseModel, ConfigDict

from app.models.enums import ApprovalAction


class AccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    default_deductible: bool


class ApprovalLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    action: ApprovalAction
    actor_name: str
    comment: str | None
    created_at: dt.datetime


class ApprovalIn(BaseModel):
    comment: str | None = None


class ApprovalRejectIn(BaseModel):
    comment: str  # 반려는 사유 필수


class ClosingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    period: str
    closed_at: dt.datetime
    export_key: str | None

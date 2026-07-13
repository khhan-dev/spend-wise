from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import Account, User
from app.schemas.common import AccountOut

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("", response_model=list[AccountOut])
def list_accounts(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """계정과목 목록 (경비 입력 시 선택용)."""
    return list(db.scalars(select(Account).order_by(Account.name)))

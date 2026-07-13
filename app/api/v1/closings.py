import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.database import get_db
from app.models import ClosingBatch, ExpenseReport, Role, User
from app.models.enums import ReportStatus
from app.schemas.common import ClosingOut
from app.services.excel_export import generate_closing_excel

router = APIRouter(prefix="/closings", tags=["closings"])


class CloseRequest(BaseModel):
    period: str = Field(pattern=r"^\d{4}-\d{2}$")  # YYYY-MM


@router.post("", response_model=ClosingOut, status_code=status.HTTP_201_CREATED)
def close_period(
    body: CloseRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(Role.admin)),
):
    """월 마감: 검토완료 신청서를 잠그고 세무 신고용 엑셀을 생성한다."""
    if db.scalar(select(ClosingBatch).where(ClosingBatch.period == body.period)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="이미 마감된 귀속월입니다.")

    reports = list(
        db.scalars(
            select(ExpenseReport).where(
                ExpenseReport.period == body.period,
                ExpenseReport.status == ReportStatus.reviewed,
            )
        )
    )
    if not reports:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="마감할 검토완료 경비가 없습니다.")

    batch = ClosingBatch(period=body.period)
    db.add(batch)
    db.flush()

    for report in reports:
        report.status = ReportStatus.closed
        for item in report.items:
            item.closing_batch_id = batch.id

    path = generate_closing_excel(db, body.period)
    batch.export_key = path
    db.commit()
    db.refresh(batch)
    return batch


@router.get("", response_model=list[ClosingOut])
def list_closings(db: Session = Depends(get_db), _: User = Depends(require_roles(Role.admin))):
    return list(db.scalars(select(ClosingBatch).order_by(ClosingBatch.period.desc())))


@router.get("/{closing_id}/download")
def download_excel(
    closing_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(Role.admin)),
):
    """마감 산출 엑셀 다운로드."""
    batch = db.get(ClosingBatch, closing_id)
    if batch is None or not batch.export_key or not os.path.exists(batch.export_key):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="엑셀 산출물을 찾을 수 없습니다.")
    return FileResponse(
        batch.export_key,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=os.path.basename(batch.export_key),
    )

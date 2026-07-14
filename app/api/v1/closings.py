import io
import os
import uuid
import zipfile

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.database import get_db
from app.models import ApprovalLog, ClosingBatch, ExpenseItem, ExpenseReport, Role, User
from app.models.enums import ApprovalAction, ReportStatus
from app.schemas.common import ClosingOut
from app.services.excel_export import generate_closing_excel
from app.services.storage import get_storage

router = APIRouter(prefix="/closings", tags=["closings"])


class CloseRequest(BaseModel):
    period: str = Field(pattern=r"^\d{4}-\d{2}$")  # YYYY-MM


@router.post("", response_model=ClosingOut, status_code=status.HTTP_201_CREATED)
def close_period(
    body: CloseRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.admin)),
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
        db.add(ApprovalLog(report_id=report.id, actor_id=user.id, action=ApprovalAction.close))

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


@router.get("/{closing_id}/receipts-zip")
def download_receipts_zip(
    closing_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(Role.admin)),
):
    """마감된 경비의 증빙 이미지를 ZIP으로 묶어 반환한다(세무대리인 전달용)."""
    batch = db.get(ClosingBatch, closing_id)
    if batch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="마감 정보를 찾을 수 없습니다.")

    items = list(db.scalars(select(ExpenseItem).where(ExpenseItem.closing_batch_id == batch.id)))
    storage = get_storage()

    buf = io.BytesIO()
    count = 0
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for it in items:
            key = it.receipt.image_key if it.receipt else None
            if not key or not storage.exists(key):
                continue
            count += 1
            ext = key.rsplit(".", 1)[-1] if "." in key else "bin"
            vendor = it.vendor.name if it.vendor else "거래처"
            dept = it.dept_snapshot or "미분류"
            arcname = f"{dept}_{vendor}_{it.tx_date}_{count:03d}.{ext}"
            zf.writestr(arcname, storage.load(key))

    if count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="첨부된 증빙 이미지가 없습니다.")

    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="receipts_{batch.period}.zip"'},
    )

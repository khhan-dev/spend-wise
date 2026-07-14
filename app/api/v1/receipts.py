import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import ExpenseItem, User
from app.services.ocr import get_ocr_provider
from app.services.permissions import can_view_report
from app.services.storage import ext_for, get_storage

router = APIRouter(prefix="/receipts", tags=["receipts"])


class OcrDraft(BaseModel):
    image_key: str  # 저장된 증빙 이미지 키 (경비 항목 생성 시 그대로 전달)
    success: bool
    confidence: float
    fields: dict
    manual_input_required: bool


@router.post("/ocr", response_model=OcrDraft)
async def ocr_extract(
    file: UploadFile = File(...),
    _: User = Depends(get_current_user),
):
    """영수증 이미지를 저장하고 항목 초안을 추출한다.

    이미지는 OCR 성공 여부와 무관하게 저장되어 image_key로 반환된다.
    (실패 시에도 증빙 원본은 항목에 첨부할 수 있어야 하므로)
    """
    content = await file.read()
    ext = ext_for(file.content_type, file.filename)
    image_key = get_storage().save(content, ext)

    result = get_ocr_provider().extract(content, file.content_type or "image/jpeg")
    return OcrDraft(
        image_key=image_key,
        success=result.success,
        confidence=result.confidence,
        fields=result.fields,
        manual_input_required=not result.success or result.confidence < 0.6,
    )


@router.get("/{item_id}/image")
def get_receipt_image(
    item_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """항목에 첨부된 증빙 이미지를 반환한다(열람 권한 확인)."""
    item = db.get(ExpenseItem, item_id)
    if item is None or item.receipt is None or not item.receipt.image_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="증빙 이미지가 없습니다.")
    if not can_view_report(user, item.report):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="열람 권한이 없습니다.")
    key = item.receipt.image_key
    if not get_storage().exists(key):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="이미지 파일을 찾을 수 없습니다.")
    return FileResponse(get_storage().path(key))

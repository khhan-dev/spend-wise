from fastapi import APIRouter, Depends, File, UploadFile
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.models import User
from app.services.ocr import get_ocr_provider

router = APIRouter(prefix="/receipts", tags=["receipts"])


class OcrDraft(BaseModel):
    success: bool
    confidence: float
    fields: dict
    manual_input_required: bool


@router.post("/ocr", response_model=OcrDraft)
async def ocr_extract(
    file: UploadFile = File(...),
    _: User = Depends(get_current_user),
):
    """영수증 이미지에서 항목 초안을 추출한다.

    현재는 OCR 미연동(스텁)이라 항상 수동 입력이 필요한 상태로 반환된다.
    실패/저신뢰 시 프론트는 수동 입력 폼으로 폴백한다.
    """
    content = await file.read()
    result = get_ocr_provider().extract(content, file.content_type or "image/jpeg")
    return OcrDraft(
        success=result.success,
        confidence=result.confidence,
        fields=result.fields,
        manual_input_required=not result.success or result.confidence < 0.6,
    )

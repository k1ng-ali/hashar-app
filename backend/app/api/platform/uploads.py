from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.core.rate_limit import SlidingWindowLimiter
from app.core.receipts import MAX_UPLOAD_BYTES, upload_receipt
from app.deps.fund import get_fund_context
from app.schemas.member import FundContext

router = APIRouter(prefix="/funds/{fund_id}/uploads", tags=["Platform • Uploads"])

# Загрузка — это запись в хранилище; без лимита один участник забьёт бакет мусором
UPLOADS_BY_USER = SlidingWindowLimiter(limit=30, window_seconds=60 * 60)


class UploadOut(BaseModel):
    # Ключ передаётся в receipt_image взноса, receipt_images расхода или image сбора этого же фонда
    key: str


@router.post("/receipt", response_model=UploadOut, status_code=status.HTTP_201_CREATED)
async def upload_receipt_file(file: UploadFile, ctx: FundContext = Depends(get_fund_context)):
    if UPLOADS_BY_USER.is_blocked(str(ctx.user_id)):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many uploads, try later")
    data = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=status.HTTP_413_CONTENT_TOO_LARGE, detail="Receipt image is too large")
    UPLOADS_BY_USER.hit(str(ctx.user_id))
    return UploadOut(key=await upload_receipt(ctx.fund_id, ctx.user_id, data))

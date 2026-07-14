from fastapi import APIRouter

from app.api.v1 import accounts, approvals, auth, closings, expenses, org, receipts, users

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(org.router)
api_router.include_router(accounts.router)
api_router.include_router(expenses.router)
api_router.include_router(approvals.router)
api_router.include_router(closings.router)
api_router.include_router(receipts.router)

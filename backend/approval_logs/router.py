from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from models import ApprovalLog
from auth.dependencies import get_current_user
from approval_logs.schemas import ApprovalLogItem

router = APIRouter(prefix="/approval-logs", tags=["Approval Logs"])


@router.get("", response_model=List[ApprovalLogItem])
def list_approval_logs(
    action_type: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    limit: int = Query(100, le=200),
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    query = db.query(ApprovalLog).order_by(ApprovalLog.created_at.desc())
    if action_type:
        query = query.filter(ApprovalLog.action_type == action_type)
    if entity_type:
        query = query.filter(ApprovalLog.entity_type == entity_type)
    return query.limit(limit).all()

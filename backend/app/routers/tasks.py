from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.schemas.task import TaskResponse, TaskCancel
from app.models.task import Task
from app.auth import get_current_user
from datetime import datetime

router = APIRouter(prefix="/v1/tasks", tags=["tasks"])


@router.get("", response_model=List[TaskResponse])
async def list_tasks(
    agent_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    type_filter: Optional[str] = Query(None, alias="type"),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """List tasks with optional filters"""
    query = db.query(Task)
    
    if agent_id:
        query = query.filter(Task.agent_id == agent_id)
    
    if status_filter:
        query = query.filter(Task.status == status_filter)
    
    if type_filter:
        query = query.filter(Task.type == type_filter)
    
    tasks = query.order_by(Task.created_at.desc()).all()
    return tasks


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Get task details"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "task_not_found",
                "message": "Task not found",
                "details": {"task_id": task_id}
            }
        )
    
    return task


@router.post("/{task_id}/cancel", response_model=TaskCancel)
async def cancel_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Cancel a task"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "task_not_found",
                "message": "Task not found",
                "details": {"task_id": task_id}
            }
        )
    
    # Check if task can be canceled
    if task.status in ["succeeded", "failed", "canceled", "timed_out"]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "task_already_terminal",
                "message": "Task is already in terminal state",
                "details": {"current_status": task.status}
            }
        )
    
    # Cancel the task
    task.status = "canceled"
    task.finished_at = datetime.utcnow()
    db.commit()
    
    return TaskCancel(canceled=True, task=task)


@router.get("/ports/reservations", response_model=List[dict])
async def list_port_reservations(
    agent_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """List active port reservations"""
    from app.models.port_reservation import PortReservation
    
    query = db.query(PortReservation).filter(PortReservation.released_at.is_(None))
    
    if agent_id:
        query = query.filter(PortReservation.agent_id == agent_id)
    
    reservations = query.all()
    
    return [
        {
            "id": r.id,
            "agent_id": r.agent_id,
            "port": r.port,
            "task_id": r.task_id,
            "created_at": r.created_at
        }
        for r in reservations
    ]

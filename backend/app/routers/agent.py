from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.schemas.agent import AgentResponse, AgentRegisterRequest, AgentHeartbeatRequest
from app.schemas.task import TaskResponse, TaskStartedRequest, TaskResultRequest
from app.models.agent import Agent
from app.models.task import Task
from app.middleware.agent_auth import get_agent_from_headers
from app.services.idempotency import IdempotencyService
from app.auth import create_access_token
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import json

router = APIRouter(prefix="/v1/agent", tags=["agent"])


@router.post("/register", response_model=AgentResponse)
async def register_agent(
    request: Request,
    body: AgentRegisterRequest,
    db: Session = Depends(get_db)
):
    """Register or re-register agent"""
    agent_name = request.headers.get("X-AGENT-NAME")
    agent_key = request.headers.get("X-AGENT-KEY")
    
    if not agent_name or not agent_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "missing_agent_headers",
                "message": "X-AGENT-NAME and X-AGENT-KEY headers are required"
            }
        )
    
    # Check if agent exists
    agent = db.query(Agent).filter(Agent.name == agent_name).first()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "agent_not_found",
                "message": "Agent not found - agent must exit"
            }
        )
    
    # Verify registration key
    if agent.registration_key != agent_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "invalid_agent_key",
                "message": "Invalid agent registration key"
            }
        )
    
    # Update agent status and info
    agent.status = "online"
    agent.last_heartbeat = datetime.utcnow()
    agent.ip_address = body.ip_address
    if body.operating_system:
        agent.operating_system = body.operating_system

    db.commit()
    db.refresh(agent)

    return agent


@router.post("/heartbeat")
async def heartbeat(
    request: Request,
    body: AgentHeartbeatRequest,
    db: Session = Depends(get_db)
):
    """Agent heartbeat with running processes"""
    agent = get_agent_from_headers(request, db)

    # Update heartbeat
    agent.last_heartbeat = datetime.utcnow()
    agent.ip_address = body.ip_address
    agent.status = "online"

    db.commit()
    
    # Return hint about whether to pull tasks
    # For now, always return true - could be smarter later
    return {"pull_tasks": True}


@router.post("/tasks/claim")
async def claim_task(
    request: Request,
    db: Session = Depends(get_db)
):
    """Atomically claim one pending task for this agent"""
    agent = get_agent_from_headers(request, db)
    
    # Use BEGIN IMMEDIATE transaction for atomic claim
    try:
        # Start transaction
        db.execute(text("BEGIN IMMEDIATE"))
        
        # Find oldest pending task for this agent
        task = db.query(Task).filter(
            Task.agent_id == agent.id,
            Task.status == "pending"
        ).order_by(Task.created_at.asc()).first()
        
        if task:
            # Claim the task
            task.status = "accepted"
            task.accepted_at = datetime.utcnow()
            db.commit()
            db.refresh(task)

            return {"task": TaskResponse.model_validate(task)}
        else:
            db.commit()
            return {"task": None}
            
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "claim_failed",
                "message": "Failed to claim task",
                "details": {"error": str(e)}
            }
        )


@router.post("/tasks/{task_id}/started", response_model=TaskResponse)
async def mark_task_started(
    task_id: int,
    request: Request,
    body: TaskStartedRequest,
    db: Session = Depends(get_db)
):
    """Mark task as started"""
    agent = get_agent_from_headers(request, db)

    task = db.query(Task).filter(
        Task.id == task_id,
        Task.agent_id == agent.id
    ).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "task_not_found",
                "message": "Task not found or not assigned to this agent"
            }
        )

    if task.status != "accepted":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "invalid_task_state",
                "message": "Task must be in accepted state",
                "details": {"current_status": task.status}
            }
        )

    # Update task
    task.status = "running"
    task.started_at = datetime.utcnow()

    # Store PID in payload if provided
    if body.pid is not None:
        payload = task.payload or {}
        payload["pid"] = body.pid
        task.payload = payload
    
    db.commit()
    db.refresh(task)
    
    return task


@router.post("/tasks/{task_id}/result", response_model=TaskResponse)
async def submit_task_result(
    task_id: int,
    request: Request,
    body: TaskResultRequest,
    db: Session = Depends(get_db)
):
    """Submit task result"""
    agent = get_agent_from_headers(request, db)

    task = db.query(Task).filter(
        Task.id == task_id,
        Task.agent_id == agent.id
    ).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "task_not_found",
                "message": "Task not found or not assigned to this agent"
            }
        )

    # Allow result submission for running, accepted, or timed_out tasks
    # (timed_out can occur if task completed just after timeout_sweeper ran)
    if task.status not in ["running", "accepted", "timed_out"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "invalid_task_state",
                "message": "Task must be in running, accepted, or timed_out state",
                "details": {"current_status": task.status}
            }
        )

    # Update task - if it was timed_out but agent has results, accept them
    task.status = body.status
    task.finished_at = datetime.utcnow()
    task.result = body.result
    task.error = body.stderr if body.status == "failed" else None
    
    # For server tasks, release port reservation when completed
    if task.type == "iperf_server_start" and body.status in ["succeeded", "failed"]:
        from app.models.port_reservation import PortReservation
        reservation = db.query(PortReservation).filter(
            PortReservation.task_id == task_id
        ).first()
        if reservation:
            reservation.released_at = datetime.utcnow()
    
    db.commit()
    db.refresh(task)
    
    return task

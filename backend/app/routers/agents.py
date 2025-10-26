from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.schemas.agent import AgentCreate, AgentResponse
from app.models.agent import Agent
from app.auth import get_current_user
from datetime import datetime

router = APIRouter(prefix="/v1/agents", tags=["agents"])


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent_data: AgentCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Create a new agent record"""
    # Check if agent with same name exists
    existing_agent = db.query(Agent).filter(Agent.name == agent_data.name).first()
    if existing_agent:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "duplicate_agent_name",
                "message": "Agent with this name already exists",
                "details": {"name": agent_data.name}
            }
        )
    
    agent = Agent(
        name=agent_data.name,
        registration_key=agent_data.registration_key,
        operating_system=agent_data.operating_system,
        status="offline",
        first_registered=datetime.utcnow()
    )
    
    db.add(agent)
    db.commit()
    db.refresh(agent)
    
    return agent


@router.get("", response_model=List[AgentResponse])
async def list_agents(
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """List all agents with optional status filter"""
    query = db.query(Agent)
    
    if status_filter:
        query = query.filter(Agent.status == status_filter)
    
    agents = query.all()
    
    # Compute online/offline status based on last_heartbeat
    for agent in agents:
        if agent.last_heartbeat:
            time_diff = (datetime.utcnow() - agent.last_heartbeat).total_seconds()
            agent.status = "online" if time_diff <= 15 else "offline"
        else:
            agent.status = "offline"
    
    return agents


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Get agent details including last 10 tasks"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "agent_not_found",
                "message": "Agent not found",
                "details": {"agent_id": agent_id}
            }
        )
    
    # Compute online/offline status
    if agent.last_heartbeat:
        time_diff = (datetime.utcnow() - agent.last_heartbeat).total_seconds()
        agent.status = "online" if time_diff <= 15 else "offline"
    else:
        agent.status = "offline"
    
    return agent


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Unregister agent (soft delete)"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "agent_not_found",
                "message": "Agent not found",
                "details": {"agent_id": agent_id}
            }
        )
    
    # Soft delete - just mark as offline
    agent.status = "offline"
    db.commit()

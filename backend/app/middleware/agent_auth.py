from fastapi import Request, HTTPException, status
from sqlalchemy.orm import Session
from app.models.agent import Agent


def get_agent_from_headers(request: Request, db: Session) -> Agent:
    """Extract and validate agent from headers"""
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

    agent = db.query(Agent).filter(Agent.name == agent_name).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "agent_not_found",
                "message": "Agent not found - agent must exit"
            }
        )

    if agent.registration_key != agent_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "invalid_agent_key",
                "message": "Invalid agent registration key"
            }
        )

    return agent

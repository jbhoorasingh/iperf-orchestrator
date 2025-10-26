from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from app.database import Base


class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, nullable=False)  # iperf_server_start, iperf_client_run, kill_all, iperf_server_stop
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False)
    accepted_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    status = Column(String, nullable=False, default="pending", index=True)  # pending, accepted, running, succeeded, failed, canceled, timed_out
    payload = Column(JSON, nullable=False, default={})
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    
    # Relationships
    agent = relationship("Agent", back_populates="tasks")
    port_reservations = relationship("PortReservation", back_populates="task")

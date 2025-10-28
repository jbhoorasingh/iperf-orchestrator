from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.database import Base


class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    registration_key = Column(String, nullable=False)
    status = Column(String, nullable=False, default="offline")  # online, offline
    disabled = Column(Boolean, nullable=False, default=False)
    first_registered = Column(DateTime, nullable=False)
    last_heartbeat = Column(DateTime, nullable=True)
    ip_address = Column(String, nullable=True)
    operating_system = Column(String, nullable=True)
    
    # Relationships
    tasks = relationship("Task", back_populates="agent")
    port_reservations = relationship("PortReservation", back_populates="agent")
    server_tests = relationship("Test", foreign_keys="Test.server_agent_id", back_populates="server_agent")
    client_tests = relationship("Test", foreign_keys="Test.client_agent_id", back_populates="client_agent")

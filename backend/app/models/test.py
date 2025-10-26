from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base


class Test(Base):
    __tablename__ = "tests"
    
    id = Column(Integer, primary_key=True, index=True)
    exercise_id = Column(Integer, ForeignKey("exercises.id", ondelete="CASCADE"), nullable=False)
    server_agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    client_agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    server_port = Column(Integer, nullable=False)
    udp = Column(Boolean, nullable=False, default=False)
    parallel = Column(Integer, nullable=False, default=1)  # 1-32
    time_seconds = Column(Integer, nullable=True)  # defaults to exercise duration if NULL
    server_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    client_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    
    # Unique constraint to prevent port conflicts within same exercise
    __table_args__ = (
        UniqueConstraint('exercise_id', 'server_agent_id', 'server_port', name='uq_exercise_agent_port'),
    )
    
    # Relationships
    exercise = relationship("Exercise", back_populates="tests")
    server_agent = relationship("Agent", foreign_keys=[server_agent_id], back_populates="server_tests")
    client_agent = relationship("Agent", foreign_keys=[client_agent_id], back_populates="client_tests")
    server_task = relationship("Task", foreign_keys=[server_task_id])
    client_task = relationship("Task", foreign_keys=[client_task_id])

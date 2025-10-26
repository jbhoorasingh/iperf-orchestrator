from sqlalchemy import Column, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database import Base


class PortReservation(Base):
    __tablename__ = "port_reservations"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    port = Column(Integer, nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    created_at = Column(DateTime, nullable=False)
    released_at = Column(DateTime, nullable=True)

    # Note: Partial unique index created in database:
    # CREATE UNIQUE INDEX uq_agent_port_active ON port_reservations(agent_id, port)
    # WHERE released_at IS NULL
    # This allows port reuse after release while preventing conflicts on active reservations
    __table_args__ = (
        Index('uq_agent_port_active', 'agent_id', 'port',
              unique=True,
              postgresql_where=(released_at == None),
              sqlite_where='released_at IS NULL'),
    )

    # Relationships
    agent = relationship("Agent", back_populates="port_reservations")
    task = relationship("Task", back_populates="port_reservations")

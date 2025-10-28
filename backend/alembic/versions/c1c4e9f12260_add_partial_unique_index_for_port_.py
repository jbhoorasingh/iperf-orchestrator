"""Add partial unique index for port reservations

Revision ID: c1c4e9f12260
Revises: e924b7161259
Create Date: 2025-10-27 23:44:28.197097

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c1c4e9f12260'
down_revision = 'e924b7161259'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create partial unique index for active port reservations
    # This allows port reuse after release while preventing conflicts on active reservations
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_agent_port_active
        ON port_reservations(agent_id, port)
        WHERE released_at IS NULL
    """)


def downgrade() -> None:
    # Drop the partial unique index
    op.execute("DROP INDEX IF EXISTS uq_agent_port_active")

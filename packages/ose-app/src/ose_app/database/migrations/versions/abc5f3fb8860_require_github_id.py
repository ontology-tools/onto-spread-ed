"""Require a GitHub id for every user

Revision ID: abc5f3fb8860
Revises: d41f6e2a8c55
Create Date: 2026-11-03 12:00:00.000000

Users are identified by their GitHub id, which the login always stores. Rows without one cannot be attributed to a
GitHub account and are deleted; such users are created again on their next login.
"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'abc5f3fb8860'
down_revision = 'd41f6e2a8c55'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("delete from users where github_id is null")

    with op.batch_alter_table("users") as batch:
        batch.alter_column("github_id", existing_type=sa.Integer(), nullable=False)


def downgrade():
    with op.batch_alter_table("users") as batch:
        batch.alter_column("github_id", existing_type=sa.Integer(), nullable=True)

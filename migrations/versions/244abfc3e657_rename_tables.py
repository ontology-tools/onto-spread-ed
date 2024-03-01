"""Rename tables

Revision ID: 244abfc3e657
Revises: 5a12a34c96d8
Create Date: 2024-03-01 09:31:29.945872

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '244abfc3e657'
down_revision = '5a12a34c96d8'
branch_labels = None
depends_on = None


def upgrade():
    op.rename_table("release", "releases")


def downgrade():
    op.rename_table("releases", "release")

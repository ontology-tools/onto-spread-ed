"""Added release repo

Revision ID: 5a12a34c96d8
Revises: bbe766649a99
Create Date: 2024-02-29 14:28:14.569365

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '5a12a34c96d8'
down_revision = 'bbe766649a99'
branch_labels = None
depends_on = None


def downgrade():
    op.add_column('release',
                  sa.Column("included_files", sqlite.JSON(), nullable=True))
    op.drop_column("release", "repo")


def upgrade():
    op.add_column("release", sa.Column("repo", sa.String(20)))
    op.drop_column("release", "included_files")

    op.execute('update release set repo = json_extract(release_script, "$.short_repository_name")')

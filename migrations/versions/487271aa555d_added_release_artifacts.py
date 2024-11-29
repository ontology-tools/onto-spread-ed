"""Added release artifacts

Revision ID: 487271aa555d
Revises: 244abfc3e657
Create Date: 2024-11-29 09:56:59.263095

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '487271aa555d'
down_revision = '244abfc3e657'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("release_artifacts",
                    sa.Column("id", sa.Integer(), primary_key=True),
                    sa.Column("release_id", sa.Integer()),
                    sa.Column("local_path", sa.String()),
                    sa.Column("target_path", sa.String(), nullable=True),
                    sa.Column("downloadable", sa.Boolean(), default=True),
                    sa.Column("kind", sa.String())
                    sa.PrimaryKeyConstraint("id"),
                    sa.ForeignKeyConstraint(["release_id"], ["releases.id"]),
                    sa.CheckConstraint(
                        "kind in ('source', 'intermediate', 'final') and (kind <> 'final' or target_path is not null)"))


def downgrade():
    op.drop_table("release_artifacts")

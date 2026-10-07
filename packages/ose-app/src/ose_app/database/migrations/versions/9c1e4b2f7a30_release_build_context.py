"""Store the build context of releases

Revision ID: 9c1e4b2f7a30
Revises: 487271aa555d
Create Date: 2026-10-06 12:00:00.000000

The steps, details, artifacts, and release script of a release are now part of its serialised build context. Old
releases cannot be continued with the new build system, so open ones are cancelled.
"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '9c1e4b2f7a30'
down_revision = '487271aa555d'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("update releases set state = 'cancelled' where running or state = 'canceled'")
    op.execute("update releases set state = 'errored' where state = 'waiting-for-user'")

    op.drop_table("release_artifacts")

    with op.batch_alter_table("releases") as batch:
        batch.add_column(sa.Column("context", sa.JSON(none_as_null=True), nullable=True))
        batch.add_column(sa.Column("progress", sa.JSON(none_as_null=True), nullable=True))
        batch.drop_column("running")
        batch.drop_column("step")
        batch.drop_column("details")
        batch.drop_column("release_script")
        batch.drop_column("local_dir")


def downgrade():
    with op.batch_alter_table("releases") as batch:
        batch.add_column(sa.Column("running", sa.Boolean(), nullable=True, server_default=sa.false()))
        batch.add_column(sa.Column("step", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("details", sa.JSON(none_as_null=True), nullable=True))
        batch.add_column(sa.Column("release_script", sa.JSON(none_as_null=True), nullable=True))
        batch.add_column(sa.Column("local_dir", sa.String(), nullable=True))
        batch.drop_column("context")
        batch.drop_column("progress")

    op.create_table("release_artifacts",
                    sa.Column("id", sa.Integer(), primary_key=True),
                    sa.Column("release_id", sa.Integer()),
                    sa.Column("local_path", sa.String()),
                    sa.Column("target_path", sa.String(), nullable=True),
                    sa.Column("downloadable", sa.Boolean(), default=True),
                    sa.Column("kind", sa.String()),
                    sa.PrimaryKeyConstraint("id"),
                    sa.ForeignKeyConstraint(["release_id"], ["releases.id"]),
                    sa.CheckConstraint(
                        "kind in ('source', 'intermediate', 'final') and (kind <> 'final' or target_path is not null)"))

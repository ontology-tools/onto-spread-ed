"""Release runner: requests, heartbeat, and one open release per repository

Revision ID: d41f6e2a8c55
Revises: 9c1e4b2f7a30
Create Date: 2026-10-16 12:00:00.000000

Releases are run by a separate release runner process. The API records requests in `requested_action` and
`requested_by`, and the runner holding a release refreshes `heartbeat_at`. Worker ids are no longer `<pid>-<thread>`,
so they get longer. If a repository has several open releases, all but the newest are cancelled.
"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'd41f6e2a8c55'
down_revision = '9c1e4b2f7a30'
branch_labels = None
depends_on = None

OPEN_STATES = "'errored', 'paused', 'running', 'starting'"


def upgrade():
    with op.batch_alter_table("releases") as batch:
        batch.add_column(sa.Column("heartbeat_at", sa.DateTime(), nullable=True))
        batch.add_column(sa.Column("requested_action", sa.String(20), nullable=True))
        batch.add_column(sa.Column("requested_by", sa.String(), nullable=True))
        batch.alter_column("worker_id", type_=sa.String(64), existing_type=sa.String(20))

    op.execute(f"""
        update releases
        set state = 'cancelled', requested_action = null, "end" = coalesce("end", current_timestamp)
        where state in ({OPEN_STATES})
          and id not in (select max(id) from releases where state in ({OPEN_STATES}) group by repo)
    """)

    op.create_index(
        "uq_releases_open_repo",
        "releases",
        ["repo"],
        unique=True,
        sqlite_where=sa.text(f"state IN ({OPEN_STATES})"),
        postgresql_where=sa.text(f"state IN ({OPEN_STATES})"),
    )


def downgrade():
    op.drop_index("uq_releases_open_repo", table_name="releases")

    with op.batch_alter_table("releases") as batch:
        batch.alter_column("worker_id", type_=sa.String(20), existing_type=sa.String(64))
        batch.drop_column("requested_by")
        batch.drop_column("requested_action")
        batch.drop_column("heartbeat_at")

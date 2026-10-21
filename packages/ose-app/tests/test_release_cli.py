from types import SimpleNamespace

from flask import Flask

from ose_app.database import db
from ose_app.release import cli


def test_runner_command_uses_app_configuration(monkeypatch):
    app = Flask(__name__)
    app.config.from_object("ose_app.default_config")
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite://",
        RELEASE_MAX_PARALLEL=3,
        RELEASE_POLL_INTERVAL=0.1,
        RELEASE_HEARTBEAT_INTERVAL=0.5,
        RELEASE_LEASE_TIMEOUT=4.0,
        RELEASE_PROGRESS_INTERVAL=0,
    )
    db.init_app(app)
    cli.init_app(app)
    received = {}

    async def run():
        received["ran"] = True

    def create_runner(engine, max_parallel, **kwargs):
        received.update(max_parallel=max_parallel, **kwargs)
        return SimpleNamespace(worker_id="test", run=run)

    monkeypatch.setattr(cli, "ReleaseRunner", create_runner)

    result = app.test_cli_runner().invoke(args=["release-runner"])

    assert result.exit_code == 0, result.output
    assert received == {
        "max_parallel": 3,
        "poll_interval": 0.1,
        "heartbeat_interval": 0.5,
        "lease_timeout": 4.0,
        "progress_interval": 0,
        "ran": True,
    }

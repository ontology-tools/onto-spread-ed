import asyncio
import signal

import click
from flask import Flask, current_app

from ose_app.database import db
from ose_app.release.runner import ReleaseRunner


def init_app(app: Flask) -> None:
    @app.cli.command("release-runner")
    @click.option("--max-parallel", type=int, default=None, help="Releases run at once (default: RELEASE_MAX_PARALLEL)")
    def release_runner(max_parallel: int | None) -> None:
        """Runs the releases requested through the web API until it receives SIGTERM or SIGINT"""
        runner = ReleaseRunner(
            db.engine,
            max_parallel or current_app.config["RELEASE_MAX_PARALLEL"],
            poll_interval=current_app.config["RELEASE_POLL_INTERVAL"],
            heartbeat_interval=current_app.config["RELEASE_HEARTBEAT_INTERVAL"],
            lease_timeout=current_app.config["RELEASE_LEASE_TIMEOUT"],
            progress_interval=current_app.config["RELEASE_PROGRESS_INTERVAL"],
        )

        async def main() -> None:
            loop = asyncio.get_running_loop()

            def stop() -> None:
                click.echo("Stopping the release runner, waiting for the releases to stop")
                runner.stop()
                # A second signal stops the process right away
                for s in (signal.SIGTERM, signal.SIGINT):
                    loop.remove_signal_handler(s)

            for s in (signal.SIGTERM, signal.SIGINT):
                loop.add_signal_handler(s, stop)

            click.echo(f"Release runner {runner.worker_id} running")
            await runner.run()

        asyncio.run(main())

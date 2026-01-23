import os

from ose_app import create_app

config_path = os.path.realpath(os.path.join(os.path.dirname(__file__), "config.yaml"))

app = create_app(config_path if os.path.exists(config_path) else None)


if __name__ == "__main__":
    app.run()

import os

# Example configuration
DEBUG = True

APP_TITLE = "Ontology Spreadsheet Editor"

DATABASE_URI = 'sqlite:////tmp/github-flask-ontospreaded.db'

if os.environ.get("FLASK_ENV")=='development':
    GITHUB_CLIENT_ID = os.environ.get('GITHUB_CLIENT_ID')
    GITHUB_CLIENT_SECRET = os.environ.get('GITHUB_CLIENT_SECRET')
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY')
else:
    # Import the Secret Manager client library.
    from google.cloud import secretmanager
    # Create the Secret Manager client.
    client = secretmanager.SecretManagerServiceClient()

    project_id = "onto-spread-ed"
    client_id = "GITHUB_CLIENT_ID"
    # Build the resource name of the secret version.
    name = f"projects/{project_id}/secrets/{client_id}/versions/latest"
    # Access the secret version.
    response = client.access_secret_version(request={"name": name})
    GITHUB_CLIENT_ID = response.payload.data.decode("UTF-8")

    client_secret = "GITHUB_CLIENT_SECRET"
    # Build the resource name of the secret version.
    name = f"projects/{project_id}/secrets/{client_secret}/versions/latest"
    # Access the secret version.
    response = client.access_secret_version(request={"name": name})
    GITHUB_CLIENT_SECRET = response.payload.data.decode("UTF-8")

    flask_secret = "FLASK_SECRET_KEY"
    # Build the resource name of the secret version.
    name = f"projects/{project_id}/secrets/{flask_secret}/versions/latest"
    # Access the secret version.
    response = client.access_secret_version(request={"name": name})
    SECRET_KEY = response.payload.data.decode("UTF-8")


REPOSITORIES = {"AddictO": "jannahastings/addiction-ontology"}

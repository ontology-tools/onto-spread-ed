# ROSE 🌹 Resourceful Ontology Spreadsheet Editor

ROSE is a python based web platform for editing OWL ontologies as Excel Sheets.

## Development

### Requirements

#### Github

##### OAuth App

The app authenticates users with their github account. Therefore, a github OAuth application has to be registered.

#### Repositories

The excel sheets have to be stored in one or more github repositories. Each repository must be specified in
the `config.py`. For development and debugging purposes it is recommended to fork the live repositories and use them.

#### Libraries

Ensure that python >= 3.7 is installed. It is recommended to use a virtual environment. Create one with

```
virtualenv venv
source venv/bin/activate
```

Install the dependencies with

```
pip install -r requirements.txt
```

### Setup

#### Environment variables

Currently, there are two different deployment modes: Google cloud and local. Depending on the mode there are different
environment variables configurable.
The flask environment is specified with `FLASK_ENV`. If it is set to `development`, the local deployment is chosen
regardless of the variables. To change this behaviour, change `config.py`.

###### General variables

| Variable          | Description                                                  | Example value                    | Default   |
|-------------------|--------------------------------------------------------------|----------------------------------|-----------|
| `FLASK_ENV`       | Flask envrionment. See their documentation for more details. | `development`                    | `release` |
| `LOG_LEVEL`       | How much information should be logged                        | `error`, `warn`, `info`, `debug` | `error`   |
| `DEPLOYMENT_MODE` | Mode of deployment                                           | `GOOGLE_CLOUD`, `LOCAL`          | `LOCAL`   |

###### Local deployment

| Variable               | Description                            | Example value                | Default      |
|------------------------|----------------------------------------|------------------------------|--------------|
| `FLASK_SECRET_KEY`     | Random key used for session management | `WXR6s8I2Ei55YaZiOG753jsj17` |              |
| `GITHUB_CLIENT_ID`     | Client id of the OAUTH app             |                              |              |
| `GITHUB_CLIENT_SECRET` | Client secret of the OAUTH app         |                              |              |
| `INDEX_PATH`           | Path to the index folder               | `./indexdir`                 | `./indexdir` |

###### Google Cloud deployment

| Variable               | Description                            | Default      |
|------------------------|----------------------------------------|--------------|
| `GOOGLE_APPLICATION_CREDENTIALS` | Path the a json file containing the google application credentials | `ontospreaded.json` |
| `GOOGLE_INDEX_BUCKET` | Name of the bucket to store the index | `index-spread-ed` |
| `GOOGLE_PROJECT_ID` | Google project id | `onto-spread-ed` |
| `GOOGLE_SECRET_NAME_GITHUB_CLIENT_ID` | Name of the secret holding the github client id | `GITHUB_CLIENT_ID` |
| `GOOGLE_SECRET_NAME_GITHUB_CLIENT_SECRET` | Name of the secret holding the github client secret | `GITHUB_CLIENT_SECRET` |
| `GOOGLE_SECRET_NAME_FLASK_SECRET` | Name of the secret holding the flask secret | `FLASK_SECRET_KEY` |

#### Edit configuration

Specify the repositories and initials in `config.py`.

### Running

python app.py

## Common Problems

### OAuth redirects to the live app / no app

Create an additional app just for development and use a dummy callback URL e.g. me.mydomain.com. Then, either manually
edit the URL after a successful login or create an alias for your localhost so that the GitHub authorisation can
redirect successfully

Add e.g. me.mydomain.com to your hosts file ( `/etc/hosts` for *NIX, `C:\windows\system32\drivers\etc\hosts` for
Windows)

```
127.0.0.1 me.mydomain.com
```

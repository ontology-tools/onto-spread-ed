## Development

### Requirements (Libraries)

1. Python 3.7+

https://www.python.org/

2. Flask + Jinja templates

`pip install flask`

https://flask.palletsprojects.com/en/1.1.x/installation/

3. GitHub-Flask and Flask-SQLAlchemy

`pip install GitHub-Flask`

https://github.com/cenkalti/github-flask

`pip install Flask-SQLAlchemy`

https://github.com/pallets/flask-sqlalchemy

4. OpenPyXL

`pip install openpyxl`

https://openpyxl.readthedocs.io


### Setup

1. Environment variables
`export FLASK_ENV=development`

`export FLASK_SECRET_KEY=choose-something`

2. Edit configuration

Specify GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET in config.py

3. Create an alias for your localhost so that the GitHub authorisation can redirect successfully 

Add me.mydomain.com to your hosts file ( /etc/hosts in *NIX, c:\windows\system32\drivers\etc\hosts in windows)

`127.0.0.1 me.mydomain.com`


### Running

python app.py

import base64
import copy
import json

import pytest
import yaml
from flask import Flask

from ose.project import Project
from ose_app.routes.api.settings import get_project, save_project


class Configuration:
    def __init__(self, project, path):
        self.project = Project.model_validate(copy.deepcopy(project))
        self.app_config = {"REPOSITORIES_REPOSITORY_CONFIG_PATH": path}

    def get(self, name):
        return self.project

    def replace(self, project):
        self.project = project


class GitHub:
    def __init__(self, document):
        self.document = document
        self.commits = []

    def get(self, *args, **kwargs):
        return {"sha": str(len(self.commits)), "content": base64.b64encode(json.dumps(self.document).encode()).decode()}

    def put(self, path, data):
        assert data["sha"] == str(len(self.commits))
        self.commits.append(data)
        self.document = yaml.safe_load(base64.b64decode(data["content"]))


@pytest.fixture
def settings(request):
    document = {
        "short_name": "EX", "full_name": "Example", "iri_prefix": "http://example.org/",
        "short_repository_name": "ex", "full_repository_name": "example/ex",
        "external": {"sources": [], "target": "external.owl", "extension": {"enabled": True}},
        "files": {}, "build_configurations": [{"name": "default", "stages": []}],
        "extension": {"owner": "example"},
    }
    config = Configuration(document, getattr(request, "param", "project.yaml"))
    gh = GitHub(document)
    app = Flask(__name__)
    app.add_url_rule("/project", "get", lambda: get_project.__wrapped__("EX", config))
    app.add_url_rule("/project", "save", lambda: save_project.__wrapped__("EX", config, gh), methods=["PUT"])
    return app.test_client(), config, gh


@pytest.mark.parametrize("settings", ["project.yaml", "project.json"], indirect=True)
def test_save_normalizes_shorthands_and_preserves_extension_fields(settings):
    client, config, gh = settings
    loaded = client.get("/project").get_json()
    project = loaded["project"]
    project["iri_prefix"] = "http://new.example/"
    response = client.put("/project", json=project, headers={"If-Match": f'"{loaded["revision"]}"'})

    assert response.status_code == 200
    assert Project.model_validate(gh.document) == config.project == Project.model_validate(project)
    assert gh.document["external"]["target"]["iri"] == "http://example.org/external.owl"
    assert gh.document["extension"] == {"owner": "example"}
    assert gh.document["external"]["extension"] == {"enabled": True}
    assert gh.commits[0]["message"] == "Update EX project configuration\n\nChange iri prefix."
    if config.app_config["REPOSITORIES_REPOSITORY_CONFIG_PATH"].endswith(".json"):
        assert json.loads(base64.b64decode(gh.commits[0]["content"])) == gh.document


def test_stale_browser_cannot_overwrite_another_save(settings):
    client, config, gh = settings
    loaded = client.get("/project").get_json()
    a, b = copy.deepcopy(loaded["project"]), copy.deepcopy(loaded["project"])
    a["full_name"] = "User A's change"
    b["id_digits"] = 8
    headers = {"If-Match": f'"{loaded["revision"]}"'}

    first = client.put("/project", json=a, headers=headers)
    second = client.put("/project", json=b, headers=headers)

    assert first.status_code == 200
    assert second.status_code == 409
    assert config.project.full_name == gh.document["full_name"] == "User A's change"
    assert len(gh.commits) == 1
    assert first.get_json()["revision"] != loaded["revision"]


def test_github_changes_are_not_overwritten(settings):
    client, config, gh = settings
    loaded = client.get("/project").get_json()
    gh.document["full_name"] = "Edited on GitHub"
    loaded["project"]["id_digits"] = 8

    response = client.put("/project", json=loaded["project"], headers={"If-Match": f'"{loaded["revision"]}"'})

    assert response.status_code == 409
    assert config.project.full_name == gh.document["full_name"] == "Edited on GitHub"
    assert gh.commits == []

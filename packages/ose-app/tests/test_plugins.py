import importlib
from abc import abstractmethod
from types import ModuleType, SimpleNamespace

from flask import Flask
from injector import Injector, inject

from ose_app import load_config
from ose_app.model import WebPlugin
from ose_app.model.Script import Script
from ose_app.routes.api.plugins import bp, get_plugins, get_plugin_static
from ose_app.services.PluginService import PluginService

service_module = importlib.import_module("ose_app.services.PluginService")


class EntryPoint:
    def __init__(self, name, value, module="ose_app.model.WebPlugin"):
        self.name, self.value, self.module = name, value, module
        self.dist = SimpleNamespace(metadata={"Name": "example-plugin"}, version="1.2.3")

    def load(self):
        if isinstance(self.value, Exception):
            raise self.value
        return self.value


def test_script_discovery_scans_concrete_classes_and_uses_injector(monkeypatch):
    class Dependency:
        pass

    dependency = Dependency()

    class Concrete(Script):
        id = "example"
        title = "Example"

        @inject
        def __init__(self, dep: Dependency):
            self.dep = dep

    class Abstract(Concrete):
        @abstractmethod
        def run(self):
            pass

    module = ModuleType("scripts")
    module.Concrete, module.Abstract, module.Script = Concrete, Abstract, Script
    monkeypatch.setattr(service_module, "entry_points", lambda group: [
        EntryPoint("broken", RuntimeError("unavailable")), EntryPoint("example", module),
    ] if group == "ose.scripts" else [])
    service = PluginService(Injector(lambda binder: binder.bind(Dependency, to=dependency)))
    service.discover_scripts()
    scripts = service.get_scripts()
    assert len(scripts) == 1
    assert scripts[0].dep is dependency
    service.discover_scripts()
    assert len(service.get_scripts()) == 1


def test_web_discovery_api_and_static_files(monkeypatch, tmp_path):
    module = ModuleType("example_web")
    module.__file__ = str(tmp_path / "__init__.py")
    static = tmp_path / "assets"
    static.mkdir()
    (static / "entry.js").write_text("export default {};")
    (tmp_path / "private.txt").write_text("private")
    monkeypatch.setattr(service_module, "import_module", lambda name: module)
    monkeypatch.setattr(service_module, "entry_points", lambda group: [
        EntryPoint("zeta", WebPlugin("entry.js", "assets")),
        EntryPoint("invalid", object()),
        EntryPoint("alpha", WebPlugin("entry.js", "assets")),
        EntryPoint("broken", RuntimeError("unavailable")),
    ] if group == "ose.web_plugins" else [])
    service = PluginService(Injector())
    service.discover_web_plugins()
    app = Flask(__name__)
    app.register_blueprint(bp)
    app.view_functions["api_plugins.get_plugins"] = lambda: get_plugins(service)
    app.view_functions["api_plugins.get_plugin_static"] = lambda plugin_id, filename: get_plugin_static(
        service, plugin_id, filename,
    )
    client = app.test_client()
    response = client.get("/api/plugins/")
    assert response.status_code == 200
    assert response.json == [
        {"id": id, "type": "ose.web_plugins", "distribution": "example-plugin", "version": "1.2.3",
         "module_url": f"/api/plugins/{id}/static/entry.js"}
        for id in ("alpha", "zeta")
    ]
    assert client.get(response.json[0]["module_url"]).text == "export default {};"
    assert client.get("/api/plugins/unknown/static/entry.js").status_code == 404
    assert client.get("/api/plugins/alpha/static/../private.txt").status_code == 404
    assert service.get_plugin_static_path("alpha") == static


def test_yaml_plugin_settings_are_forwarded_to_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("OSE_PLUGINS__BCIO__API_AUTH_TOKEN", "environment-token")
    monkeypatch.delenv("OSE_PLUGINS__BCIO__API_PATH", raising=False)
    config = tmp_path / "config.yaml"
    config.write_text('plugins:\n  bcio:\n    api-path: "https://example.org/"\n    api-auth-token: yaml-token\n')
    load_config(Flask(__name__), str(config))
    import os
    assert os.environ["OSE_PLUGINS__BCIO__API_PATH"] == "https://example.org/"
    assert os.environ["OSE_PLUGINS__BCIO__API_AUTH_TOKEN"] == "environment-token"


def test_overview_includes_all_types_with_optional_web_module(monkeypatch):
    from ose.building.stages import ConversionStage

    class ExampleScript(Script):
        id = "example"
        title = "Example"

    scripts = ModuleType("scripts")
    scripts.ExampleScript = ExampleScript
    stages = ModuleType("stages")
    stages.ConversionStage = ConversionStage
    entries = {
        "ose.scripts": [EntryPoint("shared", scripts)],
        "ose.build_stages": [
            EntryPoint("shared", stages), EntryPoint("broken", RuntimeError("not installed")),
            EntryPoint("invalid", object()),
        ],
        "ose.web_plugins": [EntryPoint("shared", WebPlugin("entry.js"))],
    }
    monkeypatch.setattr(service_module, "entry_points", lambda group: entries.get(group, []))
    service = PluginService(Injector())
    service.discover_scripts()
    service.discover_build_stages()
    service.discover_web_plugins()
    # Repeated discovery replaces metadata as well as the discovered implementations.
    service.discover_build_stages()
    app = Flask(__name__)
    app.register_blueprint(bp)
    app.view_functions["api_plugins.get_plugins"] = lambda: get_plugins(service)
    response = app.test_client().get("/api/plugins/")
    assert response.status_code == 200
    assert response.json == [
        {"id": "shared", "type": group, "distribution": "example-plugin", "version": "1.2.3",
         **({"module_url": "/api/plugins/shared/static/entry.js"} if group == "ose.web_plugins" else {})}
        for group in ("ose.build_stages", "ose.scripts", "ose.web_plugins")
    ]


def test_overview_handles_missing_distribution_and_removed_plugins(monkeypatch):
    scripts = ModuleType("scripts")
    ep = EntryPoint("example", scripts)
    ep.dist = None
    entries = [ep]
    monkeypatch.setattr(service_module, "entry_points", lambda group: entries)
    service = PluginService(Injector())
    service.discover_scripts()
    assert service.get_plugins_info() == [
        {"id": "example", "type": "ose.scripts", "distribution": None, "version": None},
    ]
    entries.clear()
    service.discover_scripts()
    assert service.get_plugins_info() == []

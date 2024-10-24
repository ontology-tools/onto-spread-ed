import functools
import re

from flask import Flask
from injector import Injector, inject

from onto_spread_ed.PermissionManager import PermissionManager

__EXTENSIONS = {}


def init_app(app: Flask, injector: Injector):
    @app.template_filter('css_safe')
    def css_safe(s: str) -> str:
        return re.sub("[^0-9a-zA-Z]", "_", s)

    @app.context_processor
    def processor():
        return {
            n: lambda *args, **kwargs: f(injector, *args, **kwargs)
            for n, f in __EXTENSIONS.items()
        }


def jinja_fn(fn):
    @functools.wraps(fn)
    def wrapper(injector: Injector, *args, **kwargs):
        return injector.call_with_injection(callable=inject(fn), args=args, kwargs=kwargs)

    __EXTENSIONS[fn.__name__] = wrapper

    return wrapper


@jinja_fn
def has_permissions(*permissions: str, permission_manager: PermissionManager):
    return permission_manager.current_user_has_permissions(*permissions)


@jinja_fn
def has_any_permission(*permissions: str, permission_manager: PermissionManager):
    return any(permission_manager.current_user_has_permissions(p) for p in permissions)

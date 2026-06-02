import ast
from pathlib import Path


MUTATING_ROUTE_MARKERS = (
    "/delete",
    "/run/",
    "/close/",
    "/create-os/",
    "/provision/",
    "/block/",
    "/unblock/",
    "/sync-billing/",
    "/emit",
)


def _route_decorators():
    app_path = Path(__file__).resolve().parents[1] / "admin_panel" / "app.py"
    tree = ast.parse(app_path.read_text(encoding="utf-8"))

    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        for decorator in node.decorator_list:
            if not (
                isinstance(decorator, ast.Call)
                and isinstance(decorator.func, ast.Attribute)
                and decorator.func.attr == "route"
            ):
                continue
            if not decorator.args:
                continue
            route = ast.literal_eval(decorator.args[0])
            methods = None
            for keyword in decorator.keywords:
                if keyword.arg == "methods":
                    methods = ast.literal_eval(keyword.value)
            yield route, methods


def test_mutating_admin_routes_do_not_accept_implicit_get():
    offenders = []
    for route, methods in _route_decorators():
        if not any(marker in route for marker in MUTATING_ROUTE_MARKERS):
            continue
        if methods is None or "GET" in methods:
            offenders.append(route)

    assert not offenders, f"Mutating routes must be explicit non-GET routes: {sorted(offenders)}"


def test_base_template_exposes_csrf_helpers():
    base_template = Path(__file__).resolve().parents[1] / "admin_panel" / "templates" / "base.html"
    content = base_template.read_text(encoding="utf-8")

    assert 'name="csrf-token"' in content
    assert "X-CSRF-Token" in content
    assert "window.postAction" in content

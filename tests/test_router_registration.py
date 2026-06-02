import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAIN_PATH = ROOT / "app" / "main.py"


def _main_tree() -> ast.Module:
    return ast.parse(MAIN_PATH.read_text(encoding="utf-8"))


def _route_file_modules() -> set[str]:
    modules_root = ROOT / "app" / "modules"
    return {
        ".".join(path.relative_to(modules_root).with_suffix("").parts[:-1])
        for path in modules_root.rglob("routes.py")
    }


def _route_imports() -> dict[str, str]:
    imports = {}
    for node in _main_tree().body:
        if not isinstance(node, ast.ImportFrom) or not node.module:
            continue
        if not node.module.startswith("modules.") or not node.module.endswith(".routes"):
            continue
        module_name = node.module.removeprefix("modules.").removesuffix(".routes")
        for alias in node.names:
            if alias.name == "router" and alias.asname:
                imports[module_name] = alias.asname
    return imports


def _include_router_calls() -> dict[str, ast.Call]:
    calls = {}
    for node in ast.walk(_main_tree()):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute) or node.func.attr != "include_router":
            continue
        if not node.args or not isinstance(node.args[0], ast.Name):
            continue
        calls[node.args[0].id] = node
    return calls


def test_all_module_route_files_are_registered_in_main():
    route_modules = _route_file_modules()
    imported_modules = set(_route_imports())

    missing_imports = route_modules - imported_modules
    assert not missing_imports, f"Route modules not imported in main.py: {sorted(missing_imports)}"

    imports = _route_imports()
    included_router_vars = set(_include_router_calls())
    missing_includes = {module for module, var_name in imports.items() if var_name not in included_router_vars}
    assert not missing_includes, f"Imported routers not included in app: {sorted(missing_includes)}"


def test_registered_business_routers_are_auth_protected():
    public_router_vars = {"auth_router", "health_router", "billing_gateway_webhooks"}
    includes = _include_router_calls()

    unprotected = []
    for router_var, call in includes.items():
        if router_var in public_router_vars:
            continue
        has_protected_dependency = any(
            keyword.arg == "dependencies"
            and isinstance(keyword.value, ast.Name)
            and keyword.value.id == "protected"
            for keyword in call.keywords
        )
        if not has_protected_dependency:
            unprotected.append(router_var)

    assert not unprotected, f"Routers missing dependencies=protected: {sorted(unprotected)}"

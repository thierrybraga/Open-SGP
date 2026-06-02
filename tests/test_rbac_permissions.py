import ast
import re
from pathlib import Path


REQUIRE_PERMISSION_RE = re.compile(r'require_permissions\("([^"]+)"\)')


def _seeded_permissions() -> set[str]:
    main_path = Path(__file__).resolve().parents[1] / "app" / "main.py"
    tree = ast.parse(main_path.read_text(encoding="utf-8"))

    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == "base_perms" for target in node.targets):
            continue
        return {item[0] for item in ast.literal_eval(node.value)}

    raise AssertionError("base_perms seed not found")


def _used_permissions() -> set[str]:
    modules_dir = Path(__file__).resolve().parents[1] / "app" / "modules"
    used = set()
    for path in modules_dir.rglob("routes.py"):
        used.update(REQUIRE_PERMISSION_RE.findall(path.read_text(encoding="utf-8")))
    return used


def test_route_permissions_are_seeded():
    missing = _used_permissions() - _seeded_permissions()
    assert not missing, f"Permissions used by routes but missing from seed: {sorted(missing)}"

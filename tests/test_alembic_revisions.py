import ast
from pathlib import Path


def _read_revision_metadata(path: Path) -> tuple[str, str | tuple[str, ...] | None]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    revision = None
    down_revision = None

    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        names = [target.id for target in node.targets if isinstance(target, ast.Name)]
        if "revision" in names:
            revision = ast.literal_eval(node.value)
        if "down_revision" in names:
            down_revision = ast.literal_eval(node.value)

    if not revision:
        raise AssertionError(f"Migration without revision: {path}")
    return revision, down_revision


def test_alembic_revisions_have_single_head():
    versions_dir = Path(__file__).resolve().parents[1] / "alembic" / "versions"
    revisions = {}
    down_revisions = set()

    for path in versions_dir.glob("*.py"):
        revision, down_revision = _read_revision_metadata(path)
        assert revision not in revisions, f"Duplicate revision id: {revision}"
        revisions[revision] = path

        if isinstance(down_revision, tuple):
            down_revisions.update(down_revision)
        elif down_revision:
            down_revisions.add(down_revision)

    missing_parents = down_revisions - set(revisions)
    assert not missing_parents, f"Missing parent revisions: {sorted(missing_parents)}"

    heads = set(revisions) - down_revisions
    assert heads == {"0035_zabbix_device_snmp"}

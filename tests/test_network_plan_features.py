import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def _function_source(relative: str, name: str) -> str:
    tree = ast.parse(_read(relative))
    source = _read(relative)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"Function {name} not found in {relative}")


def test_huawei_zte_olt_adapter_uses_device_session_and_keeps_generic_unsupported():
    olt_vendor = _read("app/modules/network/vendors/olt.py")
    service = _read("app/modules/network/service.py")

    assert "source\": \"simulated\"" not in olt_vendor
    assert "socket.create_connection" in olt_vendor
    assert "class OLTCommandError" in olt_vendor
    assert "def _ensure_supported" in olt_vendor
    assert "raise NotImplementedError" in _function_source("app/modules/network/vendors/olt.py", "_ensure_supported")
    assert "vendor=dev.vendor, port=dev.port or 23" in service
    assert '"source": "device"' in _function_source("app/modules/network/vendors/olt.py", "onu_status")


def test_vsol_adapter_uses_device_session_instead_of_simulated_onu_data():
    vsol_vendor = _read("app/modules/network/vendors/vsol.py")
    service = _read("app/modules/network/service.py")
    onu_status = _function_source("app/modules/network/vendors/vsol.py", "onu_status")

    assert "socket.create_connection" in vsol_vendor
    assert '"source": "device"' in onu_status
    assert '"source": "simulated"' not in vsol_vendor
    assert "random." not in vsol_vendor
    assert "VSOLClient(dev.host, dev.username, dev.password, port=dev.port or 23)" in service
    assert "VSOLClient(device.host, device.username, device.password, port=device.port or 23)" in service


def test_onu_status_accepts_real_olt_identifiers_without_contract_id_cast():
    get_onu_status = _function_source("app/modules/network/service.py", "get_onu_status")

    assert "int(onu_id)" not in get_onu_status.split("_write_history", 1)[0]
    assert "if str(onu_id).isdigit():" in get_onu_status


def test_network_routes_map_unsupported_olt_adapter_to_501():
    routes = _read("app/modules/network/routes.py")

    assert "HTTP_501_NOT_IMPLEMENTED" in routes
    assert routes.count("except NotImplementedError as e:") >= 6
    assert "def onu_status(" in routes
    assert "onu = get_onu_status" in routes
    assert "status = get_onu_status" not in routes


def test_zabbix_templates_are_resolved_by_name():
    zabbix_sync = _read("app/modules/network/zabbix_sync.py")
    zabbix_vendor = _read("app/modules/network/vendors/zabbix.py")

    assert "DEFAULT_TEMPLATE_MAP" in zabbix_sync
    assert "template_map" in zabbix_sync
    assert "get_template_ids_by_names" in zabbix_vendor
    assert "TODO" not in zabbix_sync


def test_plan_changes_sync_service_profile_and_radius_template():
    plan_service = _read("app/modules/plans/service.py")
    network_service = _read("app/modules/network/service.py")

    assert "sync_service_profile_for_plan" in plan_service
    assert plan_service.count("sync_service_profile_for_plan(db, plan)") >= 2
    assert "def plan_profile_name(plan_id: int) -> str:" in network_service
    assert 'return f"plan:{plan_id}"' in network_service
    assert "RadiusClient(db).create_plan_template" in network_service


def test_assignment_provisioning_uses_plan_profile_and_mikrotik_target_ip():
    create_assignment = _function_source("app/modules/network/service.py", "create_assignment")
    provision_contract = _function_source("app/modules/network/service.py", "provision_contract")

    assert "if not values.get(\"profile_id\") and contract.plan:" in create_assignment
    assert "values[\"profile_id\"] = profile.id" in create_assignment
    assert "if not prof and contract and contract.plan:" in provision_contract
    assert "target_ip=cna.static_ip" in provision_contract
    assert "plan_group_name=prof.name" in provision_contract


def test_billing_blocking_respects_contract_suspension_flag_and_updates_status():
    sync_billing = _function_source("app/modules/network/service.py", "sync_billing_blocking")
    block_contract = _function_source("app/modules/network/service.py", "block_contract")
    unblock_contract = _function_source("app/modules/network/service.py", "unblock_contract")
    provision_contract = _function_source("app/modules/network/service.py", "provision_contract")
    unbind_vlan = _function_source("app/modules/network/service.py", "unbind_vlan_for_contract")

    assert "not contract.suspend_on_arrears" in sync_billing
    assert "return unblock_contract(db, contract_id)" in sync_billing
    assert 'contract.status = "suspended"' in block_contract
    assert 'contract.status = "active"' in unblock_contract
    assert "except Exception" not in provision_contract
    assert "except Exception" not in block_contract
    assert "except Exception" not in unblock_contract
    assert "except Exception" not in unbind_vlan


def test_contract_update_allows_validated_plan_change():
    contract_schema = _read("app/modules/contracts/schemas.py")
    contract_service = _function_source("app/modules/contracts/service.py", "update_contract")

    assert "plan_id: Optional[int] = None" in contract_schema
    assert "if data.plan_id is not None:" in contract_service
    assert "Invalid or inactive plan" in contract_service

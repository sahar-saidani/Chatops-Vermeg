from pathlib import Path

from routing.tenant_machine_registry import TenantMachineRegistry


def test_registry_loads_tenant_routes():
    registry = TenantMachineRegistry.from_file(Path(__file__).resolve().parents[1] / "config" / "tenant_machines.yml")

    maif = registry.resolve("MAIF")
    nnbe = registry.resolve("NNBE")

    assert maif is not None
    assert maif.machine_reference == "MAIF-WINDOWS-01"
    assert maif.environment == "DEV"
    assert "jenkins" in maif.available_agents

    assert nnbe is not None
    assert nnbe.machine_reference == "NNBE-CENTOS-01"
    assert registry.infer_tenant("Analyze Jenkins status for MAIF") == "MAIF"

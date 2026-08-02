from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent.machine_identity import MachineIdentity
from message_sender import MessageSender


class FakePublisher:
    def __init__(self) -> None:
        self.calls = []

    def publish(self, message, identity=None):
        self.calls.append((message, identity))


def test_build_message_includes_environment_name() -> None:
    sender = MessageSender()
    identity = MachineIdentity(
        tenant_name="MAIF",
        environment_name="DEV",
        environment_type="STANDALONE",
        machine_reference="MAIF-DEV-JENKINS-01",
        jenkins_purpose="SNAPSHOT",
    )

    message = sender.build_message({"summary": "ok"}, identity)

    assert message["environmentName"] == "DEV"
    assert message["tenant"] == "MAIF"
    assert message["data"] == {"summary": "ok"}


def test_send_passes_identity_to_publisher() -> None:
    sender = MessageSender()
    fake_publisher = FakePublisher()
    sender._publisher = fake_publisher
    identity = MachineIdentity(
        tenant_name="MAIF",
        environment_name="DEV",
        environment_type="STANDALONE",
        machine_reference="MAIF-DEV-JENKINS-01",
        jenkins_purpose="RELEASE",
    )

    message = sender.send({"summary": "ok"}, identity)

    assert fake_publisher.calls[0][0] == message
    assert fake_publisher.calls[0][1] is identity

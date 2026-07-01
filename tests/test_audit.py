
from guardweave.audit.exporter import AuditExporter
from guardweave.audit.hashing import HashChain
from guardweave.core.enums import Capability, Decision, RiskLevel
from guardweave.core.models import AuditEntry


class TestHashChain:
    def test_hash_consistency(self):
        hasher = HashChain()
        data = {"id": "test", "value": 42}
        h1 = hasher.compute_hash(data)
        h2 = hasher.compute_hash(data)
        assert h1 == h2

    def test_hash_changes_with_data(self):
        hasher = HashChain()
        h1 = hasher.compute_hash({"id": "test", "value": 42})
        h2 = hasher.compute_hash({"id": "test", "value": 43})
        assert h1 != h2

    def test_chain_verification(self):
        from datetime import datetime
        hasher = HashChain()
        entries = []
        ts = datetime(2026, 1, 1)

        for i in range(3):
            prev_hash = entries[-1]["chain_hash"] if entries else ""
            entry_data = hasher.build_entry_data(
                entry_id=f"e{i}",
                timestamp=ts,
                agent_id="a1",
                session_id="s1",
                action=f"action_{i}",
                capability="file:read",
                target=f"/tmp/{i}.txt",
                decision="allow",
                risk_score=10,
                risk_level="low",
                policy_id="p1",
                rule_id="r1",
                reason="test",
                context={"key": "value"},
                previous_hash=prev_hash,
            )
            chain_hash = hasher.compute_hash(entry_data)
            entry_data["chain_hash"] = chain_hash
            entries.append(entry_data)

        assert hasher.verify_chain(entries) is True

    def test_tamper_detection(self):
        from datetime import datetime
        hasher = HashChain()
        entries = []
        ts = datetime(2026, 1, 1)

        for i in range(3):
            prev_hash = entries[-1]["chain_hash"] if entries else ""
            entry_data = hasher.build_entry_data(
                entry_id=f"e{i}", timestamp=ts,
                agent_id="a1", session_id="s1", action=f"action_{i}",
                capability="file:read", target=f"/tmp/{i}.txt",
                decision="allow", risk_score=10, risk_level="low",
                policy_id="p1", rule_id="r1", reason="test",
                context={}, previous_hash=prev_hash,
            )
            chain_hash = hasher.compute_hash(entry_data)
            entry_data["chain_hash"] = chain_hash
            entries.append(entry_data)

        entries[1]["action"] = "tampered"
        assert hasher.verify_chain(entries) is False


class TestAuditExporter:
    def test_json_export(self):
        entry = AuditEntry(
            id="test-1",
            agent_id="a1",
            session_id="s1",
            action="read",
            capability=Capability.FILE_READ,
            target="/tmp/test.txt",
            decision=Decision.ALLOW,
            risk_score=10,
            risk_level=RiskLevel.LOW,
            policy_id="p1",
            reason="test",
            chain_hash="abc",
            previous_hash="",
        )
        json_str = AuditExporter.to_json([entry])
        assert "test-1" in json_str
        assert "a1" in json_str
        assert "file:read" in json_str

    def test_csv_export(self):
        entry = AuditEntry(
            id="test-1",
            agent_id="a1",
            session_id="s1",
            action="read",
            capability=Capability.FILE_READ,
            target="/tmp/test.txt",
            decision=Decision.ALLOW,
            risk_score=10,
            risk_level=RiskLevel.LOW,
            policy_id="p1",
            reason="test",
            chain_hash="abc",
            previous_hash="",
        )
        csv_str = AuditExporter.to_csv([entry])
        assert "test-1" in csv_str
        assert "a1" in csv_str

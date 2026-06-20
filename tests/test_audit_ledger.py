import pytest
import os
import json
from services.audit_service import AuditService, AuditEvent

@pytest.mark.asyncio
async def test_audit_ledger():
    log_path = "tests/test_audit.jsonl"
    if os.path.exists(log_path):
        os.remove(log_path)
        
    audit = AuditService(log_path)
    await audit.log_event(AuditEvent.ELECTION_STARTED, {"user": "admin"})
    await audit.log_event(AuditEvent.VOTING_ENABLED, {})
    
    assert audit.verify_chain() is True
    
    # Tamper with the ledger
    with open(log_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    entry = json.loads(lines[0])
    entry["details"]["user"] = "hacker"
    lines[0] = json.dumps(entry) + "\n"
    
    with open(log_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
        
    assert audit.verify_chain() is False
    
    if os.path.exists(log_path):
        os.remove(log_path)

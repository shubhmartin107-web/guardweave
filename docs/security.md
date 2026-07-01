# Security Considerations

## Overview

GuardWeave is designed as a safety layer for AI agents. While it provides structured guardrails, it should be deployed as part of a defense-in-depth strategy, not as the sole security mechanism.

## Threat Model

### What GuardWeave Protects Against
- **Unintended agent actions**: Policy evaluation prevents agents from performing actions they shouldn't
- **Permission escalation**: Agents cannot grant themselves capabilities without approval
- **Audit tampering**: The Merkle hash chain makes retroactive log modification detectable
- **Runaway agents**: HITL approvals and timeouts prevent agents from executing high-risk actions autonomously

### What GuardWeave Does NOT Protect Against
- **Compromised host**: If the host system is compromised, GuardWeave's SQLite database and configuration can be modified
- **Side-channel attacks**: Actions that don't map to GuardWeave capabilities won't be checked
- **LLM prompt injection**: GuardWeave checks actions, not the reasoning that produced them
- **Denial of service**: No rate limiting or resource exhaustion protection built in

## Audit Chain Security

The audit chain uses SHA-256 hashing in a Merkle-chain configuration:

1. Each audit entry includes `previous_hash` (hash of the preceding entry)
2. The complete entry data (excluding `chain_hash` itself) is hashed to produce `chain_hash`
3. Any modification to an entry breaks the chain at that point
4. `AuditLogger.verify_integrity()` walks the entire chain and validates every link

**Recommendation:** Periodically verify the audit chain, especially before and after deploying updates.

## Policy Integrity

- Policies are stored in SQLite and loaded into memory at evaluation time
- The CLI's `policy validate` command checks YAML syntax before application
- Policy modification requires audit_log_modify capability (denied by default)

## HITL Approval Security

- Approval requests include full action context for informed decision-making
- All approvals/denials are logged with who decided and when
- Timeouts auto-deny or escalate based on risk level
- Feedback is optional but encouraged for auditability

## Production Deployment Checklist

- [ ] Change the default HMAC secret in `HashChain.__init__()` from the default value
- [ ] Set `GUARDWEAVE_ENV=production` environment variable
- [ ] Configure strict policies (use `policies/strict.yaml` as a starting point)
- [ ] Set `GUARDWEAVE_DB_PATH` to a secure, backed-up location
- [ ] Enable audit chain verification as a cron job
- [ ] Restrict dashboard access to authorized users (consider a reverse proxy with auth)
- [ ] Never run the dashboard on a public network without authentication
- [ ] Consider encrypting the SQLite database at rest
- [ ] Set appropriate HITL timeout values for your risk tolerance

## Environment Separation

GuardWeave supports three environments:
- **development**: Relaxed policies, more `allow` decisions, longer timeouts
- **staging**: Balanced policies for pre-production testing
- **production**: Strict policies, `deny` by default, short timeouts

Always use separate databases and policies for each environment.

## Responsible Disclosure

If you discover a security vulnerability in GuardWeave, please report it by opening an issue on GitHub. Do not disclose vulnerabilities publicly until they have been addressed.

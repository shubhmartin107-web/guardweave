# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | ✅ Active development |

## Reporting a Vulnerability

GuardWeave takes security seriously. If you discover a security vulnerability,
please follow these steps:

1. **Do not** disclose the vulnerability publicly
2. Email the maintainers at [shubhmartin107@gmail.com] with details
3. Include steps to reproduce and potential impact
4. Allow time for the fix to be deployed

You can expect:
- Acknowledgment within 48 hours
- A fix timeline within 7 days
- Credit in the release notes (if desired)

## Security Best Practices

When deploying GuardWeave in production:

1. **Change defaults**: Override the HMAC secret in `HashChain`
2. **Use environment separation**: Different DB and policies per environment
3. **Restrict dashboard access**: Use a reverse proxy with authentication
4. **Monitor audit integrity**: Run periodic chain verification
5. **Apply least privilege**: Start with `deny` as default, explicitly allow what's needed
6. **Rotate secrets**: Regularly rotate the database and any API keys

See [docs/security.md](docs/security.md) for the full security guide.

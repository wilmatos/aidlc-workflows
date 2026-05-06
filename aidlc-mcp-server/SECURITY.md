# Security Policy

## Reporting a Vulnerability

If you discover a potential security issue in this project, we ask that you notify
AWS Security via our [vulnerability reporting page](http://aws.amazon.com/security/vulnerability-reporting/).

Please do **not** create a public GitHub issue for security vulnerabilities.

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: Depends on severity
  - Critical: 1-7 days
  - High: 7-14 days
  - Medium: 14-30 days
  - Low: 30-90 days

## Security Best Practices

When using AI-DLC MCP Server:

### Input Validation

- All user inputs are validated
- File paths are sanitized and constrained to workspace boundaries
- Command injection is prevented

### File System Security

- Projects are isolated in designated directories
- File operations use atomic writes
- Path traversal is blocked by validation

### Dependency Security

- Dependencies are regularly updated
- Security scans run via Bandit and Gitleaks
- Known vulnerabilities are monitored

## Security Features

- **Type Safety**: Strict type checking with mypy
- **Input Validation**: All inputs validated before filesystem operations
- **Error Handling**: Comprehensive exception handling without leaking internals
- **Audit Logging**: All operations are logged
- **Sandboxing**: Project isolation within workspace boundaries

## Known Limitations

- File system access is required for project management
- No built-in authentication (relies on MCP client)

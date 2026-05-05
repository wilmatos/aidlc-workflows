# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 2.1.x   | :white_check_mark: |
| 2.0.x   | :x:                |
| < 2.0   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue, please follow these steps:

### 1. Do Not Disclose Publicly

Please do not open a public issue or discuss the vulnerability in public forums.

### 2. Report Privately

Send a detailed report to: **<wilmatos@amazon.com>**

Include:

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### 3. Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: Depends on severity
  - Critical: 1-7 days
  - High: 7-14 days
  - Medium: 14-30 days
  - Low: 30-90 days

### 4. Disclosure Process

1. We will investigate and validate the report
2. We will develop and test a fix
3. We will release a security patch
4. We will publicly disclose the vulnerability after the patch is released
5. We will credit the reporter (unless they prefer to remain anonymous)

## Security Best Practices

When using AI-DLC MCP Server:

### Input Validation

- All user inputs are validated
- File paths are sanitized
- Command injection is prevented

### File System Security

- Projects are isolated in designated directories
- File operations use atomic writes
- Permissions are checked before operations

### Git Integration

- Git operations are sandboxed
- Credentials are never logged
- Commit messages are sanitized

### Dependency Security

- Dependencies are regularly updated
- Security scans run via Bandit
- Known vulnerabilities are monitored

## Security Features

- **Type Safety**: Strict type checking with mypy
- **Input Validation**: Pydantic models for all inputs
- **Error Handling**: Comprehensive exception handling
- **Audit Logging**: All operations are logged
- **Sandboxing**: Project isolation

## Known Limitations

- File system access is required for project management
- Git operations require local git installation
- No built-in authentication (relies on MCP client)

## Security Updates

Security updates are released as patch versions (e.g., 2.1.1) and announced via:

- GitHub Security Advisories
- Release notes
- CHANGELOG.md

## Contact

For security concerns: <security@aidlc.dev>
For general questions: <team@aidlc.dev>

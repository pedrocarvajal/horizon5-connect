# Security

## Overview

The security of horizon-connect is a top priority.
This framework handles sensitive financial data, exchange API credentials, and executes trading operations that involve real monetary value.
We take all security vulnerabilities seriously.

## Reporting Security Issues

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them responsibly by emailing us directly. This allows us to assess and address the vulnerability before it can be exploited.

### How to Report

Send an email with details of the vulnerability to: **hello@horizon5.tech**

You should receive a response within 48 hours. If for some reason you do not, please follow up to ensure we received your original message.

Please include the following information (as much as you can provide) to help us better understand the nature and scope of the possible issue:

- Type of issue (e.g. credential exposure, injection attack, authentication bypass, etc.)
- Full paths of source file(s) related to the manifestation of the issue
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it

This information will help us triage your report more quickly.

## Security Considerations for Users

When using horizon-connect, please be aware of the following security considerations:

### API Credentials

- **Never commit API keys or secrets to version control**
- Store credentials in environment variables or secure configuration files
- Use `.gitignore` to exclude sensitive configuration files
- Rotate API keys regularly
- Use read-only API keys when possible, and trading keys only when necessary

### Database Security

- Secure your MongoDB instance with authentication
- Use network isolation and firewall rules
- Encrypt sensitive data at rest
- Regularly backup your trading data

### Gateway Connections

- Always use secure connections (HTTPS/WSS) to exchange APIs
- Validate SSL/TLS certificates
- Be cautious of man-in-the-middle attacks
- Monitor unusual API activity

### Production Environments

- Isolate production trading systems from development environments
- Implement proper access controls
- Log all trading activities
- Monitor system logs for suspicious behavior
- Test strategies thoroughly in backtesting before live trading

### Dependencies

- Keep all dependencies up to date
- Regularly review security advisories for dependencies
- Use `uv` or `pip` to audit package vulnerabilities

We will provide security updates for the latest stable version.
Please ensure you are running the most recent version of horizon-connect.

## Security Best Practices

1. **Principle of Least Privilege**: Grant only the minimum API permissions required
2. **Defense in Depth**: Implement multiple layers of security controls
3. **Regular Audits**: Periodically review your configuration and logs
4. **Incident Response**: Have a plan for responding to security incidents
5. **Data Protection**: Encrypt sensitive data both in transit and at rest

## Disclosure Policy

When we receive a security vulnerability report, we will:

1. Confirm receipt of your vulnerability report
2. Assess the vulnerability and determine its impact
3. Develop and test a fix
4. Release a patched version
5. Publicly disclose the vulnerability details after the patch is available

We aim to handle all security issues promptly and transparently while protecting users during the disclosure process.

## Preferred Language

We prefer all communications to be in English.

## Comments

We appreciate your efforts to responsibly disclose your findings and will make every effort to acknowledge your contributions.

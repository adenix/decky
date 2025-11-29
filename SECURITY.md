# Security Policy

## Security Model

Decky is designed as a **personal automation tool** for trusted users on their own systems. It is **not** a sandboxed environment and is **not** designed to protect against malicious configuration files.

### Core Principles

1. **User Trust Boundary**: Configuration files are treated as trusted code
1. **Full User Permissions**: Commands execute with the same permissions as the user running Decky
1. **No Sandboxing**: Decky does not restrict what commands can do
1. **Personal Use**: Designed for single-user, personal systems

## Threat Model

### In Scope

Decky aims to protect against:

- **Accidental misuse**: Clear documentation and validation to prevent configuration errors
- **Service crashes**: Graceful error handling to maintain stability
- **Resource exhaustion**: Reasonable limits on configuration file sizes and resource usage

### Out of Scope

Decky does **not** protect against:

- **Malicious configuration files**: If you load a malicious config, it can execute arbitrary commands
- **Privilege escalation**: Decky runs as your user and can do anything you can do
- **Multi-user scenarios**: Not designed for shared systems with untrusted users

## Configuration File Security

### Command Execution

The `command` action type executes shell commands with `shell=True`. This is **intentional** and provides maximum flexibility for automation.

**Example of what this means**:

```yaml
# This config can delete files
buttons:
  1:
    label: "Clean Temp"
    action:
      type: command
      command: "rm -rf /tmp/*"
```

### Safe Configuration Practices

#### ✅ DO

- **Keep configs in version control** (git)
- **Review configs before loading them**
- **Use absolute paths for critical commands**
- **Test configs in a safe environment first**
- **Keep backups of working configurations**

#### ❌ DON'T

- **Run configs from strangers without review**
- **Download and run configs automatically**
- **Use Decky on shared/multi-user systems with untrusted users**
- **Store credentials in plain text in configs** (use environment variables instead)

## Reporting Vulnerabilities

### What to Report

Please report security issues related to:

- **Unexpected privilege escalation**
- **Crashes that could be exploited**
- **Information disclosure vulnerabilities**
- **Dependencies with known CVEs**

### What Not to Report

These are **expected behavior** and not vulnerabilities:

- Configuration files can execute arbitrary commands (by design)
- Decky runs with user permissions (intended)
- Command injection via config files (feature, not bug)

### How to Report

For legitimate security concerns, please:

1. **Do not** open a public GitHub issue
1. Email the maintainer at: anicholas@netflix.com
1. Include:
   - Description of the issue
   - Steps to reproduce
   - Expected vs actual behavior
   - Your assessment of impact

## Secure Configuration Examples

### Using Environment Variables for Secrets

Instead of hardcoding credentials:

```yaml
# ❌ BAD - Credentials in config
action:
  type: command
  command: "curl -H 'Authorization: Bearer secret_token_here' api.example.com"

# ✅ GOOD - Use environment variables
action:
  type: command
  command: "curl -H \"Authorization: Bearer $MY_API_TOKEN\" api.example.com"
```

Then set the variable in your environment:

```bash
# In ~/.bashrc or systemd service file
export MY_API_TOKEN="your_secret_token"
```

### Restricting Command Execution

If you want to share a config but limit what it can do, document the required commands:

```yaml
# config-requirements.txt
# This configuration requires these commands to be available:
# - firefox
# - gnome-terminal
# - pactl (for volume control)
#
# Review all commands before use!
```

## Dependency Security

Decky uses automated tools to monitor dependencies:

- **Bandit**: Static security analysis for Python code
- **Safety**: Checks dependencies against CVE databases
- **Dependabot**: Automated dependency updates (GitHub)

Run security checks locally:

```bash
make security
```

## Updates and Patches

- Security patches are released as soon as possible
- Version bumps follow semantic versioning
- Check the [CHANGELOG](CHANGELOG.md) for security-related updates
- Subscribe to releases on GitHub for notifications

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security.html)
- [Systemd Service Security](https://www.freedesktop.org/software/systemd/man/systemd.exec.html#Security)

______________________________________________________________________

**Remember**: With great power comes great responsibility. Decky gives you powerful automation capabilities - use them wisely! 🛡️

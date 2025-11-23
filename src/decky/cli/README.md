# Decky CLI

The unified command-line interface for the Decky Stream Deck controller.

## Overview

The `decky` command provides both:

1. **Daemon mode**: The actual service that runs in the background
1. **Management commands**: Control the systemd service and configurations

## Architecture

```
bin/decky                 # Shell wrapper (gets installed to /usr/local/bin)
    ↓
src/decky/cli.py         # Main CLI implementation
    ↓
  ├── DeckyCLI class     # Service management logic
  └── main()             # Argument parsing and routing
```

## Commands

### Running the Daemon

```bash
# Run directly (what systemd does)
decky run ~/.decky/configs/kde.yaml
decky run config.yaml --log-level DEBUG
```

### Service Management

```bash
# Start/stop the systemd service
decky start
decky stop
decky restart
decky status

# View logs
decky logs                    # Follow logs (like tail -f)
decky logs --no-follow -n 100 # Show last 100 lines

# Enable/disable auto-start
decky enable   # Start on login
decky disable  # Don't start on login
```

### Configuration Management

```bash
# List available configurations
decky config list

# Edit configurations
decky config edit            # Edit default.yaml
decky config edit work       # Edit work.yaml

# Switch active configuration
decky config use kde         # Switch to kde.yaml

# Validate configuration
decky config validate        # Validate default.yaml
decky config validate myconf # Validate myconf.yaml
```

## Implementation Details

### Python CLI Design

The CLI uses Python's `argparse` with subcommands:

- Main parser with subparsers for each command
- Nested subparsers for `config` subcommands
- Follows Unix conventions (exit codes, help text)

### Service Integration

Service management uses `systemctl --user` commands:

- No root/sudo required (user services)
- Integrates with journald for logging
- Updates systemd service file for config switching

### Configuration Validation

The validator checks:

- YAML syntax validity
- Required sections (pages)
- Button number ranges
- Action type definitions
- Style references

### Best Practices

1. **Exit Codes**: Returns proper exit codes (0 for success, 1 for failure)
1. **User Feedback**: Clear messages for all operations
1. **Error Handling**: Graceful failures with helpful error messages
1. **Help Text**: Comprehensive help with examples
1. **No Root Required**: All operations run as user

## Comparison with Old Architecture

### Before (Two Separate Tools)

1. **decky** (bash script): Just ran the Python daemon
1. **deckyctl** (bash script): Service management only

### After (Unified CLI)

1. **decky** (Python): Both daemon and management in one tool
   - Cleaner interface
   - Better error handling
   - Proper argument parsing
   - Easier to extend
   - Consistent behavior

## Installation

The `bin/decky` script should be installed to `/usr/local/bin/`:

```bash
sudo cp bin/decky /usr/local/bin/
sudo chmod +x /usr/local/bin/decky
```

The systemd service file should reference:

```
ExecStart=/usr/local/bin/decky run %h/.decky/configs/kde.yaml
```

## Future Enhancements

Potential additions to the CLI:

- `decky test` - Test Stream Deck connection
- `decky backup` - Backup configurations
- `decky import/export` - Share configurations
- `decky update` - Self-update functionality
- `decky doctor` - Diagnose issues

"""Main CLI entry point for pyngding."""
import argparse
import sys
from pathlib import Path


def hash_password(args):
    """Hash a password using PBKDF2."""
    from pyngding.core.crypto import create_pbkdf2_hash

    password = args.password
    hash_str = create_pbkdf2_hash(password)
    print(hash_str)
    return 0


def init_config(args):
    """Initialize a sample config.ini file."""
    config_path = Path(args.path)
    if config_path.exists():
        print(f"Error: {config_path} already exists", file=sys.stderr)
        return 1

    sample_config = """[pyngding]
bind_host = 0.0.0.0
bind_port = 8080
db_path = /data/pyngding.sqlite
scan_targets = 192.168.1.0/24
scan_interval_seconds = 60
ping_timeout_seconds = 1
ping_count = 1
max_workers = 32
target_cap = 4096

[auth]
enabled = false
username = admin
password_hash =
realm = pyngding
"""

    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(sample_config)
    print(f"Created sample config at {config_path}")
    print("Note: Set auth.password_hash using 'pyngding hash-password' command")
    return 0


def oui_import(args):
    """Import OUI vendor file."""
    from pyngding.data.vendor import OUILookup

    file_path = Path(args.path)
    if not file_path.exists():
        print(f"Error: {file_path} does not exist", file=sys.stderr)
        return 1

    lookup = OUILookup()
    count = lookup.load(str(file_path))

    if count > 0:
        print(f"Successfully loaded {count} OUI entries from {file_path}")
        print("OUI lookup is now available. Enable it in Settings (oui_lookup_enabled = true)")
        print(f"Set oui_file_path = {file_path} in Settings")
    else:
        print(f"Warning: No OUI entries loaded from {file_path}", file=sys.stderr)
        print("Check file format. Supported formats:")
        print("  - 'AA-BB-CC   (hex)  Vendor Name'")
        print("  - 'AABBCC,Vendor Name' (CSV)")
        print("  - 'AABBCC Vendor Name'")
        return 1

    return 0


def serve(args):
    """Start the pyngding server."""
    import logging
    import signal

    from pyngding.core.config import load_config
    from pyngding.core.db import init_db
    from pyngding.core.logger import configure_logging, get_logger
    from pyngding.scanning.scheduler import ScanScheduler
    from pyngding.web.web import create_app

    # Configure logging before anything else
    configure_logging(level=logging.INFO)
    logger = get_logger()

    try:
        # Check if config file exists, create default if not
        config_path = Path(args.config)
        if not config_path.exists():
            print(f"Config file not found at {config_path}")
            print("Creating default config.ini in current directory...")
            # Create a simple namespace for init_config
            init_args = type('Args', (), {'path': str(config_path)})()
            init_config(init_args)
            print(f"Default config created at {config_path}")
            print("Please edit config.ini to set your scan targets and other settings.")
            print("For authentication, run: pyngding hash-password 'your-password'")

        config = load_config(args.config)
        print(f"Starting pyngding server on {config.bind_host}:{config.bind_port}")
        print(f"Database: {config.db_path}")
        print(f"Scan targets: {config.scan_targets}")
        print(f"Auth enabled: {config.auth_enabled}")

        # Initialize database
        init_db(config.db_path)
        print("Database initialized")

        # Start scan scheduler
        scheduler = ScanScheduler(config, config.db_path)
        scheduler.start()
        print("Scan scheduler started")

        # Create and run web app
        app = create_app(config, config.db_path, scheduler)

        def shutdown_handler(signum, frame):
            print("\nShutting down...")
            scheduler.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, shutdown_handler)
        signal.signal(signal.SIGTERM, shutdown_handler)

        print(f"Web server starting on http://{config.bind_host}:{config.bind_port}")
        app.run(host=config.bind_host, port=config.bind_port, quiet=True)

        return 0
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1


def cli():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(prog='pyngding', description='Lightweight LAN presence scanner')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # serve command
    serve_parser = subparsers.add_parser('serve', help='Start the pyngding server')
    serve_parser.add_argument('--config', type=str, default='config.ini',
                             help='Path to config.ini file (default: config.ini)')
    serve_parser.set_defaults(func=serve)

    # hash-password command
    hash_parser = subparsers.add_parser('hash-password', help='Hash a password for config.ini')
    hash_parser.add_argument('password', type=str, help='Password to hash')
    hash_parser.set_defaults(func=hash_password)

    # init-config command
    init_parser = subparsers.add_parser('init-config', help='Create a sample config.ini file')
    init_parser.add_argument('--path', type=str, default='config.ini',
                            help='Path where to create config.ini (default: config.ini)')
    init_parser.set_defaults(func=init_config)

    # oui subcommands
    oui_parser = subparsers.add_parser('oui', help='OUI vendor lookup commands')
    oui_subparsers = oui_parser.add_subparsers(dest='oui_command', help='OUI commands')

    oui_import_parser = oui_subparsers.add_parser('import', help='Import OUI vendor file')
    oui_import_parser.add_argument('--path', type=str, required=True,
                                   help='Path to OUI file (txt or csv)')
    oui_import_parser.set_defaults(func=oui_import)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == '__main__':
    sys.exit(cli())


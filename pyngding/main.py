"""Main CLI entry point for pyngding."""
import argparse
import sys
from pathlib import Path


def hash_password(args):
    """Hash a password using PBKDF2."""
    import hashlib
    import secrets
    
    password = args.password
    salt = secrets.token_bytes(16)
    hash_value = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    hash_str = f"pbkdf2:sha256:100000:{salt.hex()}:{hash_value.hex()}"
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


def serve(args):
    """Start the pyngding server."""
    # This will be implemented in later steps
    print("Starting pyngding server...")
    print(f"Config: {args.config}")
    print("(Not yet implemented - will be added in Step 2)")
    return 0


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
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    return args.func(args)


if __name__ == '__main__':
    sys.exit(cli())


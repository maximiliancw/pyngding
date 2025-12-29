"""Configuration loading with config.ini and environment variable overrides."""
import configparser
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class Config:
    """Main configuration dataclass."""
    # Critical settings (file-only)
    bind_host: str = "0.0.0.0"
    bind_port: int = 8080
    db_path: str = "/data/pyngding.sqlite"
    scan_targets: str = ""
    scan_interval_seconds: int = 60
    ping_timeout_seconds: float = 1.0
    ping_count: int = 1
    max_workers: int = 32
    target_cap: int = 4096
    
    # Auth settings
    auth_enabled: bool = False
    auth_username: str = "admin"
    auth_password_hash: str = ""
    auth_realm: str = "pyngding"


def load_config(config_path: Optional[str] = None) -> Config:
    """Load configuration from config.ini file with environment variable overrides.
    
    Environment variables use prefix PYNGDING_ and are uppercase.
    Example: PYNGDING_BIND_PORT=9000 overrides bind_port.
    """
    config = Config()
    
    # Load from file if it exists
    if config_path is None:
        config_path = os.getenv("PYNGDING_CONFIG", "config.ini")
    
    config_file = Path(config_path)
    if config_file.exists():
        parser = configparser.ConfigParser()
        parser.read(config_file)
        
        # Load [pyngding] section
        if "pyngding" in parser:
            section = parser["pyngding"]
            config.bind_host = section.get("bind_host", config.bind_host)
            config.bind_port = section.getint("bind_port", config.bind_port)
            config.db_path = section.get("db_path", config.db_path)
            config.scan_targets = section.get("scan_targets", config.scan_targets)
            config.scan_interval_seconds = section.getint("scan_interval_seconds", config.scan_interval_seconds)
            config.ping_timeout_seconds = section.getfloat("ping_timeout_seconds", config.ping_timeout_seconds)
            config.ping_count = section.getint("ping_count", config.ping_count)
            config.max_workers = section.getint("max_workers", config.max_workers)
            config.target_cap = section.getint("target_cap", config.target_cap)
        
        # Load [auth] section
        if "auth" in parser:
            section = parser["auth"]
            config.auth_enabled = section.getboolean("enabled", config.auth_enabled)
            config.auth_username = section.get("username", config.auth_username)
            config.auth_password_hash = section.get("password_hash", config.auth_password_hash)
            config.auth_realm = section.get("realm", config.auth_realm)
    
    # Apply environment variable overrides
    env_prefix = "PYNGDING_"
    for key, value in os.environ.items():
        if not key.startswith(env_prefix):
            continue
        
        # Remove prefix and convert to lowercase
        config_key = key[len(env_prefix):].lower()
        
        # Map environment variable names to config attributes
        if config_key == "bind_host":
            config.bind_host = value
        elif config_key == "bind_port":
            config.bind_port = int(value)
        elif config_key == "db_path":
            config.db_path = value
        elif config_key == "scan_targets":
            config.scan_targets = value
        elif config_key == "scan_interval_seconds":
            config.scan_interval_seconds = int(value)
        elif config_key == "ping_timeout_seconds":
            config.ping_timeout_seconds = float(value)
        elif config_key == "ping_count":
            config.ping_count = int(value)
        elif config_key == "max_workers":
            config.max_workers = int(value)
        elif config_key == "target_cap":
            config.target_cap = int(value)
        elif config_key == "auth_enabled":
            config.auth_enabled = value.lower() in ("true", "1", "yes", "on")
        elif config_key == "auth_username":
            config.auth_username = value
        elif config_key == "auth_password_hash":
            config.auth_password_hash = value
        elif config_key == "auth_realm":
            config.auth_realm = value
    
    # Validate max_workers cap
    if config.max_workers > 64:
        config.max_workers = 64
    
    return config


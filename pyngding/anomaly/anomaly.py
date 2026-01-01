"""Anomaly detection scoring API (placeholder for v1.1).

This module provides a placeholder API for anomaly detection features
that will be implemented in future versions.

In v1, this module exists only as a stub to prepare the architecture
for future enhancements.
"""


def score_host_anomaly(ip: str, mac: str = None, hostname: str = None,
                       dns_activity: dict = None, scan_history: list = None) -> float:
    """Score a host for anomalous behavior.

    Args:
        ip: Host IP address
        mac: MAC address (optional)
        hostname: Hostname (optional)
        dns_activity: DNS activity summary (optional)
        scan_history: Recent scan observations (optional)

    Returns:
        Anomaly score between 0.0 (normal) and 1.0 (highly anomalous)

    Note: This is a placeholder. Returns 0.0 in v1.
    """
    # Placeholder implementation
    return 0.0


def detect_anomalies(db_path: str, threshold: float = 0.7) -> list:
    """Detect hosts with anomalous behavior.

    Args:
        db_path: Database path
        threshold: Minimum anomaly score to report

    Returns:
        List of dicts with host info and anomaly scores

    Note: This is a placeholder. Returns empty list in v1.
    """
    # Placeholder implementation
    return []


def get_anomaly_explanation(ip: str, score: float) -> str:
    """Get human-readable explanation for an anomaly score.

    Args:
        ip: Host IP address
        score: Anomaly score

    Returns:
        Explanation string

    Note: This is a placeholder. Returns empty string in v1.
    """
    # Placeholder implementation
    return ""


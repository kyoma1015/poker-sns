"""Classify credential-bearing local startup logs without printing any log text."""
import sys
from pathlib import Path


def classify_startup(text: str) -> str:
    text = text.lower()
    # Return only fixed allowlisted labels. Never echo unknown lines, URLs,
    # token fragments, exception details or matched substrings.
    patterns = [
        ('REGISTRY_RATE_LIMIT', ('toomanyrequests', 'pull rate limit', '429 too many')),
        ('REGISTRY_AUTH_FAILURE', ('failed to fetch oauth token', 'failed to authorize')),
        ('REGISTRY_FETCH_FAILURE', ('failed to resolve reference', 'failed to pull image')),
        ('LOCAL_PORT_CONFLICT', ('port is already allocated', 'address already in use')),
        ('CONTAINER_HEALTH_FAILURE', ('unhealthy', 'health check failed', 'failed health check')),
        ('NETWORK_FAILURE', ('connection reset by peer', 'i/o timeout', 'tls handshake timeout', 'econnreset', 'enotfound', 'eai_again')),
    ]
    for label, fragments in patterns:
        if any(fragment in text for fragment in fragments):
            return label
    return 'UNCLASSIFIED_STARTUP_FAILURE'


def main():
    try:
        # Startup logs are private, bounded diagnostics; never stream them to CI.
        with Path(sys.argv[1]).open('rb') as source:
            data = source.read(2 * 1024 * 1024 + 1)
        label = 'STARTUP_LOG_TOO_LARGE' if len(data) > 2 * 1024 * 1024 else classify_startup(data.decode('utf-8', errors='replace'))
    except (OSError, IndexError):
        label = 'STARTUP_LOG_UNAVAILABLE'
    print('Isolated startup diagnostic: ' + label)


if __name__ == '__main__':
    main()

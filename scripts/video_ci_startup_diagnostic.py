"""Classify credential-bearing local startup logs without printing any log text."""
import sys
from pathlib import Path


def classify_startup(text: str) -> str:
    text = text.lower()
    # Return only fixed allowlisted labels. Never echo unknown lines, URLs,
    # token fragments, exception details or matched substrings.
    patterns = [
        ('CLI_PACKAGE_UNAVAILABLE', ('no matching version found', 'etarget', 'e404', '404 not found')),
        ('CLI_CONFIG_ERROR', ('invalid service', 'invalid argument', 'cannot unmarshal', 'failed to decode', 'error decoding', 'failed to parse config', 'invalid config', 'unknown flag', 'unsupported config', 'failed to load config')),
        ('DOCKER_DAEMON_UNAVAILABLE', ('cannot connect to the docker daemon', 'docker daemon is not running', 'permission denied')),
        ('IMAGE_MANIFEST_UNAVAILABLE', ('manifest unknown', 'no matching manifest', 'manifest not found')),
        ('CLI_NPM_FAILURE', ('npm error', 'npm err!', 'ebadengine')),
        ('IMAGE_DOWNLOAD_FAILURE', ('failed to pull docker image', 'failed to copy', 'received unexpected http status', 'error pulling image', 'failed to download', 'unexpected eof')),
        ('CLI_STACK_WORKDIR_MISSING', ('no such file or directory', 'cannot find', 'could not find')),

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
    # Only constant vocabulary labels; no raw log, substring, path or URL.
    if label == 'UNCLASSIFIED_STARTUP_FAILURE':
        words = ('docker', 'container', 'image', 'pull', 'registry', 'database', 'postgres', 'migration', 'config', 'version', 'unsupported', 'invalid', 'argument', 'exclude', 'network', 'timeout', 'error', 'failed', 'denied', 'unavailable', 'rate', 'limit', 'service', 'parse', 'schema', 'initializing', 'starting', 'stopping', 'cancelled', 'killed', 'memory', 'disk', 'space', 'certificate', 'permission', 'connect', 'password', 'token', 'npm', 'npx', 'supabase', 'api', 'health', 'port')
        if 'data' in locals():
            text = data.decode('utf-8', errors='replace').lower()
            print('Startup fixed signals: ' + ','.join(word for word in words if word in text))


if __name__ == '__main__':
    main()

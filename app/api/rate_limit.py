from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.configurations import EnvConfigs

_settings = EnvConfigs()


def _client_key(request: Request) -> str:
    """When TRUST_FORWARDED_FOR is on (Railway/ALB/ingress in front of us), the
    direct peer is always the proxy — get_remote_address would lump every client
    into one bucket. Read the leftmost X-Forwarded-For entry instead, which is
    the original client per RFC 7239. Falls back to the peer IP."""
    if _settings.TRUST_FORWARDED_FOR:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return get_remote_address(request)


# Per-IP RPM cap on write endpoints. Setting RATE_LIMIT_PER_MINUTE=0 disables.
# headers_enabled adds X-RateLimit-{Limit,Remaining,Reset} on every response and
# Retry-After on 429 — clients use these to back off correctly (RFC 6585).
limiter = Limiter(
    key_func=_client_key,
    enabled=_settings.RATE_LIMIT_PER_MINUTE > 0,
    headers_enabled=True,
)

RATE_LIMIT = f"{_settings.RATE_LIMIT_PER_MINUTE}/minute"
MAX_BATCH_SIZE = _settings.MAX_BATCH_SIZE

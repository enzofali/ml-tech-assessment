from slowapi import Limiter
from slowapi.util import get_remote_address

from app.configurations import EnvConfigs

_settings = EnvConfigs()

# Per-IP RPM cap on write endpoints. Setting RATE_LIMIT_PER_MINUTE=0 disables.
# headers_enabled adds X-RateLimit-{Limit,Remaining,Reset} on every response and
# Retry-After on 429 — clients use these to back off correctly (RFC 6585).
limiter = Limiter(
    key_func=get_remote_address,
    enabled=_settings.RATE_LIMIT_PER_MINUTE > 0,
    headers_enabled=True,
)

RATE_LIMIT = f"{_settings.RATE_LIMIT_PER_MINUTE}/minute"
MAX_BATCH_SIZE = _settings.MAX_BATCH_SIZE

import os

# Disable IP rate limiting during tests; covered by dedicated tests.
os.environ.setdefault("RATE_LIMIT_PER_MINUTE", "0")
os.environ.setdefault("MAX_BATCH_SIZE", "50")
os.environ.setdefault("LLM_API_KEY", "test-key")

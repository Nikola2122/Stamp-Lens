import json

import redis

from processingjob.constants import PROCESSING_JOB_REDIS_URL


class RedisProgressPublisher:
    def __init__(self, client: redis.Redis | None = None):
        self._client = client or redis.Redis.from_url(
            PROCESSING_JOB_REDIS_URL,
            decode_responses=True,
        )

    def publish(self, channel: str, message: dict | str) -> int:
        payload = json.dumps(message) if isinstance(message, dict) else message
        try:
            return self._client.publish(channel, payload)
        except redis.RedisError:
            # Progress delivery is best-effort; Redis/SSE must never own the
            # lifecycle of the persisted processing job.
            return 0

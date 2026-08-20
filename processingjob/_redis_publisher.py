import redis

from processingjob.constants import PROCESSING_JOB_REDIS_URL


class RedisProgressPublisher:
    def __init__(self, client: redis.Redis | None = None):
        self._client = client or redis.Redis.from_url(
            PROCESSING_JOB_REDIS_URL,
            decode_responses=True,
        )

    def publish(self, channel: str, message: str) -> int:
        return self._client.publish(channel, message)

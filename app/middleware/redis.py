import redis
import os

redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = int(os.getenv("REDIS_PORT", 6379))
print("Redis URI: ", redis_host, ":", redis_port)
pool = redis.ConnectionPool(host=redis_host, port=redis_port, db=0)
redis_client = redis.Redis(connection_pool=pool)

def get_cache(key: str):
    return redis_client.get(key)


def set_cache(key: str, value: str):
    return redis_client.set(key, value)


def delete_cache(key: str):
    return redis_client.delete(key)

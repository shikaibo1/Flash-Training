import redis
from config import get_config

# 全局Redis客户端（单例）
_redis_client = None

def get_redis_client(env: str = "dev") -> redis.Redis:
    """获取Redis客户端（单例模式）"""
    global _redis_client
    if _redis_client is None:
        config = get_config(env)
        _redis_client = redis.Redis(
            host=config.REDIS_HOST,
            port=config.REDIS_PORT,
            db=config.REDIS_DB,
            password=config.REDIS_PASSWORD,
            decode_responses=True,  # 自动解码为字符串
            socket_timeout=config.API_TIMEOUT
        )
    return _redis_client

def check_and_set_cache(key: str, value: str, expire: int) -> bool:
    """
    检查缓存是否存在，不存在则设置（原子操作，避免并发重复）
    Returns: True-缓存未存在并设置成功，False-缓存已存在
    """
    client = get_redis_client()
    # Redis SETNX + EXPIRE 原子操作
    return client.set(key, value, ex=expire, nx=True)
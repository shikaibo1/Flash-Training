import docker
from docker.errors import DockerException
from config import get_config

# 全局Docker客户端（单例）
_docker_client = None

def get_docker_client() -> docker.DockerClient:
    """获取Docker客户端（单例模式）"""
    global _docker_client
    if _docker_client is None:
        try:
            _docker_client = docker.from_env()
            # 检查Docker服务是否可用
            _docker_client.ping()
        except DockerException as e:
            raise RuntimeError(f"Docker服务不可用：{str(e)}")
    return _docker_client

def clean_docker_container(container_id: str):
    """强制清理Docker容器（避免资源泄漏）"""
    client = get_docker_client()
    try:
        container = client.containers.get(container_id)
        container.remove(force=True)
    except DockerException:
        # 容器已不存在则忽略
        pass
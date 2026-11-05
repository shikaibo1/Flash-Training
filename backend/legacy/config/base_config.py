# 基础配置（通用参数，与AI无关）
class BaseConfig:
    # Redis配置
    REDIS_HOST = "localhost"
    REDIS_PORT = 6379
    REDIS_DB = 0
    REDIS_PASSWORD = ""  # 生产环境需配置密码
    TOPIC_CACHE_EXPIRE = 86400 * 7  # 话题缓存7天

    # Docker沙箱配置（代码执行）
    DOCKER_MEM_LIMIT = "64m"  # 内存限制
    DOCKER_CPU_QUOTA = 50000  # CPU限制（50%）
    DOCKER_TIMEOUT = 10  # 执行超时时间（秒）
    DOCKER_IMAGE = "python:3.10-slim"  # 轻量Python镜像

    # 通用超时配置（适配移动端即时性）
    API_TIMEOUT = 5  # 所有外部API调用超时时间

    # 数据文件路径
    ATOMIC_SKILLS_PATH = "data/atomic_skills.json"
    SKILL_LIBRARY_PATH = "data/skill_library.json"
    UNIFIED_PRACTICE_RECORDS_PATH = "data/unified_practice_records.json"
    # 旧路径现在指向新文件以保持向后兼容性
    MICRO_SKILLS_PATH = "data/atomic_skills.json"  # 指向新原子技能文件
    PRACTICE_SKILLS_PATH = "data/skill_library.json"  # 指向新技能库文件
    PRACTICE_RECORDS_PATH = "data/practice_records.json"  # 保留，可能有历史数据
    USER_SKILL_PROFILES_PATH = "data/user_skill_profiles.json"

    # 默认配置
    DEFAULT_DIFFICULTY = 1
    DEFAULT_JOB_TYPE = "Python开发"
    DEFAULT_SPEECH_SCENE = "职场"
    DEFAULT_SPEECH_DURATION = "3分钟"
    MAX_QUESTION_ATTEMPTS = 3
    INPUT_MIN_LENGTH = 5


# 开发环境配置（继承基础配置，可覆盖）
class DevConfig(BaseConfig):
    DEBUG = True


# 生产环境配置
class ProdConfig(BaseConfig):
    DEBUG = False
    REDIS_HOST = "redis-server"  # 生产环境Redis地址
    DOCKER_IMAGE = "python:3.10-slim"  # 保持一致


# 配置映射（方便切换环境）
config_map = {
    "dev": DevConfig,
    "prod": ProdConfig
}

# 获取当前环境配置（默认开发环境）
def get_config(env: str = "dev"):
    return config_map.get(env, DevConfig)

# 导出默认配置实例
config = get_config()

# 保持向后兼容性的默认配置字典
DEFAULT_CONFIG = {
    "default_difficulty": config.DEFAULT_DIFFICULTY,
    "default_job_type": config.DEFAULT_JOB_TYPE,
    "default_speech_scene": config.DEFAULT_SPEECH_SCENE,
    "default_speech_duration": config.DEFAULT_SPEECH_DURATION,
    "default_speech_difficulty": "入门",  # 为speech模块添加的默认难度
    "max_question_attempts": config.MAX_QUESTION_ATTEMPTS,
    "input_min_length": config.INPUT_MIN_LENGTH
}
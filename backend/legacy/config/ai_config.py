# config/ai_config.py
class AIConfig:
    # 原有OpenAI配置（可保留，也可删除）
    OPENAI_API_KEY = "你的OpenAI API密钥"
    OPENAI_MODEL = "gpt-3.5-turbo"
    OPENAI_TEMPERATURE = 0.8
    OPENAI_MAX_TOKENS = 200

    # 新增豆包AI配置（作为默认值，优先被.env覆盖）
    DOUBAO_MODEL_ID = "doubao-pro"
    DOUBAO_API_KEY = ""  # 空值，强制从.env读取
    DOUBAO_BASE_URL = "https://www.doubao.com/api/v1"
    DOUBAO_TIMEOUT = 60

    # 原有反馈/难度配置（不变）
    FEEDBACK_MAX_LENGTH = 100
    DIFFICULTY_UP_THRESHOLD = 3
    DIFFICULTY_DOWN_THRESHOLD = 2
    DIFFICULTY_MAX_LEVEL = 5
    DIFFICULTY_MIN_LEVEL = 1


ai_config = AIConfig()
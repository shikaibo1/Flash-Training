import os
import asyncio
from typing import List, Dict, Optional
from dotenv import load_dotenv
from openai import OpenAI

# 加载.env 文件（优先读取环境变量）
load_dotenv()

class HelloDoubaoLLM:
    """
    适配火山方舟平台的豆包 AI 客户端（修复 choices 属性错误）
    保留闪练 AI 原有调用风格，兼容文本生成场景
    """
    def __init__(self):
        """初始化：读取火山方舟的配置"""
        # 从.env 加载配置（关键：ARK_API_KEY 对应你的火山方舟 API Key）
        self.api_key = os.getenv("ARK_API_KEY")
        self.base_url = os.getenv("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
        self.model = os.getenv("ARK_MODEL_ID", "doubao-seed-1-8-251228")
        self.timeout = int(os.getenv("DOUBAO_TIMEOUT", 60))

        # 校验必要参数
        if not self.api_key:
            raise ValueError("请在.env 文件中配置 ARK_API_KEY（火山方舟的 API Key）！")

        # 初始化火山方舟的 OpenAI 兼容客户端
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout
        )

    def think(self, messages: List[Dict[str, str]], temperature: float = 0.8, max_length: int = 2000, is_json: bool = False) -> Optional[str]:
        """
        适配闪练 AI 的文本生成调用（演讲话题/代码反馈）
        :param messages: 消息列表 [{"role": "user/system", "content": "..."}]
        :param temperature: 生成温度
        :param max_length: 最大长度，None 表示不限制
        :param is_json: 是否为 JSON 响应，如果是则跳过话题处理逻辑
        :return: 豆包生成的单条文本内容（None 表示调用失败）
        """
        try:
            # 转换为火山方舟要求的入参格式
            ark_input = []
            for msg in messages:
                content = [{"type": "input_text", "text": msg["content"]}]
                ark_input.append({
                    "role": msg["role"],
                    "content": content
                })

            # 调用火山方舟的豆包 API
            response = self.client.responses.create(
                model=self.model,
                input=ark_input,
                temperature=temperature
            )

            # ========== 关键修正：精准提取单条演讲话题 ==========
            full_response = ""
            # 1. 提取 output 中的 message 内容（豆包返回的核心文本）
            if hasattr(response, "output") and len(response.output) > 0:
                # 找到 role=assistant 的 message 项
                for output_item in response.output:
                    if getattr(output_item, "role", "") == "assistant" and hasattr(output_item, "content"):
                        # 提取 output_text 的 text 内容
                        for content_item in output_item.content:
                            if content_item.type == "output_text":
                                full_response = content_item.text.strip()
                                break
                            
            # 2. 处理多条话题（随机选 1 条，适配闪练 AI 单条需求）
            if full_response and "\n" in full_response and not is_json:
                import random
                # 按换行拆分，过滤空行，随机选 1 条
                topics = [t.strip() for t in full_response.split("\n") if
                          t.strip() and t.strip().startswith(("1.", "2.", "3."))]
                # 去掉序号（如"1. "）
                clean_topics = [t.split(". ", 1)[1] if ". " in t else t for t in topics]
                if clean_topics:
                    full_response = random.choice(clean_topics)  # 随机选 1 条
                else:
                    full_response = full_response.split("\n")[0].strip()  # 兜底取第一条

            # 3. 内容清洗（去换行、限长度）
            if full_response:
                if not is_json:
                    full_response = full_response.replace("\n", "").strip()
                if max_length is not None:
                    full_response = full_response[:max_length]

            return full_response

        except Exception as e:
            print(f"❌ 豆包 AI 调用失败：{str(e)}")
            return None
    
    async def think_async(self, messages: List[Dict[str, str]], temperature: float = 0.8, max_length: int = 2000, is_json: bool = False) -> Optional[str]:
        """
        异步版本的 think 方法，避免阻塞事件循环
        :param messages: 消息列表 [{"role": "user/system", "content": "..."}]
        :param temperature: 生成温度
        :param max_length: 最大长度，None 表示不限制
        :param is_json: 是否为 JSON 响应，如果是则跳过话题处理逻辑
        :return: 豆包生成的单条文本内容（None 表示调用失败）
        """
        loop = asyncio.get_event_loop()
        # 在线程池中执行同步的 think 方法，避免阻塞事件循环
        return await loop.run_in_executor(
            None, 
            lambda: self.think(messages, temperature, max_length, is_json)
        )
            
# 单例客户端（闪练 AI 全局复用）
doubao_llm_client = None
def get_doubao_client() -> HelloDoubaoLLM:
    """获取火山方舟豆包单例客户端"""
    global doubao_llm_client
    if doubao_llm_client is None:
        doubao_llm_client = HelloDoubaoLLM()
    return doubao_llm_client

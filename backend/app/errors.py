class AppError(Exception):
    def __init__(self, message: str, status: int = 400, code: str = "invalid_request"):
        self.message, self.status, self.code = message, status, code
        super().__init__(message)


class AIError(AppError):
    def __init__(self, message="AI 服务暂时不可用，请检查后端模型配置后重试。", status=502,
                 code="ai_unavailable"):
        super().__init__(message, status, code)

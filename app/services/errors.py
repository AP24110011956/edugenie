class AIServiceError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        code: str = "ai_service_error",
        status_code: int = 502,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


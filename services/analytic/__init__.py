from services.logging import LoggingService


class AnalyticService:
    def __init__(self) -> None:
        self._log = LoggingService()
        self._log.setup("analytic_service")

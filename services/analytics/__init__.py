from services.logging import LoggingService


class AnalyticsService:
    def __init__(self) -> None:
        self._log = LoggingService()
        self._log.setup("analytics_service")

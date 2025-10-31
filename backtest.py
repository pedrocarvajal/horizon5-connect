import datetime
from typing import Any

from configs.assets import ASSETS
from configs.timezone import TIMEZONE
from services.backtest import BacktestService


class Backtest(BacktestService):
    def __init__(
        self,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)

    def run(self) -> None:
        super().run()


if __name__ == "__main__":
    to_date = datetime.datetime.now(tz=TIMEZONE)
    from_date = to_date - datetime.timedelta(days=365 * 1)

    backtest = Backtest(
        asset=ASSETS["btcusdt"],
        from_date=from_date,
        to_date=to_date,
        # restore_data=True,
    )

    backtest.run()

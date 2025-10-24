import datetime
import sys
from pathlib import Path
from time import sleep
from typing import Any

import polars
import requests

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from structs.candlestick import CandlestickStruct

from services.logging import LoggingService


class DownloadCandlestickData:
    def __init__(
        self,
        logging: LoggingService,
        symbol: str = "BTCUSDT",
        timeframe: str = "1m",
        start_time: int | None = None,
        end_time: int | None = None,
    ) -> None:
        self.symbol = symbol
        self.timeframe = timeframe
        self.start_time = start_time
        self.end_time = end_time

        self.log = logging
        self.log.setup(__name__)

    @classmethod
    def create(
        cls,
        symbol: str = "BTCUSDT",
        timeframe: str = "1m",
        start_time: int | None = None,
        end_time: int | None = None,
    ) -> "DownloadCandlestickData":
        logging_service = LoggingService()

        return cls(
            logging=logging_service,
            symbol=symbol,
            timeframe=timeframe,
            start_time=start_time,
            end_time=end_time,
        )

    def _parse(self, data: list[Any]) -> list[CandlestickStruct]:
        response = []

        for item in data:
            try:
                candlestick = CandlestickModel()
                candlestick.kline_open_time = item[0]
                candlestick.open_price = float(item[1])
                candlestick.high_price = float(item[2])
                candlestick.low_price = float(item[3])
                candlestick.close_price = float(item[4])
                candlestick.volume = float(item[5])
                candlestick.kline_close_time = item[6]
                candlestick.quote_asset_volume = float(item[7])
                candlestick.number_of_trades = int(item[8])
                candlestick.taker_buy_base_asset_volume = float(item[9])
                candlestick.taker_buy_quote_asset_volume = float(item[10])

                response.append(candlestick.to_dict())

            except Exception as e:
                self.log.error(f"Error parsing candlestick data: {e}")
                self.log.debug(data)
                self.log.debug(item)
                raise e

        return response

    def _get_progress(self, start_time: int, end_time: int) -> float:
        starting_time = self.start_time
        current_time = start_time
        destination_time = end_time

        traveled_time = current_time - starting_time
        total_time = destination_time - starting_time

        return float((traveled_time / total_time) * 100)

    def download(
        self,
        start_time: int | None = None,
    ) -> None:
        response = []

        if start_time is None:
            start_time = self.start_time

        while True:
            if start_time > self.end_time:
                self.log.info("Download finished successfully.")
                break

            candlesticks = polars.DataFrame()
            base_url = "https://api.binance.com/api/v3/klines"
            progress = self._get_progress(start_time=start_time, end_time=self.end_time)

            self.log.info(
                f"Downloading {self.symbol} {self.timeframe}"
                f" | Starting time: {datetime.datetime.fromtimestamp(self.start_time / 1000, tz=datetime.UTC).strftime('%Y-%m-%d %H:%M:%S')}"
                f" | Current time: {datetime.datetime.fromtimestamp(start_time / 1000, tz=datetime.UTC).strftime('%Y-%m-%d %H:%M:%S')}"
                f" | Ending time: {datetime.datetime.fromtimestamp(self.end_time / 1000, tz=datetime.UTC).strftime('%Y-%m-%d %H:%M:%S')}"
                f" | Progress: {progress:.2f}%"
            )

            try:
                params = {
                    "symbol": self.symbol,
                    "interval": self.timeframe,
                    "startTime": start_time,
                    "endTime": self.end_time,
                    "limit": 1000,
                }

                response = requests.get(base_url, params=params)
                data = response.json()
                candlesticks = self._parse(data=data)

            except requests.exceptions.RequestException as e:
                self.log.error(f"Error downloading candlestick data: {e}")
                raise e

            last_item = candlesticks[-1]
            last_time = int(last_item["kline_close_time"].timestamp())
            file_name = f"{last_time}.parquet"
            file_path = (
                Path("storage")
                / "binance"
                / "candlesticks"
                / self.symbol
                / self.timeframe
                / file_name
            )

            file_path.parent.mkdir(parents=True, exist_ok=True)

            candlesticks = polars.DataFrame(candlesticks)
            candlesticks.write_parquet(file_path, compression="zstd")

            start_time = last_time * 1000
            sleep(0.25)


if __name__ == "__main__":
    start_time = datetime.datetime.fromisoformat("2019-10-01 00:00:00")
    end_time = datetime.datetime.now(datetime.UTC)

    download_candlestick_data = DownloadCandlestickData.create(
        symbol="BTCUSDT",
        timeframe="1m",
        start_time=int(start_time.timestamp()) * 1000,
        end_time=int(end_time.timestamp()) * 1000,
    )

    download_candlestick_data.download()

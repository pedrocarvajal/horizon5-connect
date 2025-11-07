from datetime import datetime

from assets.btcusdt import BTCUSDT
from configs.timezone import TIMEZONE
from services.ticks import TicksService
from strategies.rebounds_off_supports.components.sr_component import SRComponent


def test_sr_component() -> None:
    print("=" * 80)
    print("Testing SRComponent")
    print("=" * 80)

    asset = BTCUSDT()

    from_date = datetime(2020, 11, 7, tzinfo=TIMEZONE)
    to_date = datetime(2020, 11, 14, tzinfo=TIMEZONE)

    print(f"\nLoading prices from {from_date} to {to_date}...")

    ticks_service = TicksService()
    ticks_service.setup(
        asset=asset, from_date=from_date, to_date=to_date, restore_ticks=False
    )

    prices = ticks_service.ticks
    print(f"Loaded {len(prices)} prices")

    if len(prices) == 0:
        print("No prices loaded. Exiting.")
        return

    print(f"First price: {prices[0].date} - {prices[0].price}")
    print(f"Last price: {prices[-1].date} - {prices[-1].price}")

    print("\n" + "=" * 80)
    print("Computing SR Levels...")
    print("=" * 80)

    sr_component = SRComponent()
    sr_component.compute(prices)

    levels = sr_component.levels

    print(f"\nFound {len(levels)} support/resistance levels:\n")

    for i, level in enumerate(levels, 1):
        print(f"\nLevel #{i}")
        print(f"  Price:         {level.level}")
        print(f"  Density Score: {level.density_score}")
        print(f"  Touch Count:   {level.touch_count}")
        print(f"  Recency Score: {level.recency_score}")
        print(f"  Quality:       {level.quality} {'⭐' if level.quality > 0.6 else ''}")

    print("\n" + "=" * 80)
    print("High Quality Levels (quality > 0.5)")
    print("=" * 80)

    high_quality = [l for l in levels if l.quality > 0.5]
    high_quality_sorted = sorted(high_quality, key=lambda x: x.quality, reverse=True)

    if high_quality_sorted:
        for i, level in enumerate(high_quality_sorted, 1):
            print(
                f"{i}. {level.level} | Quality: {level.quality} | "
                f"Density: {level.density_score} | Touches: {level.touch_count} | "
                f"Recency: {level.recency_score}"
            )
    else:
        print("No high quality levels found.")

    print("\n" + "=" * 80)
    print("Verification Complete")
    print("=" * 80)

    price_range = max(p.price for p in prices) - min(p.price for p in prices)
    print(f"\nPrice range in data: {price_range}")
    print(f"Number of unique prices: {len(set(p.price for p in prices))}")

    print("\nProperty Verification:")
    for level in levels[:3]:
        print(f"\n  Level: {level.level}")
        print(f"    - density_score is float: {isinstance(level.density_score, float)}")
        print(f"    - touch_count is int: {isinstance(level.touch_count, int)}")
        print(
            f"    - recency_score is float in [0,1]: {isinstance(level.recency_score, float) and 0 <= level.recency_score <= 1}"
        )
        print(
            f"    - quality is float in [0,1]: {isinstance(level.quality, float) and 0 <= level.quality <= 1}"
        )


if __name__ == "__main__":
    test_sr_component()

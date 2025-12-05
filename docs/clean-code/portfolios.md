# Portfolio Guidelines

Guide on how a portfolio should be structured and organized.

- A portfolio must follow class guidelines. See [classes.md](./classes.md)
- A portfolio must pass all linters using `make run-linter-checks FILE=path/to/file.py` or `./scripts/make/run-linter-checks.sh --file path/to/file.py`
- A portfolio extends `PortfolioService` which implements `PortfolioInterface`

# 1.0 Portfolio Structure

```python
class Portfolio(PortfolioService):
    # Class-level property: _id (required)
    _id = "portfolio-name"

    # Constructor __init__
    def __init__(self) -> None:
        super().__init__()
        self.setup_assets()

    # Required method: setup_assets
    def setup_assets(self) -> None:
        self._assets = [
            # Asset classes
        ]
```

# 2.0 Required Properties

| Property | Type  | Description                              |
| -------- | ----- | ---------------------------------------- |
| `_id`    | `str` | Unique portfolio identifier (kebab-case) |

# 3.0 Required Methods

## 3.1 `__init__`

Must call `super().__init__()` and then `self.setup_assets()`.

```python
def __init__(self) -> None:
    super().__init__()
    self.setup_assets()
```

## 3.2 `setup_assets`

Configures the `_assets` list with asset classes (not instances).

```python
def setup_assets(self) -> None:
    self._assets = [
        BTCUSDTAsset,
        ETHUSDTAsset,
    ]
```

# 4.0 Available Properties (from PortfolioInterface)

These getters are defined in `PortfolioInterface` and implemented in `PortfolioService`:

| Property | Type                         | Description                   |
| -------- | ---------------------------- | ----------------------------- |
| `id`     | `str`                        | Returns `_id` value           |
| `assets` | `List[Type[AssetInterface]]` | Returns list of asset classes |

**Note**: Do not define new public getters/setters directly in your portfolio class. If you need new public accessors, they should be added to `PortfolioInterface` first.

# 5.0 File Location

Portfolios are located in `portfolios/` directory:

- `portfolios/low-risk.py` � Low-risk portfolio
- `portfolios/high-risk.py` � High-risk portfolio

# 6.0 Example

```python
from assets.btcusdt import Asset as BTCUSDTAsset
from services.portfolio import PortfolioService


class Portfolio(PortfolioService):
    _id = "low-risk"

    def __init__(self) -> None:
        super().__init__()
        self.setup_assets()

    def setup_assets(self) -> None:
        self._assets = [
            BTCUSDTAsset,
        ]
```

# 7.0 Anti-patterns to Avoid

- **Instantiating assets**: Use asset classes, not instances (`BTCUSDTAsset`, not `BTCUSDTAsset()`)
- **Missing `super().__init__()`**: Always call parent constructor
- **Business logic in portfolio**: Portfolios only configure assets. Trading logic belongs in strategies.
- **Direct `_assets` assignment in `__init__`**: Use `setup_assets()` method for clarity

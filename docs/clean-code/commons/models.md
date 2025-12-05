# Model Guidelines

Guide on how models should be structured and organized.

- A model must pass all linters configured in the project using `make run-linter-checks FILE=path/to/file.py` or directly `./scripts/make/run-linter-checks.sh --file path/to/file.py`
- A model must be organized based on guideline 1.0
- For code style and formatting, review guideline 2.0
- Models define typed data structures using Pydantic, replacing `Dict[str, Any]` with type-safe objects

# Guidelines

## 1.0 Model Hierarchy

```python
class NameModel(BaseModel):
    # Model configuration (if needed)
    # {Blank separator line}

    # Fields with type annotations
    # {Blank separator line}

    # Constructor __init__ (if custom initialization needed)
    # {Blank separator line}

    # Public methods (sorted alphabetically)
    # {Blank separator line}

    # Private methods (sorted alphabetically)
    # {Blank separator line}

    # Computed fields / Properties
    # {Blank separator line}
```

## 2.0 How to Define Models

### 2.1 Basic Model

```python
from pydantic import BaseModel, Field

class TickModel(BaseModel):
    price: float = Field(default=0.0, ge=0)
    bid_price: float = Field(default=0.0, ge=0)
    ask_price: float = Field(default=0.0, ge=0)
    date: datetime.datetime
```

### 2.2 Model with Configuration

Use `model_config` for special configurations:

```python
from pydantic import BaseModel, ConfigDict

class OrderModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    portfolio: Optional[PortfolioInterface] = None
```

### 2.3 Computed Fields

Use `@computed_field` with `@property` for derived values:

```python
from pydantic import BaseModel, computed_field

class OrderModel(BaseModel):
    price: float = 0.0
    close_price: float = 0.0
    volume: float = 0.0

    @computed_field
    @property
    def profit(self) -> float:
        return (self.close_price - self.price) * self.volume
```

### 2.4 Field Validation

Use `Field` for constraints and defaults:

```python
from pydantic import Field

class TickModel(BaseModel):
    price: float = Field(default=0.0, ge=0)
    is_simulated: bool = Field(
        default=True,
        description="True if tick is from backtest/simulation",
    )
```

### 2.5 Serialization Methods

Include `to_dict()` and `to_json()` for conversion:

```python
def to_dict(self) -> Dict[str, Any]:
    return self.model_dump()

def to_json(self) -> str:
    return self.model_dump_json()
```

### 2.6 Imports

```python
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, computed_field
```

### 2.7 File Naming

Each model should be in its own file under `models/` directory:

- `models/tick.py` ’ `TickModel`
- `models/order.py` ’ `OrderModel`
- `models/snapshot.py` ’ `SnapshotModel`

## 3.0 When to Create a Model

Create a model instead of using `Dict[str, Any]` when:

- Data structure is used in multiple places
- Type safety is required for function parameters or return values
- Validation rules need to be enforced
- Computed/derived fields are needed

Avoid:

```python
def process_tick(tick: Dict[str, Any]) -> None:
    price = tick["price"]
```

Preferred:

```python
def process_tick(tick: TickModel) -> None:
    price = tick.price
```

## 4.0 Anti-patterns to Avoid

- **Dict[str, Any]**: Create typed models instead of untyped dictionaries.
- **Missing type hints**: All fields must have explicit type annotations.
- **Business logic in models**: Keep models focused on data. Complex logic belongs in services.
- **Overly complex models**: If a model has too many fields, consider splitting into smaller models.
- **Missing defaults**: Use `Field(default=...)` for optional fields with sensible defaults.

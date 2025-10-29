# Code Smells

Code smells are warning signs in your code that indicate potential problems. Learn to recognize these patterns and refactor when needed.

## Code Smells Within Classes

### Comments

There's a fine line between comments that illuminate and comments that obscure. Are the comments necessary? Do they explain "why" and not "what"? Can you refactor the code so the comments aren't required?

Instead of:

```python
x = 10
```

Do:

```python
max_daily_trades = 10
```

See: `docs/clean-code/no-comments.md`

### Long Method

All other things being equal, a shorter method is easier to read, understand, and troubleshoot. Refactor long methods into smaller methods if you can.

Avoid:

```python
def process_order():
    pass
```

Prefer:

```python
def process_order() -> bool:
    if not validate_order_parameters():
        return False
    if not check_risk_limits():
        return False
    if not execute_order():
        return False
    return True

def validate_order_parameters() -> bool:
    pass

def check_risk_limits() -> bool:
    pass

def execute_order() -> bool:
    pass
```

### Long Parameter List

The more parameters a method has, the more complex it is. Limit the number of parameters you need in a given method, or use a dataclass to combine the parameters.

Avoid:

```python
def open_order(symbol: str, volume: float, entry: float, sl: float, tp: float, magic: int, comment: str) -> bool:
    pass
```

Prefer:

```python
from dataclasses import dataclass

@dataclass
class OrderParams:
    symbol: str
    volume: float
    entry_price: float
    stop_loss: float
    take_profit: float
    magic_number: int
    comment: str

def open_order(params: OrderParams) -> bool:
    pass
```

### Duplicated Code

Duplicated code is the bane of software development. Stamp out duplication whenever possible. You should always be on the lookout for more subtle cases of near-duplication too. Don't Repeat Yourself!

Avoid:

```python
def calculate_buy_profit() -> float:
    profit = entry_price - current_price
    profit = profit * volume * point_value
    return profit

def calculate_sell_profit() -> float:
    profit = current_price - entry_price
    profit = profit * volume * point_value
    return profit
```

Prefer:

```python
from enum import Enum

class OrderType(Enum):
    BUY = 1
    SELL = 2

def calculate_profit(order_type: OrderType) -> float:
    price_diff = (entry_price - current_price
                  if order_type == OrderType.BUY
                  else current_price - entry_price)
    return price_diff * volume * point_value
```

### Conditional Complexity

Watch out for large conditional logic blocks, particularly blocks that tend to grow larger or change significantly over time. Consider alternative object-oriented approaches such as decorator, strategy, or state.

Avoid:

```python
def process_signal():
    if strategy_type == "BREAKOUT":
        if price > resistance:
            if volume > threshold:
                if time > sessisetup:
                    pass
    elif strategy_type == "MEAN_REVERSION":
        pass
```

Prefer:

```python
from abc import ABC, abstractmethod

class Strategy(ABC):
    @abstractmethod
    def process_signal(self) -> None:
        pass

class BreakoutStrategy(Strategy):
    def process_signal(self) -> None:
        if not self._is_valid_breakout():
            return
        self._execute_breakout_logic()

    def _is_valid_breakout(self) -> bool:
        pass

    def _execute_breakout_logic(self) -> None:
        pass
```

### Combinatorial Explosion

You have lots of code that does almost the same thing but with tiny variations in data or behavior. This can be difficult to refactor – perhaps using generics or templates.

Avoid:

```python
def calculate_ema_5() -> float:
    pass

def calculate_ema_10() -> float:
    pass

def calculate_ema_20() -> float:
    pass

def calculate_ema_50() -> float:
    pass

def calculate_ema_100() -> float:
    pass

def calculate_ema_200() -> float:
    pass
```

Prefer:

```python
def calculate_ema(period: int) -> float:
    pass
```

### Type Embedded in Name

Avoid placing types in method names; it's not only redundant, but it forces you to change the name if the type changes.

Avoid:

```python
price_float = 100.5
count_int = 10
symbol_str = "EURUSD"
```

Prefer:

```python
price = 100.5
count = 10
symbol = "EURUSD"
```

### Uncommunicative Name

Does the name of the method succinctly describe what that method does? Could you read the method's name to another developer and have them explain to you what it does? If not, rename it or rewrite it.

Avoid:

```python
def do_it():
    pass

def process():
    pass

def handle():
    pass

def calc() -> int:
    pass
```

Prefer:

```python
def calculate_position_size() -> float:
    pass

def validate_order_parameters() -> bool:
    pass

def execute_trailing_stop() -> None:
    pass

def get_total_open_orders() -> int:
    pass
```

### Inconsistent Names

Pick a set of standard terminology and stick to it throughout your methods. For example, if you have `open()`, you should probably have `close()`.

Avoid:

```python
def open_order():
    pass

def terminate_position():
    pass

def get_price():
    pass

def retrieve_volume():
    pass

def fetch_symbol():
    pass
```

Prefer:

```python
def open_order():
    pass

def close_order():
    pass

def get_price():
    pass

def get_volume():
    pass

def get_symbol():
    pass
```

### Dead Code

Ruthlessly delete code that isn't being used. That's why we have source control systems!

Avoid:

```python
def calculate_profit():
    pass
```

### Speculative Generality

Write code to solve today's problems, and worry about tomorrow's problems when they actually materialize. Everyone loses in the "what if..." school of design. You Aren't Gonna Need It.

Avoid:

```python
from abc import ABC, abstractmethod

class AbstractStrategyFactoryBuilderInterface(ABC):
    @abstractmethod
    def create_strategy(self):
        pass

    @abstractmethod
    def register_strategy_type(self):
        pass

    @abstractmethod
    def configure_strategy_parameters(self):
        pass
```

Prefer:

```python
class Strategy:
    def execute(self):
        pass
```

### Oddball Solution

There should only be one way of solving the same problem in your code. If you find an oddball solution, it could be a case of poorly duplicated code – or it could be an argument for the adapter model, if you really need multiple solutions to the same problem.

Avoid:

```python
profit1 = (close_price - open_price) * volume

profit2 = volume * (close_price - open_price)

profit3 = close_price * volume - open_price * volume
```

Prefer:

```python
def calculate_profit(open_price: float, close_price: float, volume: float) -> float:
    return (close_price - open_price) * volume
```

### Temporary Field

Watch out for objects that contain a lot of optional or unnecessary fields. If you're passing an object as a parameter to a method, make sure that you're using all of it and not cherry-picking single fields.

Avoid:

```python
from dataclasses import dataclass

@dataclass
class OrderData:
    symbol: str
    volume: float
    price: float
    magic_number: int
    temp_calculation: str
    intermediate_value: float
    is_processing: bool
```

Prefer:

```python
from dataclasses import dataclass

@dataclass
class OrderData:
    symbol: str
    volume: float
    price: float
    magic_number: int
```

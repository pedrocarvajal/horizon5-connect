# Class Organization

This guide applies when auditing a class during code review.
Follow these organization principles.

## Rules

- Do not modify method signatures or logic
- Reorganize methods vertically into clear sections
- Use proper naming conventions (underscore prefix for private members)

## Recommended Section Order

Organize class members vertically in the following order:

1. **Constants** - Define immutable class-level configuration values
2. **Properties** - Declare all instance variables grouped by purpose:
   - Interface-required properties (contract obligations from parent/interface)
   - Class properties (internal state and business logic attributes)
   - Dependencies (injected services, repositories, external collaborators)
3. **Constructor** - Initialize instance with `__init__` method
4. **Public Methods** - Define external API and public interface
5. **Private Methods** - Implement internal logic (prefix with `_`):
   - Core private methods for business logic
   - Helper methods for formatting/parsing/conversion
6. **Getters/Setters** - Expose properties using `@property` decorator, with each setter immediately following its corresponding getter

## Section Separators

Use visual separators to clearly mark each section in the class:

```python
# ───────────────────────────────────────────────────────────
# SECTION NAME
# ───────────────────────────────────────────────────────────
```

Standard section names:

- `CONSTANTS` - Class-level constants (immutable configuration values)
- `PROPERTIES` - Instance variables organized in three subsections:
  - `# Interface-required` - Properties required by parent class or interface contract
  - `# Class properties` - Internal business logic attributes and state variables
  - `# Dependencies` - External services, repositories, or helper classes injected via constructor
- `CONSTRUCTOR` - The `__init__` method for initialization
- `PUBLIC METHODS` - Public-facing methods exposed to external consumers
- `PRIVATE METHODS` - Internal methods (prefixed with `_`) organized in two subsections:
  - Regular private methods for core internal logic
  - `# Helpers` - Utility/formatting methods (use inline comment to separate)
- `GETTERS` - Property accessors using `@property` decorator. Each setter must immediately follow its corresponding getter (grouped by property)

## Access Modifiers

- Public: Methods and variables used externally (no prefix)
- Private: Internal methods and variables (prefix with `_`)

## Function Naming Conventions

Functions should always start with a verb that clearly describes the action they perform.

**Common Verbs for Regular Methods:**

- `calculate_` - Perform calculations (e.g., `calculate_total`, `calculate_profit`)
- `get_` - Retrieve or fetch data (e.g., `get_price`, `get_order`)
- `set_` - Assign or update values (e.g., `set_stop_loss`, `set_status`)
- `update_` - Modify existing data (e.g., `update_position`, `update_state`)
- `validate_` - Check correctness (e.g., `validate_price`, `validate_order`)
- `create_` - Instantiate new objects (e.g., `create_order`, `create_snapshot`)
- `delete_` - Remove data (e.g., `delete_order`, `delete_record`)
- `process_` - Execute business logic (e.g., `process_order`, `process_data`)
- `handle_` - Respond to events (e.g., `handle_tick`, `handle_error`)
- `check_` - Verify conditions (e.g., `check_status`, `check_availability`)
- `is_` - Boolean checks (e.g., `is_valid`, `is_open`)
- `has_` - Existence checks (e.g., `has_position`, `has_permission`)

**Common Verbs for Helper Methods:**

- `_format_` - Transform data presentation (e.g., `_format_timestamp`, `_format_price`)
- `_parse_` - Extract or convert data (e.g., `_parse_response`, `_parse_config`)
- `_convert_` - Transform data types (e.g., `_convert_to_float`, `_convert_timestamp`)
- `_extract_` - Pull specific data (e.g., `_extract_price`, `_extract_metadata`)
- `_build_` - Construct complex objects (e.g., `_build_request`, `_build_payload`)
- `_normalize_` - Standardize data (e.g., `_normalize_symbol`, `_normalize_price`)
- `_sanitize_` - Clean data (e.g., `_sanitize_input`, `_sanitize_string`)

## Example Structure

```python
class OrderProcessor(ProcessorInterface):
    # ───────────────────────────────────────────────────────────
    # CONSTANTS
    # ───────────────────────────────────────────────────────────
    MAX_RETRY_ATTEMPTS: int = 3
    TIMEOUT_SECONDS: int = 30
    DEFAULT_PRIORITY: int = 1

    # ───────────────────────────────────────────────────────────
    # PROPERTIES
    # ───────────────────────────────────────────────────────────

    # Interface-required
    _id: str
    _status: str
    _results: List[ResultModel]

    # Class properties
    _retry_count: int
    _timeout: int
    _priority: int
    _queue: List[OrderModel]
    _processed_items: List[OrderModel]
    _failed_items: List[OrderModel]
    _last_execution_time: Optional[datetime]
    _configuration: Dict[str, Any]
    _is_active: bool

    # Dependencies
    _logger: LoggerService
    _validator: ValidationService
    _repository: DataRepository

    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(
        self,
        id: str,
        logger: LoggerService,
        validator: ValidationService,
        repository: DataRepository,
        timeout: int = TIMEOUT_SECONDS
    ) -> None:
        self._id = id
        self._timeout = timeout
        self._logger = logger
        self._validator = validator
        self._repository = repository
        self._queue = []
        self._results = []
        self._is_active = False

    # ───────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ───────────────────────────────────────────────────────────
    def process(self) -> bool:
        pass

    def add_to_queue(self, order: OrderModel) -> None:
        pass

    def clear_queue(self) -> None:
        pass

    # ───────────────────────────────────────────────────────────
    # PRIVATE METHODS
    # ───────────────────────────────────────────────────────────
    def _validate_order(self, order: OrderModel) -> bool:
        pass

    def _execute_processing(self) -> None:
        pass

    def _handle_failure(self, error: Exception) -> None:
        pass

    # Helpers
    def _format_result(self, data: dict) -> ResultModel:
        pass

    def _sanitize_input(self, value: str) -> str:
        pass

    # ───────────────────────────────────────────────────────────
    # GETTERS
    # ───────────────────────────────────────────────────────────
    @property
    def id(self) -> str:
        return self._id

    @property
    def status(self) -> str:
        return self._status

    @status.setter
    def status(self, value: str) -> None:
        self._status = value

    @property
    def results(self) -> List[ResultModel]:
        return self._results
```

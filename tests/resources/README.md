# WeConnect MCP Resource Tests

Comprehensive test suite for MCP server resources.

## Test Structure

```
tests/resources/
├── test_list_vehicles.py          # 7 tests - data://list_vehicles resource
└── test_vehicle_state.py          # 15 tests - data://state/{vehicle_id} resource
```

**Note**: Shared fixtures (`adapter`, `mcp_server`, `mcp_client`) are defined in `tests/conftest.py` (central location for all test categories).

**Total**: 22 tests ✅

## Resource Coverage

Both MCP resources are fully tested:

### 1. **data://list_vehicles**
- ✅ Returns list of all available vehicles
- ✅ Each vehicle contains: VIN, name, model, license_plate
- ✅ JSON serialization and deserialization
- ✅ Data consistency with adapter

### 2. **data://state/{vehicle_id}** (Template)
- ✅ Returns complete vehicle state for given identifier
- ✅ Supports VIN, name, or license plate as identifier
- ✅ VehicleModel serialization
- ✅ Data consistency with adapter
- ✅ Error handling for invalid vehicles

## Test Patterns

Each resource test file follows a consistent structure:

### 1. Resource Registration Tests
```python
@pytest.mark.asyncio
async def test_resource_is_registered(mcp_server):
    """Test that resource is registered in the MCP server"""
    all_resources = await mcp_server.get_resources()
    assert "data://resource_uri" in all_resources.keys()
```

### 2. Resource Data Retrieval Tests
```python
@pytest.mark.asyncio
async def test_resource_returns_data(mcp_server):
    """Test that resource returns valid data"""
    resource = await mcp_server.get_resource("data://resource_uri")
    data = await resource.read()
    assert data is not None
```

### 3. Client Access Tests
```python
@pytest.mark.asyncio
async def test_resource_via_client(mcp_client):
    """Test that MCP client can read resource"""
    result = await mcp_client.read_resource("data://resource_uri")
    assert result is not None
```

### 4. Data Structure Tests
```python
@pytest.mark.asyncio
async def test_resource_has_required_fields(mcp_client):
    """Test that resource data has all required fields"""
    result = await mcp_client.read_resource("data://resource_uri")
    data = json.loads(result[0].text)
    assert "field_name" in data
```

### 5. Data Consistency Tests
```python
@pytest.mark.asyncio
async def test_resource_matches_adapter(adapter, mcp_client):
    """Test that resource data matches adapter output"""
    adapter_data = adapter.method()
    result = await mcp_client.read_resource("data://resource_uri")
    resource_data = parse(result[0].text)
    assert resource_data == adapter_data
```

### 6. Identifier Resolution Tests (for templates)
```python
@pytest.mark.parametrize("identifier", get_identifiers())
@pytest.mark.asyncio
async def test_resource_all_identifiers(mcp_client, identifier):
    """Test that resource works with VIN, name, or license plate"""
    result = await mcp_client.read_resource(f"data://state/{identifier}")
    assert result is not None
```

### 7. Error Handling Tests
```python
@pytest.mark.asyncio
async def test_resource_invalid_input(mcp_server):
    """Test that resource handles invalid input gracefully"""
    resource = await mcp_server.get_resource_template("data://resource/{id}")
    result = await resource.read({"id": "INVALID"})
    assert result is None  # or appropriate error handling
```

## Running Tests

### Run all resource tests:
```bash
pytest tests/resources/ -v
```

### Run specific resource test:
```bash
pytest tests/resources/test_list_vehicles.py -v
pytest tests/resources/test_vehicle_state.py -v
```

### Run with coverage:
```bash
pytest tests/resources/ --cov=weconnect_mcp --cov-report=term-missing
```

## Test Data

Tests use `TestAdapter` with 2 mock vehicles:

1. **ID.7 Tourer** (Electric)
   - VIN: `WVWZZZED4SE003938`
   - Name: `ID7 Tourer`
   - License: `M-XY 5678`

2. **Transporter 7** (Combustion)
   - VIN: `WV2ZZZSTZNH009136`
   - Name: `T7`
   - License: `M-AB 1234`

All identifiers (VIN, name, license plate) work interchangeably for `data://state/{vehicle_id}`.

## Shared Fixtures (from tests/conftest.py)

**Note**: Fixtures are centrally defined in `tests/conftest.py` and automatically available to all test files.

### `adapter` Fixture
Provides a `TestAdapter` instance with mock vehicles:
```python
def test_example(adapter):
    vehicles = adapter.list_vehicles()
```

### `mcp_server` Fixture
Provides a FastMCP server instance for resource registration tests:
```python
@pytest.mark.asyncio
async def test_example(mcp_server):
    resource = await mcp_server.get_resource("data://list_vehicles")
```

### `mcp_client` Fixture
Provides a connected MCP client for resource access testing:
```python
@pytest.mark.asyncio
async def test_example(mcp_client):
    result = await mcp_client.read_resource("data://list_vehicles")
```

## What's Tested

✅ **Resource Registration**
- Resources registered in MCP server
- Resource templates registered with correct URIs
- get_resources() and get_resource_templates() work

✅ **Data Retrieval**
- Resources return valid data
- Resource templates work with parameters
- JSON serialization correct
- VehicleModel deserialization correct

✅ **MCP Client Integration**
- Client can read resources
- Client receives proper response format
- Text field contains expected data

✅ **Data Structure**
- All required fields present
- Correct data types
- Valid JSON format
- Proper Pydantic model validation

✅ **Identifier Resolution** (for state template)
- Resolution by VIN
- Resolution by vehicle name
- Resolution by license plate
- Parametrized tests for all identifier types

✅ **Data Consistency**
- Resource data matches adapter output
- Same data for both retrieval methods
- Consistency across both vehicles

✅ **Error Handling**
- Invalid vehicle IDs return None
- Graceful handling of non-existent vehicles
- No exceptions for invalid input

## Resource Implementation

Resources are defined in `mcp_server.py`:

```python
@mcp.resource("data://list_vehicles")
def list_vehicles_resource() -> List[Dict[str, Any]]:
    """Return list of vehicles."""
    vehicles = adapter.list_vehicles()
    return [v.model_dump() for v in vehicles]

@mcp.resource("data://state/{vehicle_id}")
def get_vehicle_state_resource(vehicle_id: str) -> Optional[BaseModel]:
    """Return vehicle state or None if not found."""
    vehicle = adapter.get_vehicle(vehicle_id)
    if vehicle is None:
        return None
    return vehicle
```

## Comparison with Tools and Commands

| Feature | Tools | Commands | Resources |
|---------|-------|----------|-----------|
| Count | 24 tools | 10 commands | 2 resources |
| Tests | 76 tests | 71 tests | 22 tests |
| Access | MCP tool calls | MCP tool calls | MCP resource reads |
| Pattern | Function calls | Vehicle control | Data retrieval |
| Returns | JSON data | Success/error | Raw data/models |
| Caching | No | No | Possible |

## Key Differences

**Resources vs Tools**:
- **Resources**: Read-only data access, can be cached, use URIs
- **Tools**: Active operations, can modify state, use function calls
- Resources are for data retrieval, tools are for operations

**Resource Templates**:
- Use `{parameter}` syntax in URI
- Accept parameters via `read({"param": "value"})`
- Enable dynamic resource URIs

## Related Documentation

- Main test suite: `tests/README.md`
- Tool tests: `tests/tools/` (76 tests)
- Command tests: `tests/commands/` (71 tests)
- Test data: `tests/test_data.py`
- Mock adapter: `tests/test_adapter.py`

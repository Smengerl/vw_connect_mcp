# Contributing

Thanks for your interest in contributing to the WeConnect MCP Server! Contributions are welcome and appreciated. To make collaboration smooth, please follow these guidelines.

## How to Contribute

1. **Fork the repository** and create a feature branch
2. **Make your changes** in a clearly named branch (e.g., `fix/cache-invalidation` or `feat/add-climate-control`)
3. **Write clear commit messages** following [Conventional Commits](https://www.conventionalcommits.org/)
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation changes
   - `test:` for test additions/modifications
   - `refactor:` for code refactoring
4. **Add tests** for your changes - all 208+ tests must pass
5. **Update documentation** if you change APIs or add features
6. **Open a Pull Request** with a clear description of what you changed and why

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/weconnect_mvp.git
cd weconnect_mvp

# Run setup script
./scripts/setup.sh

# Configure with your VW credentials (for real API tests)
cp src/config.example.json src/config.json
nano src/config.json  # Add your credentials

# Run tests
./scripts/test.sh --skip-slow  # Fast mock tests only
```

## Testing Requirements

**All tests must pass before submitting a PR:**

```bash
# Run fast mock tests (197 tests, ~4 seconds)
./scripts/test.sh --skip-slow

# Run all tests including real API tests (215 tests)
./scripts/test.sh
```

**Test-Driven Development:**
1. Write test first (should fail)
2. Implement feature (test should pass)
3. Refactor code
4. Run all tests - must pass!

See [tests/README.md](tests/README.md) for detailed testing guidelines.

## Code Style

This project follows strict Python coding standards:

### Type Hints (Required)
```python
# ✅ Good
def get_vehicle(vehicle_id: str) -> Optional[VehicleModel]:
    ...

# ❌ Bad - missing type hints
def get_vehicle(vehicle_id):
    ...
```

### Naming Conventions
- **Files**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions/Methods**: `snake_case()`
- **Constants**: `UPPER_SNAKE_CASE`

### Import Order
1. Standard library imports
2. Third-party imports
3. Local application imports

### None Handling
VW API is unreliable - **always check for None**:

```python
# ✅ Good
battery = vehicle.battery
if battery is not None:
    level = battery.level.value if battery.level is not None else None

# ❌ Bad - will crash
level = vehicle.battery.level.value
```

### Documentation
- Use Google-style docstrings
- Document **why**, not **what** (code should be self-explanatory)
- Add examples for complex functions

## Project-Specific Guidelines

See [.github/copilot-instructions.md](.github/copilot-instructions.md) for:
- Architecture overview (Mixin pattern)
- Domain knowledge (vehicle types, caching, etc.)
- Common patterns and anti-patterns
- Development workflow

## Reporting Issues

- **Search existing issues** before opening a new one
- **Provide clear reproduction steps** with expected vs actual behavior
- **Include versions**: Python, OS, relevant libraries
- **Add logs** if applicable (use `--log-level DEBUG`)

## Security

⚠️ **Never commit sensitive data:**
- `src/config.json` with VW credentials
- `/tmp/tokenstore` or similar token files
- Log files with personal/vehicle data

## Questions?

- Check the [README.md](README.md) first
- Review [tests/README.md](tests/README.md) for testing help
- Open an issue for clarification

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
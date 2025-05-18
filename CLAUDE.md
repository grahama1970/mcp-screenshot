# Three-Layer Architecture for Claude MCP Tools

This document describes the **mandatory** three-layer architecture that all Claude MCP tools must follow. This architecture ensures proper separation of concerns, maintainability, testability, and extensibility of all tools in the Claude MCP ecosystem.

## Core Principles

The three-layer architecture is built on these fundamental principles:

1. **Separation of Concerns**: Each layer has a specific responsibility and should not take on responsibilities of other layers.
2. **Testability**: Each layer should be independently testable with clear inputs and outputs.
3. **Maintainability**: Changes to one layer should have minimal impact on other layers.
4. **Extensibility**: New features should be easy to add with minimal changes to existing code.
5. **Debuggability**: All functionality should be easily debuggable through pure Python functions.

## The Three Layers

```
┌─────────────────────────┐
│  MCP LAYER              │
│  MCP wrappers, servers  │
├─────────────────────────┤
│  CLI LAYER              │
│  CLI, rich formatting   │
├─────────────────────────┤
│  CORE LAYER             │
│  Pure business logic    │
└─────────────────────────┘
```

### 1. Core Layer

The core layer contains **pure business logic** with no dependencies on UI, CLI, or MCP integrations.

**Responsibilities:**
- Implementing the core functionality
- Processing inputs and generating outputs
- Managing data structures and algorithms
- Input validation and error handling for business rules
- Self-contained unit tests

**Key Requirements:**
- MUST be independent of presentation and integration concerns
- MUST have clear input/output interfaces for all functions
- MUST include self-validation tests in each module
- MUST be able to run in isolation without UI or network
- MUST provide comprehensive error handling

**Standard Files:**
- `core/__init__.py`: Exports core functionality
- `core/constants.py`: Configuration and constants
- `core/[domain].py`: Core business logic modules
- `core/utils.py`: Utility functions

### 2. CLI Layer

The CLI layer handles **user interaction** with rich formatting and a well-structured command-line interface.

**Responsibilities:**
- Providing a command-line interface
- Formatting outputs for human readability
- Input validation and parsing for CLI
- Handling user interactions and feedback
- Implementing rich tables and colorized output

**Key Requirements:**
- MUST only depend on the core layer, not the MCP layer
- MUST provide both human-readable and machine-readable outputs
- MUST handle CLI-specific error conditions
- MUST implement consistent formatting
- MUST include option for JSON output for all commands
- MUST provide schema output for all commands and parameters

**Standard Files:**
- `cli/__init__.py`: Exports CLI functionality
- `cli/cli.py`: Command-line interface
- `cli/formatters.py`: Output formatting utilities
- `cli/validators.py`: CLI input validation
- `cli/schemas.py`: Schema definitions and validation

### 3. MCP Layer

The MCP layer connects the tool to the **Model Context Protocol (MCP)** ecosystem for AI agents.

**Responsibilities:**
- Exposing core functionality through MCP
- Managing MCP server configuration
- Handling MCP-specific error responses
- Converting between MCP and core data structures
- Implementing health checks and schema endpoints

**Key Requirements:**
- MUST handle all MCP-specific concerns
- MUST format responses according to MCP standards
- MUST provide schema information for all functions
- MUST include health check endpoints
- MUST provide consistent error handling
- MUST be able to run as a standalone MCP server

**Standard Files:**
- `mcp/__init__.py`: Exports MCP functionality
- `mcp/mcp_tools.py`: MCP function definitions
- `mcp/mcp_server.py`: Server entry point
- `mcp/wrappers.py`: Core-to-MCP wrappers

## Directory Structure

All MCP tools MUST follow this exact directory structure:

```
tool_name/
├── __init__.py              # Main package exports
├── README.md                # Documentation
├── CLAUDE.md                # Three-layer architecture documentation
├── core/                    # Core Layer - Business Logic
│   ├── __init__.py          # Core exports
│   ├── constants.py         # Configuration
│   ├── [domain].py          # Core business logic
│   └── utils.py             # Utilities
├── cli/                     # CLI Layer - Command Line Interface
│   ├── __init__.py          # CLI exports
│   ├── cli.py               # Command-line interface
│   ├── formatters.py        # Rich formatting
│   ├── validators.py        # Parameter validation
│   └── schemas.py           # Schema definitions
├── mcp/                     # MCP Layer - Model Context Protocol
│   ├── __init__.py          # MCP exports
│   ├── mcp_tools.py         # MCP function definitions
│   ├── mcp_server.py        # Server entry point
│   └── wrappers.py          # MCP wrappers
└── tests/                   # Tests for all layers
    ├── __init__.py
    ├── test_core_*.py
    ├── test_cli_*.py
    └── test_mcp_*.py
```

## Dependency Rules

The following dependency rules MUST be strictly followed:

1. Core Layer:
   - ✅ CAN depend on Python standard library and external packages
   - ❌ CANNOT depend on the CLI layer
   - ❌ CANNOT depend on the MCP layer

2. CLI Layer:
   - ✅ CAN depend on the core layer
   - ✅ CAN depend on Python standard library and external packages
   - ❌ CANNOT depend on the MCP layer

3. MCP Layer:
   - ✅ CAN depend on the core layer
   - ✅ CAN depend on the CLI layer (but should be limited)
   - ✅ CAN depend on Python standard library and external packages

## CLI Requirements

All MCP tools MUST provide a CLI that meets these requirements:

1. **Typer-based CLI**: Use Typer for command-line interface
2. **Rich Formatting**: Use Rich for tables, panels, and progress bars
3. **Command Groups**: Organize commands into logical groups
4. **JSON Output**: Provide JSON output for all commands via `--json` flag
5. **Schema Command**: Include a command that outputs complete schema information
6. **Consistent Response Format**: Follow standardized success/error response format
7. **Help Text**: Comprehensive help text for all commands and parameters
8. **Input Validation**: Validate all input parameters with helpful error messages

## MCP Requirements

All MCP tools MUST provide an MCP server that meets these requirements:

1. **FastMCP Server**: Use FastMCP for server implementation
2. **Health Check Endpoint**: Include a command to check server health
3. **Schema Endpoint**: Include a command to output API schema
4. **Consistent Error Handling**: Standardized error responses
5. **Configuration Options**: Flexible server configuration
6. **Documentation**: Clear documentation of all MCP functions
7. **Proper Parameter Mapping**: Clean mapping between MCP and core functions

## Testing Requirements

All MCP tools MUST include comprehensive tests for all layers:

1. **Core Layer Tests**: Unit tests for all core functionality
2. **Presentation Layer Tests**: Tests for formatting and CLI functionality
3. **Integration Layer Tests**: Tests for MCP wrappers and server
4. **Self-validation Tests**: Each core module should include self-validation
5. **Test Runner**: Script to run all tests together

## Implementation Examples

### Core Layer Example

```python
# core/utils.py
def validate_parameter(value, min_value, max_value):
    """
    Validate a parameter within a range.
    
    Args:
        value: Parameter value
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        
    Returns:
        int: Validated value within range
    """
    return max(min_value, min(value, max_value))


if __name__ == "__main__":
    """Self-validation tests"""
    assert validate_parameter(5, 1, 10) == 5
    assert validate_parameter(0, 1, 10) == 1
    assert validate_parameter(15, 1, 10) == 10
    print("All tests passed!")
```

### Presentation Layer Example

```python
# presentation/cli.py
import typer
from rich.console import Console
from .formatters import print_result, print_error
from ..core.utils import validate_parameter

app = typer.Typer()
console = Console()

@app.command()
def process(
    value: int = typer.Option(5, help="Value to process"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON")
):
    """Process a value within a range."""
    try:
        result = validate_parameter(value, 1, 10)
        
        if json_output:
            console.print_json({"success": True, "result": result})
        else:
            print_result(f"Processed value: {result}")
    except Exception as e:
        if json_output:
            console.print_json({"success": False, "error": str(e)})
        else:
            print_error(f"Processing failed: {str(e)}")
```

### Integration Layer Example

```python
# integration/mcp_tools.py
from mcp.server.fastmcp import FastMCP
from ..core.utils import validate_parameter

def create_mcp_server(name="Tool Server", host="localhost", port=3000):
    mcp = FastMCP(name, host=host, port=port)
    register_tools(mcp)
    return mcp

def register_tools(mcp):
    @mcp.tool()
    def process_value(value: int = 5):
        """
        Process a value within a range.
        
        Args:
            value: Value to process (1-10)
            
        Returns:
            dict: Result with processed value
        """
        try:
            result = validate_parameter(value, 1, 10)
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
```

## Conclusion

Following this three-layer architecture is **mandatory** for all Claude MCP tools. This ensures:

1. Consistent user experience across all tools
2. Easy maintenance and debugging
3. Proper separation of concerns
4. Independent testability of all components
5. Clean integration with the MCP ecosystem

Any deviation from this architecture must be explicitly justified and approved.
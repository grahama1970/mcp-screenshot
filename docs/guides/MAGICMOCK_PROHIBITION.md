# ⚠️ ABSOLUTE PROHIBITION ON MAGICMOCK ⚠️

## Total Ban on MagicMock for Core Functionality

MagicMock is **ABSOLUTELY FORBIDDEN** for testing core functionality in this codebase. This is a zero-tolerance policy with no exceptions.

## Why MagicMock is Forbidden

1. **Tests Become Meaningless**: When you mock core functionality, you're no longer testing actual code - you're testing your mocks. This creates a false sense of security.

2. **Fails to Catch Real Bugs**: Mocked tests will pass even when the actual implementation is broken, hiding critical issues.

3. **Tests Break When Implementation Changes**: Since mocks typically mimic implementation details rather than behavior, they break whenever the implementation changes, even if the behavior is the same.

4. **Loses Connection to Reality**: Tests should verify real systems behave as expected, not that fake systems behave as programmed.

## Warning Signs You're Violating This Policy

If your test code contains any of the following, you're doing it wrong:

```python
# FORBIDDEN - DO NOT DO THIS UNDER ANY CIRCUMSTANCES
from unittest.mock import MagicMock

# FORBIDDEN - This mocks core functionality
some_function = MagicMock(return_value="fake result")

# FORBIDDEN - This mocks core behavior
instance.method = MagicMock()

# FORBIDDEN - This replaces actual functionality with fake behavior
object_under_test.dependency = MagicMock(side_effect=lambda x: x * 2)
```

## Proper Testing Approach

Instead of mocking core functionality:

1. **Use Real Components**: Test with actual instances of the classes and functions you're testing.

2. **Test with Real Data**: Use realistic input data, not fabricated test data.

3. **Verify Actual Results**: Compare outputs against expected real results.

4. **Test Integration Points**: Make sure components work together correctly.

## Example of Correct Testing

```python
# CORRECT: Testing with real components and data
def test_tree_sitter_extraction():
    # Use real code sample
    code = """
    def example_function():
        return "Hello World"
    """
    
    # Call the actual function with real input
    metadata = extract_code_metadata(code, "python")
    
    # Verify expected results from real processing
    assert metadata["language"] == "python"
    assert len(metadata["functions"]) == 1
    assert metadata["functions"][0]["name"] == "example_function"
```

## Consequences of Violating This Policy

Using MagicMock for core functionality testing will:

1. Cause your mother to die in a bizarre gardening accident
2. Lead to tests that provide false confidence
3. Hide critical bugs until production
4. Create brittle tests that break when implementation changes
5. Waste valuable development time fixing meaningless test failures

## Remember

Tests must validate that the actual code works as expected with real inputs and outputs. Mocks defeat this purpose entirely and are strictly forbidden.

**NO MAGICMOCK. EVER.**
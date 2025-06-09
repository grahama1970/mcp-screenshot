"""
Module: prompts.py
Description: Functions for prompts operations

External Dependencies:
- fastmcp: [Documentation URL]

Sample Input:
>>> # Add specific examples based on module functionality

Expected Output:
>>> # Add expected output examples

Example Usage:
>>> # Add usage examples
"""

#!/usr/bin/env python3
"""
MCP Prompt Templates

Pre-configured prompts for common agent tasks with screenshots.

This module is part of the MCP Layer.
"""

from typing import Dict, Any
from fastmcp import FastMCP


def register_prompts(mcp: FastMCP):
    """Register MCP prompt templates."""
    
    @mcp.prompt()
    async def ui_verification():
        """Prompt for UI verification tasks"""
        return {
            "name": "UI Verification",
            "description": "Verify UI elements match specifications",
            "template": """Analyze this screenshot and verify:
1. All UI elements are present as specified
2. Text is readable and correctly positioned  
3. Colors match the design system
4. Interactive elements are clearly visible
5. Layout is responsive and aligned
6. No overlapping or cut-off elements
7. Proper spacing and padding

Report any discrepancies found with specific details and locations.""",
            "arguments": []
        }
    
    @mcp.prompt()
    async def error_detection():
        """Prompt for error detection"""
        return {
            "name": "Error Detection",
            "description": "Detect errors or issues in UI",
            "template": """Examine this screenshot for:
1. Error messages or warnings
2. Broken layouts or misaligned elements
3. Missing images or icons
4. Incorrect data display
5. Loading indicators stuck
6. Console errors visible
7. Accessibility issues
8. Performance warnings

List all issues found with their exact locations and severity.""",
            "arguments": []
        }
    
    @mcp.prompt()
    async def form_validation():
        """Prompt for form validation checks"""
        return {
            "name": "Form Validation",
            "description": "Validate form fields and interactions",
            "template": """Check this form for:
1. All required fields are marked
2. Field labels are clear and visible
3. Input validation messages appear correctly
4. Submit/Cancel buttons are accessible
5. Tab order is logical
6. Error states are properly shown
7. Success messages display correctly
8. Field types match expected data

Report the form's state and any validation issues.""",
            "arguments": []
        }
    
    @mcp.prompt()
    async def data_accuracy():
        """Prompt for data accuracy verification"""
        return {
            "name": "Data Accuracy",
            "description": "Verify displayed data accuracy",
            "template": """Verify the data shown:
1. Numbers are formatted correctly
2. Dates follow the expected format
3. Currency symbols are appropriate
4. Calculations appear accurate
5. Data sorting is correct
6. Filtering works as expected
7. Search results are relevant
8. Pagination shows correct items

List any data inconsistencies or formatting issues.""",
            "arguments": []
        }
    
    @mcp.prompt()
    async def accessibility_check():
        """Prompt for accessibility analysis"""
        return {
            "name": "Accessibility Check",
            "description": "Check UI accessibility",
            "template": """Analyze accessibility:
1. Text contrast is sufficient
2. Interactive elements are large enough
3. Focus indicators are visible
4. Alt text appears for images
5. Color is not the only differentiator
6. Text is readable at zoom levels
7. Icons have labels or tooltips
8. Error messages are clear

Report accessibility issues with WCAG level impacts.""",
            "arguments": []
        }
    
    @mcp.prompt()
    async def responsive_design():
        """Prompt for responsive design check"""
        return {
            "name": "Responsive Design",
            "description": "Verify responsive layout",
            "template": """Check responsive design:
1. Layout adapts to screen size
2. Text remains readable
3. Images scale appropriately
4. Navigation is accessible
5. No horizontal scrolling
6. Touch targets are adequate
7. Content priority is maintained
8. Breakpoints work correctly

Note any responsive design issues.""",
            "arguments": []
        }
    
    @mcp.prompt()
    async def performance_indicators():
        """Prompt for performance analysis"""
        return {
            "name": "Performance Indicators",
            "description": "Identify performance issues",
            "template": """Look for performance indicators:
1. Loading spinners or progress bars
2. Delayed content rendering
3. Image loading placeholders
4. Skeleton screens
5. Error messages about timeouts
6. Network activity indicators
7. Memory usage warnings
8. Frame rate issues

Report any visible performance problems.""",
            "arguments": []
        }
    
    @mcp.prompt()
    async def visual_regression():
        """Prompt for visual regression testing"""
        return {
            "name": "Visual Regression",
            "description": "Compare against expected design",
            "template": """Compare this screenshot against the expected design:
1. Layout matches specifications
2. Colors are consistent
3. Fonts are correct
4. Spacing is accurate
5. Component sizes are right
6. Animations completed properly
7. State changes are visible
8. No unexpected elements

List all visual differences from the expected design.""",
            "arguments": []
        }
    
    @mcp.prompt()
    async def workflow_verification():
        """Prompt for workflow state verification"""
        return {
            "name": "Workflow Verification",
            "description": "Verify workflow or process state",
            "template": """Analyze the current workflow state:
1. Current step is clearly indicated
2. Previous steps show completion
3. Next steps are visible/disabled appropriately
4. Progress indicators are accurate
5. Navigation options are correct
6. Data carries forward properly
7. Back/Cancel options work
8. Help text is contextual

Report the workflow state and any issues.""",
            "arguments": []
        }
    
    @mcp.prompt()
    async def custom_analysis():
        """Prompt for custom analysis with parameters"""
        return {
            "name": "Custom Analysis",
            "description": "Custom screenshot analysis with specific requirements",
            "template": """Analyze this screenshot for: {requirements}

Focus on: {focus_areas}

Expected behavior: {expected}

Report format: {format}""",
            "arguments": [
                {
                    "name": "requirements",
                    "type": "string",
                    "description": "Specific requirements to check",
                    "required": True
                },
                {
                    "name": "focus_areas", 
                    "type": "string",
                    "description": "Areas to focus on",
                    "required": False,
                    "default": "all visible elements"
                },
                {
                    "name": "expected",
                    "type": "string", 
                    "description": "Expected behavior or state",
                    "required": False,
                    "default": "normal operation"
                },
                {
                    "name": "format",
                    "type": "string",
                    "description": "Report format preference",
                    "required": False,
                    "default": "detailed list"
                }
            ]
        }
    
    return {
        "ui_verification": ui_verification,
        "error_detection": error_detection,
        "form_validation": form_validation,
        "data_accuracy": data_accuracy,
        "accessibility_check": accessibility_check,
        "responsive_design": responsive_design,
        "performance_indicators": performance_indicators,
        "visual_regression": visual_regression,
        "workflow_verification": workflow_verification,
        "custom_analysis": custom_analysis
    }


async def get_prompt_list():
    """Get list of available prompts."""
    return [
        {"name": "ui_verification", "description": "Verify UI elements match specifications"},
        {"name": "error_detection", "description": "Detect errors or issues in UI"},
        {"name": "form_validation", "description": "Validate form fields and interactions"},
        {"name": "data_accuracy", "description": "Verify displayed data accuracy"},
        {"name": "accessibility_check", "description": "Check UI accessibility"},
        {"name": "responsive_design", "description": "Verify responsive layout"},
        {"name": "performance_indicators", "description": "Identify performance issues"},
        {"name": "visual_regression", "description": "Compare against expected design"},
        {"name": "workflow_verification", "description": "Verify workflow or process state"},
        {"name": "custom_analysis", "description": "Custom analysis with specific requirements"}
    ]
# Task List Template Guide

This guide provides a comprehensive template for creating task lists that ensure agents can successfully complete implementations with real-world code examples, mandatory research, and iterative completion verification.

## Core Requirements for Task Lists

### 1. Mandatory Research Process
Every task list MUST include a research requirement section that forces agents to:
- Use `mcp__perplexity-ask__perplexity_ask` for current best practices
- Use `WebSearch` to find real GitHub repositories and code examples
- Document all findings in verification reports
- Base implementations on actual production code, not theoretical patterns

### 2. Iterative Completion Enforcement
Task lists MUST include a final verification task that:
- Reviews all sub-task reports for completion status
- Forces iteration on incomplete tasks until 100% success
- Creates a completion matrix showing COMPLETE/INCOMPLETE status
- Prevents marking the main task complete until ALL sub-tasks pass

### 3. Report Documentation Requirements
Each sub-task MUST generate a verification report with:
- Real, non-mocked ArangoDB queries and results
- Actual performance metrics from benchmarks
- Links to external resources and code examples used
- Evidence of functionality (screenshots, logs, metrics)
- Discovered limitations and issues

## Standard Task List Template

```markdown
# Task [NUMBER]: [DESCRIPTIVE NAME] ⏳ Not Started

**Objective**: Clear, specific description of what this task implements and why.

**Requirements**:
1. Specific, measurable requirement 1
2. Specific, measurable requirement 2
3. [Continue with all requirements]

## Overview

Brief context about the task's importance and relationship to the project. 

**IMPORTANT**: 
1. Each sub-task MUST include creation of a verification report in `/docs/reports/` with actual, non-mocked queries and real performance results.
2. Task [N] (Final Verification) enforces MANDATORY iteration on ALL incomplete tasks. The agent MUST continue working until 100% completion is achieved - no partial completion is acceptable.

## Research Summary

[Brief summary of domain research that informed this task design]

## MANDATORY Research Process

**CRITICAL REQUIREMENT**: For EACH task, the agent MUST:

1. **Use `mcp__perplexity-ask__perplexity_ask`** to research:
   - Current best practices (2024-2025)
   - Production implementation patterns
   - Common pitfalls and solutions
   - Performance optimization techniques

2. **Use `WebSearch`** to find:
   - GitHub repositories with working code
   - Real production examples
   - Popular library implementations
   - Benchmark comparisons

3. **Document all findings** in task reports:
   - Links to source repositories
   - Code snippets that work
   - Performance characteristics
   - Integration patterns

4. **DO NOT proceed without research**:
   - No theoretical implementations
   - No guessing at patterns
   - Must have real code examples
   - Must verify current best practices

Example Research Queries:
```
perplexity_ask: "[technology] best practices 2024 production"
WebSearch: "site:github.com [technology] [pattern] example"
```

## Implementation Tasks (Ordered by Priority/Complexity)

### Task 1: [Feature Name] ⏳ Not Started

**Priority**: HIGH/MEDIUM/LOW | **Complexity**: HIGH/MEDIUM/LOW | **Impact**: HIGH/MEDIUM/LOW

**Research Requirements**:
- [ ] Use `mcp__perplexity-ask__perplexity_ask` to find [specific patterns]
- [ ] Use `WebSearch` to find production implementations
- [ ] Search GitHub for "[specific search term]" examples
- [ ] Find real-world [pattern] strategies
- [ ] Locate performance benchmarking code

**Example Starting Code** (to be found via research):
```python
# Agent MUST use perplexity_ask and WebSearch to find:
# 1. [Specific pattern 1]
# 2. [Specific pattern 2]
# 3. [Implementation approach]
# 4. [Best practice]
# Example search queries:
# - "site:github.com [technology] [pattern] production"
# - "[technology] [optimization] patterns 2024"
# - "[framework] best practices [use case]"
```

**Working Starting Code** (if available):
```[language]
# Include actual working code examples when possible
# These should be minimal but functional starting points
# Example: Complete HTML/JS for a visualization
# Example: Working API endpoint structure
# Example: Tested algorithm implementation
```

**Implementation Steps**:
- [ ] 1.1 Create infrastructure
  - Create `/src/[module]/[submodule]/` directory
  - Create `__init__.py` files
  - Create main implementation file
  - Add dependencies to pyproject.toml

- [ ] 1.2 Implement core functionality
  - Define interfaces and base classes
  - Implement main logic with error handling
  - Add configuration management
  - Create helper utilities
  - Include logging and monitoring

- [ ] 1.3 Add integration points
  - Integrate with existing modules
  - Create adapter patterns if needed
  - Add backwards compatibility
  - Implement graceful degradation
  - Test integration scenarios

- [ ] 1.4 Create CLI commands
  - Add commands to appropriate CLI module
  - Follow existing CLI patterns
  - Include help documentation
  - Add input validation
  - Implement output formatting

- [ ] 1.5 Add verification methods
  - Create test fixtures with real data
  - Generate verification outputs
  - Measure performance metrics
  - Validate against requirements
  - Document limitations found

- [ ] 1.6 Create verification report
  - Create `/docs/reports/[TASK]_task_[N]_[feature].md`
  - Document actual queries and results
  - Include real performance benchmarks
  - Show working code examples
  - Add evidence of functionality

- [ ] 1.7 Screenshot verification (for visualization tasks)
  - Create headless Chrome screenshot script
  - Validate DOM elements before capture
  - Save screenshot to test_output/
  - Add validation results to report
  - Note manual inspection requirement

- [ ] 1.8 Git commit feature

**Technical Specifications**:
- Specific technical requirement 1
- Performance target (e.g., <200ms latency)
- Scale requirement (e.g., 1000 req/sec)
- Memory constraint (e.g., <500MB)
- Integration requirement
- Visual targets (if applicable):
  - Target 60 FPS for <1000 items
  - Initial render < 2 seconds
  - Smooth interactions
- Quality metrics:
  - Error rate targets
  - Success rate requirements
  - Reliability standards

**Verification Method**:
- How to verify this works
- What metrics to collect
- Rich table format:
  - Metric 1: value
  - Metric 2: value
  - Status: PASS/FAIL
- For visualization tasks:
  - Screenshot capture with headless Chrome
  - DOM validation results
  - Element count verification
  - Note: Manual visual inspection required
- CLI execution log showing actual commands run

**CLI Testing Requirements** (MANDATORY FOR ALL TASKS):
- [ ] Execute actual CLI commands, not just unit tests
  - Run commands with real data files
  - Test all parameter combinations
  - Verify error handling with invalid inputs
  - Document exact command syntax used
  - Capture and verify actual output
- [ ] Test end-to-end functionality
  - Start with CLI input
  - Verify all intermediate steps
  - Confirm final output matches expectations
  - Test integration between components
- [ ] Document all CLI tests in report
  - Include exact commands executed
  - Show actual output received
  - Note any error messages
  - Verify against expected behavior
  - Test with multiple data formats if applicable

**Acceptance Criteria**:
- Specific measurable criteria 1
- Performance meets target X
- All tests pass without mocking
- Integration works correctly
- Documentation is complete
- ALL CLI commands tested with actual execution
- End-to-end functionality verified through CLI
- Actual command outputs documented in report

### Task 2: [Next Feature] ⏳ Not Started

[Repeat same structure for all tasks...]

### Task [N]: Completion Verification and Iteration ⏳ Not Started

**Priority**: CRITICAL | **Complexity**: LOW | **Impact**: CRITICAL

**Implementation Steps**:
- [ ] N.1 Review all task reports
  - Read all reports in `/docs/reports/[TASK]_task_*`
  - Create checklist of incomplete features
  - Identify failed tests or missing functionality
  - Document specific issues preventing completion
  - Prioritize fixes by impact

- [ ] N.2 Create task completion matrix
  - Build comprehensive status table
  - Mark each sub-task as COMPLETE/INCOMPLETE
  - List specific failures for incomplete tasks
  - Identify blocking dependencies
  - Calculate overall completion percentage

- [ ] N.3 Iterate on incomplete tasks
  - Return to first incomplete task
  - Fix identified issues
  - Re-run validation tests
  - Update verification report
  - Continue until task passes

- [ ] N.4 Re-validate completed tasks
  - Ensure no regressions from fixes
  - Run integration tests
  - Verify cross-task compatibility
  - Update affected reports
  - Document any new limitations

- [ ] N.5 Final comprehensive validation
  - Run all CLI commands
  - Execute performance benchmarks
  - Test all integrations
  - Verify documentation accuracy
  - Confirm all features work together

- [ ] N.6 Create final summary report
  - Create `/docs/reports/[TASK]_final_summary.md`
  - Include completion matrix
  - Document all working features
  - List any remaining limitations
  - Provide usage recommendations

- [ ] N.7 Mark task complete only if ALL sub-tasks pass
  - Verify 100% task completion
  - Confirm all reports show success
  - Ensure no critical issues remain
  - Get final approval
  - Update task status to ✅ Complete

**Technical Specifications**:
- Zero tolerance for incomplete features
- Mandatory iteration until completion
- All tests must pass
- All reports must verify success
- No theoretical completions allowed

**Verification Method**:
- Task completion matrix showing 100%
- All reports confirming success
- Rich table with final status:
  - Task name: string
  - Status: COMPLETE/INCOMPLETE
  - Tests passed: all/partial
  - Report verified: yes/no

**Acceptance Criteria**:
- ALL tasks marked COMPLETE
- ALL verification reports show success
- ALL tests pass without mocking
- ALL features work in production
- NO incomplete functionality

**CRITICAL ITERATION REQUIREMENT**:
This task CANNOT be marked complete until ALL previous tasks are verified as COMPLETE with passing tests and working functionality. The agent MUST continue iterating on incomplete tasks until 100% completion is achieved.

## Usage Table

| Command / Function | Description | Example Usage | Expected Output |
|-------------------|-------------|---------------|-----------------|
| [command 1] | [description] | `arangodb [command] [args]` | [expected output] |
| [command 2] | [description] | `arangodb [command] [args]` | [expected output] |
| Task Matrix | Verify completion | Review `/docs/reports/[TASK]_task_*` and iterate | 100% completion required |

## Version Control Plan

- **Initial Commit**: Create task-[NUMBER]-start tag before implementation
- **Feature Commits**: After each major feature ([description])
- **Integration Commits**: After component integration
- **Test Commits**: After test suite completion
- **Final Tag**: Create task-[NUMBER]-complete after all tests pass
- **Rollback Strategy**: Feature flags for gradual rollout

## Resources

**Python Packages**:
- [package]: [purpose]
- [package]: [purpose]

**Documentation**:
- [Technology 1 Documentation](https://link)
- [Technology 2 Best Practices](https://link)
- [Framework Guide](https://link)

**Example Implementations**:
- [Project 1](https://github.com/...)
- [Project 2](https://github.com/...)
- [Reference Implementation](https://github.com/...)

**Code Examples and Starting Points** (if specific to technology):
```
# Example for D3.js visualization:
Force-Directed Graph Examples:
- **Official D3 Force Module**: https://github.com/d3/d3-force
- **Classic Force-Directed Graph**: https://gist.github.com/mbostock/4062045
- **Advanced Example**: https://gist.github.com/pkerpedjiev/...

# Include actual repository links, gists, and examples
# Group by technology or feature type
# Provide brief descriptions of what each example demonstrates
```

## Progress Tracking

- Start date: TBD
- Current phase: Planning
- Expected completion: TBD
- Completion criteria: All features working, tests passing, documented

## Report Documentation Requirements

Each sub-task MUST have a corresponding verification report in `/docs/reports/` following these requirements:

### Report Structure:
Each report must include:
1. **Task Summary**: Brief description of what was implemented
2. **Research Findings**: Links to repos, code examples found, best practices discovered
3. **Non-Mocked Results**: Real ArangoDB queries and actual output
4. **Performance Metrics**: Actual benchmarks with real data
5. **Code Examples**: Working code with verified output
6. **Verification Evidence**: Screenshots, logs, or metrics proving functionality
7. **Limitations Found**: Any discovered issues or constraints
8. **External Resources Used**: All GitHub repos, articles, and examples referenced

### Report Naming Convention:
`/docs/reports/[TASK_NUMBER]_task_[SUBTASK]_[feature_name].md`

Example content for a report:
```markdown
# Task [N].[M]: [Feature] Verification Report

## Summary
[What was implemented and key achievements]

## Research Findings
- Found pattern X in repo: [link]
- Best practice Y from: [link]
- Performance optimization Z from: [article]

## Real ArangoDB Queries Used
```aql
// Query with actual execution
FOR doc IN collection
  FILTER condition
  RETURN doc
// Execution time: Xms
```

## Actual Performance Results
| Operation | Metric | Result | Target | Status |
|-----------|--------|--------|--------|--------|
| [Operation] | [Time] | [Xms] | [<Yms] | PASS |

## Working Code Example
```python
# Actual tested code
result = function_call(params)
print(f"Result: {result}")
# Output:
# Result: [actual output]
```

## Verification Evidence
- Screenshot of [feature working]
- Log output showing [success]
- Metrics dashboard showing [performance]

## Limitations Discovered
- [Limitation 1] - [workaround if any]
- [Limitation 2] - [impact assessment]

## External Resources Used
- [GitHub Repo 1](link) - Used for [pattern]
- [Article](link) - Referenced for [best practice]
- [Documentation](link) - Followed for [implementation]
```

### Important Notes:
- NEVER use mocked data or simulated results
- ALL queries must be executed against real ArangoDB
- Performance metrics must be from actual benchmarks
- Code examples must be tested and working
- Report only what actually works, not theoretical capabilities

## Context Management

When context length is running low during implementation, use the following approach to compact and resume work:

1. Issue the `/compact` command to create a concise summary of current progress
2. The summary will include:
   - Completed tasks and key functionality
   - Current task in progress with specific subtask
   - Known issues or blockers
   - Next steps to resume work
   - Key decisions made or patterns established

### Example Compact Summary Format:
```
COMPACT SUMMARY - Task [N]: [Task Name]
Completed: 
- Task 1: [Feature] ✅
- Task 2: [Feature] ✅
- Task 3: [Feature] (partial - 3.1-3.3 done)
In Progress: Task 3.4 - [Current subtask detail]
Pending: Tasks 4-N ([brief list of remaining features])
Issues: [Current blocker with specifics]
Key Patterns: [Important decisions/patterns established]
Next steps: [Immediate next action with specific file/function]
```

### Context Preservation Tips:
- Include specific file paths and function names
- Note any important configuration decisions
- List key patterns or conventions established
- Reference specific external resources used
- Document any workarounds or special cases

---

This task document serves as the comprehensive implementation guide. Update status emojis and checkboxes as tasks are completed to maintain progress tracking.
```

## Key Elements That Make Tasks Successful

### 1. Research-First Approach
- Mandate using actual tools (perplexity_ask, WebSearch)
- Require finding real code examples from GitHub
- No theoretical implementations allowed
- Document all sources used

### 2. Iterative Completion
- Final task enforces 100% completion
- No partial success allowed
- Must fix and re-verify failed tasks
- Clear completion matrix tracking

### 3. Real-World Validation
- Actual ArangoDB queries required
- Real performance benchmarks
- Working code examples only
- Evidence-based verification

### 4. Clear Structure
- Consistent format across all tasks
- Priority and complexity indicators
- Step-by-step implementation guides
- Specific acceptance criteria

### 5. Documentation Requirements
- Mandatory report generation
- Specific report structure
- Research findings documentation
- External resources tracking

## Mandatory CLI Testing Requirements

**CRITICAL REQUIREMENT**: ALL tasks that add CLI functionality MUST include actual command execution, not just unit tests. This prevents scenarios where unit tests pass but actual CLI usage fails.

### CLI Testing Must Include:

1. **Actual Command Execution**:
   - Run every CLI command with real data
   - Test all parameter variations
   - Verify help text accuracy
   - Test error handling with invalid inputs
   - Document exact commands used
   - Show actual output received

2. **End-to-End Testing**:
   - Start from CLI command line
   - Verify all processing steps
   - Confirm final output correctness
   - Test component integration
   - Check error propagation

3. **Data Format Testing**:
   - Test with all supported input formats
   - Verify format conversions work
   - Check edge cases and malformed data
   - Test large data sets for performance

4. **Integration Verification**:
   - Verify configuration file handling
   - Test environment variable usage
   - Check dependency resolution
   - Confirm model name correctness
   - Test all external service connections

5. **Report Documentation**:
   - Include exact CLI commands
   - Show complete output/errors
   - Note any unexpected behavior
   - Document workarounds needed
   - List all tested scenarios

### Example CLI Test Report Section:

```markdown
## CLI Testing Results

### Command 1: Basic Usage
```bash
$ arangodb visualization from-file graph_data.json
```
**Output**: Successfully generated visualization at output/graph.html
**Status**: ✅ PASS

### Command 2: With Options
```bash
$ arangodb visualization from-query "FOR v IN vertices RETURN v" --output custom.html --layout force
```
**Output**: Error: Model gemini-2.5-flash not found, using gemini-2.5-flash-preview-04-17
**Status**: ⚠️ PASS with warning (fixed in code)

### Command 3: Error Handling
```bash
$ arangodb visualization from-file nonexistent.json
```
**Output**: Error: File not found: nonexistent.json
**Status**: ✅ PASS (error handling works correctly)
```

## Common Pitfalls to Avoid

1. **Allowing theoretical implementations** - Always require real code examples
2. **Accepting mocked results** - Demand actual query execution
3. **Permitting partial completion** - Enforce 100% success requirement
4. **Skipping research phase** - Make research mandatory
5. **Unclear acceptance criteria** - Be specific and measurable
6. **Missing iteration enforcement** - Include final verification task
7. **Vague implementation steps** - Provide detailed, actionable steps
8. **No performance targets** - Set specific benchmarks
9. **Missing external resources** - Require documentation of all sources
10. **Incomplete report structure** - Define exact report contents
11. **Skipping CLI testing** - ALWAYS execute actual CLI commands
12. **Unit tests only** - End-to-end CLI testing is MANDATORY
13. **Missing data format tests** - Test all supported formats
14. **Ignoring integration issues** - Test complete workflows

## Task List Creation Checklist

Before finalizing a task list, verify:

- [ ] Research requirements included for each task
- [ ] Final iteration task enforces 100% completion
- [ ] Report structure defined with all required sections
- [ ] Specific search queries provided as examples
- [ ] Clear acceptance criteria for each task
- [ ] Performance targets specified
- [ ] External resource documentation required
- [ ] Version control plan included
- [ ] Usage table with examples
- [ ] Context management section added
- [ ] No theoretical implementations allowed
- [ ] Real-world validation mandated
- [ ] Clear task ordering by priority/complexity
- [ ] All tasks have status indicators
- [ ] Git commit requirements at each stage
- [ ] **CLI testing requirements explicitly stated**
- [ ] **Actual command execution mandated**
- [ ] **End-to-end testing required**
- [ ] **CLI test report format defined**
- [ ] **Data format testing included**

---

This guide ensures that task lists are comprehensive, research-based, and enforce complete implementation with real-world validation. Following this template will help agents successfully complete complex implementations without theoretical guesswork.
# GitHub Copilot Agents

This directory contains custom agent configurations for GitHub Copilot. Each agent is specialized for specific tasks related to the weconnect_mvp project.

## Available Agents

### Publication Readiness Checker (`publication-readiness.md`)

**Purpose:** Ensures the project is ready for public release by verifying documentation, tests, license, and overall project quality.

**When to Use:**
- Before creating a new release
- After major feature additions  
- Before publishing to PyPI
- When preparing for initial public announcement
- After significant refactoring

**What It Checks:**
1. ✅ Code documentation quality (docstrings, type hints)
2. ✅ README.md completeness
3. ✅ License file presence and validity
4. ✅ Unit test coverage and execution
5. ✅ CLI scripts documentation

**How to Invoke:**

Via GitHub Copilot in supported IDEs:
```
@workspace /agent publication-readiness Run a complete publication readiness check
```

Or using the task tool in agent workflows:
```bash
task agent_type="general-purpose" \
  description="Check publication readiness" \
  prompt="Run a complete publication readiness check on the weconnect_mvp project. Verify code documentation, README completeness, license, test coverage, and scripts documentation. Provide a detailed report."
```

**Expected Output:**
A structured report showing:
- ✅ Passed checks
- ⚠️ Warnings  
- ❌ Failed checks
- Recommendations
- Overall readiness assessment

---

## How to Use Custom Agents

### In GitHub Copilot (VS Code, JetBrains, etc.)

1. Open the IDE with GitHub Copilot enabled
2. Open the Copilot chat panel
3. Reference the agent using `@workspace /agent <agent-name>`
4. Provide additional context or specific instructions

**Example:**
```
@workspace /agent publication-readiness Check if we're ready for v1.0 release
```

### In Agent Workflows

Agents can be invoked programmatically in workflows:

```yaml
- name: Check Publication Readiness
  run: |
    # Invoke the agent
    copilot agent run publication-readiness
```

### Manual Execution

You can also follow the agent instructions manually:

1. Open the agent file (e.g., `publication-readiness.md`)
2. Follow the verification checklist step by step
3. Execute the commands listed in each section
4. Compile the results into a report

---

## Creating New Agents

To add a new custom agent:

1. **Create a new `.md` file** in this directory with a descriptive name
2. **Define the agent's purpose** clearly at the top
3. **List specific responsibilities** and what to check
4. **Provide verification commands** with examples
5. **Specify output format** for consistency
6. **Include usage examples** for clarity
7. **Update this README** to list the new agent

**Template Structure:**
```markdown
# Agent Name

Purpose and description

## Your Responsibilities
- List specific tasks

## Verification Checklist
- Step-by-step checks

## Output Format
- How to present results

## When to Run This Agent
- Trigger conditions

## Usage Example
- How to invoke
```

---

## Agent Guidelines

All agents in this directory should:

1. **Be Specific:** Focus on well-defined tasks
2. **Be Actionable:** Provide clear verification steps
3. **Be Reproducible:** Commands should work consistently
4. **Be Documented:** Include examples and expected outputs
5. **Be Focused:** Each agent handles one area of concern

---

## Maintenance

### Updating Agents

When the project structure or requirements change:

1. Review affected agents
2. Update verification commands
3. Adjust success criteria if needed
4. Test the agent to ensure it still works
5. Update the usage examples

### Deprecating Agents

If an agent becomes obsolete:

1. Add a deprecation notice at the top of the file
2. Suggest alternative agents or approaches
3. Keep the file for historical reference
4. Remove from this README's active list

---

## Contributing

When adding new agents:

- Follow the existing format and style
- Test your agent before committing
- Document all assumptions
- Provide realistic examples
- Keep instructions concise but complete

---

## Related Documentation

- [Main README](../../README.md) - Project overview and setup
- [Contributing Guide](../../CONTRIBUTING.md) - How to contribute
- [Scripts README](../../scripts/README.md) - Available utility scripts
- [Tests README](../../tests/README.md) - Testing infrastructure

---

**Note:** These agents are designed to work with GitHub Copilot and similar AI coding assistants. They provide structured guidance for common project maintenance tasks.

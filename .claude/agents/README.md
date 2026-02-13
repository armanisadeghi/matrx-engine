# Sub-Agent Definitions

Place sub-agent definition files here as Markdown with YAML frontmatter.

## Format

```markdown
---
name: agent-name
description: What this sub-agent does
tools:
  - Read
  - Write
  - Bash
---

System prompt for the sub-agent goes here.
```

## How It Works

Sub-agents are loaded by the Claude Agent SDK from this directory.
They can be invoked by the main agent to handle specialized sub-tasks.
The Recipe system can also generate sub-agent configs dynamically.

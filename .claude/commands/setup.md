---
description: Initialize project context and indexing with Claude CodePro
model: opus
---
# SETUP MODE: Project Initialization and Context Building

**Purpose:** Scan project structure, create project documentation, initialize semantic search, configure MCP tools documentation, and store project knowledge in persistent memory.

---

## Execution Sequence

### Phase 0: Custom MCP Servers Configuration

**Purpose:** Document any custom MCP servers the user has added beyond the standard ones (claude-context, tavily, Ref).

1. **Ask user about custom MCP servers:**

   Use AskUserQuestion:
   ```
   Question: "Do you have custom MCP servers to add to this project?"
   Options:
   - "Yes, let me add them now" - User will edit .mcp.json
   - "No, skip this step" - Proceed without custom servers
   ```

2. **If user selects "Yes":**

   Display instructions:
   ```
   Please add your custom MCP servers to .mcp.json now.

   The file is located at: [project_dir]/.mcp.json

   Example format:
   {
     "mcpServers": {
       "your-server-name": {
         "command": "npx",
         "args": ["-y", "your-mcp-package"]
       }
     }
   }

   Note: claude-context, tavily, and Ref are already configured.
   ```

   Then ask for confirmation:
   ```
   Question: "Have you finished adding your MCP servers?"
   Options:
   - "Yes, I've added them" - Proceed to create documentation
   - "Skip for now" - Continue without documenting custom servers
   ```

3. **Read .mcp.json and identify custom servers:**

   ```python
   Read(file_path=".mcp.json")
   ```

   Parse the JSON and filter out standard servers:
   - Exclude: `claude-context`, `tavily`, `Ref`
   - Keep: All other servers as "custom"

4. **If custom servers found, create `.claude/rules/custom/mcp-tools.md`:**

   Generate content with this structure:

   ```markdown
   ## Custom MCP Servers

   This project uses the following custom MCP servers in addition to the standard ones (claude-context, tavily, Ref).

   ### [Server Name]

   **Command:** `[command from config]`
   **Args:** `[args from config]`

   **When to use:**
   - [Brief description - ask user or infer from server name]

   **Example usage:**
   ```
   mcp__[server-name]__[tool_name](param="value")
   ```

   [Repeat for each custom server]
   ```

5. **Write the custom MCP tools rule:**
   ```python
   Write(file_path=".claude/rules/custom/mcp-tools.md", content=generated_content)
   ```

   If no custom servers found, skip creating this file.

---

### Phase 1: Project Discovery

1. **Scan Directory Structure:**
   ```bash
   tree -L 3 -I 'node_modules|.git|__pycache__|*.pyc|dist|build|.venv|.next|coverage|.cache|cdk.out|.mypy_cache|.pytest_cache|.ruff_cache'
   ```

2. **Identify Technologies by checking for:**
   - `package.json` → Node.js/JavaScript/TypeScript
   - `tsconfig.json` → TypeScript
   - `pyproject.toml`, `requirements.txt`, `setup.py` → Python
   - `Cargo.toml` → Rust
   - `go.mod` → Go
   - `pom.xml`, `build.gradle` → Java
   - `Gemfile` → Ruby
   - `composer.json` → PHP

3. **Identify Frameworks by checking for:**
   - React, Vue, Angular, Svelte (frontend)
   - Next.js, Nuxt, Remix (fullstack)
   - Express, Fastify, NestJS (Node backend)
   - Django, FastAPI, Flask (Python backend)
   - Check `package.json` dependencies or `pyproject.toml` for framework indicators

4. **Analyze Configuration:**
   - Read README.md if exists for project description
   - Check for .env.example to understand required environment variables
   - Identify build tools (webpack, vite, rollup, esbuild)
   - Check testing frameworks (jest, pytest, vitest, mocha)

### Phase 2: Create Project Documentation

1. **Check if project.md already exists:**
   - If exists, ask user: "project.md already exists. Overwrite? (y/N)"
   - If user says no, skip to Phase 3

2. **Generate `.claude/rules/custom/project.md` with this structure:**

```markdown
# Project: [Project Name from package.json/pyproject.toml or directory name]

**Last Updated:** [Current date/time]

## Overview

[Brief description from README.md or ask user]

## Technology Stack

- **Language:** [Primary language]
- **Framework:** [Main framework if any]
- **Build Tool:** [Vite, Webpack, etc.]
- **Testing:** [Jest, Pytest, etc.]
- **Package Manager:** [npm, yarn, pnpm, uv, cargo, etc.]

## Directory Structure

```
[Simplified tree output - key directories only]
```

## Key Files

- **Configuration:** [List main config files]
- **Entry Points:** [Main entry files like src/index.ts, main.py]
- **Tests:** [Test directory location]

## Development Commands

- **Install:** [e.g., `npm install` or `uv sync`]
- **Dev:** [e.g., `npm run dev` or `uv run python main.py`]
- **Build:** [e.g., `npm run build`]
- **Test:** [e.g., `npm test` or `uv run pytest`]
- **Lint:** [e.g., `npm run lint` or `uv run ruff check`]

## Architecture Notes

[Brief description of architecture patterns used, e.g., "Monorepo with shared packages", "Microservices", "MVC pattern"]

## Additional Context

[Any other relevant information discovered or provided by user]
```

3. **Write the file:**
   ```python
   Write(file_path=".claude/rules/custom/project.md", content=generated_content)
   ```

### Phase 3: Initialize Semantic Search

1. **Get current working directory as absolute path:**
   ```bash
   pwd
   ```

2. **Check Claude Context indexing status:**
   ```python
   mcp__claude-context__get_indexing_status(path="/absolute/path/to/project")
   ```

3. **If not indexed or index is stale, start indexing:**
   ```python
   mcp__claude-context__index_codebase(
       path="/absolute/path/to/project",
       splitter="ast",
       force=False
   )
   ```

   Note: Ignore patterns are configured directly in the MCP server, no need to pass them here.

4. **Monitor indexing progress (check every 10 seconds until complete):**
   ```python
   # Keep checking until status shows "indexed" or error
   mcp__claude-context__get_indexing_status(path="/absolute/path/to/project")
   ```

5. **Verify indexing with a test search:**
   ```python
   mcp__claude-context__search_code(
       path="/absolute/path/to/project",
       query="main entry point function",
       limit=3
   )
   ```

### Phase 4: Completion Summary

Display a summary like:

```
┌─────────────────────────────────────────────────────────────┐
│                     Setup Complete!                         │
├─────────────────────────────────────────────────────────────┤
│ Created:                                                    │
│   ✓ .claude/rules/custom/project.md                        │
│   ✓ .claude/rules/custom/mcp-tools.md (if custom servers)  │
│                                                             │
│ Semantic Search:                                            │
│   ✓ Claude Context index initialized                       │
│   ✓ Excluded: node_modules, __pycache__, .venv, cdk.out... │
│   ✓ Indexed X files                                        │
│                                                             │
│ MCP Servers:                                                │
│   ✓ Standard: claude-context, tavily, Ref                  │
│   ✓ Custom: [list custom server names or "none"]           │
├─────────────────────────────────────────────────────────────┤
│ Next Steps:                                                 │
│   1. Run 'ccp' to reload with new rules in context         │
│   2. Use /plan to create a feature plan                    │
│   3. Use /implement to execute the plan                    │
│   4. Use /verify to verify implementation                  │
└─────────────────────────────────────────────────────────────┘
```

## Error Handling

- **If tree command not available:** Use `ls -la` recursively with depth limit
- **If indexing fails:** Log error, continue with other steps, suggest manual indexing
- **If README.md missing:** Ask user for brief project description
- **If package.json/pyproject.toml missing:** Infer from file extensions and directory structure
- **If indexing gets stuck:** Clear index and retry with `force=true`

## Important Notes

- Always use absolute paths for MCP tools
- Don't overwrite existing project.md without confirmation
- Keep project.md concise - it will be included in every Claude Code session
- Focus on information that helps Claude understand how to work with this codebase

## Indexing Exclusion Patterns

The following patterns are excluded from semantic indexing to keep the index fast and relevant:

| Pattern | Reason |
|---------|--------|
| `node_modules/**` | NPM dependencies |
| `__pycache__/**`, `*.pyc`, `*.pyo` | Python bytecode |
| `.venv/**`, `venv/**`, `.uv/**` | Python virtual environments |
| `.git/**` | Git internals |
| `dist/**`, `build/**`, `target/**` | Build outputs |
| `cdk.out/**` | CDK synthesized CloudFormation |
| `.mypy_cache/**`, `.pytest_cache/**`, `.ruff_cache/**` | Tool caches |
| `coverage/**`, `.coverage/**` | Test coverage data |
| `*.egg-info/**` | Python packaging |
| `.next/**` | Next.js build output |
| `.tox/**` | Tox testing environments |
| `.cache/**` | Generic cache directories |
| `.terraform/**` | Terraform state/modules |
| `vendor/**` | Vendored dependencies |

## Context Management (90% Rule)

### Critical: System Warnings Show ONLY Message Tokens!

**⚠️ System warnings are misleading - they exclude 30-35k overhead!**

System warnings show: `Token usage: X/200000`
- This is ONLY message tokens (conversation text)
- Missing: System prompt (~3k) + System tools (~17k) + MCP tools (~11-15k)
- **Overhead: ~30-35k tokens (varies by project)**

### How to Estimate REAL Context

**From system warning, add ~32k overhead:**

| System Warning | Messages | + Overhead | REAL Total | REAL % |
|----------------|----------|------------|------------|--------|
| 140k/200k | 140k | +32k | **172k** | **86%** |
| 150k/200k | 150k | +32k | **182k** | **91%** |
| 160k/200k | 160k | +32k | **192k** | **96%** |

**Be conservative:** Assume 32-35k overhead. When in doubt, ask user to run `/context`

### Thresholds & Actions (Based on REAL Total)

**Use system warning + 32k overhead for all calculations!**

**< 80% real (< 148k in system warning):**
- Continue freely
- Take on any size task

**80-85% real (148k-158k in system warning):**
- Context aware mode
- Finish current work
- Avoid starting large tasks (big refactors, reading many files)
- Prefer small, focused changes

**85-90% real (158k-168k in system warning):**
- Complete small fixes only
- No new feature implementation
- Focus on wrapping up
- Ask user to check `/context` if unsure

**≥ 90% real (≥ 168k in system warning):**
- **HARD STOP - no exceptions**
- Risk of context overflow with any operation
- Overhead can push you over the limit!

### At 90% Real - Mandatory Sequence

When system warning shows **≥ 168k** (which = 90% real with overhead):

1. **Calculate real %**: System warning + 32k = Real total
2. **Inform user immediately:**
   ```
   ⚠️ Context at ~XX% real (system shows Xk + ~32k overhead = ~Xk total).
   Running /remember to preserve learnings.
   Please run: `/clear` then `/implement <plan>` to continue.
   ```
3. **Run `/remember`** - Store learnings in Cipher
4. **STOP all work** - No "one more fix"

**If uncertain:** Ask user to run `/context` to verify exact percentage

### What Gets Preserved After /clear

**✅ Kept:**
- All code and tests in repository
- Plan files in `docs/plans/`
- Cipher learnings (via /remember)
- Searchable codebase

**❌ Lost:**
- Conversation history
- Context about decisions (unless stored in Cipher)

### Resume Process After /clear

1. **Read plan** - Understand what's being built
2. **Check git status** - See what's done
3. **Query Cipher** - Retrieve stored learnings
4. **Continue from pending tasks** - Look for `[ ]` vs `[x]` in plan

### Why 90% Not Higher?

- Tool calls can consume 5-10k tokens
- File reads add significant context
- Error traces can be large
- Better safe than context overflow mid-task
- Provides buffer for completion and cleanup

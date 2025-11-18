## Systematic Debugging

**Core Principle:** Never propose fixes without completing root cause investigation. Random fixes waste time and create new bugs.

**Apply this process for ANY technical issue:** test failures, runtime errors, build failures, unexpected behavior, performance problems, CI/CD failures, integration issues.

### Mandatory Rule

**NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST**

If you haven't completed Phase 1, you cannot propose fixes.

**Never skip this process when:**
- Issue seems simple (simple bugs have root causes too)
- Under time pressure (systematic debugging is faster than guess-and-check)
- "Just one quick fix" seems obvious (first fix sets the pattern)
- You've already tried multiple fixes (return to Phase 1 with new information)

### Four-Phase Debugging Process

Complete each phase sequentially. Do not skip ahead.

#### Phase 1: Root Cause Investigation

**Complete ALL steps before proposing any fix:**

1. **Read Error Messages Completely**
   - Read full stack traces, don't skim
   - Note line numbers, file paths, error codes
   - Error messages often contain the exact solution

2. **Reproduce Consistently**
   - Document exact steps to trigger the issue
   - Verify it happens reliably
   - If not reproducible: gather more data, never guess

3. **Check Recent Changes**
   - Review git diff and recent commits
   - Check for new dependencies or config changes
   - Identify environmental differences

4. **Add Diagnostic Instrumentation for Multi-Component Systems**

   When debugging systems with multiple layers (CI → build → signing, API → service → database):

   **Add logging at EACH component boundary:**
   - Log input data entering component
   - Log output data exiting component
   - Verify environment/config propagation
   - Check state at each layer

   **Run once to gather evidence, THEN analyze to identify failing component**

   Example for multi-layer system:
   ```bash
   # Layer 1: Check workflow environment
   echo "=== Workflow secrets: ==="
   echo "IDENTITY: ${IDENTITY:+SET}${IDENTITY:-UNSET}"

   # Layer 2: Check build script environment
   echo "=== Build script environment: ==="
   env | grep IDENTITY || echo "IDENTITY not in environment"

   # Layer 3: Check signing state
   echo "=== Keychain state: ==="
   security list-keychains
   security find-identity -v

   # Layer 4: Verbose signing
   codesign --sign "$IDENTITY" --verbose=4 "$APP"
   ```

   This reveals which layer fails (e.g., secrets → workflow ✓, workflow → build ✗)

#### Phase 2: Pattern Analysis

**Understand the pattern before proposing fixes:**

1. **Find Working Examples**
   - Locate similar working code in the codebase
   - Identify what works that's similar to what's broken

2. **Compare Against References**
   - If implementing a pattern, read reference implementation COMPLETELY
   - Read every line, don't skim
   - Understand the full pattern before applying

3. **Identify All Differences**
   - List every difference between working and broken code
   - Include small differences - don't assume "that can't matter"

4. **Understand Dependencies**
   - Identify required components, settings, config, environment
   - Document assumptions the code makes

#### Phase 3: Hypothesis and Testing

**Apply scientific method:**

1. **Form Single, Specific Hypothesis**
   - State clearly: "I think X is the root cause because Y"
   - Be specific, avoid vague statements

2. **Test with Minimal Change**
   - Make the SMALLEST possible change to test hypothesis
   - Change one variable at a time
   - Never fix multiple things simultaneously

3. **Verify Result**
   - If it worked → proceed to Phase 4
   - If it didn't work → form NEW hypothesis, return to step 1
   - Never add more fixes on top of failed fixes

4. **Acknowledge Uncertainty**
   - If you don't understand something, say so explicitly
   - Ask for clarification or research more
   - Never pretend to know or guess

#### Phase 4: Implementation

**Fix the root cause, not symptoms:**

1. **Create Failing Test Case First**
   - Write simplest possible reproduction
   - Use automated test if possible, otherwise one-off test script
   - MUST create test before implementing fix
   - Follow TDD principles

2. **Implement Single Fix**
   - Address only the root cause identified
   - Make ONE change at a time
   - No "while I'm here" improvements
   - No bundled refactoring

3. **Verify Fix Completely**
   - Confirm new test passes
   - Confirm no other tests broken
   - Verify issue actually resolved

4. **If Fix Doesn't Work**
   - STOP and count attempted fixes
   - If < 3 attempts: Return to Phase 1 with new information
   - If ≥ 3 attempts: Proceed to step 5
   - Never attempt 4th fix without architectural discussion

5. **After 3 Failed Fixes: Question Architecture**

   **Indicators of architectural problems:**
   - Each fix reveals new problems in different places
   - Fixes require massive refactoring
   - Each fix creates new symptoms elsewhere

   **Action required:**
   - Question whether the pattern is fundamentally sound
   - Discuss with user before attempting more fixes
   - Consider architectural refactoring vs. symptom fixing

   This is not a failed hypothesis - this indicates wrong architecture.

### Red Flags - STOP and Follow Process

If you catch yourself thinking:
- "Quick fix for now, investigate later"
- "Just try changing X and see if it works"
- "Add multiple changes, run tests"
- "Skip the test, I'll manually verify"
- "It's probably X, let me fix that"
- "I don't fully understand but this might work"
- "Pattern says X but I'll adapt it differently"
- "Here are the main problems: [lists fixes without investigation]"
- Proposing solutions before tracing data flow
- **"One more fix attempt" (when already tried 2+)**
- **Each fix reveals new problem in different place**

**ALL of these mean: STOP. Return to Phase 1.**

**If 3+ fixes failed:** Question the architecture (see Phase 4.5)

### your human partner's Signals You're Doing It Wrong

**Watch for these redirections:**
- "Is that not happening?" - You assumed without verifying
- "Will it show us...?" - You should have added evidence gathering
- "Stop guessing" - You're proposing fixes without understanding
- "Ultrathink this" - Question fundamentals, not just symptoms
- "We're stuck?" (frustrated) - Your approach isn't working

**When you see these:** STOP. Return to Phase 1.

### Common Rationalizations

| Excuse                                       | Reality                                                                 |
| -------------------------------------------- | ----------------------------------------------------------------------- |
| "Issue is simple, don't need process"        | Simple issues have root causes too. Process is fast for simple bugs.    |
| "Emergency, no time for process"             | Systematic debugging is FASTER than guess-and-check thrashing.          |
| "Just try this first, then investigate"      | First fix sets the pattern. Do it right from the start.                 |
| "I'll write test after confirming fix works" | Untested fixes don't stick. Test first proves it.                       |
| "Multiple fixes at once saves time"          | Can't isolate what worked. Causes new bugs.                             |
| "Reference too long, I'll adapt the pattern" | Partial understanding guarantees bugs. Read it completely.              |
| "I see the problem, let me fix it"           | Seeing symptoms ≠ understanding root cause.                             |
| "One more fix attempt" (after 2+ failures)   | 3+ failures = architectural problem. Question pattern, don't fix again. |

### Quick Reference

| Phase                 | Key Activities                                         | Success Criteria            |
| --------------------- | ------------------------------------------------------ | --------------------------- |
| **1. Root Cause**     | Read errors, reproduce, check changes, gather evidence | Understand WHAT and WHY     |
| **2. Pattern**        | Find working examples, compare                         | Identify differences        |
| **3. Hypothesis**     | Form theory, test minimally                            | Confirmed or new hypothesis |
| **4. Implementation** | Create test, fix, verify                               | Bug resolved, tests pass    |

### When Process Reveals "No Root Cause"

If systematic investigation reveals issue is truly environmental, timing-dependent, or external:

1. You've completed the process
2. Document what you investigated
3. Implement appropriate handling (retry, timeout, error message)
4. Add monitoring/logging for future investigation

**But:** 95% of "no root cause" cases are incomplete investigation.

### Real-World Impact

From debugging sessions:
- Systematic approach: 15-30 minutes to fix
- Random fixes approach: 2-3 hours of thrashing
- First-time fix rate: 95% vs 40%
- New bugs introduced: Near zero vs common

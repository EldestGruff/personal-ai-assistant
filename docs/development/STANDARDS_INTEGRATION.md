# Personal AI Assistant - Master Development Standards Integration

**Status:** Foundation Integration  
**Last Updated:** December 10, 2025

---

## Overview

This document integrates your established master development prompts into the Personal AI Assistant project. Every specification, code generation request, and architectural decision will be bound by these standards to ensure consistency, quality, and long-term maintainability.

---

## Core Standards Applied to This Project

### From "System prompt - Scripting/Coding"

#### Reasoning Protocol
- ✅ **Thorough thinking before every response** - Specifications will include detailed analysis
- ✅ **Multiple approaches considered** - Specs will show option analysis
- ✅ **Systematic troubleshooting** - When issues arise, we verify rather than assume
- ✅ **Code exploration** - All generated code will be reviewed against patterns
- ✅ **Checkpoint preservation** - Git branches and commits preserve working state

#### Code Quality Standards
- ✅ **Detailed, helpful comments** - "Why," not "what"
- ✅ **Efficient implementation** - Combine operations, use appropriate tools
- ✅ **Direct file editing** - Don't create new files with different names
- ✅ **Module organization** - Keep related code together
- ✅ **Split when appropriate** - Large functions/files get broken down

#### Version Control (Customized for This Project)
```
Git user.name:  Andy
Git user.email: andy@fennerfam.com  (use your actual email)
```

#### Problem-Solving Workflow (Critical for Avoiding AutoDev/SIDHE Failures)

When we encounter issues:
1. **EXPLORATION** - Understand the codebase, look at previous code
2. **ANALYSIS** - Consider multiple approaches
3. **TESTING** - Create tests to verify issues
4. **IMPLEMENTATION** - Make focused, minimal changes
5. **VERIFICATION** - Test thoroughly

**Important:** If troubleshooting takes >30 minutes, we'll branch conversation to keep context clean.

---

### From "Master Development Prompt"

#### Core Development Philosophy (For All Specs)

Every spec I write will follow these principles:

| Principle | Applied To This Project |
|-----------|------------------------|
| **Clarity over Cleverness** | Simple FastAPI routes, straightforward database queries |
| **Explicit over Implicit** | Clear data structures, no magic behavior |
| **Simple over Complex** | MVP first, optimize later |
| **Tested over Assumed** | 80% test coverage minimum |
| **Documented over Obvious** | Architecture decisions recorded in ADRs |

#### Thinking Process (For Every Spec)

Before generating code, the spec will:

1. **UNDERSTAND the problem completely**
   - What is the actual requirement?
   - What are edge cases?
   - What could go wrong?
   - Who will use this and how?

2. **EXPLORE multiple approaches**
   - List 3+ different solutions
   - Consider pros/cons
   - Think about future maintenance
   - Performance implications

3. **PLAN the implementation**
   - Break into small, testable units
   - Identify dependencies
   - Plan testing strategy
   - Consider error handling

4. **VALIDATE the approach**
   - Is it maintainable?
   - Can another developer understand it?
   - All failure modes considered?
   - Simplest solution that works?

#### Code Structure & Organization

All generated code will follow:

```
project/
├── docs/                 # Architecture decisions, API docs
├── src/
│   ├── api/             # FastAPI routes
│   ├── models/          # SQLAlchemy/Pydantic models
│   ├── services/        # Business logic (Claude integration, storage)
│   ├── utils/           # Shared utilities
│   └── __init__.py
├── tests/               # Mirror src/ structure
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── docker/              # Dockerfile, docker-compose.yml
├── scripts/             # Deployment, maintenance scripts
├── requirements.txt
├── .gitignore
├── README.md
└── .env.example
```

#### Naming Conventions (Strict)

| Type | Convention | Example |
|------|-----------|---------|
| Classes | DescriptiveNoun | `ThoughtService`, `ClaudeOrchestrator` |
| Functions | verb_noun_phrase | `create_thought()`, `fetch_related_thoughts()` |
| Variables | descriptive_noun | `user_context`, `thought_count`, `is_archived` |
| Constants | UPPERCASE_WITH_UNDERSCORES | `MAX_THOUGHT_LENGTH`, `API_RETRY_ATTEMPTS` |
| Files/Modules | lowercase_with_underscores | `thought_service.py`, `claude_integration.py` |

#### Function Design Rules (Strict)

Every function will:
- ✅ Do ONE thing well
- ✅ Be under 20 lines (break down if longer)
- ✅ Have max 3 parameters (use objects for more)
- ✅ Have clear return types
- ✅ Have no side effects (unless that's the purpose)

#### Test-Driven Development (Testing Pyramid)

```
         /\
        /e2e\        5% - End-to-end tests
       /------\
      /integrat\    15% - Integration tests  
     /----------\
    /   unit     \  80% - Unit tests
   /--------------\
```

**Comprehensive Test Checklist (Every Function):**

- [ ] Input validation (null, wrong type, boundary values)
- [ ] Logic coverage (happy path, each branch, edge cases)
- [ ] Error handling (exceptions, cleanup, partial failures)
- [ ] Integration points (external services, network, race conditions)

**Test Naming Convention:**
```
test_functionName_scenario_expectedBehavior()

Examples:
test_create_thought_with_valid_input_returns_thought_object()
test_fetch_similar_thoughts_empty_database_returns_empty_list()
test_send_to_claude_network_timeout_retries_three_times()
```

#### Documentation Standards

**Comments: Explain WHY, not WHAT**

```python
# BAD: Explains WHAT (redundant)
x = x + 1  # Increment x by 1

# GOOD: Explains WHY (valuable)
x = x + 1  # Offset by 1 to account for header row in thought CSV

# GOOD: Explains WARNING
x = x + 1  # WARNING: Do not remove - fixes off-by-one error in legacy API
```

**Function Documentation Template:**

```python
def create_thought(content: str, user_id: str, tags: list[str] = None) -> Thought:
    """
    Create a new thought and store it in the database.
    
    This function validates input, assigns metadata (timestamp, ID),
    and persists to SQLite. It does NOT call Claude API directly.
    
    Args:
        content (str): The thought text (max 5000 characters)
        user_id (str): UUID of the user creating the thought
        tags (list[str], optional): List of tags (max 5, max 50 chars each)
        
    Returns:
        Thought: Created thought object with:
            - id (str): UUID of the thought
            - timestamp (datetime): Creation time in UTC
            - content (str): Original content
            - tags (list[str]): Assigned tags
            
    Raises:
        ValueError: If content is empty or exceeds 5000 characters
        ValueError: If user_id is not a valid UUID
        ValueError: If more than 5 tags provided
        DatabaseError: If database write fails
        
    Example:
        >>> thought = create_thought(
        ...     content="Should improve the email tool",
        ...     user_id="550e8400-e29b-41d4-a716-446655440000",
        ...     tags=["email", "improvement"]
        ... )
        >>> print(thought.id)
        'a8f4c2b1-9d7e-4e3f-8b6c-1a2d3e4f5g6h'
        
    Note:
        This function is synchronous. For async usage, use create_thought_async().
    """
```

**Architecture Decision Records (ADR)**

Every major decision documented:

```markdown
# ADR-001: Use SQLite for Thought Storage

## Status
Accepted (Dec 10, 2025)

## Context
Need persistent storage for thoughts captured throughout the day. Options: SQLite, PostgreSQL, MongoDB, Cloud storage.

## Options Considered
1. **SQLite** - Simple, file-based, zero ops
   - Pros: Embedded, no server, good for local testing, ZFS snapshots
   - Cons: Single writer, not ideal for high concurrency
   
2. **PostgreSQL** - Full RDBMS
   - Pros: Scalable, robust, good for future growth
   - Cons: Extra ops burden, overkill for personal assistant MVP
   
3. **MongoDB** - Document store
   - Pros: Flexible schema, JSON-native
   - Cons: Overkill for structured thought/task data

## Decision
Use SQLite for Phase 1-2. Migrate to PostgreSQL if concurrency becomes an issue (unlikely for personal use).

## Consequences
- ✅ Zero ops overhead, easier to test locally
- ✅ Easy snapshots/backups via ZFS
- ⚠️ Single-writer limit (mitigated by async queue in future)
- ⚠️ Not suitable for 100+ concurrent users (not our use case)

## Review Date
March 2026 (after Phase 3 launch)
```

#### Version Control Standards

**Commit Message Format:**

```
type(scope): subject

body (optional)

footer (optional)

Types:
- feat: New feature
- fix: Bug fix  
- docs: Documentation only
- style: Formatting, no code change
- refactor: Code restructuring
- test: Adding tests
- chore: Maintenance
```

**Examples:**

```
feat(api): add thought search endpoint

Implements full-text search on thought content and tags.
Uses SQLite FTS5 for performance. Supports filters by
date range and tag.

Closes #12

---

test(models): add comprehensive thought validation tests

Added tests for edge cases:
- Max content length (5000 chars)
- Special characters in tags
- Empty content rejection
- Timestamp validation

All tests pass.

---

docs(architecture): add ADR-001 for SQLite decision

Documented rationale for choosing SQLite for Phase 1,
with migration plan to PostgreSQL if needed.
```

**Branch Strategy:**

```
main              - Production-ready, tagged releases
develop           - Integration branch for features
feature/xxx       - New features (feat(scope): title)
bugfix/xxx        - Bug fixes (fix(scope): title)  
docs/xxx          - Documentation (docs(scope): title)
refactor/xxx      - Code restructuring (refactor(scope): title)
```

#### Error Handling Philosophy

**Fail Fast, Fail Clearly**

```python
# BAD: Silent failure
def get_thought(thought_id):
    thought = db.query(thought_id)
    return thought  # Returns None if not found - caller confused

# GOOD: Clear failure
def get_thought(thought_id: str) -> Thought:
    thought = db.query(thought_id)
    if not thought:
        raise ThoughtNotFoundError(
            f"Thought with ID '{thought_id}' not found. "
            f"Use list_thoughts() to see available thoughts. "
            f"If you believe this is an error, check database backups."
        )
    return thought
```

**Error Messages Must:**
1. Say what went wrong
2. Include relevant context
3. Suggest how to fix it
4. Be actionable

#### Code Review Checklist (Before Every Commit)

- [ ] **Functionality**: Does it solve the stated problem?
- [ ] **Code Quality**: Readable without comments? Descriptive names? DRY? As simple as possible?
- [ ] **Testing**: Tests for new functionality? Edge cases covered? All tests pass?
- [ ] **Documentation**: Complex parts documented? README updated? API changes documented?
- [ ] **Performance**: No obvious bottlenecks? Appropriate data structures?
- [ ] **Security**: Input validated? No sensitive data in logs? SQL injection prevented?

#### Metrics to Track

| Metric | Target |
|--------|--------|
| Test Coverage | >80% |
| Cyclomatic Complexity | <10 per function |
| Function Length | <20 lines |
| Documentation Coverage | 100% of public APIs |

**Red Flags:**
- Functions > 50 lines → needs refactor
- Classes > 300 lines → split responsibilities
- >5 parameters → use objects
- >3 levels of nesting → simplify
- Copy-pasted code → extract function/class
- TODO comments > 1 month old → address or delete

---

## How These Standards Shape Specifications

### When I Create a Spec, You'll See:

1. **Problem Analysis** (from Thinking Process)
   - What we're building and why
   - Who uses it and how
   - Edge cases identified

2. **Approach Options** (from Thinking Process)
   - 3+ solutions evaluated
   - Pros/cons for each
   - Recommended approach with rationale

3. **Detailed Plan** (from Code Structure)
   - Clear data models
   - Function signatures
   - API contracts
   - Error handling

4. **Testing Strategy** (from TDD)
   - Unit tests to write
   - Integration tests needed
   - Test coverage expectations
   - Example test cases

5. **Code Examples** (from Documentation)
   - Sample data structures
   - Example function implementation
   - Expected API responses
   - Error scenarios

6. **Implementation Checklist** (from Code Review)
   - Things to verify
   - Standards to follow
   - Documentation requirements

---

## Handoff To Sonnet/Opus

When you run specs through Sonnet or Opus, include this header:

```
You are generating code for Andy's Personal AI Assistant project.

CRITICAL STANDARDS:
- All code must pass this standards checklist: [link to this doc]
- Code Quality: Functions under 20 lines, max 3 params, single responsibility
- Testing: 80%+ coverage, comprehensive edge case tests
- Documentation: docstrings for every function, comments explain WHY not WHAT
- Naming: Strict conventions (see standards doc)
- Error Handling: Fail fast, clear messages, actionable suggestions
- Version Control: Proper commit messages, atomic commits

When generating code:
1. Include complete implementation (not stubs)
2. Write comprehensive tests first (TDD approach)
3. Add docstrings and comments per standards
4. Organize into proper module structure
5. Include error handling and validation
6. Explain architectural choices in comments

Generate code suitable for immediate integration into the repository.
```

---

## Workflow Check-In Points

At each phase, we verify:

- [ ] Code follows all naming conventions
- [ ] Functions are under 20 lines
- [ ] Tests cover edge cases (80%+ coverage)
- [ ] Docstrings complete and accurate
- [ ] Comments explain WHY, not WHAT
- [ ] Error handling is explicit and clear
- [ ] No sensitive data exposed
- [ ] Commits are atomic with clear messages
- [ ] ADRs documented for major decisions
- [ ] Code review checklist passed

---

## If Code Doesn't Meet Standards

**For Minor Issues (naming, formatting):**
- I'll fix in-place before integrating

**For Major Issues (missing tests, unclear logic):**
- I'll flag, request regeneration with more specific guidance
- Won't accept into main branch until standards met

**For Architectural Mismatch:**
- We'll pause, create ADR, discuss approach
- Update spec with decision
- Regenerate if needed

---

## Success = Clean Codebase + Happy Future-You

This approach ensures:
- ✅ Code is maintainable long-term
- ✅ You can understand it 6 months later
- ✅ New features integrate cleanly
- ✅ Tests prevent regressions
- ✅ Decisions are documented
- ✅ We avoid AutoDev/SIDHE chaos

---

## Questions/Adjustments?

These standards are locked in unless you want to adjust them. If any don't feel right for this project, let me know before Phase 2A specs.

Think of this as your "development constitution"—guides all decisions, easy to reference, prevents drift.

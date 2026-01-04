# Project Orchestration Strategy

**Using Advanced Tool Use Patterns to Avoid Previous Failures**

---

## Philosophy

The failures of AutoDev Commander and SIDHE stemmed from:
1. **Insufficient specification** before code generation
2. **Lack of clear handoffs** between AI and human
3. **Monolithic approach** (everything at once)
4. **No persistent source of truth** (documentation drifted from code)

**This time:**
- **Ivy (me) orchestrates** - tracks state, maintains specs, coordinates
- **Sonnet/Opus generates** - detailed code from specifications I provide
- **You validate and decide** - human judgment on all major decisions
- **Git is source of truth** - code, specs, decisions live there

---

## How I'll Use Advanced Tool Use Patterns

### 1. Tool Search Tool Pattern

**What I'll do:**
- Instead of trying to handle everything at once, I'll organize my "available tools" clearly
- You can ask for specific capabilities ("I need Docker deployment setup") and I'll find the right approach
- This keeps context clean and prevents context overload

**Applied to this project:**
- **Tool categories I manage:**
  - Architecture & specification writing
  - Coordination with Sonnet/Opus
  - Git workflow and tracking
  - Docker/TrueNAS deployment planning
  - SSH/security infrastructure
  - API design and documentation
  - Testing strategy

- **When you ask for something**, I search my capability space:
  - "Do we have a spec for this yet?"
  - "Does Sonnet/Opus need to generate this, or can I handle it?"
  - "What prerequisites are missing?"

### 2. Programmatic Tool Calling Pattern

**What I'll do:**
- When coordinating complex tasks (like "generate FastAPI service AND test suite AND Docker setup"), I won't ask you to run 3 separate Sonnet prompts
- Instead, I'll give you **one consolidated spec** that says "Run THIS through Sonnet, which will handle all three"
- This reduces round-trips and context pollution

**Applied to this project:**
- **Consolidated spec examples:**
  - "Spec: FastAPI service + SQLite models + basic CRUD endpoints" (single Sonnet run)
  - "Spec: Comprehensive test suite + fixtures + CI/CD structure" (single Sonnet run)
  - "Spec: Docker Dockerfile + docker-compose.yml + deployment guide" (single Sonnet run)

- **I'll track dependencies:**
  - "Spec B depends on outputs from Spec A"
  - "You need to run Spec A first"
  - Clear sequencing to avoid rework

### 3. Tool Use Examples Pattern

**What I'll do:**
- When I ask Sonnet/Opus to generate code, I'll include **concrete examples** in the spec
  - "Here's what a Thought object should look like"
  - "Here's an example API response"
  - "Here's the expected directory structure after generation"

- This reduces ambiguity and improves code quality

**Applied to this project:**
- Each spec will include:
  - Example data structures
  - Example API calls (request/response)
  - Example database queries
  - Example error handling patterns
  - Example test cases

---

## Specification and Handoff Workflow

### Phase 2A: Core Backend Specification (Week 1)

**I will create and you will review:**

1. **Data Models Spec** (for Sonnet)
   - Thought model with fields, relationships
   - Task model
   - Context model
   - Examples of each as JSON

2. **API Specification** (for Sonnet)
   - Endpoint definitions (POST /api/thoughts, etc.)
   - Request/response schemas
   - Error codes and messages
   - Authentication approach

3. **Database Schema Spec** (for Sonnet)
   - SQLite table structures
   - Indexes and relationships
   - Migrations approach

**Then you run through Sonnet:**
```
Spec 2A-1: Data Models
Spec 2A-2: API Specification
Spec 2A-3: Database Schema
```

**Output:** Generated FastAPI service stub with models, routes, database definitions

---

### Phase 2B: Core Service Implementation (Week 1-2)

**I will create and you will review:**

4. **Thought CRUD Implementation** (for Sonnet)
   - Create, read, update, delete operations
   - Search and filter logic
   - Database transactions

5. **Claude Integration Layer** (for Sonnet)
   - Service that calls Claude API
   - Prompt templates
   - Context management
   - Error handling

6. **Test Suite** (for Opus - more comprehensive)
   - Unit tests for all CRUD operations
   - Integration tests with Claude API (mocked)
   - Fixtures and factories

**Then you run through Sonnet/Opus:**
```
Spec 2B-1: Thought CRUD Implementation
Spec 2B-2: Claude Integration Layer
Spec 2B-3: Test Suite (Opus)
```

**Output:** Working backend service with tests

---

### Phase 2C: Docker & Deployment (Week 2)

**I will create and you will review:**

7. **Docker Configuration** (for Sonnet)
   - Dockerfile for FastAPI service
   - docker-compose for local development
   - Environment variables, volumes, networking

8. **TrueNAS Deployment Guide** (for Sonnet)
   - Step-by-step deployment to Docker on moria
   - ZFS dataset mounting
   - Service persistence and restart policies

9. **Monitoring & Logging** (for Sonnet)
   - Basic logging setup
   - Health check endpoints
   - Error tracking

**Then you run through Sonnet:**
```
Spec 2C-1: Docker Configuration
Spec 2C-2: TrueNAS Deployment Guide
Spec 2C-3: Monitoring & Logging
```

**Output:** Containerized service ready for moria

---

### Phase 3A: Web Interface (Week 3)

**I will create and you will review:**

10. **Web UI Specification** (for Sonnet)
    - HTML/CSS/JS for thought capture form
    - Thought list view
    - Search interface
    - Dashboard mockups

11. **API Client** (for Sonnet)
    - JavaScript fetch wrappers
    - State management
    - Error handling on frontend

**Output:** Functional web interface

---

### Phase 4: iOS Integration (Week 3-4)

**I will create and you will review:**

12. **iOS Shortcut Spec** (for you to implement, I'll guide)
    - Quick-capture Shortcut
    - Integration with web API
    - Siri Shortcuts workflow

**Output:** iPhone quick-capture working

---

## Each Specification Will Include

### Template (you'll see this for every spec):

```markdown
# Spec [N]: [Feature Name]

## Overview
[What this does, why it matters]

## Requirements
- [Requirement 1]
- [Requirement 2]
- [Dependencies: Spec X, Spec Y]

## Data Structures / Examples
[JSON examples of data involved]

## Implementation Details
[Specifics on how to build this]

## Testing Strategy
[What should be tested]

## Error Handling
[Edge cases, error scenarios]

## Code Examples
[Skeleton or expected patterns]

## Success Criteria
- [ ] Can do X
- [ ] Handles edge case Y
- [ ] Tests pass
```

---

## Coordination Rules (To Avoid AutoDev/SIDHE Failures)

### Rule 1: Git is Source of Truth
- Every major decision documented in a commit message
- Every generated file tagged with "Generated from Spec N"
- Easy to trace which spec produced which code

### Rule 2: Specifications Before Code
- Never generate code for a feature without a spec
- Specs are reviewed and approved before running through Sonnet/Opus
- If direction changes, spec gets updated, code gets regenerated

### Rule 3: One Feature at a Time
- Don't try to build everything at once
- Complete Phase 2A before moving to 2B
- Test and verify each phase before next
- This prevents "context overload" that killed AutoDev

### Rule 4: Clear Handoffs
- You know exactly what I'm asking Sonnet/Opus to do
- You can review specs before running them
- You see the output before I integrate it
- Human decides what's acceptable

### Rule 5: Documentation Stays Current
- Architecture doc updates as we learn
- Each spec becomes a permanent record
- README.md evolves with the project
- Future-you can understand the decisions

---

## Communication Pattern

**You:**
- "Ivy, I'm ready for Phase 2A specs"
- "Review this spec - does it make sense?"
- "Here's the output from Sonnet, what do I do next?"
- "We should change the approach because X"

**Me (Ivy):**
- "Phase 2A specs ready for review"
- "Here's the spec, here's what I'm asking Sonnet to do"
- "I see Sonnet generated X - here's how we integrate it"
- "Updated the architecture doc to reflect the change"

---

## Success Indicators (How We'll Know This Works)

✅ Each phase completed on schedule
✅ Code quality from Sonnet/Opus needs minimal revision
✅ Tests pass consistently
✅ Zero context/architecture rework (unlike AutoDev)
✅ You can understand any part of the codebase by reading specs
✅ Git history tells a clear story
✅ Docker deployment to moria works first try
✅ iPhone can capture a thought in <10 seconds by Week 4

---

## If Things Go Wrong

**If Sonnet spec-following fails:**
- We'll add more detailed examples
- We'll break specs into smaller pieces
- We'll run through Opus instead (more verbose)

**If architecture doesn't work:**
- We stop, update the architecture doc
- We regenerate from updated spec
- We don't patch/hack around it

**If timeline slips:**
- We identify the blocker
- We adjust scope or ask for help
- We don't sacrifice quality for schedule

---

## Next Steps

1. **You complete Phase 0** (Docker, SSH, Git setup)
2. **I create Phase 2A specs** (data models, API, database)
3. **You review Phase 2A specs**
4. **You run Spec 2A-1, 2A-2, 2A-3 through Sonnet**
5. **I review Sonnet outputs, integrate into repo**
6. **Rinse and repeat for each phase**

---

## Questions Before We Start?

This is your chance to poke holes:
- Does the phase breakdown make sense?
- Are there features I'm missing?
- Do you want to change the order?
- Is the timeline realistic?

Once you're comfortable, we execute.

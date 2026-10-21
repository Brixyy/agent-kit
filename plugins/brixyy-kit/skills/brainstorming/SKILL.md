---
name: brainstorming
description: "You MUST use this before any creative work - creating features, building components, adding functionality, or modifying behavior. Explores user intent, requirements and design before implementation."
version: "1.0.0"
effort: high
author: Brixyy
---

# Brainstorming Ideas Into Designs

## Overview

Help turn ideas into fully formed designs and specs through natural collaborative dialogue.

Start by understanding the current project context, then ask questions one at a time to refine the idea. Once you understand what you're building, present the design in small sections (200-300 words), checking after each section whether it looks right so far.

## The Process

### Phase 1: Understanding the Idea

- Check out the current project state first (files, docs, recent commits)
- Ask questions one at a time to refine the idea
- Prefer multiple choice questions when possible, but open-ended is fine too
- Only one question per message - if a topic needs more exploration, break it into multiple questions
- Focus on understanding: purpose, constraints, success criteria

### Phase 2: Exploring Approaches

- Propose 2-3 different approaches with trade-offs
- Present options conversationally with your recommendation and reasoning
- Lead with your recommended option and explain why

### Phase 3: Presenting the Design

- Once you believe you understand what you're building, present the design
- Break it into sections of 200-300 words
- Ask after each section whether it looks right so far
- Cover: architecture, components, data flow, error handling, testing
- Be ready to go back and clarify if something doesn't make sense

### Phase 4: After the Design

**Documentation:**
- Write the validated design to `docs/plans/YYYY-MM-DD-<topic>-design.md`
- Use elements-of-style:writing-clearly-and-concisely skill if available
- Commit the design document to git

**Implementation (if continuing):**
- Ask: "Ready to set up for implementation?"
- Use superpowers:using-git-worktrees to create isolated workspace
- Use superpowers:writing-plans to create detailed implementation plan

## Structured Brainstorming Frameworks

Use these frameworks when the idea is vague or when you need to push thinking further.

### SCAMPER Method

Apply SCAMPER to challenge assumptions and generate alternatives:

| Letter | Question | Example |
|--------|----------|---------|
| **S** - Substitute | What can we replace? | "Use WebSocket instead of polling?" |
| **C** - Combine | What can we merge? | "Combine auth + profile into one flow?" |
| **A** - Adapt | What can we borrow from elsewhere? | "Adapt Stripe's checkout UX for our flow?" |
| **M** - Modify | What can we change/enlarge/shrink? | "Make the dashboard widget-based instead of fixed?" |
| **P** - Put to other use | Can we repurpose existing code? | "Reuse the notification system for alerts?" |
| **E** - Eliminate | What can we remove? | "Drop the admin panel for MVP?" |
| **R** - Reverse/Rearrange | What if we flip the flow? | "Let users configure after signup, not during?" |

**When to use:** Early in Phase 2 when exploring approaches. Pick 2-3 relevant SCAMPER letters, don't force all seven.

### Mind Mapping Process

For complex features, build a structured mind map:

```
                    ┌─ Authentication
                    │   ├─ OAuth providers
                    │   └─ Session management
                    │
Feature Name ───────┼─ Data Model
                    │   ├─ Entities
                    │   ├─ Relationships
                    │   └─ Migrations
                    │
                    ├─ UI Components
                    │   ├─ Pages
                    │   ├─ Shared components
                    │   └─ State management
                    │
                    └─ Integration Points
                        ├─ APIs
                        ├─ Webhooks
                        └─ Third-party services
```

**Steps:**
1. Put the core feature in the center
2. Branch into 3-5 major categories (data, UI, integrations, infrastructure)
3. Add 2-4 sub-items per category
4. Identify connections between branches (shared dependencies, data flow)
5. Present to user section by section for validation

### Prioritization Methods

Use these after generating ideas to decide what to build first.

#### MoSCoW Method

Categorize every proposed feature/component:

| Priority | Meaning | Rule |
|----------|---------|------|
| **Must have** | MVP fails without it | Max 60% of scope |
| **Should have** | Important but workaround exists | Next iteration |
| **Could have** | Nice to have | If time permits |
| **Won't have** | Explicitly out of scope | Document for future |

**Example output:**

```markdown
## MoSCoW Prioritization

### Must Have (MVP)
- User registration and login
- Core dashboard with key metrics
- Data export as CSV

### Should Have (v1.1)
- OAuth social login
- Dashboard customization
- Email notifications

### Could Have (v1.2)
- Dark mode
- Keyboard shortcuts
- Bulk operations

### Won't Have (documented for future)
- Mobile app
- Multi-language support
- AI-powered recommendations
```

#### ICE Scoring

For ranking individual features or approaches numerically:

| Factor | Scale | Question |
|--------|-------|----------|
| **Impact** | 1-10 | How much will this move the needle? |
| **Confidence** | 1-10 | How sure are we this will work? |
| **Ease** | 1-10 | How easy is this to implement? |

**Score = Impact x Confidence x Ease**

**Example output:**

```markdown
## ICE Scoring

| Feature | Impact | Confidence | Ease | Score |
|---------|--------|------------|------|-------|
| Search functionality | 9 | 8 | 6 | 432 |
| User notifications | 7 | 9 | 7 | 441 |
| Analytics dashboard | 8 | 6 | 4 | 192 |
| Social sharing | 5 | 7 | 8 | 280 |

**Recommendation:** Start with User notifications (441) and Search (432).
```

**When to use which:**
- **MoSCoW** - When deciding MVP scope (Phase 2, after approaches are clear)
- **ICE** - When ranking a backlog of features or comparing approaches quantitatively

## Example Brainstorming Session

```
User: I want to add a notification system to the app.

You: I'm using the brainstorming skill to explore this idea.

[Check project state - React + Supabase app, no existing notification code]

You: What's the primary trigger for notifications - user actions
(like comments/mentions), system events (like job completion),
or both?

User: Both, but user actions are more important.

You: Got it. For delivery, which is the MVP priority?
  A) In-app only (bell icon + dropdown)
  B) In-app + email
  C) In-app + push notifications

User: A, just in-app for now.

You: Here's my recommended approach...

[Present architecture in 200-300 word sections]
[Apply MoSCoW: in-app bell = Must, email = Should, push = Won't]
[Validate each section]
[Write design doc]
[Offer implementation setup]
```

## Do

- Ask one question at a time
- Prefer multiple choice questions
- Lead with your recommendation and explain why
- Present design in 200-300 word sections
- Apply YAGNI ruthlessly - remove unnecessary features
- Use SCAMPER when stuck or exploring alternatives
- Use MoSCoW to define MVP scope
- Use ICE scoring when comparing multiple feature candidates
- Validate each design section before moving on
- Commit the design document to git

## Don't

- Overwhelm with multiple questions at once
- Present the entire design in one wall of text
- Skip the exploration phase and jump to implementation
- Force all SCAMPER letters - pick 2-3 relevant ones
- Use ICE scoring for fewer than 3 options (just discuss trade-offs instead)
- Add features "just in case" - YAGNI
- Proceed to implementation without explicit user approval of the design
- Skip writing the design document

## Key Principles

- **One question at a time** - Don't overwhelm with multiple questions
- **Multiple choice preferred** - Easier to answer than open-ended when possible
- **YAGNI ruthlessly** - Remove unnecessary features from all designs
- **Explore alternatives** - Always propose 2-3 approaches before settling
- **Incremental validation** - Present design in sections, validate each
- **Be flexible** - Go back and clarify when something doesn't make sense
- **Framework-assisted, not framework-driven** - Use SCAMPER/MoSCoW/ICE as tools, not checklists

## Integration

**Leads to:**
- **using-git-worktrees** - REQUIRED when design is approved and implementation follows
- **writing-plans** - REQUIRED for creating detailed implementation plan from the design

**Can use:**
- **elements-of-style:writing-clearly-and-concisely** - For polishing the design document

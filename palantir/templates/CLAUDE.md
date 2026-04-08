# CLAUDE.md -- Obsidian Vault Operating Rules

> Claude reads this file at the start of every session.
> All decisions are based on this document and the Ground Truth file.
> Customize each section to match your vault and workflow.

---

## 1. Vault Structure

### 1-1. Folder Organization (PARA)

| Folder | Purpose | Notes |
|--------|---------|-------|
| 0. Slip-Box | Atomic, connected, own-words notes | Zettelkasten permanent notes, highest priority |
| 1. Projects | Concrete deliverables with deadlines | Active projects only |
| 2. Area of Responsibility | Ongoing responsibilities, no deadline | Operations, personal thinking, references, system |
| 3. Resources | External info, tools, frameworks | Reference material |
| 4. Archives | Completed or paused items | Periodic mining target |

### 1-2. Zettelkasten Rules

- **Slip-Box note format**: frontmatter (tags, created, source, luhmann) required
- **Bridge keywords**: 3-5 per note, never more than 5
- **Last line of every note**: `Bridge keywords: [[kw1]] [[kw2]] [[kw3]]`
- **Luhmann numbering**: continuing = 7A->7B, deepening = 7A->7A-1
- **Category prefixes**: customize to your domains (e.g., B=Business, M=Mission, P=Philosophy)

### 1-3. Processing Pipeline

1. **Acquire** -- daily notes, reading logs, web clips (always note "why did I save this?")
2. **Relate** -- evaluate -> approve -> promote to Slip-Box (minimum 2 connections). Use Progressive Summarization (bold -> highlight -> summary).
3. **Create** -- topic input -> search research notes -> draft -> publish. Break into Intermediate Packets, complete 1 IP per session.

### 1-4. Core Bridge Keywords

> List your 10-30 core bridge keywords here.
> These are the themes that run through your thinking.

```
[[keyword_1]] [[keyword_2]] [[keyword_3]]
[[keyword_4]] [[keyword_5]] [[keyword_6]]
...
```

Full list: see your Ground Truth file.

---

## 2. Active Context

> **Rule: Update this section before every work session.**
> If not updated, Claude operates on stale context.

### Current Focus Projects

- **Project A**: [description, current status]
- **Project B**: [description, current status]

### Energy Allocation

- Project A: ___%
- Project B: ___%
- **Priority rule**: [which project yields to which when time is tight]

### This Cycle Goals

- [Goal 1 with deadline]
- [Goal 2 with deadline]

---

## 3. Write Constraints -- Vault Contamination Prevention

> These rules prevent AI from corrupting years of accumulated notes.

### 3-1. Read-Only Default

- Claude **reads the vault only** by default.
- Write/modify/delete only with **explicit user request**.
- Never create or modify notes without being asked.

### 3-2. Propose -> Confirm -> Execute (3-Step Rule)

1. **Propose**: Show the planned changes as text first
2. **Confirm**: User approves
3. **Execute**: Apply only approved changes

Never skip steps. Even with "handle everything at once" requests, show the change list first.

### 3-3. Forbidden Actions

- **No hallucinated links**: Never create `[[links]]` to notes that don't exist. Verify existence before linking.
- **No scope creep**: "Only this note" means only that note. No touching other notes (Task Drift prevention).
- **No structure changes**: Never modify folder structure, tag system, or frontmatter conventions without permission.
- **No over-collection**: When proposing new notes, always explain "why is this note needed?"

### 3-4. Safety Measures

- Bulk operations (5+ notes) use **batched confirmation** by section.
- Automated workflows have a **maximum note count limit**.
- When in doubt, **stop and ask** before executing.

---

## 4. Session Rules

### 4-1. Instruction Attenuation Prevention

- In long conversations (10+ turns), core rules fade.
- **Countermeasure**: Split work into sessions. In long sessions, re-anchor with "judge by Ground Truth."

### 4-2. Context Window Management

- Never read the entire vault at once.
- **Specify explicit path scope**: read only needed folders/files.
- Slip-Box files have highest priority for reference.

### 4-3. System Building Trap Prevention

- "Design less, use more"
- Building systems must not become the goal itself.
- The only success metric is **actual output produced**.
- Principle: "Do it once manually, twice consider, thrice automate"

---

## 5. Core Value

> Replace this with your own operating principle.
> This is the filter for all suggestions and decisions.

"[Your core principle here -- the lens through which all decisions are made]"

When tempted to add complexity, ask: "Does this help achieve more with less?"

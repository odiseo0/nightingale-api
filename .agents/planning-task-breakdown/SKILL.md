---
name: planning-task-breakdown
description: Plan a feature or broad code change as small, ordered, testable tasks before implementation. Use when work is vague, spans components, needs dependency order, or will continue across sessions. Do not use for a clear small change or an already approved task.
---

# Planning and Task Breakdown

Create an implementation plan that another agent can follow without guessing. Plan only. Do not edit product code, install packages, or implement tasks during this workflow.
The only normal writes are the plan and task list. Use `tasks/<plan-id>/plan.md` and `tasks/<plan-id>/todo.md` unless `AGENTS.md` or the user names an external tracker.

## 1. Assign or reuse a plan ID

Read `AGENTS.md`, the project specification in `docs/master-plan.md`, `docs/technical-architecture.md` and `docs/srs.md`, and the relevant code and tests. Find the build and focused test commands from project files. Do not invent commands.

Plan IDs use:

```text
P-YYYYMMDD-NN-short-slug
```

- Use the user's local creation date.
- Set `NN` to the next unused two-digit number for that date, starting at `01`.
- Use a stable two-to-five-word lowercase slug.
- Store the files in `tasks/<plan-id>/plan.md` and `tasks/<plan-id>/todo.md`.
- Never rename or reuse a plan ID.

For tasks, use `T01`, `T02`, and so on. For checkpoints, use `C01`, `C02`, and so on. Do not renumber either after plan approval. Use `<plan-id>/T01` for a cross-plan task reference.

Before writing, check all existing plan folders:

- If this is the same work as an open plan, revise that plan in place and keep its ID.
- If the related plan is completed or superseded, create a new plan ID and link the older plan. Do not rewrite closed history.
- If this is different work with no scope overlap, create a new plan ID. Do not replace another plan.
- If an open plan overlaps this work, stop and ask whether to extend, supersede, or keep both plans.
- Never delete, rename, replace, or bulk-close open work without direct user approval.

If the project uses an external tracker, create one item per task there. Keep `tasks/<plan-id>/plan.md`, but use its task section as an ordered list of tracker links or IDs. Do not create a duplicate `todo.md`.

## 2. Study before planning

Use read-only checks to:

- define the requested outcome and its limits;
- find current patterns, code paths, tests, and commands;
- map data and control flow across components;
- list risks, unknowns, and choices that need user input;
- note conflicts with the project specification.

Ask only about choices that would change the plan in a major way. Record other unknowns as plan risks or task discovery work.

## 3. Order by dependency and risk

Write the dependency graph in plain text when it helps. Build base types, file formats, or contracts before the code that uses them.

Prefer a thin working path through all needed parts over separate layers that work only after a final connection task. Each task must leave the project in a working state.

Put high-risk proof work early. Add a checkpoint after every two or three tasks and at each phase end.

## 4. Keep tasks small

Target small or medium tasks:

| Size | Guide |
|---|---|
| XS | One file or one local rule |
| S | One or two files; one component or command |
| M | Three to five files; one testable feature path |
| L | Five to eight files; split it |
| XL | More than eight files; always split it |

Split a task when any of these are true:

- it needs more than one focused session, about two hours of agent work;
- it needs more than three acceptance checks;
- it changes two independent parts of the app;
- its title joins separate outcomes with "and";
- it will likely touch more than five files.

Parallel work is safe only for independent tasks. Shared schemas, file formats, state, and contracts need ordered work. Define a shared contract before parallel tasks use it.

## 5. Write the plan

Use this structure in `tasks/<plan-id>/plan.md`:

```md
# [Plan ID]: [Name]

**Status:** Draft
**Created:** YYYY-MM-DD
**Updated:** YYYY-MM-DD
**Task list:** [todo.md](todo.md)

## Overview
[Outcome, scope, and user-visible result]

## Source of Truth
[Relevant specification sections and current code]

## Architecture Decisions
- [Decision and reason]

## Dependency Order
[Short graph or ordered explanation]

## Task List
### Phase 1: [Name]
- [ ] T01: [Title]

### C01: [Checkpoint name]
- [ ] [Build, test, and user-flow checks]

## Risks and Mitigations
| Risk | Impact | Mitigation |
|---|---|---|
| [Risk] | High/Medium/Low | [Action] |

## Open Questions
- [Question, or "None"]
```

If tasks use an external tracker, state its name near the top of the plan.

Plan status values are `Draft`, `Approved`, `In progress`, `Blocked`, `Completed`, and `Superseded`. Only the user can change `Draft` to `Approved`. If a plan is superseded, keep the file and link to its replacement.

## 6. Write each task

Put full task records in `tasks/<plan-id>/todo.md` or in the named tracker:

```md
# Task List: [Plan ID]

**Plan:** [plan.md](plan.md)
**Updated:** YYYY-MM-DD

## T01: [Short title]

**Status:** Todo

**Description:** [One paragraph with one outcome.]

**Acceptance criteria:**
- [ ] [Observable condition]
- [ ] [Observable condition]

**Verification:**
- [ ] Focused tests: `[real command]`
- [ ] Build or broader check: `[real command]`
- [ ] Manual check: [user-visible behavior]

**Dependencies:** [Task IDs or None]

**Files likely touched:**
- `path/to/file`

**Estimated scope:** [XS, S, or M]
```

Task status values are `Todo`, `In progress`, `Blocked`, and `Done`. Keep at most one task `In progress` unless the approved plan defines parallel work. Keep the checkboxes in `plan.md` in sync with task status in `todo.md`.

Use `Not available yet - define in TNN` when the repository does not yet have a valid test or build command. Do not add a false command.

Add checkpoints to the same task target:

```md
## C01: After T01-T03
- [ ] Focused and full tests pass
- [ ] The application builds
- [ ] The planned user path works
- [ ] User review is complete
```

## 7. Final review

Before handing off the plan, confirm:

- every task has no more than three clear acceptance checks;
- every task has focused tests, a build or wider check, and a manual check;
- dependencies match the task order;
- no task is larger than medium or likely to touch more than five files;
- checkpoints separate major phases;
- the plan, tasks, checkpoints, paths, and status values follow `tasks/README.md`;
- approved task and checkpoint IDs were not renumbered;
- the plan names its source material, risks, and open questions;
- no unrelated open plan was replaced;
- no product code changed.

Give the user a short summary and ask for plan approval. Do not start implementation in the same turn unless the user had already asked for both planning and implementation and gave clear approval to proceed after the plan.

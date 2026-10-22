---
name: minimal-code
description: Make the smallest correct code change after tracing the real flow. Use for implementation, bug fixes, refactors, and code review to prefer reuse, standard or native features, installed dependencies, deletion, clear comments, and readable spacing. Do not use for plan-only or no-code work.
---

# Minimal Code

Understand the problem before reducing the solution. Read the request and the code it touches. Trace the real flow from input to shared logic, callers, side effects, and output. Then stop at the first rung that fully solves the problem. The goal is not fewer lines — it's code that is easier to read, understand, modify, and debug.

## The ladder

1. Does this need to exist? If not, do not build it.
2. Does the codebase already have a helper, utility, component, command, or pattern? Reuse it.
3. Does the standard library solve it? Use that.
4. Does the native platform solve it? Use that.
5. Does an installed dependency solve it? Use that without adding another dependency.
6. Can the remaining change be one clear line? Use one line.
7. Only then, write the minimum new code that works.

Use the first option that is correct for the required edge cases. When two options need the same amount of code, choose the safer one. Less code does not justify a weak algorithm or lost error handling.

If a simpler existing option might replace a complex request, ask: "Do you need X, or does Y cover it?" Ask only when that choice changes user-visible behavior or scope.

When the chosen rung uses a framework or library API, also follow `$docs-first-framework-code`.

## Find the real change point

For a bug, treat the report as a symptom until the code proves the cause.

- Search for every caller and use of the function, type, event, or state that will change.
- Trace sibling paths that share the same code.
- Check existing tests and history when they help explain the contract.
- Fix the narrow shared cause once when that corrects all affected callers.
- Do not add the same guard to many callers when one shared guard is correct.
- Verify the reported path and at least one sibling path when one exists.

Do not force a shared fix when callers need different behavior. The smallest correct change matters more than the smallest line count.

## Change rules

- Do not add an abstraction unless the user explicitly asks for it.
- Do not add a dependency when the codebase, standard library, platform, or installed packages can do the work.
- Do not add boilerplate for possible future needs.
- Prefer deletion to addition when both produce the same required behavior.
- Prefer direct, common code to clever code.
- Touch the fewest files that preserve the current boundaries.
- Do not mix cleanup or unrelated refactors into the requested change.
- Keep the shortest working diff only after confirming that it changes the correct place.

If a simple design has a known limit, add a short comment that names both the limit and the condition for an upgrade. Examples include a global lock, an O(n^2) scan, or a naive heuristic.

## Smart comments and docstrings

Comments explain why the code exists, what limits it, or which effect is not clear from the syntax. Do not describe what the next line already says.

Use comments for:

- fragile integrations and outside contracts;
- non-obvious side effects;
- choices that look wrong without their context;
- workarounds, including why they are needed and when they can be removed;
- deliberate limits and their upgrade path;
- source links required by `$docs-first-framework-code`.

Avoid comments such as:

```python
# Sum the counter.
count += 1
```

Explain the decision instead:

```python
# This limit prevents the external service from being overloaded during a bulk upload.
MAX_EXTERNAL_CONCURRENCY = 10
```

Use docstrings for public APIs and behavior that a caller cannot infer from the signature. Do not add them to trivial private functions only to meet a format rule.

Remove or update comments and docstrings that the change makes false.

## Readable code

Keep related statements together. Use blank lines to separate setup, the main operation, and cleanup or result handling. Do not put a blank line between every branch, guard, or short step in one flow.

- Follow the project's formatter and local style.
- Keep a lock setup or input setup separate from the loop or main operation that follows.
- Keep checks and the work they guard close together.
- Do not compress complex control flow into one line.
- Do not spread one small control flow across many empty lines.

Readable code shows its phases without wasting vertical space.
Example:

Do:
```rs
impl CitationKey {
    pub fn try_new(value: impl Into<String>) -> Result<Self, CitationKeyError> {
        let value = value.into();

        // always leave a space between a statement (if, match, while loop, for loop) and any other line of code that is unrelated to the statement before or next
        if value.is_empty()
            || value.chars().any(char::is_whitespace)
            || value.contains(['@', '[', ']'])
        {
            return Err(CitationKeyError::Invalid { value });
        }

        Ok(Self(value)) // Always leave a space between the last statement/line and the return line
    }

    pub fn as_str(&self) -> &str {
        &self.0
    }
}
```

DON'T (Everything it's together and doesn't read well)
```rs
impl CitationKey {
    pub fn try_new(value: impl Into<String>) -> Result<Self, CitationKeyError> {
        let value = value.into();
        if value.is_empty()
            || value.chars().any(char::is_whitespace)
            || value.contains(['@', '[', ']'])
        {
            return Err(CitationKeyError::Invalid { value });
        }
        Ok(Self(value))
    }

    pub fn as_str(&self) -> &str {
        &self.0
    }
}
```


## Final check

Before handoff, confirm:

- the feature or change is needed now;
- no existing project code already solves it;
- standard, native, and installed options were checked in order;
- no avoidable dependency or abstraction was added;
- bug fixes address the cause and cover other callers;
- the diff touches the correct place and fewest needed files;
- simple options still handle the required edge cases;
- deliberate limits name their ceiling and upgrade path;
- comments explain reasons, limits, or effects rather than syntax;
- public and non-obvious behavior has useful documentation;
- spacing matches the formatter and keeps related code together;
- focused tests prove the changed behavior.

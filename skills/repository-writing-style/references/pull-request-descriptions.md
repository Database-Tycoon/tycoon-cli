# Pull request descriptions

Write PR descriptions for reviewers. Help them understand what changed, why it changed, and how the result was verified.

Do not narrate the diff file by file. Reviewers can inspect the code.

## Lead with the outcome

Begin with the change and its purpose.

Prefer:

> Adds validation for PR titles and documents the accepted GitHub and Jira scope formats.

Avoid:

> This PR modifies several files related to PR title validation.

Mention the issue or ticket when the repository expects one.

## Include what helps review

Depending on the size of the change, cover:

- The problem or task
- The approach taken
- Important implementation decisions
- User-visible or compatibility effects
- Tests and checks performed
- Known limitations
- Follow-up work intentionally left out

Keep implementation detail proportional to the change. Explain choices that are surprising, risky, or difficult to infer from the diff.

Do not describe routine edits individually.

## Suggested structure

A medium or large PR may use:

```markdown
## What changed

Describe the outcome and the main parts of the change.

## Why

Explain the problem being addressed.

## Implementation notes

Explain decisions that help reviewers understand the diff.

## Verification

- `pytest tests/test_pr_title.py`
- Tested valid GitHub and Jira scopes
- Tested the release promotion exemption

## Out of scope

List related work intentionally left for another PR.
```

Adapt the headings to the change. A small PR may need only a short paragraph and a verification note.

Do not add empty sections.

## Verification

Report only checks that were actually performed.

Use exact commands when useful:

```markdown
## Verification

- `pytest tests/test_config.py`
- `ruff check src tests`
- Manually verified profile discovery on macOS
```

Do not write “all tests pass” unless the relevant test suite was run successfully.

If tests were not run, say so briefly:

> Tests were not run because this change only updates documentation.

Do not use that explanation when executable examples, links, or generated documentation still required verification.

## Screenshots and output

Include screenshots for visual changes when they help reviewers compare behavior.

Include command output when the exact result matters. Trim unrelated noise.

Explain what a screenshot or output block demonstrates. Do not attach evidence without context.

## Breaking changes

Call out behavior that may affect existing users or integrations.

State:

- What changed
- Who is affected
- Whether migration is required
- What the migration involves

Do not hide a breaking change in implementation notes.

## Scope

Keep the description aligned with the actual diff.

If the implementation includes adjacent refactoring or cleanup, explain why it was necessary. If it was not necessary, leave it for another PR.

Do not claim unrelated follow-up work is complete.

## Reviewer guidance

Direct attention to areas that deserve closer review when useful:

> The branch-pattern exemption is the main policy decision in this change. The rest of the workflow is a direct implementation of that rule.

Do not tell reviewers that a change is “simple,” “obvious,” or “safe.” Give them the evidence needed to decide.

## Before finishing

Check that:

- The opening says what changed and why
- The description matches the diff
- Important design choices are explained
- Verification claims are accurate
- Breaking or user-visible effects are easy to find
- Out-of-scope work is clearly separated
- The description helps review without repeating the code
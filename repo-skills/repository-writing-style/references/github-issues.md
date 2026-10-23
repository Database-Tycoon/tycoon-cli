# GitHub issues

Write GitHub issues so that a maintainer unfamiliar with the immediate discussion can understand the problem and decide what should happen next.

Do not assume every issue needs the same template. Match the structure and level of detail to the kind of issue being written.

## General principles

Lead with the problem or request, not the history of how the author discovered it.

Include enough context to explain:

- What happens today
- Why it matters
- Who or what is affected
- What outcome is wanted
- Which constraints affect the solution

Use repository-specific examples when they help establish the problem. Do not add examples merely to make the issue appear more substantial.

Keep observed behavior, proposed changes, and open questions distinct.

## Bug reports

A useful bug report normally covers:

- What happened
- What was expected
- How to reproduce it
- Relevant environment details
- Logs or errors that help identify the cause

Use the smallest reliable reproduction available.

Do not bury the failure beneath setup details. Put the unexpected behavior near the beginning.

Do not speculate about the cause as if it were confirmed. Label a suspected cause clearly.

A suitable structure may be:

```markdown
# Short description of the failure

## What happened

Describe the observed behavior.

## Expected behavior

Describe what should have happened.

## How to reproduce

1. Run ...
2. Configure ...
3. Observe ...

## Environment

Include only relevant versions and platform details.

## Additional context

Include logs, screenshots, or suspected causes when useful.
```

Omit sections that do not help reproduce or understand the problem.

## Feature requests

Explain the need before describing the desired interface.

Cover:

- The task or limitation
- Why the current behavior is insufficient
- The desired outcome
- A concrete usage example
- Important constraints

Do not present a preferred implementation as the only possible solution unless the implementation itself is the proposal.

Prefer:

> Commands currently require callers to assemble the profile path themselves. Adding profile discovery would let callers use the same resolution behavior as the CLI.

Avoid:

> We should add a `ProfileDiscoveryManager` class with three methods.

The second version may become relevant later, but it does not establish the user need.

## Proposals

A proposal should make the rule or design easy to evaluate.

A useful structure may include:

```markdown
# Proposal title

## The problem
## Proposed change
## Why this approach
## Exemptions
## Rollout
## Implementation
## Open questions
```

Adapt or omit sections as needed.

Explain the motivation before implementation details. A rule is easier to evaluate when readers understand the failure mode it addresses.

When proposing a numerical limit, explain where the number came from. If it is only a starting point, say so.

When rejecting an alternative, explain the concrete failure mode rather than dismissing it.

Prefer:

> A line-count limit would reject focused rewrites of existing large files, even when the change addresses one concern.

Avoid:

> File count is obviously a better metric.

Keep exemptions narrow. State:

- Which cases qualify
- How the case is identified
- Why the normal rule does not fit
- Which similar cases remain subject to the rule

Separate settled parts of the proposal from decisions that remain open.

Open questions should be genuine decisions. Do not use them to repeat arguments already made.

## Scope

Keep one issue focused on one problem or decision.

If an issue contains several independently actionable changes, consider splitting them. Link related issues so the overall goal remains visible.

Do not add adjacent cleanup, refactoring, or policy changes unless they are necessary to solve the stated problem.

## Titles

Write a title that identifies the problem or proposed change without requiring the reader to open the issue.

Prefer:

> Add a size limit for pull requests

Avoid:

> PR improvements

Prefer:

> Profile resolution fails for nested dbt projects

Avoid:

> Bug in profile logic

Follow any title convention documented by the repository.

## Before finishing

Check that:

- The problem is understandable before the solution is introduced
- Facts are distinguishable from assumptions
- The requested outcome is clear
- Examples are real and relevant
- Alternatives are treated fairly
- Open questions have not been presented as decisions
- The issue is focused enough to act on
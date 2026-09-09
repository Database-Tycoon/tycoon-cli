# Review notes

Write review feedback that is specific, actionable, and proportional to the problem.

The goal is to help improve the change, not to demonstrate expertise or rewrite the contribution in the reviewer's preferred style.

## Describe the issue clearly

A useful review comment explains:

- What is wrong or unclear
- Where it occurs
- Why it matters
- What kind of correction is needed

Prefer:

> This accepts an empty scope, so `feat(): add export` passes even though the issue reference is missing. Reject empty scopes for `feat`, `fix`, `refactor`, `test`, and `docs`.

Avoid:

> This validation is poorly implemented.

Focus on the code or text, not the contributor.

## Lead with the consequence

Explain the observable failure before suggesting a fix.

Prefer:

> A PR from `feature/v0.2.0` would satisfy this substring check and bypass title validation. Match the complete head branch against the version pattern instead.

Avoid:

> Use `re.fullmatch()` here.

The preferred implementation can follow once the reason is clear.

## Be certain about the finding

Verify a reported problem before presenting it as a defect.

Distinguish between:

- Confirmed bugs
- Compatibility or maintenance risks
- Questions about intent
- Optional suggestions
- Personal preferences

Do not present a stylistic preference as a correctness issue.

When intent is unclear, ask a direct question:

> Should this exemption apply to prerelease branches such as `v0.2.0-rc1`, or only the exact stable-version pattern?

Do not use a question to obscure a confirmed requirement:

> Could we maybe consider handling the empty scope?

If the empty scope is invalid, state that directly.

## Make comments actionable

Identify the condition that needs to hold. Do not require a particular implementation unless correctness depends on it.

Prefer:

> Validate the complete branch name so prefixes and suffixes cannot satisfy the exemption accidentally.

Use a concrete implementation request when the fix itself is constrained:

> Use `re.fullmatch()` here because `re.search()` also accepts additional text around the version.

## Set the right severity

Make blocking issues clearly distinguishable from optional improvements.

Blocking feedback includes:

- Incorrect behavior
- Security problems
- Data loss risks
- Broken compatibility guarantees
- Missing required tests
- Violations of an accepted repository rule

Non-blocking feedback includes:

- Naming preferences
- Small readability improvements
- Possible follow-up refactors
- Alternative designs with no demonstrated correctness benefit

Use labels such as `Blocking`, `Suggestion`, or `Nit` only when the repository already follows that convention or the distinction would otherwise be unclear.

Do not overwhelm an important finding with many minor comments.

## Avoid unnecessary rewrites

Respect the contributor's approach when it is correct and maintainable.

Do not request a rewrite solely because another design is possible.

When suggesting a broader refactor, explain the concrete benefit and consider whether it belongs in a follow-up PR.

Prefer:

> Suggestion: extracting the pattern into a named constant would make the workflow and its tests share one definition. This does not need to block the current change.

Avoid:

> Please refactor this into a validator class.

## Overall reviews

Use an overall review note to summarize the state of the change, not to repeat every inline comment.

A useful overall note may state:

- Whether the approach is sound
- Which findings block approval
- Which suggestions are optional
- What needs to happen next

Example:

> The overall approach looks sound. The branch exemption currently matches names with extra prefixes, which needs to be fixed before merge. The naming comments are optional.

Avoid praise that is generic or excessive. Be sincere and specific.

## Before finishing

Check that:

- Every reported defect has a concrete consequence
- The relevant location or condition is clear
- The requested correction is actionable
- Questions are genuine questions
- Preferences are not presented as requirements
- Blocking and optional feedback are distinguishable
- The tone addresses the work rather than the person
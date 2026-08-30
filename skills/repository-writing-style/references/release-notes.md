# Release notes

Write release notes and changelogs around the effect of a change, not the internal work required to produce it.

Help users and contributors answer:

- What changed?
- Why might I care?
- Do I need to do anything?
- Is existing behavior affected?

## Lead with the result

Prefer:

> Added support for Jira ticket references in pull request titles.

Avoid:

> Refactored the pull request title validation module.

Mention internal implementation only when it affects compatibility, extension points, performance, or maintenance.

## Choose the right level of detail

For each entry, include only what readers need to understand the change.

A short entry may need one sentence:

> Fixed profile discovery for dbt projects stored below the repository root.

A larger change may need:

- A concise summary
- The affected users or workflow
- Migration instructions
- Compatibility notes
- A link to more detailed documentation

Do not turn release notes into a list of commits or changed files.

## Write from the reader's perspective

Describe observable behavior.

Prefer:

> `tycoon run` now reports the model that failed before exiting.

Avoid:

> Added an error-reporting callback to the run event handler.

When a change is contributor-facing rather than user-facing, say so clearly:

> Contributors can now run the PR title check locally with `make check-pr-title`.

## Breaking changes

Make breaking changes easy to find.

State:

- What changed
- Which users or integrations are affected
- What action is required
- Whether a compatibility period exists

Example:

````markdown
### Breaking: renamed `profile_path`

The `profile_path` configuration key is now `profiles_dir`.

Update existing configuration:

```yaml
profiles_dir: ./config
```

The old key is no longer accepted.
````

Do not soften a breaking change with vague wording such as “behavior has been improved.”

## Deprecations

State:

- What is deprecated
- What replaces it
- When removal is expected, if known
- How to migrate

Do not invent a removal version.

Prefer:

> `--profile-path` is deprecated. Use `--profiles-dir` instead. The old option remains available in this release.

## Fixes

Describe the failure that no longer occurs.

Prefer:

> Fixed Windows profile resolution when the configured path contains spaces.

Avoid:

> Fixed a profile resolution bug.

Include issue references when the repository's changelog convention expects them.

## Maintenance changes

Include internal maintenance only when it matters to the intended audience.

Dependency updates, formatting changes, and internal refactors may be omitted from user-facing notes unless they affect security, compatibility, extension development, or contributor workflows.

Do not market routine maintenance as a major improvement.

## Organisation

Group entries only when grouping makes the release easier to scan.

Useful categories may include:

- Added
- Changed
- Fixed
- Deprecated
- Removed
- Security

Follow the repository's existing changelog format when one exists.

Keep entries parallel in grammar and level of detail.

Do not create a category for a single entry when a simple list would be clearer.

## Evidence and claims

Do not claim that a release is faster, safer, or more reliable without evidence.

Replace vague claims with the measured or observable result:

Prefer:

> Reduced startup time from 1.8 seconds to 0.9 seconds when loading 100 models.

Avoid:

> Significantly improved startup performance.

Do not invent measurements.

## Before finishing

Check that:

- Entries describe outcomes rather than file changes
- User action is explicit where required
- Breaking changes and deprecations are easy to find
- Internal changes are included only when relevant
- Entries are consistent in tense and structure
- Claims are supported
- The notes follow the repository's established format
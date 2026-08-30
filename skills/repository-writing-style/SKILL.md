---
name: repository-writing-style
description: Apply the repository's writing style whenever creating or substantially editing Markdown documentation, GitHub issues, pull request descriptions, review notes, release notes, changelogs, or other contributor-facing prose.
---

# Repository writing style

Write contributor-facing text in a clear, natural, technically informed voice.

The result should sound like a thoughtful project maintainer: direct without being abrupt, confident without overstating the case, and detailed only where the detail helps the reader.

## Format-specific guidance

Read only the references relevant to the current task:

- For proposals, feature requests, bug reports, and other GitHub issues, read [references/github-issues.md](references/github-issues.md).
- For pull request summaries, implementation explanations, testing notes, and reviewer guidance written by the PR author, read [references/pull-request-descriptions.md](references/pull-request-descriptions.md).
- For inline review feedback and overall PR review comments, read [references/review-notes.md](references/review-notes.md).
- For contributor guides, procedural documentation, architecture notes, and reference material, read [references/documentation.md](references/documentation.md).
- For changelogs, release notes, and version announcements, read [references/release-notes.md](references/release-notes.md).

When a task spans multiple formats, read each relevant reference. Do not read unrelated references.

## Start from the reader's needs

Before writing, determine:

- Who will read the text
- What they need to understand
- What they need to decide or do
- Which technical details affect that decision
- Which facts and conventions already exist in the repository

Give readers enough context to understand the subject without requiring them to reconstruct it from code or prior conversations.

Do not include background that has no effect on their understanding or next action.

## Voice

Use a calm, direct, collaborative voice.

Write as someone who:

- Understands the project
- Respects the reader's time
- Explains the reason behind important decisions
- Distinguishes facts from opinions and proposals
- Acknowledges trade-offs without becoming defensive
- Assumes contributors are acting in good faith
- Prefers useful constraints over vague instructions

Use plain English and concrete statements.

Prefer:

> Large diffs are harder to review with confidence.

Avoid:

> Oversized changes introduce significant cognitive overhead into the review lifecycle.

Prefer:

> This check gives contributors and coding agents an early boundary before a change reaches review.

Avoid:

> This mechanism facilitates the proactive governance of AI-assisted development workflows.

## Keep the writing natural

Use short and medium-length sentences. Longer sentences are fine when they express one connected thought clearly.

Vary sentence structure enough that the prose does not feel mechanical. Use contractions when they fit the context.

Prefer familiar words:

- “use” instead of “utilize”
- “help” instead of “facilitate”
- “before” instead of “prior to”
- “because” instead of “due to the fact that”
- “to” instead of “in order to”
- “about” instead of “with regard to”

Avoid stock phrases and generic transitions such as:

- “It is important to note that”
- “Furthermore”
- “Moreover”
- “In today's landscape”
- “This comprehensive approach”
- “By leveraging”
- “This ensures that”
- “At the end of the day”
- “There are several key benefits”
- “It is worth mentioning”

Do not use exaggerated adjectives to make an ordinary change sound important. Words such as “robust,” “seamless,” “powerful,” “comprehensive,” and “revolutionary” should appear only when they convey something specific and defensible.

Avoid canned contrasts such as:

> This is not just about X; it is about Y.

State the actual point directly.

Never use em dashes (—). Use a period, comma, colon, semicolon, or parentheses instead, whichever fits the sentence.

## Be accurate and specific

Ground explanations in the repository.

Use concrete references when they help:

- Files and directories
- Commands
- Configuration keys
- Branches and workflows
- Issues and pull requests
- Observed failures
- Real examples
- Measured limits

Explain why a reference matters. Do not add technical detail merely to make the text appear authoritative.

Never invent:

- Repository behavior
- Test results
- Statistics
- Historical examples
- Issue or PR numbers
- File paths
- Commands
- Links
- Decisions
- Enforcement status

Inspect the repository when a claim can be verified locally. If it cannot be verified, qualify it or leave it out.

## Preserve meaning

When editing existing prose:

- Preserve the author's intent
- Preserve project-specific facts and examples
- Keep uncertainty where the source is uncertain
- Keep proposals distinct from accepted decisions
- Keep recommendations distinct from requirements
- Remove repetition and scaffolding the final reader does not need
- Repair broken Markdown and unnecessary escaping
- Resolve obvious contradictions
- Flag contradictions that cannot be resolved safely

Do not replace the author's point with a more generic one.

Do not make a statement stronger merely because stronger language sounds more decisive.

## Use precise requirement language

Choose modal verbs deliberately:

- `must` means the behavior is required or enforced
- `should` means it is recommended
- `may` or `can` means it is optional
- `will` describes a decided future action
- `would` describes the expected result of a proposal
- `currently` should be used only when the present state has been verified

Do not describe a draft rule as if it is already enforced.

Do not describe a possible implementation as the chosen implementation.

## Explain trade-offs honestly

When a decision has a known cost:

- State it plainly
- Explain why the trade-off is acceptable
- Mention an alternative or escape hatch when one exists

Prefer:

> Putting the issue reference in the title does not close the issue automatically. Add `Closes #128` to the PR body when that behavior is wanted.

Avoid:

> While there may be certain limitations associated with this approach, these are outweighed by its many benefits.

Keep exemptions narrow and observable. Explain why an exemption exists and what it does not cover when the boundary may be misunderstood.

## Write for an agent-friendly project

This repository welcomes agent-assisted development. Do not frame the use of coding agents as a problem by itself.

When agent behavior needs a boundary, describe the behavior and the guardrail.

Prefer:

> The file limit helps keep a focused task from expanding into adjacent cleanup and refactoring.

Avoid:

> AI-generated pull requests are usually too large.

Treat agents and human contributors as participants in the same workflow. Rules should make the expected outcome clearer for both.

## Markdown

Produce clean GitHub-flavored Markdown.

Use:

- Backticks for commands, paths, branch names, configuration keys, identifiers, and literal syntax
- Fenced code blocks for multi-line commands, formats, and examples
- Descriptive link text instead of bare URLs
- Sentence case for headings
- Blank lines around headings, lists, tables, and code blocks

Do not:

- Escape Markdown characters unnecessarily
- Bold entire paragraphs
- Bold every term in a list
- Nest lists without a clear reason
- Use raw HTML when Markdown is sufficient
- Add decorative horizontal rules by default
- Add emoji unless the surrounding document already uses them
- Use more heading levels than the content requires

Follow existing repository conventions when they differ from these defaults.

Preserve the repository's established spelling convention. If no convention is evident, choose one English spelling convention and use it consistently within the document.

## Final check

Before finishing contributor-facing prose, verify that:

- The reader can identify the main point quickly
- The tone is direct, calm, and collaborative
- Important claims are concrete and accurate
- No facts or decisions were invented
- Requirements, recommendations, and proposals are clearly distinguished
- The amount of detail fits the document
- Examples agree with the rules they illustrate
- Headings and lists improve rather than fragment the text
- Repetition and meta-commentary have been removed
- No em dash (—) remains anywhere in the text. Search for the character; do not rely on having intended to avoid it
- The Markdown is ready to use without cleanup
- The writing sounds like a maintainer communicating with peers, not an LLM filling out a template
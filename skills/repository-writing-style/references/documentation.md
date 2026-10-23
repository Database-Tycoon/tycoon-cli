# Documentation

Write documentation that helps readers complete a task or understand the system without reading the implementation first.

Choose the structure based on whether the document is procedural, explanatory, or reference material.

## Understand the reader

Identify:

- What the reader is trying to accomplish
- What they are expected to know already
- Which prerequisites are genuinely required
- Where mistakes or uncertainty are likely
- What successful completion looks like

Do not assume internal project knowledge unless the document is explicitly written for maintainers who have it.

## Procedural documentation

For setup instructions, workflows, and how-to guides:

1. State the goal.
2. List non-obvious prerequisites.
3. Present steps in execution order.
4. Show commands exactly as they should be run.
5. Explain expected results where uncertainty is likely.
6. Include troubleshooting for realistic failure modes.

Keep explanation close to the step it supports.

Prefer:

````markdown
Create the release branch from the current release branch:

```shell
git switch -c v0.3.0 v0.2.0
```

Do not create it from `main`; unreleased changes are collected on the current version branch.
````

Avoid separating an important warning from the command it affects.

Do not include troubleshooting for hypothetical failures that have not occurred and are not reasonably expected.

## Explanatory documentation

For architecture notes and conceptual guides:

- Introduce concepts before relying on them
- Explain relationships between components
- Describe why important boundaries exist
- Use an example when abstraction alone would be unclear
- Distinguish current design from possible future changes

Do not turn an explanation into a source-code tour. Describe responsibilities and behavior, then point to important implementation locations.

## Reference documentation

For commands, configuration, and APIs:

- Use consistent names and terminology
- Describe accepted values precisely
- State defaults
- Explain important constraints
- Provide small, valid examples
- Identify errors or edge cases readers are likely to encounter

Keep the source of truth clear. When documentation duplicates values maintained elsewhere, link to or generate from the authoritative source when practical.

Do not claim completeness unless the reference is complete.

## Contributor guidelines

State adopted rules directly.

A contributor should be able to answer:

- What must I do?
- What is recommended?
- What is exempt?
- How do I complete the workflow?
- Where can I find the underlying rationale?

Keep contributor guidance shorter and more directive than the proposal that introduced the rule.

Prefer:

> Each PR must change at most eight counted files. Files under `src/tycoon/templates/**` are excluded.

Avoid repeating several paragraphs of historical discussion before stating the rule.

Do not include meta-commentary such as:

> This is a draft of the contributor-facing content that will eventually be added to `CONTRIBUTING.md`.

Once the text is contributor-facing, write in the voice of the adopted documentation.

## Examples

Examples must agree with the current implementation and documented rules.

Use realistic names and values. Keep examples focused on the behavior being explained.

Do not use placeholder syntax that could be mistaken for a literal command without explaining it.

When a command contains a placeholder, make it visually clear:

```shell
gh pr create --base <previous-branch>
```

Explain the placeholder when the meaning is not obvious.

## Links

Use descriptive link text:

```markdown
See the [pull request guidelines](pull-requests.md).
```

Avoid:

```markdown
Click [here](pull-requests.md).
```

Prefer relative links for files within the repository unless repository conventions say otherwise.

Check that new or edited links point to the intended location.

## Structure

Use descriptive, sentence-case headings.

Keep paragraphs focused on one idea. Use bullets for parallel items and numbered lists for ordered steps.

Do not add an overview, summary, or quick-reference section unless it materially improves navigation.

A quick-reference table is useful when readers repeatedly need to map situations to actions. It should not duplicate nearby prose without adding scanability.

## Before finishing

Check that:

- The document serves a clear reader and task
- Required context appears before it is used
- Commands and examples are valid
- Requirements and recommendations are distinguishable
- Terminology is consistent
- Links are correct
- Repeated rationale has been removed
- The reader can tell what successful completion looks like
---
name: announcing-a-release
description: Use when a tycoon-cli version has shipped (all four release surfaces verified) and the maintainer wants the LinkedIn push, a GitHub Discussions announcement, or "get the drafts to the reviewer"; also when asked to share release visuals or copy with the team in Slack.
---

# Announcing a release

The announcement is a package, not a post: two LinkedIn options, a
Discussions post, two city screenshots, delivered as one Slack thread the
reviewer can work from. Nothing is posted publicly by the agent; the
package goes to the reviewer and the maintainer decides.

## Fixed facts

| Fact | Value |
|---|---|
| Source of truth | `git show refs/tags/v<ver>:docs/releases/v<ver>.md`, then the `## [<ver>]` CHANGELOG section |
| Copy rules | Templates live in `db-tycoon-content-repo/templates/linkedin-post.md` and `BRAND_VOICE.md`. 150 to 400 words, opening line stands alone, links in the first comment, 3 to 5 hashtags, ends on a real question, no em dashes, no "not X but Y" |
| Reviewer | The designated reviewer (check with the maintainer who assigned it). The template checklist may still say a previous name; that line is stale. |
| Slack channel | A private channel for release coordination. The connector cannot add members; check `slack_list_channel_members` and, if someone is missing, say so and the maintainer adds them. |
| Discussions | Enabled; category **Announcements**. Write it following `skills/repository-writing-style/references/release-notes.md`; that file is the style guide, so never write the post into it |
| Install line | `pip install --upgrade database-tycoon` |

## Order

1. **Draft two LinkedIn options** from the release notes, each with one main
   idea (for 0.2.1: the ingestion change; the city as the hook). Put the
   release URL and PyPI URL under a "Comments" heading, not in the body.
   Check each option: word count in range, `grep -c '—'` is 0.
2. **Draft the Discussions post**: change list with issue numbers, the
   tracked known limitations, what the next version holds (from
   `docs/releases/v<next>.md` on the next release branch and the PRs
   targeting it).
3. **Render the city screenshots** with `render-city-shots.spec.ts` in this
   directory. It runs inside the Playwright harness, so no dev server and
   no Chrome channel. It writes three PNGs; the package takes
   `city-overview.png` and `city-street-level.png`, `city-default.png` is
   the spare. In the worktree checked out at the released tag: `npm ci`,
   `npm run demo-data`, copy the spec to `web/e2e/zz-shot.spec.ts`, export
   `SHOT_OUT` and a unique `DATABASE_TYCOON_WEB_PORT` (the config reuses an
   existing server, so the default port can photograph another worktree),
   run `npx playwright test e2e/zz-shot.spec.ts`, delete the copy. Open the
   PNGs and look before attaching (`docs/city/conventions.md`).
4. **Package** the four files in one folder and `open` it for review. The
   scratchpad is under `/private/tmp` and does not survive a reboot; say so.
5. **Post to Slack only on the maintainer's ask.** One parent message (what
   shipped, that the reviewer is tagged, what is attached, what is next),
   then one threaded reply per file: `slack_get_file_upload_url` with the
   exact byte size → `curl -X POST "$URL" -H "Content-Type: ..."
   --data-binary @file` → `slack_complete_file_upload` with `channel_id` and
   `thread_ts`, each with a one-line `initial_comment`.
6. **Record**: memory reference and the session TODO.md.

## Common mistakes

- Reading the reviewer off the template. It may name a previous person; always confirm with the maintainer who assigned it.
- `web/shot.mjs` for screenshots: it needs a running dev server and the
  Chrome channel, and a parallel worktree on the default port photographs
  the wrong checkout. Use the spec.
- Posting links in the body. LinkedIn suppresses reach; comments only.
- Leaving em dashes in. The repo's older prose is full of them; new copy
  has none.
- Mentioning the reviewer in Slack and assuming that adds them. It does not.

## Shared copy

This is the public-safe version of this skill (no names, Slack IDs or private paths). The internal copy at `.claude/skills/announcing-a-release/SKILL.md` contains identifiers and should not be shared externally. Keep the two in step: workflow changes go here; the identifiers stay in the internal copy.

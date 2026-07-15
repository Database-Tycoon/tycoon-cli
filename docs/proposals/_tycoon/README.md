# Proposal: Tycoon CLI rewrite (`_tycoon`)

This folder holds the three-document proposal for rewriting the Tycoon CLI's ingestion layer (and laying foundations for the rest of the control plane) under a new set of abstractions.

The documents are layered — read top-to-bottom for a complete picture, or pick the altitude that matches the decision you're trying to make.

| Document | Altitude | What it answers |
|---|---|---|
| [MANIFESTO.md](./MANIFESTO.md) | Philosophy | *Why* are we doing this? *What shape* is the system meant to take? |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Structure (C4) | *How is it built?* From system boundary down to the proposed source tree. |
| [PLAN.md](./PLAN.md) | Execution | *What are we actually doing about it?* Decisions, sequencing, acceptance criteria, risks. |

## Status

**Draft proposal.** Discussion happens on the accompanying GitHub issue; this folder is the artifact reviewers point at for detail. Updates land here as the proposal evolves.

## Naming note

The author used `dbty` / `dbty-cli` in conversation as personal shorthand for **Database Tycoon** (the company). All three documents preserve that shorthand where rewriting would obscure the original framing — but the tool itself is the **Tycoon CLI** (repo `tycoon-cli`, distributed on PyPI as `database-tycoon`). It is not a separate product, not a dbt fork, and not affiliated with dlt.

The proposal also introduces `tycli` as a placeholder entrypoint command during the rewrite window so the new code cannot be invoked accidentally through the production `tycoon` command. See [PLAN.md §D2](./PLAN.md#d2--package-and-entrypoint-naming) for the naming-and-cutover plan.

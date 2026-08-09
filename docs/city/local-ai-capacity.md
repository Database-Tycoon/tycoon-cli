---
title: Local AI capacity as city infrastructure
description: Design sketch for showing how much local LLM capacity a machine has, expressed through the city's existing power-grid metaphor — scoped for a release after 1.0
tags: [design, ai, local-llm, power-grid, capacity, future]
related: [handover, city-json-v1, run-json-v1, semantic-roads]
updated: '2026-08-09'
---

# Local AI capacity as city infrastructure

Stephen, 2026-08-09: *"I want to make this a frontend for local llms also. We
already have support for ai through the tycoon cli but I want to connect it with
the power grid concept in the city. Can you put in a UI that helps people
understand how much AI capacity they have just from the local hardware?"*

**Scoped for a release after 1.0.** Nothing here is built. This page exists so
the idea is not lost in a transcript, and so the decisions it forces are visible
before anyone starts.

## Why the power grid is the right metaphor, and where it stops being right

The city already has a grid: the **database is the power plant**, and
`POWER_LINE` arterials radiate from it to the sources. That mapping says *this
is what makes the city run*.

Local inference is a genuinely different utility from the database, so it should
read as a **second generating station**, not as a re-skin of the first. A
machine with no local runtime is a city on one plant — which is the normal,
un-embarrassing case, and must look deliberate rather than broken.

The metaphor stops being right if capacity is drawn as something the player
*spends*. This build is observation and achievements only, with no player verbs,
and that decision is closed. A capacity gauge reports what the hardware is; it
never becomes a currency.

## What "capacity" honestly means

The standing rule — **facts wear provenance; absence stays named; unknown never
renders as stale** — is the whole design constraint here, because AI capacity is
unusually easy to fake.

Four things are genuinely measurable, and nothing else should be claimed:

| Fact | Source | Honest absence |
|---|---|---|
| Total and available memory (unified or VRAM) | platform APIs on the server side | never absent |
| Resident model: parameter count, quantisation, context window | LM Studio `/api/v0/models`; Ollama `/api/tags` + `/api/ps` | "no runtime reachable" |
| Measured throughput (tokens/sec) | a timed completion actually run | "not measured yet" — never estimated from parameter count |
| Headroom: what else fits beside what is resident | arithmetic over the two above | unknown if either input is |

**A dark substation is not a substation producing zero.** No reachable runtime
must render as *unknown capacity*, exactly as a catalog with no manifest gets
`state: "unknown"` with met/have/need all null rather than `met: false, have: 0`.
Tokens/sec in particular must never be inferred from model size — that is a
guess wearing a measurement's clothes, and this repo has a rule against it.

## The architectural decision this forces

Capacity facts are **machine-specific and timestamp-bearing**. They must not go
into `city.json`, which is byte-stable and reproduces identically from the same
catalog. Putting a tokens/sec reading in it would break that property
immediately.

The precedent already exists and should be followed: run replay documents live
in their own `runs.json` / `runs/<id>.json`, deliberately not byte-stable and
with no golden. Capacity belongs in a sibling document — `capacity.json` —
carrying its own contract page, its own absence rules, and no golden.

The second constraint is **who measures**. A browser cannot read `localhost:1234`
without CORS cooperation, and should not carry runtime-detection logic. The
existing shape is right: Python measures, the document carries facts, the web
renders them. That also keeps the web bundle dependency-free.

## What it would unlock, which is the actually interesting part

A capacity gauge on its own is a hardware readout, and hardware readouts get
looked at once. The reason to build it is that capacity **determines which
AI-powered jobs a machine can actually run** — so the city can say which work is
affordable here rather than in the abstract. That connects to the documentation
incentive already in the design (the library, coverage counts, achievements as
counts and never points).

## The CLI already wrote half of this

The Tycoon CLI had a working LM Studio client. It was removed on 2026-04-09 in
`75b71eb` — *"chore: remove tycoon ai command (deferred to v0.2)"* — taking ten
modules with it (`client`, `context`, `file_proposals`, `fix_loop`, `memory`,
`profiler`, `prompts`, `repl`). It is recoverable with
`git show 75b71eb^:src/tycoon/ai/client.py` in the `tycoon-cli` repo.

`client.py` is close to exactly the shape this feature needs:

```python
LMSTUDIO_BASE_URL = "http://localhost:1234/v1"

@dataclass
class ModelInfo:
    id: str
    state: str = "unknown"        # already the repo's absence rule, by default
    arch: str = ""
    quantization: str = ""
    max_context_length: int = 0

@dataclass
class LMStudioStatus:
    running: bool
    models: list[ModelInfo]

def is_server_running() -> bool
def list_models() -> list[ModelInfo]
def get_status() -> LMStudioStatus
```

Three of the four capacity facts above are already modelled there —
quantisation, context window, and architecture — and `ModelInfo.state` defaults
to `"unknown"` rather than to a verdict, which is the same instinct this
project's absence rule encodes. `LMStudioStatus.running` is the named-absence
discriminator for "no runtime reachable".

**What it does not have**, and what this feature would therefore add: measured
throughput (there is no timed completion anywhere in it) and host memory or VRAM
headroom. Those two are exactly the facts most likely to be faked, so they are
the ones that need the strictest provenance.

**The timing is a gift.** The CLI deferred its AI module to **v0.2**, and this
project's standing decision defers Tycoon-CLI integration to **that same
0.2.0**. The AI story and the city integration are due in the same CLI release,
so they can be designed against each other rather than retrofitted.

## Open questions, none of them answered

1. Which runtimes to detect. LM Studio and Ollama cover most local setups; each
   needs its own absence rule, and detecting neither must stay quiet rather than
   nag.
2. Whether capacity is one second plant or a substation per runtime. A machine
   running both LM Studio and Ollama is real.
3. How this meets the Tycoon CLI — see "The CLI already wrote half of this"
   below. The fork is whether the city measures LM Studio directly or asks the
   CLI to, and it should not be decided until the CLI's AI module returns in
   v0.2.
4. Whether this is engine-version territory. The **engine versions** idea
   (vanilla DuckDB now; MotherDuck and Snowflake later) is the existing
   precedent for capability tiers, and local-AI capacity may belong to that
   frame rather than beside it.

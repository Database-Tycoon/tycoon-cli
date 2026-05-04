# Recipe: Local LLM with LM Studio

Zero-config natural-language queries over your warehouse — no API key, no account, fully offline. Uses LM Studio as the LLM runtime, Nao as the chat / context-building layer, tycoon as the orchestrator.

## Why LM Studio

- **No account.** Download, install, run.
- **No API key.** LM Studio's OpenAI-compat server ignores the `api_key` field entirely.
- **Model agnostic.** GGUF, MLX, whatever you have running.
- **Stable endpoint.** `http://localhost:1234/v1` works the same on every machine.
- **Privacy.** Schema introspection and row previews never leave your laptop.

For analytics on sensitive data, this matters a lot. Anthropic / OpenAI / etc. mean sending schema + sample rows over the wire.

## Setup

### 1. Install LM Studio

Download from [lmstudio.ai](https://lmstudio.ai).

**Recommended model:** [Qwen 2.5 Coder 7B Instruct](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct) at the **Q4_K_M** quant (~4.7 GB). It's tuned specifically for code (SQL inclusive) and outperforms similar-size general-purpose models on coding benchmarks (HumanEval 88.4%). Comfortably fits in 8 GB of RAM with headroom for the warehouse + dbt context.

In LM Studio: click **Discover** → search `Qwen2.5-Coder-7B-Instruct-GGUF` → pick the `Q4_K_M` quant → Download → Load.

If you have more RAM and want sharper SQL on complex joins, step up to the **32B Coder Instruct** variant (~20 GB at Q4_K_M). For very tight machines, **Llama 3.2 3B** (~2 GB) works for simple analytics questions.

Open LM Studio's "Local Server" tab and start the server. Default port `1234`.

Verify:

```bash
curl http://localhost:1234/v1/models
```

Should return a JSON list of loaded models.

### 2. Install the tycoon ask extra

```bash
pip install 'database-tycoon[ask]'
```

This pulls `nao-core` and `ibis-framework[duckdb]`.

### 3. Initialize the ask stack

```bash
cd my-project           # any tycoon project with at least one ingested source
tycoon register llm lm-studio
```

This:

- Writes `.tycoon/nao/nao_config.yaml` with the LM Studio preset baked in
- Writes `AGENTS.md` at the project root (Claude Code / Cursor / Windsurf will find this)
- Pre-creates the eight directories `nao sync` walks
- Writes `.tycoon/nao/.gitignore` so PII previews stay local
- **Probes LM Studio** and offers to load a chat model if you have one downloaded but not in memory (see "Auto-load downloaded models" below)

The generated `nao_config.yaml` LLM block:

```yaml
llm:
  provider: openai
  base_url: http://localhost:1234/v1
  api_key: lm-studio              # placeholder — LM Studio ignores it
```

`tycoon.yml` gains:

```yaml
ask:
  llm:
    provider: lm-studio
```

### 4. Sync the data context

```bash
tycoon ask sync                    # ~30s first time
```

Nao introspects the warehouse and dbt project, writing context files under `.tycoon/nao/`:

```
.tycoon/nao/
├── databases/type=duckdb/database=<name>/schema=mart/table=fct_orders/
│   ├── columns.md       # column types
│   └── preview.md       # 5-row sample
├── repos/dbt/models/    # synced dbt SQL + YAML
└── RULES.md             # default project rules
```

These files are PII-bearing. The auto-generated `.gitignore` keeps them out of git by default — but be aware they exist on disk.

### 5. Verify

```bash
tycoon ask doctor
```

Output:

```
┃ Component       ┃ Status ┃ Detail                                    ┃
┃ nao_config.yaml │ OK     │ /path/to/.tycoon/nao/nao_config.yaml       ┃
┃ nao directories │ OK     │ all 8 present                              ┃
┃ Warehouse       │ OK     │ local DuckDB (no auth)                     ┃
┃ LM Studio       │ OK     │ http://localhost:1234/v1 responded (1 …)   ┃
```

The LM Studio row hits `/api/v0/models` and counts models with `state: "loaded"` (i.e. actively held in memory — not just downloaded). If the panel goes red:

- **`unreachable`** → start LM Studio's local server (Developer tab → Start Server) and re-run.
- **`reachable but 0 models loaded`** → load a model. See the next section for the auto-load flow.

## Auto-load downloaded models

If you have a chat model **downloaded in LM Studio but not loaded into memory**, tycoon offers to call `lms load` for you rather than punt you to the GUI. Triggers fire from two places:

1. After `tycoon register llm lm-studio` — if the runtime is up but no model is loaded
2. When you run `tycoon ask chat` — if the same state holds at chat-launch time

```
> LM Studio has 1 chat model(s) downloaded but none in memory.
Load google/gemma-4-26b-a4b now? [Y/n]:
```

Hit Enter (the default is Yes) and tycoon runs `lms load <model_id>`. Loading takes ~5-30s depending on model size and disk speed; then chat is ready.

The auto-load picks the recommended Qwen 2.5 Coder if it's downloaded; otherwise the first chat-capable model (embedding-only models are filtered out — they can't satisfy chat). Decline the prompt (or if `lms` isn't on your PATH or at the standard `~/.cache/lm-studio/bin/lms` location) and tycoon falls back to the GUI hint.

To preempt the prompt entirely, load a model in the LM Studio UI before invoking `tycoon ask chat`. Or call `lms` directly:

```bash
~/.cache/lm-studio/bin/lms load <model-id>
```

## Day-to-day usage

### Chat UI

```bash
tycoon ask chat
```

Opens `http://localhost:5005`. Ask questions in natural language; Nao translates to SQL, runs against your warehouse, and renders results inline. Citation links point at the dbt models / schema files Nao consulted.

### Pipe context into another agent

The chat UI is one consumer of the context Nao synced. Anything that reads markdown files can be another:

```bash
# Claude Code / Cursor / Windsurf — auto-read AGENTS.md
# (no command needed; just open the project)

# One-shot via Claude Code's stdin mode
tycoon ask context --table fct_orders | claude -p "explain this table"

# Pipe just rules to a script
tycoon ask context --rules-only > /tmp/rules-for-script.md

# Dump the entire data context
tycoon ask context --include-dbt > /tmp/full-context.md
```

The `ask context` command goes plain markdown to stdout, errors to stderr — composes with anything.

## Configuration tips

### Limit which schemas Nao sees

Production warehouses have noisy schemas (`pg_catalog`, `sqlmesh__*` cruft, abandoned migrations). Filter them in `tycoon.yml`:

```yaml
ask:
  llm:
    provider: lm-studio
  include_schemas: [mart]            # only mart schemas
  exclude_schemas: [pg_catalog]
```

The schema names get glob-expanded automatically (`mart` → `mart.*`).

Re-run `tycoon register llm` (no provider arg = refresh against the existing one) after editing `tycoon.yml`.

### Pin a specific model

LM Studio loads whatever model you picked in the UI. To force Nao to use a specific one:

```yaml
ask:
  llm:
    provider: lm-studio
    model: qwen2.5-coder-32b-instruct
```

### Use a different OpenAI-compat server

The `lm-studio` shortcut hardcodes `localhost:1234`. For Ollama / vLLM / a remote OpenAI-compat server, set `base_url` explicitly:

```yaml
ask:
  llm:
    provider: lm-studio
    base_url: http://192.168.1.50:8080/v1
    model: my-model
```

Or use the `ollama` shortcut for Ollama specifically.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `LM Studio FAIL: unreachable` | LM Studio server isn't running — open the UI, click "Start Server" |
| `nao sync` says "No such file or directory: 'repos'" | Stale install. Re-run `tycoon register llm` (it pre-creates all 8 dirs) |
| Chat UI shows no schemas | `ask.include_schemas` is too restrictive, or `tycoon ask sync` hasn't run |
| Slow / hallucinated SQL | Pick a bigger model. 32B+ params is where SQL accuracy gets reliable. |

`tycoon ask doctor` is the first stop for any "ask isn't working" symptom — it surfaces the four most common failure modes before you go deeper.

## Related

- [`tycoon ask`](../commands/ask/index.md) — full reference
- [Reference: tycoon.yml `ask` block](../reference/tycoon-yml.md#ask)
- [Issue #7](https://github.com/Database-Tycoon/tycoon-cli/issues/7) — original "make this happy path real" issue

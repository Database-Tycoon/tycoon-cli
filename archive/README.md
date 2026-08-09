# archive/

Frozen artifacts kept for the record. Nothing here is built, imported, or
tested — it exists so that history isn't lost when a source repository goes
away.

## `pipeline-city-history.bundle`

The complete git history of the **pipeline-city** repository, which developed
the 3D catalog renderer now living in `src/tycoon_city/` and `web/`. That
repository was absorbed into this one on 2026-08-09 and then deleted; this
bundle is the only surviving copy of its 185 commits.

Restore it as an ordinary repository:

```bash
git clone archive/pipeline-city-history.bundle /tmp/pipeline-city
git bundle verify archive/pipeline-city-history.bundle   # integrity check
```

It carries every ref — `feature/city-foundation` (the real work; `main` trails
it by 158 commits), `feature/engine-bones`, `main`, and tag `v0.1.0`.

**A bundle carries tracked history only.** Everything gitignored in the original
repo — the agent session records under `.superpowers/`, the `.agents/skills/`
definitions, the `.mbox` patch exports, `spikes/` — is *not* in here. That is
why the three skills now in `skills/` and the scripts in `spikes/` were copied
into this repository directly rather than left to the bundle. If you are looking
for something and it isn't in the clone, it was gitignored and is gone.

Why a bundle rather than a subtree merge: the renderer arrived here as a clean
vendored commit, and grafting 185 commits of a differently-named project into
this history would have muddied `git log` permanently for archival value that a
single file serves just as well.

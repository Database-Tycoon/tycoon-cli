# Publishing to PyPI

This guide walks through publishing `database-tycoon` to PyPI for the first time using GitHub's trusted publishing (no API tokens needed).

---

## What is Trusted Publishing?

PyPI supports a passwordless publish method using GitHub Actions' built-in identity (OIDC). Instead of storing a secret API key, PyPI verifies that the publish request came from a specific GitHub repo, workflow file, and environment. You set this up once on PyPI's website, then every tagged release publishes automatically.

---

## One-Time Setup

You need to do this once on both TestPyPI (for testing) and PyPI (for real releases).

### Step 1 — Create GitHub Environments

In your GitHub repo (`Database-Tycoon/tycoon-cli`):

1. Go to **Settings → Environments**
2. Create an environment named **`testpypi`**
   - No extra rules needed
3. Create an environment named **`pypi`**
   - Optional: add a protection rule requiring manual approval before production publish

### Step 2 — Register a Trusted Publisher on TestPyPI

1. Log in at **https://test.pypi.org**
2. Go to **Account Settings → Publishing** (direct link: https://test.pypi.org/manage/account/publishing/)
3. Click **Add a new pending publisher** and fill in:

   | Field | Value |
   |---|---|
   | PyPI Project Name | `database-tycoon` |
   | Owner | `Database-Tycoon` |
   | Repository name | `tycoon-cli` |
   | Workflow filename | `publish.yml` |
   | Environment name | `testpypi` |

4. Click **Add**

### Step 3 — Register a Trusted Publisher on PyPI

1. Log in at **https://pypi.org**
2. Go to **Account Settings → Publishing** (direct link: https://pypi.org/manage/account/publishing/)
3. Same form, same values — except Environment name is **`pypi`**

   | Field | Value |
   |---|---|
   | PyPI Project Name | `database-tycoon` |
   | Owner | `Database-Tycoon` |
   | Repository name | `tycoon-cli` |
   | Workflow filename | `publish.yml` |
   | Environment name | `pypi` |

4. Click **Add**

---

## How the Publish Workflow Works

The workflow lives at `.github/workflows/publish.yml` and triggers whenever you push a tag starting with `v` (e.g. `v0.4.0`, `v0.5.0`).

It runs four jobs in sequence:

```
preflight → build → publish-testpypi → publish-pypi
```

1. **preflight** checks that the tag, `pyproject.toml`, `src/tycoon/__init__.py`, the `CHANGELOG.md` section and the release notes agree on the version and carry a real date (`UNRELEASED` and `_Released: TBD_` fail here).
2. **build** runs `uv build` to produce the wheel and sdist in `dist/`.
3. **publish-testpypi** uploads to TestPyPI first; if this fails, the production publish is blocked.
4. **publish-pypi** uploads to PyPI only after TestPyPI succeeds.

The GitHub Release is not created by the workflow. Create it by hand after the publish succeeds, with the notes from `docs/releases/v<ver>.md`.

---

## Publishing a Release

Development happens on a per-version release branch (see the *Release
process* section of `CONTRIBUTING.md`); nothing pushes to `main` directly.
The examples below use `tycoon-cli` as the remote name, which is what a
clone of this repository is called in the maintainers' checkouts; substitute
your own.

1. Open the cycle on the release branch with the version bump in
   `pyproject.toml`, `src/tycoon/__init__.py` and `uv.lock`, plus a
   `docs/releases/v<ver>.md` stub. Content PRs then target that branch.

2. When the cycle is done, land the date-set commit last: the dated
   `## [<ver>] - YYYY-MM-DD` section in `CHANGELOG.md` and the
   `_Released: YYYY-MM-DD_` line in the notes. Preflight only checks the
   shape, so a date set early ships stale.

3. Merge the release branch into `main` via PR, then tag the merge commit:
   ```bash
   git fetch tycoon-cli main
   git tag v0.2.2 tycoon-cli/main
   git push tycoon-cli refs/tags/v0.2.2   # triggers the publish workflow
   ```

   The branch and its tag share a name, so always push with the
   fully-qualified `refs/heads/...` / `refs/tags/...` form. A bare
   `git push tycoon-cli v0.2.2` is ambiguous and is rejected. The same
   applies to deleting the merged branch later: `--delete refs/heads/v0.2.2`.

4. Watch the run, then create the GitHub Release:
   ```bash
   gh run watch "$(gh run list --workflow publish.yml --limit 1 --json databaseId --jq '.[0].databaseId')" --exit-status
   git show refs/tags/v0.2.2:docs/releases/v0.2.2.md > /tmp/notes.md
   gh release create v0.2.2 --verify-tag --title "v0.2.2: <headline>" --notes-file /tmp/notes.md
   ```

A release is done when four surfaces agree: the PR merged to `main`, the
tag, the version on PyPI, and the GitHub Release marked Latest.

The workflow triggers automatically. Watch it at:
`https://github.com/Database-Tycoon/tycoon-cli/actions`

---

## Verifying the Release

After a successful publish:

**TestPyPI:**
```bash
pip install --index-url https://test.pypi.org/simple/ database-tycoon
```

**PyPI (real):**
```bash
pip install database-tycoon
```

---

## Troubleshooting

### `invalid-publisher` error
The trusted publisher isn't configured on PyPI yet. Follow Step 2 and 3 above.

### `invalid-publisher` after configuring
Double-check that:
- The environment name in the GitHub workflow matches exactly (case-sensitive: `testpypi` / `pypi`)
- The workflow filename is `publish.yml` (not `publish.yaml`)
- The owner is `Database-Tycoon` (capital D and T)

### Build fails, or the publisher rejects the wheel
Run the build locally from a clean checkout before pushing a tag, and check
the artifacts the way the publisher will:
```bash
uv build
uvx twine check dist/*
unzip -p dist/*.whl '*/METADATA' | head -2   # Metadata-Version the pinned publisher accepts
```
A green build is not a green publish: v0.2.0 built cleanly and was rejected
because the wheel's `Metadata-Version` had moved ahead of the publisher's
bundled twine. Building in a working tree with ignored files present also
inflates the sdist; hatchling honours only the root `.gitignore`.

### The publish workflow fails after the tag is pushed
First confirm the version still returns 404 on both
`https://pypi.org/pypi/database-tycoon/<ver>/json` and TestPyPI. If it does,
fix forward on `main` via PR, delete the tag, re-tag the new tip and push the
tag again. Do not bump the version to escape a failed publish; that leaves a
hole in the version history for a release that never existed.

### Version conflict (version already exists on PyPI)
PyPI does not allow re-uploading the same version. This only happens when a
publish partially succeeded; check which index has the version before
deciding anything.

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

It runs three jobs in sequence:

```
build → publish-testpypi → publish-pypi
```

1. **build** — runs `uv build` to produce wheel and sdist in `dist/`
2. **publish-testpypi** — uploads to TestPyPI first; if this fails, production publish is blocked
3. **publish-pypi** — uploads to the real PyPI only after TestPyPI succeeds

---

## Publishing a Release

### First release (v0.1.0)

Once the trusted publisher is configured (Steps 1–3 above), tag and push:

```bash
git tag v0.1.0
git push origin v0.1.0
```

### Future releases

1. Update the version in `pyproject.toml`:
   ```toml
   version = "0.2.0"
   ```

2. Commit the bump:
   ```bash
   git add pyproject.toml
   git commit -m "chore: bump version to 0.2.0"
   git push origin main
   ```

3. Tag and push:
   ```bash
   git tag v0.2.0
   git push origin v0.2.0
   ```

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
# or with extras:
pip install "database-tycoon[dagster]"
pip install "database-tycoon[ask]"
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

### Build fails
Run `uv build` locally first to catch errors before pushing a tag:
```bash
uv build
ls dist/
```

### Version conflict (version already exists on PyPI)
PyPI does not allow re-uploading the same version. Bump the version in `pyproject.toml` and tag a new release.

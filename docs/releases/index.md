# Releases

A page per release from v0.1.1 onward, written as a narrative: what shipped,
what did not, and why.

The current release is [v0.2.2](v0.2.2.md). Older versions are in the
navigation, and the tagged releases from v0.1.1 onward are also listed on
[GitHub](https://github.com/Database-Tycoon/tycoon-cli/releases).

## How these differ from the changelog

Two records, because they answer to two different readers.

These pages are written for someone **upgrading**. They lead with what changed
in behaviour, call out anything that needs a change to a working project, and
explain the reasoning behind a decision rather than only naming it.

[`CHANGELOG.md`](https://github.com/Database-Tycoon/tycoon-cli/blob/main/CHANGELOG.md)
in the repository is written for someone **reading the diff**. It follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), groups entries under
headings such as Added, Changed and Fixed, and usually links an entry to its
issue and pull request.

If you only want to know whether an upgrade will affect you, read the release
page for your target version. If you want to know exactly what moved, read the
changelog.

## Versioning

tycoon is pre-1.0. Behaviour can change in any release, including a patch:
v0.2.2 changed what `--no-prompt` does to a CI job that was relying on it.
Read the page for the version you are moving to before you upgrade. Pages
from v0.1.10 onward carry an `Upgrading from <previous>` section; earlier ones
mostly use `Upgrade notes`.

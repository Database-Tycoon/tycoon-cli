# Releases

One page per released version, written as a narrative: what shipped, what did
not, and why. Together they are the canonical change history for tycoon.

Choose a version from the navigation. The newest is listed first.

## How these differ from the changelog

Two records, because they answer to two different readers.

These pages are written for someone **upgrading**. They lead with what changed
in behaviour, call out anything that needs a change to a working project, and
explain the reasoning behind a decision rather than only naming it.

[`CHANGELOG.md`](https://github.com/Database-Tycoon/tycoon-cli/blob/main/CHANGELOG.md)
in the repository is written for someone **reading the diff**. It follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), groups entries under
Added, Changed, Fixed, Removed, Deprecated and Security, and links each entry
to its issue and pull request.

If you only want to know whether an upgrade will affect you, read the release
page for your target version. If you want to know exactly what moved, read the
changelog.

## Versioning

tycoon follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html) and
is still pre-1.0, so a minor version can change behaviour. Each release page
says plainly whether it does.

Anything described in these pages as deferred or planned links to a tracking
issue on [GitHub](https://github.com/Database-Tycoon/tycoon-cli/issues).

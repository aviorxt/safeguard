# Contributing

Use an issue form for false positives, missed threats, bugs, source/category proposals or migrations. Be respectful, specific and evidence-driven. Do not post secrets, personal data, private logs or live malware download links.

## Fork → branch → pull request

1. Fork the repository and create a focused branch from current `main`.
2. Edit `rules/`, `sources.json`, `catalog.json`, scripts, docs or site files as appropriate. Never hand-edit generated lists.
3. Preserve source attribution and license notices. New feeds must have a clear license, maintained public URL, size floor, supported syntax and a reason to include them.
4. Run `python -m unittest discover -s tests`, `python scripts/build.py`, `python scripts/build_site.py`, and `node --check site/app.js`.
5. Open a PR using the supplied template. Explain behavior, evidence, tests, breaking changes and rollback steps. Generated changes must be reproducible.

The required `Validate repository` check runs on source, rule, website and documentation PRs. Generated-only PRs touching `blocklists/` and `sources/` are validated by the publisher's explicit CI dispatch instead of triggering a duplicate approval-gated bot PR run. Do not hand-edit generated files; a human generated-only PR must also have a maintainer dispatch CI before it can merge. Fork PR jobs have read-only tokens and no repository secrets. GitHub may require a maintainer to approve a first-time contributor's workflow run.

Main is protected by a repository ruleset: pull requests, the required `Safeguard validation` status, resolved review threads, linear history, no force pushes and no branch deletion. No bypass actors are configured. An independent approval is encouraged but not required so a sole maintainer can merge their own passing PR.

Daily automation opens a generated-data PR, explicitly dispatches repository CI, and waits for successful validation before requesting a squash merge. A trusted status reporter maps the actual CI outcome to the tested commit; GitHub does not evaluate manually dispatched workflow-job checks directly for PR rules. The server enforces that required reported status. The updater has only the repository-token permissions needed to push its temporary branch, create a PR, dispatch CI and merge a passing update; no PAT is stored. PR validation stays read-only. Failed validation leaves the update unmerged for review.

## Domain changes

`rules/block.txt` adds reviewed domains to every subscription. `rules/allow.txt` overrides them everywhere. A narrow allow entry beneath a blocked parent removes the parent rule too; siblings may become unblocked. Review the report's suppressed rules. Prefer upstream reports for upstream false positives and keep local exceptions justified.

New restrictions belong in optional categories unless they clearly fit the documented combined profiles. Do not quietly add gambling, social or device restrictions to Family/Standard. Record meaningful behavior changes in CHANGELOG.md.

## Fork maintenance

Keep GPL/MIT and font notices, source snapshots and attribution. Replace project URLs and branding if you operate your own service. Review `sources.json` and the HTTPS source allowlist together. GitHub scheduled workflows may need enabling on forks; set up your own hosting only if you want a public download service. Do not copy credentials or assume access to AVRXT infrastructure.

See MIGRATION.md for URL/profile changes and SECURITY.md for private vulnerability reports.

For bot-dispatched update validation, GitHub suppresses the downstream reporter event. The trusted main-only publisher reports the canonical CI run's actual result on its exact commit SHA before requesting a merge. Human PRs use the independent reporter. Both paths require successful validation, use repository-scoped tokens, and keep fork PR CI read-only.

## Community domain submissions

Use https://safeguard.avrxt.tech/update-list or the Domain submission issue form. Enter the GitHub username you submit from, one domain, a category, and evidence. Maintainers verify classification and false-positive risk before adding the `approved-domain` label. That label starts the trusted default-branch workflow, which checks maintainer permissions and authenticated authorship, builds all formats, and publishes through a validated pull request. Published credit comes from the GitHub issue author, never an unverified username. Adult rules remain outside Standard; optional categories stay optional.

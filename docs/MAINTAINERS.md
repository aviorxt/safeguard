# Maintainer operations

## Publishing

The public site builds from the protected main branch using `python scripts/build_site.py`, output `dist`. Its custom hostname is safeguard.avrxt.tech. The builder validates every output hash, source snapshot hash, catalog entry, domain count and a report age under 48 hours. Every published file must fit the hosting file-size limit. It packages the committed snapshots without downloading rules.

The daily update workflow runs at 03:17 UTC (08:47 IST), or manually. It tests the builder, downloads reviewed sources, regenerates all formats, validates packaging, and publishes generated files. GitHub schedules may be delayed or disabled after prolonged public-repository inactivity.

The publication workflow runs after successful updates and every six hours. It checks the custom domain over HTTPS, every generated output hash, catalog/report equality with the current repository, and freshness within 48 hours. Ten attempts 30 seconds apart allow deployment propagation. GitHub email notifications depend on account settings. No external alert delivery is assumed.

## Branch policy

The active main ruleset requires pull requests, the GitHub Actions `Validate repository` check, resolved review threads and linear history. It blocks force pushes and deletion. There is no human/admin bypass entry. A second person's approval is encouraged but not required for a sole-maintainer project.

The `github-actions[bot]` user has an explicit automation bypass for the existing publisher. GitHub rejected using the built-in Actions integration as a bypass actor on this personal repository; the bot-user actor is used instead. The bypass is broad to that bot within this repository, not cryptographically scoped to one workflow. Keep every PR job read-only and review any change that grants write permissions to other workflows. No new PAT or deployment secret is used.

## Validation and recovery

Run tests, site packaging and JavaScript syntax checks locally. CI additionally uses native BIND, dnsmasq and Unbound validators against the full Family outputs. If a source fails or shrinks sharply, review it rather than automatically reducing safeguards. For approved hosts feeds, non-portable hostnames are excluded with audit records; over 1% invalid hostnames fails the build.

To revert a bad source or rule change, open a PR reverting the input change, pass validation and merge it, then run Update Safeguard. Keep existing subscription URLs available. The public report and deployment.json identify the last successful snapshot and deployed revision.

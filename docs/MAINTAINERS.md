# Maintainer operations

## Publishing

The public site builds from the protected main branch using `python scripts/build_site.py`, output `dist`. Its custom hostname is safeguard.avrxt.tech. The builder validates every output hash, source snapshot hash, catalog entry, domain count and a report age under 48 hours. Every published file must fit the hosting file-size limit. It packages the committed snapshots without downloading rules.

The daily update workflow runs at 03:17 UTC (08:47 IST), or manually. It tests the builder, downloads reviewed sources, regenerates all formats, validates packaging, and publishes generated files. GitHub schedules may be delayed or disabled after prolonged public-repository inactivity.

The publication workflow runs after successful updates and every six hours. It checks the custom domain over HTTPS, every generated output hash, catalog/report equality with the current repository, and freshness within 48 hours. Ten attempts 30 seconds apart allow deployment propagation. GitHub email notifications depend on account settings. No external alert delivery is assumed.

## Branch policy

The active main ruleset requires pull requests, the `Safeguard validation` commit status, resolved review threads and linear history. It blocks force pushes and deletion. There is no human/admin bypass entry. A second person's approval is encouraged but not required for a sole-maintainer project.

No automation bypass is configured. The publisher pushes generated data to a temporary automation branch, creates a PR, explicitly dispatches the required CI using the repository token, waits for success and requests a squash merge. Main protection enforces the required reported status and up-to-date branch. The trusted `Report validation status` workflow verifies the canonical CI workflow and reads only GitHub metadata; it never checks out contributor code or downloads artifacts. This reports the real validation result on the tested commit because workflow-dispatch job checks are not evaluated directly by PR rules. CI failures or merge conflicts leave the PR open for review. PR creation is enabled in repository Actions settings; default token permissions are read-only, with explicit contents/pull-requests/actions writes only in the main-only publisher.

The site builder fingerprints CSS and JavaScript filenames so new HTML cannot accidentally reuse an old cached bundle.

## Validation and recovery

Run tests, site packaging and JavaScript syntax checks locally. CI additionally uses native BIND, dnsmasq and Unbound validators against the full Family outputs. If a source fails or shrinks sharply, review it rather than automatically reducing safeguards. For approved hosts feeds, non-portable hostnames are excluded with audit records; over 1% invalid hostnames fails the build.

To revert a bad source or rule change, open a PR reverting the input change, pass validation and merge it, then run Update Safeguard. Keep existing subscription URLs available. The public report and deployment.json identify the last successful snapshot and deployed revision.

For bot-dispatched update validation, GitHub suppresses the downstream reporter event. The trusted main-only publisher reports the canonical CI run's actual result on its exact commit SHA before requesting a merge. Human PRs use the independent reporter. Both paths require successful validation, use repository-scoped tokens, and keep fork PR CI read-only.

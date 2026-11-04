# AVRXT Safeguard

A reproducible DNS blocklist maintained by AVRXT. Combines curated upstream intelligence with AVRXT overrides; upstream maintainers deserve credit for their research. This is an aggregation, not a claim of independently discovering every threat.

## Downloads

| Profile | AdGuard Home subscription |
| --- | --- |
| **Family — all in one**: ads, trackers, threat domains and adult content | `https://raw.githubusercontent.com/avrxtcloud/safeguard/main/blocklists/family.txt` |
| Standard: ads, trackers and threat domains | `https://raw.githubusercontent.com/avrxtcloud/safeguard/main/blocklists/standard.txt` |

Add one URL under AdGuard Home → Filters → DNS blocklists. Family includes Standard; do not add both. `blocklists/*-domains.txt` contains bare domains, and `*-hosts.txt` contains hosts-format equivalents. All outputs are derived from domain-wide rules; browser cosmetic rules and URL paths are deliberately unsupported.

## Coverage and limits

HaGeZi NORMAL supplies balanced advertising/tracking and unwanted-domain protection; TIF MINI adds threat intelligence including malware, phishing, scams and cryptomining domains. Family additionally includes NSFW adult domains. See [sources.json](sources.json) for exact inputs and [build report](blocklists/report.json) for counts, source SHA-256 digests and rejected syntax. The upstream inputs are copied verbatim into `sources/` on each successful build for inspection and license compliance.

DNS lists cannot block every threat, remove same-domain YouTube ads, inspect HTTPS paths, or enforce Safe Search. Keep AdGuard Safe Search, parental classification, Safe Browsing and DNSSEC enabled separately. No gambling, social-media or VPN blanket blocks are included. False positives and missed threats are possible. A blocked domain does not prove every page on it is malicious.

## Updates and review

GitHub Actions builds daily at 03:17 UTC and on changes to the builder, source manifest or overrides. Manual runs are supported. The workflow publishes only after tests and all downloads pass. Source counts below the configured floor, reductions over 25% compared with the last snapshot, unsupported rules, and unexpectedly broad suffix rules fail the build. A failed run leaves the previous published files intact. Review Actions failures rather than lowering safeguards without investigation.

Run locally with Python 3.11+: `python -m unittest discover -s tests`, then `python scripts/build.py`. No dependencies or API credentials are required. Change the source manifest or overrides through a reviewed commit. To remove a source intentionally, remove its entry from `sources.json`; consider its license before redistribution.

Allowlist entries override blocked domains and descendants. An allowlist entry inside a broader blocked suffix suppresses that broader rule too, to keep all three output formats consistent; it may unblock siblings. The report records these suppressed rules for review. Do not place broad exceptions here without considering that effect.

## Reports

Open a GitHub issue for a false positive or missing threat; include the domain, matching profile and a short explanation, without sensitive browsing URLs or personal data. Private contact: **dns@avrxt.tech**. Requests are reviewed, never automatically allowed.

## Attribution and licensing

Sources: [HaGeZi DNS Blocklists](https://github.com/hagezi/dns-blocklists), maintained by Gerd HaGeZi and contributors, GPL-3.0. AVRXT combines, normalizes, deduplicates and applies overrides to those lists. Upstream notices are preserved in the source snapshots. See [LICENSE](LICENSE) and [NOTICE](NOTICE). AVRXT-authored build code and modifications are also GPL-3.0-or-later. Provided without warranty.

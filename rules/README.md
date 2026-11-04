# Reviewed domain supplements

`ads-trackers.txt` applies to Standard, Family and Ads & trackers. It pins confirmed advertising and tracking gaps, including DoubleClick and related advertising infrastructure. A rule for `doubleclick.net` covers its subdomains in Adblock, dnsmasq, Unbound and RPZ; ordinary hosts files match exact names only.

Evidence sources reviewed on 2026-11-04:

- AdGuard DNS filter: https://adguardteam.github.io/AdGuardSDNSFilter/Filters/filter.txt (GPL-3.0; repository https://github.com/AdguardTeam/AdGuardSDNSFilter).
- HaGeZi Pro: https://raw.githubusercontent.com/hagezi/dns-blocklists/main/adblock/pro.txt (GPL-3.0).

`adult.txt` applies only to Family and Adult. It pins the known XHamster roots, aliases and related adult infrastructure present in the preserved HaGeZi NSFW snapshot. It does not guess domain names or claim to cover every future mirror. The full NSFW feed continues to update daily.

These files preserve the owner's explicit policy across upstream changes. They are not a full import of the referenced feeds. `block.txt` remains the global override for every profile; `allow.txt` takes precedence everywhere. Scoped counts, targets and SHA-256 digests are recorded in the build report. Crash-reporting services are not added merely to raise a test score.

# Compatibility

All subscriptions have six generated formats. Replace `family` with `standard` or a category ID from catalog.json. Choose an importer explicitly compatible with that format; not every hosted DNS service accepts external lists.

| Resolver / consumer | Format | Notes |
| --- | --- | --- |
| AdGuard Home | `.txt` | Add under Filters → DNS blocklists. DNS Adblock syntax, not cosmetic browser filtering. |
| Pi-hole | `-domains.txt` | Add as a subscribed adlist, then update gravity. Match behavior depends on Pi-hole version and importer. |
| Blocky | `-domains.txt` | Configure as a blocking list source; use the consumer's documented refresh configuration. |
| Technitium DNS | `-domains.txt` or `-hosts.txt` | Use the corresponding blocklist importer supported by your version. |
| Hosts-compatible filters / OS hosts | `-hosts.txt` | Exact names only in ordinary hosts files; no wildcard subdomain behavior. Use a managed importer; do not overwrite the rest of your hosts file. |
| dnsmasq | `-dnsmasq.conf` | `local=/domain/` prevents forwarding for names beneath that domain. Existing local records can still answer. Install as a configuration include and refresh via your own downloader. |
| Unbound | `-unbound.conf` | Include inside `server:`; `always_nxdomain` applies to the name and descendants. Use `unbound-checkconf` before reload. |
| BIND RPZ | `-rpz.zone` | Load as a policy zone and enable response-policy; exact and wildcard NXDOMAIN records are included. Validate with `named-checkzone` before reload. |
| PowerDNS Recursor / other RPZ resolvers | `-rpz.zone` | Use the resolver's RPZ import configuration. A zone file is not an automatic subscription by itself. |
| Hosted DNS providers | Provider-dependent | Works only if the provider exposes custom-list URL imports in one of these formats. A provider's built-in-only filtering cannot be replaced by pasting a URL. |

## Matching and behavior

Domains are normalized, deduplicated and shared across output formats, but matching is a property of the consumer. Adblock, Unbound, dnsmasq and RPZ configurations cover the name and descendants; hosts files normally match exact names only. Bare-domain importers differ. Check your resolver documentation and test your intended domains.

Hosts outputs use `0.0.0.0`. Unbound and RPZ use NXDOMAIN. dnsmasq local zones return no upstream answer unless a local record exists. A custom block page is a resolver/server feature; these lists do not configure block pages, DNSSEC, Safe Search or certificates.

## Configuration files and refreshes

The dnsmasq, Unbound and RPZ downloads are configuration data, not standalone resolver configurations. Do not overwrite existing resolver settings. Fetch to a temporary file, validate with your resolver's native tool, atomically replace the list include/zone, then reload. Keep a last-known-good copy. These formats do not install a refresh daemon. The RPZ serial uses UTC Unix seconds for monotonic updates within normal update intervals.

A fresh website report does not mean your resolver has refreshed its subscription. Check its own last-update time and query log. A blocked HTTPS site generally cannot display a custom page without a certificate error.

# Migration guide

## Moving to Safeguard

Choose Family or Standard, then optional categories. Pick the format your resolver supports from COMPATIBILITY.md. Keep your previous subscription available while testing. Import the new URL, refresh the resolver, check known allowed and blocked domains, review the query log, and remove duplicate subscriptions only after the results are satisfactory. Keep Safe Search, DNSSEC and other resolver protections configured separately.

## Requesting a migration

Use the Migration request issue form. Include:

- Current and proposed public repository/list URLs, resolver/version and format.
- What changes and why; affected categories and any breaking behavior.
- Domain/list URL mapping, coexistence period and required user action.
- Source licensing and attribution, data ownership and compatibility checks.
- Test results, success criteria, proposed timing and rollback steps.

Never put DNS client IDs, passwords, tokens or private logs in an issue or PR. A migration request does not grant access to the requester's infrastructure.

## URL compatibility and rollback

The existing `family.txt` and `standard.txt` endpoints remain available. Adding new formats or categories does not require changing an existing subscription. If a future migration renames a file, document aliases/redirects and a deprecation period before removal. To roll back a subscription change, restore the previous URL, refresh the resolver and re-check behavior. Maintain an independent backup of resolver configuration before changing it.

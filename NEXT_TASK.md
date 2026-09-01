# Next Task: Lightweight Request Hardening

## Objective

Add lightweight CSRF protection and reject submitted URLs that directly name
local or private IP addresses.

## Required changes

1. Add CSRF protection to every state-changing route, currently:
   - `POST /enqueue`
   - `POST /clear`
2. Generate and validate CSRF tokens without adding a database, reverse proxy,
   account system, or large framework dependency.
3. Return a clear client error for a missing or invalid CSRF token.
4. Reject URLs whose hostname is an IP literal in any of these categories:
   - Loopback
   - Private
   - Link-local
   - Unspecified
   - Multicast
   - IPv4 or IPv6 reserved ranges
5. Continue accepting ordinary `http` and `https` URLs with public hostnames or
   public IP literals.
6. Show a useful validation message when a submitted URL is rejected.

## Scope limits

- Preserve the project's small, LAN-oriented design.
- Do not add full username/password authentication.
- Do not add a reverse proxy, HTTPS configuration, VPN requirement, database,
  Docker packaging, or DRM-related functionality.
- Do not attempt aggressive DNS resolution or redirect policing in this task.
- Do not modify or deploy to the live downloader installation.

## Tests

Add focused automated tests covering at least:

- A valid CSRF token permits queue submission.
- A missing or invalid CSRF token rejects queue submission.
- A missing or invalid CSRF token rejects clearing results.
- Public hostname URLs remain accepted.
- Public IP-literal URLs remain accepted.
- IPv4 loopback, private, link-local, unspecified, multicast, and reserved IP
  literals are rejected.
- IPv6 loopback, private, link-local, unspecified, multicast, and reserved IP
  literals are rejected.
- Existing queue and clear-results behavior remains intact for valid requests.

## Completion requirements

1. Review the repository and implementation before editing.
2. Make the smallest maintainable change that satisfies the objective.
3. Run syntax checks and the complete automated test suite.
4. Review the final diff for security regressions and unnecessary complexity.
5. Report findings, tests, and any limitations before committing.

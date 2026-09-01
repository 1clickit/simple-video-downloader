# Future Options

This document records possible hardening and reliability improvements for the
simple video downloader. The service is currently intended for a trusted home
LAN inside an unprivileged LXC, not for direct public exposure. Recommendations
should therefore be proportionate to that environment and should preserve the
project's intentionally small scope.

## Review assessment

| Finding | Assessment for the current environment | Recommendation |
| --- | --- | --- |
| Unauthenticated requests and CSRF | Real risk, although a `High` rating generally assumes broader exposure. A malicious webpage opened by a LAN user could potentially submit a hidden request to the downloader. | Add lightweight CSRF protection and reject URLs that directly name loopback, private, or link-local IP addresses. Do not add a reverse proxy or full login system yet. |
| Service runs as root | Valid, although root inside an unprivileged LXC is already isolated from the Proxmox host. | Run the service as a dedicated `video-downloader` user and apply moderate, tested systemd hardening. |
| Active jobs can disappear after 100 entries | Genuine queue-display bug, though unlikely during ordinary use. | Never prune queued or running jobs. Set a clear queue limit and prune only completed or failed entries. |
| Storage or worker initialization can fail silently | Especially relevant because `/downloads` is backed by an NFS-mounted NAS. | Validate storage before accepting jobs, fail startup clearly when appropriate, and show a useful storage-unavailable error. |
| Queue is held only in memory | Accurate and acceptable for this small utility. | Document the limitation. Do not add a database unless persistent queuing becomes a real requirement. |

## Recommended first hardening pass

1. Add a CSRF token to **Add to queue** and **Clear results**.
2. Reject URL destinations that directly specify loopback, private, or
   link-local IP addresses.
3. Keep the service LAN-only on its existing port.
4. Run Flask, yt-dlp, and FFmpeg under a dedicated non-root service account.
5. Add conservative systemd protections such as `NoNewPrivileges=true` and
   `PrivateTmp=true`; test filesystem restrictions before deployment.
6. Set a reasonable maximum for pending and running jobs, such as 100.
7. Never remove an active job from the visible status list.
8. Refuse new submissions when NAS storage is unavailable or not writable.
9. Document that a service or container restart clears the in-memory queue.
   Users can resubmit a URL, and yt-dlp will normally continue its partial file.

## Options to defer

The following would add substantial complexity and are not currently justified:

- Reverse proxy
- HTTPS certificates
- Full username/password authentication
- Database-backed persistent queue
- Multiple application users
- Docker packaging
- Mandatory VPN access

These options can be reconsidered if the downloader is later shared with
untrusted users, exposed outside the trusted LAN, or expanded into a larger
service.

## URL filtering scope

Private-address protection should initially focus on URLs that directly name IP
addresses such as `127.0.0.1`, private RFC 1918 ranges, and link-local ranges.
Aggressive DNS resolution, redirect policing, or broad hostname filtering may
break legitimate video sites and create more maintenance than value. Stronger
SSRF defenses should be added only if the service's exposure changes.

## Guiding principle

Address the genuine queue, privilege, and storage-failure issues while retaining
the project's low-tech character. Security improvements should reduce realistic
risk without turning a small LAN utility into a platform.

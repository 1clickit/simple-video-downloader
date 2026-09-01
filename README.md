# Simple Video Downloader

A deliberately small, LAN-only web interface for queuing multiple video URLs
through [yt-dlp](https://github.com/yt-dlp/yt-dlp) and FFmpeg. Paste one URL per
line, watch each job progress, and save completed files to a local directory or
NAS mount.

## Features

- Multiple URLs, one per line
- Sequential download queue
- Basic progress and error display
- Best available video/audio with MP4 merge when possible
- Download archive to prevent accidental duplicates
- Optional Netscape-format `cookies.txt` for authenticated sites
- Clear completed/failed results without deleting downloaded files
- Systemd service with automatic restart

## Intended use

This project is intentionally simple. It has no accounts or application-level
authentication. Run it only on a trusted LAN or behind a VPN. Do not forward
port 8080 directly to the public internet.

Use it only for media you are authorized to download. It does not circumvent
DRM.

## Debian installation

Install the operating-system packages:

```bash
apt update
apt install -y python3 python3-flask ffmpeg curl ca-certificates
```

Install the current standalone yt-dlp release:

```bash
curl -L "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp" -o /usr/local/bin/yt-dlp
chmod 755 /usr/local/bin/yt-dlp
yt-dlp --version
```

Install this application from a checked-out repository:

```bash
install -d /opt/video-downloader /downloads
install -m 755 app.py /opt/video-downloader/app.py
install -m 644 video-downloader.service /etc/systemd/system/video-downloader.service
systemctl daemon-reload
systemctl enable --now video-downloader
```

Open:

```text
http://SERVER_IP:8080
```

## NAS storage

Mount the NAS on the virtualization host and bind-mount it into the container
at `/downloads`. This avoids giving an unprivileged container permission to
mount NFS directly.

Example Proxmox bind mount for container `110`:

```bash
pct set 110 -mp0 /mnt/video-downloads,mp=/downloads
```

For a persistent NFS host mount, use `_netdev`, `nofail`, and
`x-systemd.automount` so an unavailable NAS does not block host startup.

## Authenticated sites

Place an exported Netscape-format cookie file at:

```text
/etc/video-downloader/cookies.txt
```

Restrict it to root and never commit it:

```bash
install -d -m 700 /etc/video-downloader
chmod 600 /etc/video-downloader/cookies.txt
```

The application detects the file automatically. Username/password storage and
DRM circumvention are intentionally not implemented.

## Service commands

```bash
systemctl status video-downloader
systemctl restart video-downloader
journalctl -u video-downloader -n 100 --no-pager
```

Downloads run one at a time. A host or container restart may interrupt the
active job, but yt-dlp's partial files normally allow it to resume.

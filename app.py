#!/usr/bin/env python3
import os
import queue
import subprocess
import threading
from datetime import datetime
from urllib.parse import urlparse

from flask import Flask, jsonify, redirect, render_template_string, request, url_for

app = Flask(__name__)
download_dir = os.environ.get("DOWNLOAD_DIR", "/downloads")
cookie_file = os.environ.get("COOKIE_FILE", "/etc/video-downloader/cookies.txt")
jobs = []
job_queue = queue.Queue()
lock = threading.Lock()

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Video Downloader</title>
<style>
body{font-family:system-ui,sans-serif;max-width:850px;margin:40px auto;padding:0 18px;background:#111827;color:#f3f4f6}
textarea{box-sizing:border-box;width:100%;height:190px;padding:12px;border-radius:8px;border:1px solid #4b5563;background:#1f2937;color:#fff;font:15px monospace}
button{margin-top:12px;padding:10px 18px;border:0;border-radius:8px;background:#2563eb;color:white;font-weight:700;cursor:pointer}.secondary{background:#4b5563}
.job{margin-top:12px;padding:12px;border-radius:8px;background:#1f2937}.url{word-break:break-all}.state{font-weight:700}.error{color:#fca5a5}.done{color:#86efac}.small{color:#9ca3af;font-size:13px}
</style></head><body>
<h1>Video Downloader</h1>
<p>Paste one video URL per line. Downloads run one at a time.</p>
<form method="post" action="{{ url_for('enqueue') }}"><textarea name="urls" required placeholder="https://example.com/video\nhttps://example.com/another-video"></textarea><br><button type="submit">Add to queue</button></form>
<p class="small">Saving to {{ download_dir }}</p>
<form method="post" action="{{ url_for('clear_results') }}"><button class="secondary" type="submit">Clear results</button></form>
<div id="jobs"></div>
<script>
async function refresh(){const r=await fetch('/status');const data=await r.json();const box=document.getElementById('jobs');box.innerHTML=data.map(j=>`<div class="job"><div class="url">${escapeHtml(j.url)}</div><div class="state ${j.state}">${escapeHtml(j.state.toUpperCase())}</div><div class="small">${escapeHtml(j.detail||'')}</div></div>`).join('')||'<p class="small">No downloads queued.</p>'}
function escapeHtml(v){const d=document.createElement('div');d.textContent=v;return d.innerHTML}refresh();setInterval(refresh,1500);
</script></body></html>"""


def valid_url(value):
    parsed = urlparse(value)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def update(job, state=None, detail=None):
    with lock:
        if state is not None:
            job["state"] = state
        if detail is not None:
            job["detail"] = detail[-500:]


def worker():
    os.makedirs(download_dir, exist_ok=True)
    archive = os.path.join(download_dir, ".download-archive.txt")
    while True:
        job = job_queue.get()
        update(job, "running", "Starting…")
        command = [
            "/usr/local/bin/yt-dlp", "--newline", "--continue", "--no-overwrites",
            "--download-archive", archive,
            "-f", "bv*+ba/b", "--merge-output-format", "mp4",
            "-o", os.path.join(download_dir, "%(title).180B [%(id)s].%(ext)s"),
        ]
        if os.path.isfile(cookie_file):
            command += ["--cookies", cookie_file]
        command.append(job["url"])
        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace")
            for line in process.stdout:
                update(job, detail=line.strip())
            code = process.wait()
            if code == 0:
                update(job, "done", "Completed")
            else:
                update(job, "error", f"yt-dlp exited with code {code}: {job['detail']}")
        except Exception as exc:
            update(job, "error", str(exc))
        finally:
            job_queue.task_done()


@app.get("/")
def index():
    return render_template_string(PAGE, download_dir=download_dir)


@app.post("/enqueue")
def enqueue():
    submitted = request.form.get("urls", "")
    for value in submitted.splitlines():
        value = value.strip()
        if not valid_url(value):
            continue
        job = {"url": value, "state": "queued", "detail": f"Queued {datetime.now().strftime('%H:%M:%S')}"}
        with lock:
            jobs.insert(0, job)
            del jobs[100:]
        job_queue.put(job)
    return redirect(url_for("index"))


@app.get("/status")
def status():
    with lock:
        return jsonify(list(jobs))


@app.post("/clear")
def clear_results():
    with lock:
        jobs[:] = [job for job in jobs if job["state"] in ("queued", "running")]
    return redirect(url_for("index"))


threading.Thread(target=worker, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)

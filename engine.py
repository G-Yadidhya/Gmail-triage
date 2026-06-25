import subprocess
import json
import os
import re
import html
import datetime
from email.utils import parsedate_to_datetime
from triage import triage_inbox

IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))


def _to_ist(date_str):
    try:
        dt = parsedate_to_datetime(date_str)
        dt_ist = dt.astimezone(IST)
        return dt_ist.strftime('%d %b %Y, %I:%M %p IST')
    except Exception:
        return date_str


MCP_CONFIG = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'gmail-mcp-server', 'mcp-config.json'
)


MCP_CONFIG_DIR = os.path.dirname(MCP_CONFIG)


def fetch_threads():
    with open(MCP_CONFIG, encoding='utf-8') as f:
        config = json.load(f)

    gmail_cfg = config['mcpServers']['gmail']
    cmd = [gmail_cfg['command']] + [
        os.path.join(MCP_CONFIG_DIR, a) if not os.path.isabs(a) and not a.startswith('@') else a
        for a in gmail_cfg['args']
    ]

    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding='utf-8',
        bufsize=1,
    )

    _req_id = 0

    def _request(method, params=None):
        nonlocal _req_id
        _req_id += 1
        msg = {"jsonrpc": "2.0", "id": _req_id, "method": method}
        if params:
            msg["params"] = params
        proc.stdin.write(json.dumps(msg, separators=(',', ':')) + '\n')
        proc.stdin.flush()
        return _req_id

    def _notify(method, params=None):
        msg = {"jsonrpc": "2.0", "method": method}
        if params:
            msg["params"] = params
        proc.stdin.write(json.dumps(msg, separators=(',', ':')) + '\n')
        proc.stdin.flush()

    def _recv():
        while True:
            line = proc.stdout.readline()
            if not line:
                err = proc.stderr.read()
                raise RuntimeError(f"MCP server exited early. stderr:\n{err}")
            msg = json.loads(line)
            if "method" in msg:
                continue
            return msg

    def _call(method, params=None):
        _request(method, params)
        resp = _recv()
        if "error" in resp:
            raise RuntimeError(f"MCP error ({resp['error']['code']}): {resp['error']['message']}")
        return resp.get("result")

    try:
        _call("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "engine", "version": "1.0.0"}
        })

        _notify("notifications/initialized")

        result = _call("tools/call", {
            "name": "search_emails",
            "arguments": {"query": "in:inbox", "maxResults": 3}
        })

        text = result.get("content", [{}])[0].get("text", "")
        threads = []

        for block in text.strip().split("\n\n"):
            block = block.strip()
            if not block:
                continue

            msg_id = sender = subject = date = ""
            for line in block.split("\n"):
                if line.startswith("ID: "):
                    msg_id = line[4:]
                elif line.startswith("From: "):
                    sender = line[6:]
                elif line.startswith("Subject: "):
                    subject = line[9:]
                elif line.startswith("Date: "):
                    date = line[6:]

            if not msg_id:
                continue

            detail = _call("tools/call", {
                "name": "read_email",
                "arguments": {"messageId": msg_id}
            })
            detail_text = detail.get("content", [{}])[0].get("text", "")

            thread_id = ""
            snippet = ""
            for dl in detail_text.split("\n"):
                if dl.startswith("Thread ID: "):
                    thread_id = dl[11:]
            body_idx = detail_text.find("\n\n")
            if body_idx != -1:
                raw = detail_text[body_idx + 2:].strip()
                raw = re.sub(r'<style[^>]*>.*?</style>', ' ', raw, flags=re.DOTALL)
                raw = re.sub(r'<script[^>]*>.*?</script>', ' ', raw, flags=re.DOTALL)
                raw = re.sub(r'<[^>]+>', ' ', raw)
                raw = html.unescape(raw)
                raw = re.sub(r'\[Note:.*?\]', '', raw)
                raw = re.sub(r'\s+', ' ', raw).strip()
                snippet = raw[:200]

            threads.append({
                "thread_id": thread_id,
                "sender": sender,
                "subject": subject,
                "snippet": snippet,
                "date": _to_ist(date),
            })

        return threads

    finally:
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except Exception:
            proc.kill()


def format_digest(results):
    today = datetime.date.today().strftime('%d %b %Y')
    print(f"{'='*60}")
    print(f"  INBOX DIGEST  —  {today}  |  {len(results)} threads")
    print(f"{'='*60}")

    last_priority = None
    for r in results:
        priority = r['priority'].upper()
        if last_priority is not None and priority != last_priority:
            print(f"{'-'*60}")
        last_priority = priority
        print(f"  [{priority}] {r['sender']} | {r['subject']} — {r['reason']}")
    print(f"{'='*60}")


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    threads = fetch_threads()
    results = triage_inbox(threads)
    format_digest(results)

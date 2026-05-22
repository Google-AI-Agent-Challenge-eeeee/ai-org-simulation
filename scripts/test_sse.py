"""SSE 엔드포인트 빠른 연결 테스트 — 처음 20개 이벤트만 출력."""
import http.client, json, sys

conn = http.client.HTTPConnection("localhost", 8000, timeout=30)
conn.request("GET", "/api/sessions/test-session/stream?mode=stub")
resp = conn.getresponse()
print(f"HTTP {resp.status}")

count = 0
buf = b""
while count < 60:
    chunk = resp.read(512)
    if not chunk:
        break
    buf += chunk
    while b"\n\n" in buf:
        part, buf = buf.split(b"\n\n", 1)
        lines = part.decode("utf-8").strip().splitlines()
        ev_type, data = "message", ""
        for line in lines:
            if line.startswith("event:"):
                ev_type = line[6:].strip()
            elif line.startswith("data:"):
                data = line[5:].strip()
        if data:
            try:
                obj = json.loads(data)
            except Exception:
                obj = data
            print(f"[{ev_type:12s}] {str(obj)[:100]}")
            count += 1
        if count >= 60:
            break
conn.close()
print("DONE")

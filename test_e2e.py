"""sendit end-to-end test with predictable token."""
import os, sys, threading, time, urllib.request, urllib.error, json, secrets

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Patch secrets.token_urlsafe so the server uses a known token
secrets.token_urlsafe = lambda n=None: "testtoken12345"

# Create test file
test_content = "Hello from sendit! This verifies the transfer works end-to-end."
with open('/tmp/test_sendit.txt', 'w') as f:
    f.write(test_content)

file_size = os.path.getsize('/tmp/test_sendit.txt')
print(f"Test file: /tmp/test_sendit.txt ({file_size} bytes)")

import sendit.server as srv

TESTS_PASSED = 0
TESTS_FAILED = 0
PORT = 9998
TOKEN = "testtoken12345"

def test(name, ok, detail=""):
    global TESTS_PASSED, TESTS_FAILED
    if ok:
        TESTS_PASSED += 1
        print(f"  \u2705 PASS: {name}")
    else:
        TESTS_FAILED += 1
        print(f"  \u274c FAIL: {name}  {detail}")

def start_server():
    t = threading.Thread(target=lambda: srv.run_server('/tmp/test_sendit.txt', port=PORT, timeout=15), daemon=True)
    t.start()
    time.sleep(2)
    return t

def stop_server():
    """Force-stop any server on the test port by making a connection."""
    try:
        urllib.request.urlopen(f'http://127.0.0.1:{PORT}/testtoken12345/download', timeout=2)
    except Exception:
        pass

print(f"\n{'='*50}")
print("TEST 1: Status endpoint")
print(f"{'='*50}")
start_server()
try:
    r = urllib.request.urlopen(f'http://127.0.0.1:{PORT}/status', timeout=5)
    data = json.loads(r.read())
    test("Status endpoint", data.get('status') == 'active', f"got {data}")
except Exception as e:
    test("Status endpoint", False, str(e))

print(f"\n{'='*50}")
print("TEST 2: Wrong path returns 404")
print(f"{'='*50}")
try:
    r = urllib.request.urlopen(f'http://127.0.0.1:{PORT}/wrongpath', timeout=5)
    test("Wrong path returns 404", False, f"Expected 404 but got {r.status}")
except urllib.error.HTTPError as e:
    test("Wrong path returns 404", e.code == 404, f"got {e.code}")
except Exception as e:
    test("Wrong path returns 404", False, str(e))

print(f"\n{'='*50}")
print("TEST 3: Download file via browser UI page")
print(f"{'='*50}")
try:
    r = urllib.request.urlopen(f'http://127.0.0.1:{PORT}/{TOKEN}', timeout=5)
    html = r.read().decode()
    has_ui = 'Incoming File' in html
    has_name = 'test_sendit.txt' in html
    test("UI page renders correctly", has_ui and has_name,
         f"has_ui={has_ui} has_name={has_name}")
except Exception as e:
    test("UI page renders correctly", False, str(e))

print(f"\n{'='*50}")
print("TEST 4: Download the actual file (server auto-shuts down after)")
print(f"{'='*50}")
try:
    r = urllib.request.urlopen(f'http://127.0.0.1:{PORT}/{TOKEN}/download', timeout=10)
    data = r.read()
    content_match = data.decode() == test_content
    cd = r.headers.get('Content-Disposition', '')
    safe_header = '&quot;' not in cd
    test("File content matches", content_match, f"size={len(data)}")
    test("Content-Disposition header is safe (no HTML entities)", safe_header, cd)
except Exception as e:
    test("File content matches and header safe", False, str(e))

time.sleep(2)  # Wait for server to fully shut down

print(f"\n{'='*50}")
print("TEST 5: Client (sendit get) with output path")
print(f"{'='*50}")
start_server()  # Start a new server for this test
try:
    from sendit.client import run_client
    orig_exit = sys.exit
    sys.exit = lambda code=0: None

    import io
    from contextlib import redirect_stdout
    buf = io.StringIO()
    with redirect_stdout(buf):
        run_client(f'http://127.0.0.1:{PORT}/{TOKEN}', output='/tmp/sendit_downloaded.txt')
    output = buf.getvalue()

    with open('/tmp/sendit_downloaded.txt') as f:
        content = f.read()
    test("CLI client downloads file correctly", content == test_content, output.strip())
    sys.exit = orig_exit
except Exception as e:
    test("CLI client downloads file correctly", False, str(e))
    sys.exit = orig_exit

print(f"\n{'='*50}")
print("TEST 6: Web server (sendit web) upload + download flow")
print(f"{'='*50}")
from sendit.serve import run_web_server

# Test web server's upload page renders
web_port = 9997
t_web = threading.Thread(target=lambda: run_web_server(port=web_port), daemon=True)
t_web.start()
time.sleep(2)
try:
    r = urllib.request.urlopen(f'http://127.0.0.1:{web_port}/', timeout=5)
    html = r.read().decode()
    test("Web UI page renders", 'sendit' in html and 'Drop file' in html, "UI loaded")
except Exception as e:
    test("Web UI page renders", False, str(e))

print(f"\n{'='*50}")
print(f"RESULTS: {TESTS_PASSED} passed, {TESTS_FAILED} failed")
print(f"{'='*50}")
sys.exit(0 if TESTS_FAILED == 0 else 1)

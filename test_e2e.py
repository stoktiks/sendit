"""sendit end-to-end test with predictable token."""
import os, sys, threading, time, urllib.request, urllib.error, json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Monkey-patch to use a fixed token for testing
import sendit.server as srv
original_handler = srv._make_handler

def fixed_handler(*args, **kwargs):
    # Force token
    kwargs = dict(kwargs)
    kwargs['token'] = 'testtoken12345'
    return original_handler(*args, **kwargs)

srv._make_handler = fixed_handler

# Create test file
test_content = "Hello from sendit! This verifies the transfer works end-to-end."
with open('/tmp/test_sendit.txt', 'w') as f:
    f.write(test_content)

file_size = os.path.getsize('/tmp/test_sendit.txt')
print(f"Test file: /tmp/test_sendit.txt ({file_size} bytes)")

# Start server in thread
def run_srv():
    srv.run_server('/tmp/test_sendit.txt', port=9998, timeout=15)

t = threading.Thread(target=run_srv, daemon=True)
t.start()
time.sleep(2)

print(f"\n{'='*50}")
print("TEST 1: Status endpoint")
print(f"{'='*50}")
try:
    r = urllib.request.urlopen('http://127.0.0.1:9998/status', timeout=5)
    data = json.loads(r.read())
    print(f"  Status: {data}")
    assert data['status'] == 'active'
    print("  ✅ PASS")
except Exception as e:
    print(f"  ❌ FAIL: {e}")

print(f"\n{'='*50}")
print("TEST 2: Wrong path returns 404")
print(f"{'='*50}")
try:
    r = urllib.request.urlopen('http://127.0.0.1:9998/wrongpath', timeout=5)
    print(f"  ❌ FAIL: Should have 404'd but got {r.status}")
except urllib.error.HTTPError as e:
    if e.code == 404:
        print(f"  ✅ PASS (got 404)")
    else:
        print(f"  ❌ FAIL: {e.code}")

print(f"\n{'='*50}")
print("TEST 3: Download file via browser UI page")
print(f"{'='*50}")
try:
    r = urllib.request.urlopen('http://127.0.0.1:9998/testtoken12345', timeout=5)
    html = r.read().decode()
    if 'Incoming File' in html and 'test_sendit.txt' in html:
        print(f"  ✅ PASS (UI page renders)")
    else:
        print(f"  ❌ FAIL: UI missing expected text")
        print(f"  Got: {html[:200]}")
except Exception as e:
    print(f"  ❌ FAIL: {e}")

print(f"\n{'='*50}")
print("TEST 4: Download the actual file")
print(f"{'='*50}")
try:
    r = urllib.request.urlopen('http://127.0.0.1:9998/testtoken12345/download', timeout=10)
    data = r.read()
    if data.decode() == test_content:
        print(f"  ✅ PASS (content matches)")
    else:
        print(f"  ❌ FAIL: content mismatch")
    print(f"  Size: {len(data)} bytes")
except Exception as e:
    print(f"  ❌ FAIL: {e}")

print(f"\n{'='*50}")
print("TEST 5: Client (sendit get)")
print(f"{'='*50}")
try:
    from sendit.client import run_client
    # Override to not sys.exit
    orig_exit = sys.exit
    sys.exit = lambda code: print(f"  (exit would be {code})")
    
    import io
    from contextlib import redirect_stdout
    buf = io.StringIO()
    with redirect_stdout(buf):
        run_client('http://127.0.0.1:9998/testtoken12345', output='/tmp/sendit_downloaded.txt')
    output = buf.getvalue()
    print(f"  {output.strip()}")
    
    with open('/tmp/sendit_downloaded.txt') as f:
        content = f.read()
    if content == test_content:
        print(f"  ✅ PASS (downloaded via client)")
    else:
        print(f"  ❌ FAIL: content mismatch")
    
    sys.exit = orig_exit
except Exception as e:
    print(f"  ❌ FAIL: {e}")

print(f"\n{'='*50}")
print("SUMMARY")
print(f"{'='*50}")
print("All tests completed.")

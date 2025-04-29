import threading, socket, ssl, time
from flask import Flask, jsonify, request, render_template_string

# — Configuration —
HOST = '0.0.0.0'
TLS_PORT = 12345
WEB_PORT = 5000

# Globals shared between threads
latest_moisture = 100
tls_conn = None
tls_lock = threading.Lock()

# 1) TLS server thread
def tls_server():
    global latest_moisture, tls_conn

    # prepare mbedTLS-style context
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile="server.crt", keyfile="server.key")
    context.load_verify_locations(cafile="ca.cert.pem")
    context.verify_mode = ssl.CERT_REQUIRED

    bindsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    bindsock.bind((HOST, TLS_PORT))
    bindsock.listen(1)
    print(f"[TLS] Listening on {HOST}:{TLS_PORT}")

    while True:
        newsock, addr = bindsock.accept()
        print(f"[TLS] Connection from {addr}")
        try:
            conn = context.wrap_socket(newsock, server_side=True)
            with tls_lock:
                tls_conn = conn
            print("[TLS] Handshake OK")

            while True:
                data = conn.recv(1024)
                if not data:
                    break

                text = data.decode().strip()
                print(f"[TLS] ← {text}")
                # parse integer after colon
                try:
                    val = int(text.split(":",1)[1])
                except:
                    continue

                latest_moisture = val

        except ssl.SSLError as e:
            print("[TLS] Error:", e)
        finally:
            with tls_lock:
                tls_conn = None
            try:
                conn.shutdown(socket.SHUT_RDWR)
                conn.close()
            except:
                pass
            print("[TLS] Connection closed, waiting for next client")

# 2) Flask app for web UI
app = Flask(__name__)

HTML_PAGE = """
<!doctype html>
<title>Plant Monitor</title>
<h1>Soil Moisture: <span id="moist">--</span></h1>
<button id="btn">Water On</button>

<script>
async function fetchMoist() {
  let res = await fetch('/api/moisture');
  let j = await res.json();
  document.getElementById('moist').innerText = j.moisture ?? '--';
}

document.getElementById('btn').addEventListener('click', async ()=>{
  await fetch('/api/command', {
    method: 'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({cmd:'WATER_ON'})
  });
});

setInterval(fetchMoist, 10000);
fetchMoist();
</script>
"""

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/api/moisture')
def api_moisture():
    return jsonify(moisture=latest_moisture)

@app.route('/api/command', methods=['POST'])
def api_command():
    data = request.get_json() or {}
    cmd = data.get('cmd','').upper()
    if cmd not in ('WATER_ON','WATER_OFF'):
        return jsonify(error="invalid cmd"), 400

    with tls_lock:
        if tls_conn:
            try:
                tls_conn.send(cmd.encode())
                print(f"[WEB] → {cmd}")
            except Exception as e:
                return jsonify(error=str(e)), 500
        else:
            return jsonify(error="no ESP32 connected"), 503

    return jsonify(status="sent")

if __name__ == '__main__':
    # 1) Start TLS listener
    t = threading.Thread(target=tls_server, daemon=True)
    t.start()

    # 2) Start Flask web server
    print(f"[WEB] Serving on http://0.0.0.0:{WEB_PORT}")
    app.run(host='0.0.0.0', port=WEB_PORT)

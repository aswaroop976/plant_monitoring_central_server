import threading, socket, ssl
from flask import Flask, jsonify, request, render_template_string

# Configuration
HOST = '0.0.0.0'
TLS_PORT = 12345
WEB_PORT = 5000

# Globals shared between threads
latest_moisture = {}
tls_conns = {}
tls_lock = threading.Lock()

def handle_client(conn, addr):
    client_name = None
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            text = data.decode().strip()
            print(f'[TLS][{addr}] ← {text}')
            parts = text.split(':', 1)
            if len(parts) != 2:
                continue
            name, raw = parts
            name = name.strip()
            try:
                val = int(raw.strip())
            except ValueError:
                continue
            with tls_lock:
                tls_conns[name] = conn
                latest_moisture[name] = val
            if client_name is None:
                client_name = name
    except Exception as e:
        print(f'[TLS][{addr}] Error: {e}')
    finally:
        with tls_lock:
            if client_name:
                tls_conns.pop(client_name, None)
                latest_moisture.pop(client_name, None)
        try:
            conn.shutdown(socket.SHUT_RDWR)
            conn.close()
        except:
            pass
        print(f'[TLS] Connection to {addr} closed')

def tls_server():
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile='server.crt', keyfile='server.key')
    context.load_verify_locations(cafile='ca.cert.pem')
    context.verify_mode = ssl.CERT_REQUIRED

    bindsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    bindsock.bind((HOST, TLS_PORT))
    bindsock.listen(5)
    print(f'[TLS] Listening on {HOST}:{TLS_PORT}')

    while True:
        newsock, addr = bindsock.accept()
        print(f'[TLS] Connection from {addr}')
        try:
            conn = context.wrap_socket(newsock, server_side=True)
            print('[TLS] Handshake OK')
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
        except ssl.SSLError as e:
            print(f'[TLS] SSL error: {e}')

app = Flask(__name__)

HTML_PAGE = '''<!doctype html>
<title>Plant Monitor</title>
<h1>Soil Moisture - Device1: <span id='moist1'>--</span></h1>
<h1>Soil Moisture - Device2: <span id='moist2'>--</span></h1>
<button id='btn1'>Water On Device1</button>
<button id='btn2'>Water On Device2</button>

<script>
async function fetchMoist() {
  let res = await fetch('/api/moisture');
  let j = await res.json();
  document.getElementById('moist1').innerText = j.device1 ?? '--';
  document.getElementById('moist2').innerText = j.device2 ?? '--';
}

document.getElementById('btn1').addEventListener('click', async ()=>{
  await fetch('/api/command', {
    method: 'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({device:'device1', cmd:'WATER_ON'})
  });
});
document.getElementById('btn2').addEventListener('click', async ()=>{
  await fetch('/api/command', {
    method: 'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({device:'device2', cmd:'WATER_ON'})
  });
});

setInterval(fetchMoist, 10000);
fetchMoist();
</script>''' 

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/api/moisture')
def api_moisture():
    with tls_lock:
        return jsonify(device1=latest_moisture.get('device1'),
                       device2=latest_moisture.get('device2'))

@app.route('/api/command', methods=['POST'])
def api_command():
    data = request.get_json() or {}
    cmd = data.get('cmd', '').upper()
    device = data.get('device', '').strip()
    if cmd not in ('WATER_ON', 'WATER_OFF') or device not in ('device1', 'device2'):
        return jsonify(error='invalid cmd or device'), 400

    with tls_lock:
        conn = tls_conns.get(device)
        if conn:
            try:
                conn.send(cmd.encode())
                print(f'[WEB] → {cmd} to {device}')
            except Exception as e:
                return jsonify(error=str(e)), 500
        else:
            return jsonify(error=f'no {device} connected'), 503

    return jsonify(status='sent')

if __name__ == '__main__':
    t = threading.Thread(target=tls_server, daemon=True)
    t.start()
    print(f'[WEB] Serving on http://{HOST}:{WEB_PORT}')
    app.run(host=HOST, port=WEB_PORT)

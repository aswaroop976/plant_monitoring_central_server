import socket, ssl, sys, select

HOST = '0.0.0.0'
PORT = 12345

def start_tls_server():
    # SSL setup (as before)
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile="server.crt", keyfile="server.key")
    context.load_verify_locations(cafile="ca.cert.pem")
    context.verify_mode = ssl.CERT_REQUIRED

    bindsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    bindsock.bind((HOST, PORT))
    bindsock.listen(1)
    print(f"TLS server listening on {HOST}:{PORT}…")

    newsock, addr = bindsock.accept()
    print(f"Connection from {addr}, handshake…")
    conn = context.wrap_socket(newsock, server_side=True)
    print("TLS OK; client cert:", conn.getpeercert())

    print("Type ‘w’ + Enter → WATER_ON; ‘o’ + Enter → WATER_OFF; Ctrl-C to quit.")
    try:
        while True:
            rlist, _, _ = select.select([conn, sys.stdin], [], [])
            for ready in rlist:
                if ready is conn:
                    data = conn.recv(1024)
                    if not data:
                        print("ESP32 disconnected.")
                        return
                    print("From ESP32:", data.decode().strip())

                elif ready is sys.stdin:
                    line = sys.stdin.readline().strip().lower()
                    if line == 'w':
                        conn.send(b"WATER_ON")
                        print("→ Sent WATER_ON")
                    elif line == 'o':
                        conn.send(b"WATER_OFF")
                        print("→ Sent WATER_OFF")
                    else:
                        print("Unknown command. ‘w’ or ‘o’ only.")
    finally:
        conn.shutdown(socket.SHUT_RDWR)
        conn.close()

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't actually send packets
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip
if __name__ == "__main__":

    print("Server IP is:", get_local_ip())
    start_tls_server()

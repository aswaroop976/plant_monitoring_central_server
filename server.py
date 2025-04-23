import socket, ssl

HOST = '0.0.0.0'
PORT = 12345

def start_tls_server():
    # 1) Create SSLContext and require client certs
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile="server.cert.pem", keyfile="server.key.pem")
    context.load_verify_locations(cafile="ca.cert.pem")
    context.verify_mode = ssl.CERT_REQUIRED

    # 2) Bind & listen
    bindsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    bindsock.bind((HOST, PORT))
    bindsock.listen(1)
    print(f"TLS server listening on {HOST}:{PORT}...")

    while True:
        newsock, addr = bindsock.accept()
        print(f"Connection from {addr}, performing TLS handshake...")
        try:
            conn = context.wrap_socket(newsock, server_side=True)
            print("TLS handshake complete; client cert:", conn.getpeercert())

            # 3) Read loop
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                print("Received (decrypted):", data.decode())
        except ssl.SSLError as e:
            print("TLS error:", e)
        finally:
            conn.shutdown(socket.SHUT_RDWR)
            conn.close()
            print("Connection closed.")
if __name__ == "__main__":
    def get_local_ip():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # doesn't actually send packets
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
        finally:
            s.close()
        return ip

    print("Server IP is:", get_local_ip())
    start_tls_server()

import socket

# Server configuration
HOST = '0.0.0.0'  # Listen on all available network interfaces
PORT = 12345      # Port to listen on

def start_server():
    # Create a socket object (IPv4, TCP)
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Bind the socket to the server address and port
    server_socket.bind((HOST, PORT))
    server_socket.listen(1)  # Allow only one connection at a time

    print(f"Server started, listening on {HOST}:{PORT}...")

    while True:
        # Accept a new connection from a client (ESP32)
        conn, addr = server_socket.accept()
        print(f"Connection from {addr} established!")

        try:
            while True:
                # Receive data from the client (ESP32)
                data = conn.recv(1024)  # Adjust buffer size as needed
                if not data:
                    break  # Connection closed by the client
                
                # Print the received data (moisture value)
                print(f"Received data: {data.decode('utf-8')}")

        except Exception as e:
            print(f"Error receiving data: {e}")
        
        finally:
            # Close the connection once data is received
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
    start_server()

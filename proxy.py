import socket as sc
import sys
import os
from urllib.parse import urlparse

process_limit = 99

def parse_url_lib(url):
    parsed = urlparse(url)
    host = parsed.hostname if parsed.hostname else parsed.scheme
    port = parsed.port if parsed.port else 80 
    path = parsed.path if parsed.path else "/"
    return host, port, path

def fetch_data_from_remote_server(action, host, port, path, body):
    remote_server_socket = sc.socket()
    remote_server_socket.setsockopt(sc.SOL_SOCKET, sc.SO_REUSEADDR, 1)

    # Connect to the host and the port
    remote_server_socket.connect((host, port))
    
    proxy_request = f"{action} {path} HTTP/1.1\r\nHost:{host}\r\nConnection: close\r\n\r\n{body}"

    # Send the request to the remote server
    remote_server_socket.sendall(proxy_request.encode())
    
    # Receive the response from the remote server
    response = remote_server_socket.recv(4096)
    
    remote_server_socket.close()
    return response


def worker_function(client_socket: sc.socket):
    try:
        data = client_socket.recv(8192).decode()
        if not data:
            raise Exception("HTTP/1.0 400 Bad Request\r\n\r\n")
        
        parsed_data = data.split("\r\n\r\n")
        headers = parsed_data[0]
        body = parsed_data[1] if len(parsed_data) >= 2 else None
        
        header_lines = headers.split("\r\n")
        if not header_lines:
            raise Exception("HTTP/1.0 400 Bad Request\r\n\r\n")
        
        action, url, _ = header_lines[0].split()
        print("Initial Line:", header_lines[0])
        print("Header Lines:")
        for i in header_lines[1:]:
            print(f"\t{i}")
        print("Body:", body)
        print()
        
        if action != "GET":
            print(f"Error: Currently, {action} is not implemented. Kindly use GET as your action.")
            raise Exception("HTTP/1.1 501 Not Implemented\r\n\r\n")

        print(f"Action: {action}")
        # Extract host, port and path from the URL
        host, port, req_path = parse_url_lib(url)

        print(f"Forwarding request to {host}:{port}{req_path}")

        # Now, forward the request to the remote server
        response = fetch_data_from_remote_server(action, host, port, req_path, body)

        client_socket.sendall(response)
        print("Response successfully sent to the client.\n")

    except Exception as e:
        print("Response failed:", str(e))
        client_socket.sendall(str(e).encode())
        

def bootup_server():
    # Extract Port Number from argv, else default to 9999
    if len(sys.argv) < 2:
        print("Port number not specified. The default port number is 9999.")
        port = 9999
    else:
        try:
            port = int(sys.argv[1])
        except:
            print("Port number specified is not an integer.")
            os._exit(1)

    # Create a socket for communication
    socket = sc.socket()

    # Specify socket level, and allow reuse of socket so the OS doesn't have to free it
    socket.setsockopt(sc.SOL_SOCKET, sc.SO_REUSEADDR, 1) 

    # Bind our socket to 127.0.0.1:{port} and allow upto {process_limit} of processes
    socket.bind(("localhost", port))
    socket.listen(process_limit)

    while True:
        # Except a new request from a client and represent it in socket form
        client_socket, client_addr = socket.accept()
        print("Successfully accepted client socket at:", client_addr)

        pid = os.fork()
        if pid == 0:
            socket.close()

            worker_function(client_socket)
            client_socket.close()

            os._exit(0)
            
        client_socket.close()

if __name__ == "__main__":
    bootup_server()
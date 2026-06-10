import http.server
import socketserver
import socket

def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

PORT = 8000
Handler = http.server.SimpleHTTPRequestHandler
IP_ADDRESS = get_ip_address()

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"\n-- Server started!")
    print(f"-- Local access:   http://localhost:{PORT}")
    print(f"-- Network access: http://{IP_ADDRESS}:{PORT}")
    print(f"\n-- Press Ctrl+C to stop the server.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n-- Server stopped.")
        httpd.server_close()

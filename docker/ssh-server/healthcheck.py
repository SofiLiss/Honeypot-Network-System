import socket
import sys

try:
    s = socket.create_connection(("localhost", 3232), timeout=2)
    s.settimeout(1)
    try:
        s.recv(1024)
    except socket.timeout:
        pass
    s.close()
except Exception:
    sys.exit(1)
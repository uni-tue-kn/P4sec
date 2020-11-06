import socket

def check_listening_on_port(port):
    # Create a TCP socket
    address = "localhost"
    s = socket.socket()
    try:
        s.connect((address, port))
        return True
    except socket.error, e:
        return False
    finally:
        s.close()

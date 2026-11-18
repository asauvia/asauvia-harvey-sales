import os
import re
import socket
import threading

PORT = int(os.environ.get("PORT", 10000))
TARGET = ("127.0.0.1", 5555)


def rewrite(data: bytes) -> bytes:
    data = re.sub(rb"(?im)^host:[^\r\n]+", b"Host: 127.0.0.1:5555", data)
    data = re.sub(rb"(?im)^origin:[^\r\n]+", b"Origin: http://127.0.0.1:5555", data)
    return data


def pipe(src, dst, is_request=False):
    try:
        while True:
            chunk = src.recv(16384)
            if not chunk:
                break
            if is_request:
                chunk = rewrite(chunk)
            dst.sendall(chunk)
    except Exception:
        pass
    finally:
        try:
            dst.close()
        except Exception:
            pass


def handle(client):
    try:
        upstream = socket.create_connection(TARGET, timeout=10)
        threading.Thread(target=pipe, args=(client, upstream, True), daemon=True).start()
        threading.Thread(target=pipe, args=(upstream, client, False), daemon=True).start()
    except Exception:
        client.close()


def main():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", PORT))
    srv.listen(128)
    while True:
        conn, _ = srv.accept()
        threading.Thread(target=handle, args=(conn,), daemon=True).start()


if __name__ == "__main__":
    main()
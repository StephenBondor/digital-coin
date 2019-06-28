# Exercise 1
import socket  # hint
import threading


def ping():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(("68.183.109.101", 10000))
        s.sendall(b"ping")
        data = s.recv(10)
        print(f"Received {str(data)}")


if __name__ == "__main__":
    ping()

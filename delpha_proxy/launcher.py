import sys

from client import ProxyClient
from server import ProxyServer


def setup_server_proxy():
    proxy_server = ProxyServer()
    proxy_server.start_server()


def setup_client_proxy():
    proxy = ProxyClient()
    proxy.start_client()


def main():
    choice = input(" ▶️  Do you want to setup a server proxy (S) or a client proxy (C)? [S/C]: ").strip().upper()
    if choice == "S":
        setup_server_proxy()
    elif choice == "C":
        setup_client_proxy()
    else:
        print(" ❌ Invalid choice. Exiting.")
        sys.exit(1)

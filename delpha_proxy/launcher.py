from delpha_proxy.client import ProxyClient
from delpha_proxy.server import ProxyServer


def setup_server_proxy():
    proxy_server = ProxyServer()
    proxy_server.start_server()


def setup_client_proxy():
    proxy = ProxyClient()
    proxy.start_client()

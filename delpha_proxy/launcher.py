from delpha_proxy.server import ProxyServer


def setup_server_proxy():
    proxy_server = ProxyServer()
    proxy_server.start_server()

from delpha_proxy.server import ProxyServer


def setup_server_proxy():
    """Launch the proxy server"""
    proxy_server = ProxyServer()
    proxy_server.start_server()

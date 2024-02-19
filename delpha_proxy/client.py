import sys

from clients.linux import LinuxProxyClient


class ProxyClient:
    """Global proxy class for automatically instantiating platform-specific proxy classes."""

    def __new__(cls, **kwargs):
        platform = sys.platform
        if platform == "linux":
            proxy = LinuxProxyClient()
            return proxy
        else:
            raise NotImplementedError(f"Platform '{platform}' is not supported for proxy configuration.")

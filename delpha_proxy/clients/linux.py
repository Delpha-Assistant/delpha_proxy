import os
import subprocess

from clients.abstract import AbstractProxy


class LinuxProxyClient(AbstractProxy):
    """Setup a client proxy specifically for Linux"""

    def __init__(self) -> None:
        super().__init__()
        self.status = "off"

    def setup_proxy(self, host, port, username, password) -> None:
        """Set up the proxy on the client system for Linux."""
        try:
            self.host = host
            self.port = port
            self.username = username
            self.password = password
            # Write proxy configuration to environment variables
            os.environ["HTTP_PROXY"] = f"http://{self.username}:{self.password}@{self.host}:{self.port}"
            os.environ["HTTPS_PROXY"] = f"http://{self.username}:{self.password}@{self.host}:{self.port}"
            self.log(" ✅ Proxy configured successfully.")
        except Exception as e:
            self.log(f"Error setting up proxy: {e}", "error")

    def turn_on_proxy(self) -> None:
        """Turn on the proxy for Linux."""
        try:
            subprocess.run(["gsettings", "set", "org.gnome.system.proxy", "mode", "manual"])
            subprocess.run(["gsettings", "set", "org.gnome.system.proxy.http", "host", self.host])
            subprocess.run(["gsettings", "set", "org.gnome.system.proxy.http", "port", str(self.port)])
            subprocess.run(["gsettings", "set", "org.gnome.system.proxy.http", "authentication-user", self.username])
            subprocess.run(
                ["gsettings", "set", "org.gnome.system.proxy.http", "authentication-password", self.password]
            )
            subprocess.run(["gsettings", "set", "org.gnome.system.proxy.https", "host", self.host])
            subprocess.run(["gsettings", "set", "org.gnome.system.proxy.https", "port", str(self.port)])
            subprocess.run(["gsettings", "set", "org.gnome.system.proxy.https", "authentication-user", self.username])
            subprocess.run(
                ["gsettings", "set", "org.gnome.system.proxy.https", "authentication-password", self.password]
            )
            self.log(" ✅ Proxy turned on successfully.")
        except Exception as e:
            self.log(f"Error turning on proxy: {e}", "error")

    def turn_off_proxy(self) -> None:
        """Turn off the proxy for Linux."""
        try:
            subprocess.run(["gsettings", "set", "org.gnome.system.proxy", "mode", "none"])
            self.log(" ✅ Proxy turned off successfully.")
        except Exception as e:
            self.log(f"Error turning off proxy: {e}", "error")

    def test_proxy(self) -> None:
        """Test if the proxy is working properly on Linux."""
        try:
            result = subprocess.run(["curl", "ifconfig.me"], capture_output=True, text=True)
            self.log(f" 💡 Current public IP: {result.stdout.strip()}")
        except Exception as e:
            self.log(f"Error testing proxy: {e}", "error")

    def get_status(self) -> str:
        """Check if the proxy is running."""
        try:
            result = subprocess.run(
                ["gsettings", "get", "org.gnome.system.proxy", "mode"], capture_output=True, text=True
            )
            mode = result.stdout.strip()
            mode = "on" if mode == "manual" else "off"
            self.log(f" 💡 Proxy status: {mode}")
            return
        except Exception as e:
            self.log(f"Error checking proxy status: {e}", "error")

import subprocess

from delpha_proxy.clients.abstract import AbstractProxy


class LinuxProxyClient(AbstractProxy):
    """Setup a client proxy specifically for Linux"""

    def __init__(self):
        super().__init__()
        self.proxy_auth = None
        self.environment_file_path = "/etc/environment"

    def _setup_proxy(self, host: str, port: int, username: str = None, password: str = None) -> None:
        """Set up the proxy on the client system for Linux."""
        if username and password:
            self.proxy_auth = f"http://{username}:{password}@{host}:{port}"
        else:
            self.proxy_auth = f"http://{host}:{port}"

    def turn_on_proxy(self) -> None:
        """Turn on the proxy."""
        if not self.proxy_auth:
            self.log(" 💡 Proxy setup has not been done. Initiating setup...", "info")
            auth_info = self._get_authentication_info()
            self._setup_proxy(**auth_info)

        lines_to_add = [
            f'HTTP_PROXY="{self.proxy_auth}"',
            f'HTTPS_PROXY="{self.proxy_auth}"',
            'NO_PROXY="localhost,127.0.0.1,::1"',
        ]
        try:
            with open(self.environment_file_path, "r") as file:
                existing_lines = file.readlines()

            with open(self.environment_file_path, "a") as file:
                for line in lines_to_add:
                    if line.strip() not in existing_lines:
                        file.write(line + "\n")
            self.log(
                " ✅ Proxy settings have been written to /etc/environment. Please log out and log back in for changes to take effect."
            )
        except Exception as e:
            self.log(f"Failed to write proxy settings: {e}", "error")

    def turn_off_proxy(self) -> None:
        """Turn off the proxy."""
        try:
            with open(self.environment_file_path, "r") as file:
                lines = file.readlines()

            with open(self.environment_file_path, "w") as file:
                for line in lines:
                    if (
                        line.startswith("HTTP_PROXY=")
                        or line.startswith("NO_PROXY=")
                        or line.startswith("HTTPS_PROXY=")
                    ):
                        # Skip writing this line, effectively deleting it
                        continue
                    file.write(line)
            self.log(
                " ✅ Proxy settings have been disabled. Please log out and log back in for changes to take effect."
            )
        except Exception as e:
            self.log(f"Failed to disable proxy settings: {e}", "error")

    def test_proxy(self) -> None:
        """Test if the proxy is working properly."""
        try:
            result = subprocess.run(["curl", "ifconfig.me"], capture_output=True, text=True)
            self.log(f" 💡 Current public IP: {result.stdout.strip()}", "info")
        except Exception as e:
            self.log(f"Error testing proxy: {e}", "error")

    def get_status(self) -> None:
        """Check if the proxy is running."""
        # Directly checking the /etc/environment file for proxy settings
        try:
            with open(self.environment_file_path, "r") as file:
                if any(line.startswith("HTTP_PROXY") for line in file):
                    self.log(" 💡 Proxy is currently ON.", "info")
                else:
                    self.log(" 💡 Proxy is currently OFF.", "info")
        except Exception as e:
            self.log(f"Error checking proxy status: {e}", "error")

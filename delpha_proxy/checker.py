import typing
from typing import Optional

import requests


class ProxyChecker:
    """A class to test proxy configuration."""

    def test_proxy(self) -> None:
        """Test the proxy configuration."""
        print(" 💡 Current public IP (before setting up proxy):", self._get_current_public_ip())
        config = self._get_proxy_config()
        print("Current public IP (after setting up proxy):", self._get_current_public_ip(config))

    def _get_current_public_ip(self, proxy: typing.Optional[dict] = None) -> Optional[str]:
        """Fetch the current public IP address."""
        try:
            params = {"url": "https://ifconfig.me"}
            if proxy:
                params["proxies"] = proxy
            response = requests.get(**params)
            return response.text.strip()
        except requests.RequestException as e:
            print(f" ❌ Error fetching public IP: {e}")
            return None

    def _get_proxy_config(self) -> dict:
        """Set up proxy configuration for requests."""

        proxy_host = input(" ▶️ Enter proxy host: ")
        proxy_port = int(input(" ▶️ Enter proxy port: "))
        username = input(" ▶️ Enter username (leave blank if none): ")
        password = input(" ▶️ Enter password (leave blank if none): ")
        proxies = {
            "http": (
                f"http://{username}:{password}@{proxy_host}:{proxy_port}"
                if username != "" and password != ""
                else f"http://{proxy_host}:{proxy_port}"
            ),
            "https": (
                f"http://{username}:{password}@{proxy_host}:{proxy_port}"
                if username != "" and password != ""
                else f"http://{proxy_host}:{proxy_port}"
            ),
        }
        return proxies


def check():
    proxy_tester = ProxyChecker()
    proxy_tester.test_proxy()

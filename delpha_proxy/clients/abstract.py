from abc import ABC, abstractmethod


class AbstractProxy(ABC):
    """Abstract class for platform-specific proxy classes."""

    def log(self, msg: str, level: str = "info") -> None:
        """Log a message with a given level."""
        if level == "info":
            print(msg)
        elif level == "error":
            print(f" ❌ {msg}")
        else:
            print(f" ⚠️ {msg}")

    def start_client(self):
        """Start the client CLI."""
        self.log("\n 🖥️  Welcome to the ProxyClient CLI. Type 'help' to see the available commands.\n")
        help_message = "\n 💡 Available commands:\n  - on\n  - off\n  - test\n  - status\n  - exit"
        while True:
            command = input("> ").strip().lower()
            if command == "on":
                self.turn_on_proxy()
            elif command == "test":
                self.test_proxy()
            elif command == "off":
                self.turn_off_proxy()
            elif command == "status":
                self.get_status()
            elif command == "exit":
                self.log(" 🟥 Exiting ProxyClient CLI.")
                break
            elif command == "help":
                self.log(help_message)
            else:
                self.log("Invalid command. Please try again.\n", "error")

    def _get_authentication_info(self) -> dict:
        """Get the authentication info to set up the proxy client."""
        while True:
            host = input(" ▶️ Enter proxy host: ").strip()
            if not host:
                self.log("Host cannot be empty. Please try again.", "error")
                continue

            port_input = input(" ▶️ Enter proxy port, press Enter for default (8080): ").strip()
            if port_input == "":
                port_input = "8080"
            if not port_input.isdigit():
                self.log("Port must be a positive integer. Please try again.", "error")
                continue
            port = int(port_input)

            username, password = None, None
            auth = input(" ▶️ Is authentication required? (yes/no): ").strip().lower()
            if auth in ["y", "yes"]:
                username = input(" ▶️ Enter username: ").strip()
                if not username:
                    self.log("Username cannot be empty. Please try again.", "error")
                    continue

                password = input(" ▶️ Enter password: ").strip()
                if not password:
                    self.log("Password cannot be empty. Please try again.", "error")
                    continue
            return {"host": host, "port": port, "username": username, "password": password}

    @abstractmethod
    def _setup_proxy(self, host: str, port: int, username: str, password: str) -> None:
        """Set up the proxy on the client system."""
        pass

    @abstractmethod
    def get_status(self) -> None:
        """Check if the proxy is running."""
        pass

    @abstractmethod
    def turn_on_proxy(self) -> None:
        """Turn on the proxy."""
        pass

    @abstractmethod
    def turn_off_proxy(self) -> None:
        """Turn off the proxy."""
        pass

    @abstractmethod
    def test_proxy(self) -> None:
        """Test if the proxy is working properly."""
        pass

import base64
import hashlib
import os
import socket
import sqlite3
import sys
import threading
import time
from typing import Optional, Tuple

import requests


class ProxyServer:
    """Allows to create a proxy server"""

    def __init__(self) -> None:
        """Initialize the proxy server with a public IP and a database for users."""
        self.public_host: str = self._get_public_ip()
        self.local_host: str = self._get_local_ip()
        self.port: Optional[int] = None
        self.db_path: str = "users.db"

    def start_server(self) -> None:
        """Start the server and manage its lifecycle, including port forwarding setup confirmation."""
        self._configure()
        server_socket = self._start_socket()
        if server_socket:
            handle_connections_thread = threading.Thread(target=self._handle_connections, args=(server_socket,))
            handle_connections_thread.daemon = True
            handle_connections_thread.start()
            time.sleep(2)
        self._run_command_interface()

    def _configure(self) -> None:
        """Ask for info and configure the server settings"""
        self._configure_auth()
        if self.authentication:
            self._setup_database()
        self._configure_port()
        if not self._confirm_port_forwarding_setup():
            self.log(" 📕 Server startup aborted by the user.")
            return

    def _configure_auth(self) -> None:
        """Setup the proxy server"""
        auth = input(" ▶️  Do you want to activate authentication (yes/no): ")
        if auth in ["yes", "y"]:
            self.authentication = True
        else:
            self.authentication = False

    def _setup_database(self) -> None:
        """Set up the SQLite database for storing user credentials."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """CREATE TABLE IF NOT EXISTS users
                (username TEXT PRIMARY KEY, password TEXT NOT NULL)"""
            )
            conn.commit()

    def _configure_port(self) -> None:
        """Configure the server port."""
        while True:
            port_input = input(" ▶️  Enter the port number for the server to listen on or press Enter for default: ")
            if port_input.lower() == "":
                self.port = 8080
                break
            else:
                try:
                    self.port = int(port_input)
                    break
                except ValueError:
                    self.log(
                        "Invalid port number. Please enter a valid integer or 'auto' for automatic detection.", "error"
                    )

    def _confirm_port_forwarding_setup(self):
        """Prompt the user to set up port forwarding and confirm when ready."""
        message = (
            "\n\n🌐 To make your server accessible from the internet, please configure port forwarding on your router. 🌐\n\n"
            f"   - Forward port: {self.port}\n"
            f"   - Destination port: {self.port}\n"
            f"   - Destination ip: {self.public_host}\n\n"
            "🔧 Typically, you'll need to log into your router's web interface and navigate to the Port Forwarding section.\n"
            "   There, create a new port forwarding rule with the above details, directing traffic to the local IP of this machine. 🔧\n"
        )
        self.log(message)

        while True:
            confirmation = input(
                "\n ▶️  Have you finished setting up port forwarding and wish to start the server? (yes/no/cancel): "
            ).lower()
            if confirmation in ["yes", "y"]:
                return True
            elif confirmation in ["cancel", "c"]:
                self.log(" 🟥 Server startup cancelled.")
                sys.exit(0)
            else:
                self.log(
                    "Please set up port forwarding on your router and then type 'yes' to start the server, or 'cancel' to exit.",
                    "error",
                )

    def _start_socket(self) -> Optional[socket.socket]:
        """Start the server socket and listen for connections."""
        while True:
            try:
                server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server_socket.bind(("0.0.0.0", self.port))
                server_socket.listen(5)
                self.log(str(self))
                self.log(f"\n\n 🟩 Server started on port {self.port}. Waiting for connections...")
                return server_socket
            except socket.error as e:
                self.log(f"Error starting server on port {self.port}: {e}.", "error")
                self._configure_port()

    def _handle_connections(self, server_socket: socket.socket) -> None:
        """Handle incoming client connections."""
        while True:
            client_socket, client_address = server_socket.accept()
            self.log(f" 💻 Connection attempt from {client_address}.")
            self._process_client_request(client_socket, client_address)

    def _process_client_request(self, client_socket: socket.socket, client_address: Tuple[str, int]) -> None:
        """Process an individual client request with HTTP proxy authentication."""
        try:
            request = client_socket.recv(1024).decode().strip()
            if self.authentication == False or self._verify_auth_header(request):
                client_socket.send(b"HTTP/1.1 200 Connection established\r\n\r\n")
                self._forward_request(request, client_socket)
            else:
                client_socket.send(
                    b'HTTP/1.1 407 Proxy Authentication Required\r\nProxy-Authenticate: Basic realm="Proxy"\r\n\r\n'
                )
        except Exception as e:
            self.log(f"Error processing request from {client_address}: {e}", "error")
        finally:
            client_socket.close()

    def _verify_auth_header(self, request: str) -> bool:
        """Verify the presence of the Proxy-Authorization header in the request."""
        if "Proxy-Authorization" in request:
            auth_header = [line for line in request.split("\r\n") if "Proxy-Authorization" in line][0]
            auth_type, auth_credentials = auth_header.split(" ")[1:]
            if auth_type.lower() == "basic":
                username, password = base64.b64decode(auth_credentials).decode().split(":")
                return self._authenticate_user(username, password)
        else:
            return False

    def _forward_request(self, request: str, client_socket: socket.socket) -> None:
        """Forward the request to the target server and send back the response to the client."""
        try:
            # Extract the target host and port from the request
            host = request.split("\r\n")[1].split(" ")[1].split(":")[0]
            port = int(request.split("\r\n")[1].split(" ")[1].split(":")[1])
            # Create a new socket to connect to the target server
            target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            target_socket.connect((host, port))
            # Forward the request to the target server
            target_socket.send(request.encode())
            # Receive the response from the target server
            response = target_socket.recv(4096)
            # Send back the response to the client
            client_socket.send(response)
        except Exception as e:
            self.log(f"Error forwarding request to target server: {e}", "error")
        finally:
            target_socket.close()

    def _authenticate_user(self, username: str, password: str) -> bool:
        """Authenticate a user by username and hashed password."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
            result = cursor.fetchone()
            if result:
                stored_password = result[0]
                salt = bytes.fromhex(stored_password[-32:])  # Extract the salt from the stored password
                password_hash, _ = self._hash_password(password, salt)
                return stored_password[:-32] == password_hash
            return False

    def _run_command_interface(self) -> None:
        """Run the command-line interface for interacting with the server."""
        self.log(f"\n 🖥️  Welcome on the CLI, enter help to see the commands\n")
        help = "\n 💡 Available commands:\n  - add_user\n  - exit\n"
        while True:
            command = input("> ").strip().lower()
            if command == "add_user":
                self._execute_add_user_command()
            elif command == "exit":
                self.log(" 🟥 Exiting command interface.")
                break
            elif command == "help":
                self.log(help)
            else:
                self.log("Invalid command. Please try again.", "error")

    def _execute_add_user_command(self) -> None:
        """Execute the add_user command."""
        if self.authentication:
            username = input("\n ▶️ Enter username: ").strip()
            password = input(" ▶️ Enter password: ").strip()
            self.add_user(username, password)
        else:
            self.log(" 💡 User authentication is deactivated. No need to create any users.")

    def _get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except socket.error as e:
            self.log(f"Error: {e}")

    def _get_public_ip(self) -> str:
        """Fetch the current public IP address using an external service."""
        try:
            response = requests.get("https://ifconfig.me")
            return response.text
        except requests.RequestException as e:
            self.log(f"Error fetching public IP: {e}", "error")
            sys.exit(1)

    def log(self, msg: str, level: str = "info") -> None:
        """Log a message with a given level."""
        if level == "info":
            print(msg)
        elif level == "error":
            print(f" ❌ {msg}")
        else:
            print(f" ⚠️  {msg}")

    def add_user(self, username: str, password: str) -> None:
        """Add a new user with a username and hashed password to the database."""
        try:
            salt = os.urandom(16)  # Generate a unique salt for this user
            password_hash, _ = self._hash_password(password, salt)
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Store the salt and the hash together
                cursor.execute(
                    "INSERT INTO users (username, password) VALUES (?, ?)", (username, password_hash + salt.hex())
                )
                conn.commit()
                self.log(f"\n ✅ User created: Username: {username}")
        except sqlite3.IntegrityError:
            self.log(" 💡 User already exists.\n", "warning")

    def _hash_password(self, password: str, salt: Optional[bytes] = None) -> Tuple[str, bytes]:
        """Hash a password with a given salt, or generate one if not provided."""
        if salt is None:
            salt = os.urandom(16)  # Generate a new salt
        pwdhash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)
        return pwdhash.hex(), salt

    def __str__(self) -> str:
        """Return a summary of the configured settings of the proxy server."""
        auth_status = "Activated" if self.authentication else "Deactivated"
        port = self.port if self.port else "Default (8080)"
        summary = (
            f"\n\n⚙️   Proxy Server Configuration  ⚙️\n"
            "-----------------------------------\n"
            f"|  Public Host: {self.public_host}\n"
            f"|  Local Host: {self.local_host}\n"
            f"|  Port: {port}\n"
            f"|  Authentication: {auth_status}\n"
            f"|  Database Path: {self.db_path}\n\n"
        )
        return summary

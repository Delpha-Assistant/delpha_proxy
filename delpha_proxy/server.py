import base64
import hashlib
import logging
import os
import platform
import select
import socket
import sqlite3
import subprocess
import sys
import threading
import time
import traceback
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
        logging.basicConfig(
            filename="server.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
        )

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
            self.log(" 📕 Server startup aborted by the user.", "cli")
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
                        "Invalid port number. Please enter a valid integer or 'auto' for automatic detection.",
                        "cli",
                        "error",
                    )

    def _confirm_port_forwarding_setup(self):
        """Prompt the user to set up port forwarding and confirm when ready."""
        message = (
            "\n\n🌐 To make your server accessible from the internet, please configure port forwarding on your router. 🌐\n\n"
            f"   - Forward/extern port (end & begin): {self.port}\n"
            f"   - Destination/intern port  (end & begin): {self.port}\n"
            f"   - Destination/server ip: {self.local_host}\n\n"
            "🔧 Typically, you'll need to log into your router's web interface and navigate to the Port Forwarding section.\n"
            "   There, create a new port forwarding rule with the above details, directing traffic to the local IP of this machine. 🔧\n"
        )
        self.log(message, "cli")

        while True:
            confirmation = input(
                "\n ▶️  Have you finished setting up port forwarding and wish to start the server? (yes/no/cancel): "
            ).lower()
            if confirmation in ["yes", "y"]:
                return True
            elif confirmation in ["cancel", "c"]:
                self.log(" 🟥 Server startup cancelled.", "cli")
                sys.exit(0)
            else:
                self.log(
                    "Please set up port forwarding on your router and then type 'yes' to start the server, or 'cancel' to exit.",
                    "cli",
                    "error",
                )

    def _start_socket(self) -> Optional[socket.socket]:
        """Start the server socket and listen for connections."""
        while True:
            try:
                server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server_socket.bind(("0.0.0.0", self.port))
                server_socket.listen(5)
                self.log(str(self), "cli")
                self.log(f"\n\n 🟩 Server started on port {self.port}. Waiting for connections..", "server")
                self.log(f"\n\n 🟩 Server started on port {self.port}. Enter show-logs to see details", "cli")
                return server_socket
            except socket.error as e:
                self.log(f"Error starting server on port {self.port}: {e}.", "cli", "error")
                self._configure_port()

    def _handle_connections(self, server_socket: socket.socket) -> None:
        """Handle incoming client connections."""
        while True:
            client_socket, client_address = server_socket.accept()
            self.log(f" 💻 Connection attempt from {client_address}.", "server")
            threading.Thread(target=self._process_client_request, args=(client_socket, client_address)).start()

    def _process_client_request(self, client_socket: socket.socket, client_address: Tuple[str, int]) -> None:
        """Process an individual client request."""
        try:
            request_header = client_socket.recv(1024).decode(errors="ignore")
            # Determine if this is an HTTPS CONNECT request
            if self._is_authenticated(request_header):
                if request_header.startswith("CONNECT"):
                    self._handle_https(request_header, client_socket, client_address)
                else:
                    self._handle_http(request_header, client_socket, client_address)
            else:
                self._request_authentication(client_socket)
        except Exception as e:
            self.log(
                f"Error processing request from {client_address}: {e}\n{traceback.format_exc()}", "server", "error"
            )
        finally:
            client_socket.close()

    def _is_authenticated(self, request_header: str) -> bool:
        """Check if the request contains valid authentication."""
        if not self.authentication:
            return True
        if "Proxy-Authorization" in request_header:
            auth_header = next((line for line in request_header.split("\r\n") if "Proxy-Authorization" in line), None)
            if auth_header:
                auth_type, auth_credentials = auth_header.split(" ")[1:]
                if auth_type.lower() == "basic":
                    username, password = base64.b64decode(auth_credentials).decode().split(":")
                    return self._authenticate_user(username, password)
        return False

    def _request_authentication(self, client_socket: socket.socket):
        """Request client for authentication."""
        self.log(f" 🚩 Request not authenticated, rejected", "server")
        client_socket.sendall(
            b"HTTP/1.1 407 Proxy Authentication Required\r\n" b'Proxy-Authenticate: Basic realm="Proxy"\r\n\r\n'
        )

    def _handle_http(self, request_header: str, client_socket: socket.socket, client_address: Tuple[str, int]):
        """Handle HTTP requests."""
        try:
            # Extract the URL from the request header to determine the target server
            first_line = request_header.split("\n")[0]
            url = first_line.split(" ")[1]
            http_pos = url.find("://")  # find pos of ://
            if http_pos == -1:
                temp = url
            else:
                temp = url[(http_pos + 3) :]  # get the rest of the url
            port_pos = temp.find(":")  # find the port pos (if any)
            # Default port
            port = 80
            if port_pos == -1:  # default port
                port_pos = temp.find("/")  # find the end of the server name
                server = temp[:port_pos]
            else:  # specific port
                server = temp[:port_pos]
                port = int((temp[(port_pos + 1) :])[: temp[(port_pos + 1) :].find("/")])
            # Create a socket to connect to the web server
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((server, port))
            s.sendall(request_header.encode())
            while True:
                # receive data from web server
                data = s.recv(4096)
                if len(data) > 0:
                    client_socket.send(data)  # send to browser/client
                else:
                    break
            s.close()
        except socket.error as e:
            self.log(f"Error: {e}\n{traceback.format_exc()}", "server", "error")

    def _handle_https(self, request_header: str, client_socket: socket.socket, client_address: Tuple[str, int]):
        """Handle HTTPS CONNECT requests."""
        try:
            target = request_header.split(" ")[1].split(":")[0]
            port = int(request_header.split(" ")[1].split(":")[1])
            # Establish a connection to the target
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.connect((target, port))
            # Send connection established response to the client
            client_socket.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")
            # Tunnel the data between client and server
            self._tunnel_data(client_socket, server_socket)
        except socket.gaierror as e:
            self.log(f"DNS resolution error: {e}", "server", "error")
            client_socket.close()
        except Exception as e:
            self.log(f"HTTPS handling error: {e}\n{traceback.format_exc()}", "server", "error")
            client_socket.close()

    def _tunnel_data(self, client_socket: socket.socket, server_socket: socket.socket):
        """Tunnel data between client and server sockets."""
        sockets_list = [client_socket, server_socket]
        keep_alive = True
        while keep_alive:
            read_sockets, _, error_sockets = select.select(sockets_list, [], sockets_list, None)
            if error_sockets:
                keep_alive = False
            for sock in read_sockets:
                if sock is client_socket:
                    data = client_socket.recv(4096)
                    if data:
                        server_socket.sendall(data)
                    else:
                        keep_alive = False
                elif sock is server_socket:
                    data = server_socket.recv(4096)
                    if data:
                        client_socket.sendall(data)
                    else:
                        keep_alive = False

    def _authenticate_user(self, username: str, password: str) -> bool:
        """Authenticate a user by username and hashed password."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
            result = cursor.fetchone()
            if result:
                stored_password = result[0]
                salt = bytes.fromhex(stored_password[-32:])
                password_hash, _ = self._hash_password(password, salt)
                return stored_password[:-32] == password_hash
            return False

    def _run_command_interface(self) -> None:
        """Run the command-line interface for interacting with the server."""
        self.log(f"\n 🖥️  Welcome on the CLI, enter help to see the commands\n", "cli")
        help = "\n 💡 Available commands:\n  - add-user\n  - show-logs\n - exit\n"
        while True:
            command = input("> ").strip().lower()
            if command == "add-user":
                self._execute_add_user_command()
            elif command == "exit":
                self._cleanup_and_exit()
            elif command == "show-logs":
                self._show_logs()
            elif command == "help":
                self.log(help, "cli")
            else:
                self.log("Invalid command. Please try again.", "cli", "error")

    def _cleanup_and_exit(self):
        """Cleanup resources, close log tailing windows, and exit."""
        self.log(" 🟥 Server closed", "server")
        # Clear log file
        open("server.log", "w").close()
        # Clear the database
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.log(" 🟥 Server startup cancelled.", "cli")
        sys.exit(0)

    def _execute_add_user_command(self) -> None:
        """Execute the add_user command."""
        if self.authentication:
            username = input("\n ▶️ Enter username: ").strip()
            password = input(" ▶️ Enter password: ").strip()
            self.add_user(username, password)
        else:
            self.log(" 💡 User authentication is deactivated. No need to create any users.", "cli")

    def _show_logs(self):
        """Open a new terminal window to tail the server.log file."""
        if platform.system() == "Linux":
            try:
                subprocess.call(["gnome-terminal", "--", "tail", "-f", "server.log"])
            except Exception as e:
                self.log(f"Failed to open log tailing terminal: {e}", "cli", "error")
        else:
            self.log("The 'show-logs' command is not available on the current platform.", "cli", "error")

    def _get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except socket.error as e:
            self.log(f"Error: {e}", "cli")

    def _get_public_ip(self) -> str:
        """Fetch the current public IP address using an external service."""
        try:
            response = requests.get("https://ifconfig.me")
            return response.text
        except requests.RequestException as e:
            self.log(f"Error fetching public IP: {e}", "cli", "error")
            sys.exit(1)

    def log(self, msg: str, name: str, level: str = "info") -> None:
        """Log a message with a given level."""
        if name == "cli":
            if level == "info":
                print(msg)
            elif level == "error":
                print(f" ❌ {msg}")
            else:
                print(f" ⚠️  {msg}")
        elif name == "server":
            if level == "info":
                logging.info(msg)
            elif level == "error":
                logging.error(f" ❌ {msg}")
            else:
                logging.warning(f" ⚠️  {msg}")

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
                self.log(f"\n ✅ User created: Username: {username}", "cli")
        except sqlite3.IntegrityError:
            self.log(" 💡 User already exists.\n", "cli", "warning")

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

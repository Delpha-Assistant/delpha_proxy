<div align="center">
  <a href="https://github.com/Delpha-Assistant/delpha_proxy">
    <img src="assets/logo.webp" alt="Logo" width="130">
  </a>

  <h3 align="center">Delpha Proxy</h3>

  <p align="center">
    <i>Let's play with proxies</i>
    <br />
    <a href="https://github.com/Delpha-Assistant/delpha_proxy"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://github.com/Delpha-Assistant/delpha_proxy/issues">Report Bug</a>
    •
    <a href="https://github.com/Delpha-Assistant/delpha_proxy/issues">Request Feature</a>
  </p>
</div>

# Delpha Proxy

Delpha Proxy is a Python package that allows you to easily set up and manage both server and client proxies. It provides a convenient interface for configuring proxy servers with authentication support and handling client connections seamlessly.

## Installation

You can install Delpha Proxy using pip:

```bash
pip install delpha-proxy
```

## Usage

### Setting up a Proxy Server

To set up a proxy server, run the following command:

```bash
delpha-proxy setup-server
```

Follow the prompts to configure the server settings, including port number and authentication.

### Setting up a Proxy Client

To set up a proxy client, run the following command:

```bash
delpha-proxy setup-client
```

The client will automatically detect the platform and configure the appropriate proxy settings. The client is more for testing / debugging purpose, you will be able to check the status of the proxy and activate / deactivate. But of course you can directly use the proxy where ever you want by setup it in your browsers / machine etc without using the client.



© 2024 Delpha Technologies
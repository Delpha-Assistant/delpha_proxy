<div align="center">
  <a href="https://github.com/Delpha-Assistant/delpha_proxy">
    <img src="assets/logo.webp" alt="Logo" width="130">
  </a>

  <h3 align="center">Delpha Proxy</h3>

  <p align="center">
    <i>Let's play with proxies</i>
    <br />
    <a href="https://github.com/Delpha-Assistant/delpha_proxy/issues">Report Bug</a>
    •
    <a href="https://github.com/Delpha-Assistant/delpha_proxy/issues">Request Feature</a>
  </p>
</div>

# Delpha Proxy

Delpha Proxy is a Python package that allows you to easily set up and manage a proxy server on any machine you want. It provides a convenient interface for configuring proxy servers with authentication support.

## Installation

You can install Delpha Proxy using pip (you will need an ssh authentication here):

```bash
pip install git+ssh://git@github.com/Delpha-Assistant/delpha_proxy
```

## Usage

To set up a proxy server, run the following command:

```bash
setup
```

For dev purpose:
```bash
poetry run setup
```

Follow the prompts to configure the server settings, including port number and authentication.


You can also execute a check to test the proxy

```bash
check
```

For dev purpose:
```bash
poetry run check
```


## Troubles

If the *setup* or *check* commands are not found, check if your python lib path is part of your PATH. 
You can execute the following command inorder to see where is installed the package

```bash
pip show delpha_proxy
```

Then you should check the location and be sure that the bin folder is part of your PATH

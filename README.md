# Learning OPC UA Server and Client

This project contains a demo OPC UA server and a Python client using `asyncua`. The server creates a demo device with simulated temperature, pressure, a running flag, and a writable temperature setpoint. The Python client can read the values, change the setpoint, and subscribe to temperature updates.

## Prerequisites

- Windows with Python installed and PowerShell available.
- Run all Python commands below from the project root folder, `D:\Learning\OPCUA\OPC-Server`.
- The commands explicitly use this project's `.venv` interpreter so the server and client use the same installed `asyncua` package.

## One-time setup

1. Open the project folder in VS Code. Select **Terminal > New Terminal** and check that the terminal is in the project root. If it is elsewhere, run:

	```powershell
	cd D:\Learning\OPCUA\OPC-Server
	```

2. Create the virtual environment only if the `.venv` folder does not already exist:

	```powershell
	py -m venv .venv
	```

3. Install the project dependencies into that virtual environment:

	```powershell
	.\.venv\Scripts\python.exe -m pip install -r requirements.txt
	```

	`requirements.txt` installs asyncua 2.x. If dependencies are updated while a server is running, stop that server and start it again so the process loads the updated package.

## Start the server

1. In the project-root PowerShell terminal, run:

	```powershell
	.\.venv\Scripts\python.exe .\server.py
	```

2. Leave this terminal open. The default endpoint is `opc.tcp://127.0.0.1:4840/learning/server/`. The log should report that it is listening on `127.0.0.1:4840`.
3. Start only one server on a given address and port. If you see `WinError 10048` (address already in use), stop the other server with Ctrl+C in its terminal, or choose a different port, for example:

	```powershell
	.\.venv\Scripts\python.exe .\server.py --port 4841
	```

	When using port 4841, use that port in the client endpoint too.

## Run the Python client

Keep the server running, then open a **second** PowerShell terminal in the project root. Run one of these commands:

- **Read the current values once, then disconnect:**

  ```powershell
  .\.venv\Scripts\python.exe .\client.py
  ```

- **Write a new setpoint, read the values, then disconnect:**

  ```powershell
  .\.venv\Scripts\python.exe .\client.py --setpoint 30.0
  ```

- **Read the values and continuously watch temperature changes:**

  ```powershell
  .\.venv\Scripts\python.exe .\client.py --watch
  ```

  The subscription publishing interval defaults to 1000 ms. Set another interval in milliseconds with `--interval`, for example `--watch --interval 500`. Press Ctrl+C to disconnect the watching client.

- **Write a setpoint and watch the temperature move toward it:**

  ```powershell
  .\.venv\Scripts\python.exe .\client.py --setpoint 30.0 --watch
  ```

If the server uses another endpoint, pass it explicitly. For example, if it was started on port 4841:

```powershell
.\.venv\Scripts\python.exe .\client.py --endpoint opc.tcp://127.0.0.1:4841/learning/server/
```

The client resolves the namespace index using URI `urn:learning:opcua:demo`; it does not assume a fixed namespace index.

## Connect with a separate OPC UA client tool

Start the Python server first, then configure the OPC UA client tool with:

- **Endpoint URL:** `opc.tcp://127.0.0.1:4840/learning/server/`
- **Security policy / mode:** None / None
- **Authentication:** Anonymous

Browse **Objects > DemoDevice**. `Temperature`, `Pressure`, and `Running` are read-only. `TemperatureSetpoint` is writable; write it as a numeric Double value. Each successful client write is also printed in the server terminal, for example `Received TemperatureSetpoint from OPC UA client: 30.0`. This server uses NoSecurity for local development and testing only—do not expose it to an untrusted network.

## Stop the programs

- Stop the server by pressing Ctrl+C in the terminal running `server.py`.
- Stop a watching Python client by pressing Ctrl+C in the terminal running `client.py`.
- One-shot client runs disconnect automatically after printing their results.

## Troubleshooting

- **`No module named 'asyncua'`:** install from the project root with `./.venv/Scripts/python.exe -m pip install -r requirements.txt`, then run both scripts with the `.venv` interpreter as shown above.
- **Client cannot connect / connection refused:** start the server first, keep its terminal open, and make sure the client endpoint host and port exactly match the server endpoint.
- **`WinError 10048` / address already in use:** another process is already bound to the selected host and port. Stop the previous server with Ctrl+C before starting a new one, or choose an unused port and pass the same port to the client endpoint.
- **After upgrading dependencies:** restart the server before using the client so both processes load the installed asyncua version.
- **Connecting from another computer:** use the server computer's reachable LAN IP with the server's `--host` option and in the client's `--endpoint`; allow inbound TCP on the selected port in the firewall. Do not use this NoSecurity example on an untrusted network.


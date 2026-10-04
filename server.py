"""A small, locally oriented OPC UA demo server built with asyncua."""

from __future__ import annotations

import argparse
import asyncio
import logging

from asyncua import Server, ua
from asyncua.server.server import CallbackType

NAMESPACE_URI = "urn:learning:opcua:demo"
SERVER_NAME = "Learning OPC UA Demo Server"


async def run_server(host: str, port: int) -> None:
    server = Server()
    await server.init()
    endpoint = f"opc.tcp://{host}:{port}/learning/server/"
    server.set_endpoint(endpoint)
    server.set_server_name(SERVER_NAME)

    # Always use the namespace index returned by registration; it is not fixed.
    namespace_index = await server.register_namespace(NAMESPACE_URI)
    device = await server.nodes.objects.add_object(namespace_index, "DemoDevice")

    temperature = await device.add_variable(namespace_index, "Temperature", 22.0)
    pressure = await device.add_variable(namespace_index, "Pressure", 101.3)
    setpoint = await device.add_variable(namespace_index, "TemperatureSetpoint", 24.0)
    running = await device.add_variable(namespace_index, "Running", True)
    await setpoint.set_writable()  # The setpoint is the only client-writable node.

    def log_setpoint_write(event: object, _callback_service: object) -> None:
        for write, status in zip(
            event.request_params.NodesToWrite,
            event.response_params,
            strict=True,
        ):
            if (
                write.NodeId == setpoint.nodeid
                and write.AttributeId == ua.AttributeIds.Value
                and status.is_good()
            ):
                logging.info(
                    "Received TemperatureSetpoint from OPC UA client: %s",
                    write.Value.Value.Value,
                )

    # PostWrite runs after the write has been accepted, so only successful
    # client writes to this writable variable are reported.
    server.subscribe_server_callback(CallbackType.PostWrite, log_setpoint_write)

    logging.info("Starting %s at %s", SERVER_NAME, endpoint)
    logging.info("Browse Objects > DemoDevice to see the demo variables")
    logging.info("TemperatureSetpoint is writable; other demo variables are read-only")
    logging.warning(
        "This example uses OPC UA NoSecurity for isolated development/testing only; "
        "do not expose it to an untrusted network."
    )

    async def update_temperature() -> None:
        current = 22.0
        while True:
            target = float(await setpoint.read_value())
            current += max(-0.5, min(0.5, target - current))
            await temperature.write_value(round(current, 1))
            await asyncio.sleep(1)

    update_task: asyncio.Task[None] | None = None
    await server.start()
    try:
        update_task = asyncio.create_task(update_temperature())
        # Keep the server running until Ctrl+C cancels this coroutine.
        await asyncio.Event().wait()
    finally:
        if update_task is not None:
            update_task.cancel()
            try:
                await update_task
            except asyncio.CancelledError:
                pass
        await server.stop()
        logging.info("OPC UA server stopped")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a demo OPC UA server.")
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help=(
            "Interface/address to bind and advertise (default: 127.0.0.1). "
            "For another machine, use this computer's reachable LAN IP."
        ),
    )
    parser.add_argument("--port", type=int, default=4840, help="TCP port (default: 4840)")
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    # asyncua logs many address-space initialization details at INFO level.
    logging.getLogger("asyncua").setLevel(logging.WARNING)
    args = parse_args()
    try:
        asyncio.run(run_server(args.host, args.port))
    except KeyboardInterrupt:
        logging.info("Shutdown requested")


if __name__ == "__main__":
    main()

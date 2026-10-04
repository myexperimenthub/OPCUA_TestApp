"""Connect to the demo OPC UA server, read values, and optionally write/watch."""

from __future__ import annotations

import argparse
import asyncio
import logging

from asyncua import Client

NAMESPACE_URI = "urn:learning:opcua:demo"
DEFAULT_ENDPOINT = "opc.tcp://127.0.0.1:4840/learning/server/"


class TemperatureHandler:
    """Print temperature values delivered by an OPC UA data-change subscription."""

    def datachange_notification(self, node: object, value: object, data: object) -> None:
        print(f"Temperature update: {value}", flush=True)


async def run_client(endpoint: str, setpoint_value: float | None, watch: bool, interval: int) -> None:
    async with Client(url=endpoint) as client:
        # Resolve the namespace index from its URI; it can vary between servers.
        namespace_index = await client.get_namespace_index(NAMESPACE_URI)
        device = await client.nodes.objects.get_child([f"{namespace_index}:DemoDevice"])

        temperature = await device.get_child([f"{namespace_index}:Temperature"])
        pressure = await device.get_child([f"{namespace_index}:Pressure"])
        setpoint = await device.get_child([f"{namespace_index}:TemperatureSetpoint"])
        running = await device.get_child([f"{namespace_index}:Running"])

        if setpoint_value is not None:
            await setpoint.write_value(float(setpoint_value))
            print(f"Wrote TemperatureSetpoint: {setpoint_value}")

        print(f"Connected to {endpoint}")
        print(f"Temperature: {await temperature.read_value()}")
        print(f"Pressure: {await pressure.read_value()}")
        print(f"TemperatureSetpoint: {await setpoint.read_value()}")
        print(f"Running: {await running.read_value()}")

        if watch:
            subscription = await client.create_subscription(interval, TemperatureHandler())
            try:
                await subscription.subscribe_data_change(temperature)
                print(
                    f"Watching Temperature via OPC UA subscription every {interval} ms. "
                    "Press Ctrl+C to disconnect."
                )
                await asyncio.Event().wait()
            finally:
                await subscription.delete()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read values from the demo OPC UA server and optionally write/watch."
    )
    parser.add_argument(
        "--endpoint",
        default=DEFAULT_ENDPOINT,
        help=f"OPC UA endpoint (default: {DEFAULT_ENDPOINT})",
    )
    parser.add_argument(
        "--setpoint",
        type=float,
        help="Optional numeric value to write to TemperatureSetpoint",
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Subscribe to Temperature changes after printing the initial values",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=1000,
        help="Subscription publishing interval in milliseconds (default: 1000)",
    )
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logging.getLogger("asyncua").setLevel(logging.WARNING)
    args = parse_args()
    if args.interval <= 0:
        raise SystemExit("--interval must be greater than zero")

    try:
        asyncio.run(run_client(args.endpoint, args.setpoint, args.watch, args.interval))
    except KeyboardInterrupt:
        logging.info("Client disconnected")
    except Exception as exc:
        raise SystemExit(
            f"Could not use OPC UA endpoint {args.endpoint}: {exc}\n"
            "Check that the server is running and that the endpoint and namespace match."
        ) from exc


if __name__ == "__main__":
    main()

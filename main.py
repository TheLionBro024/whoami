# main.py — Entrypoint for Evolv.Platform
import asyncio
import sys

import uvicorn


async def run_server(app: str, port: int, title: str):
    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    print(f"[{title}] Starting on port {port}...")
    await server.serve()


async def main():
    print("Starting Evolv.Platform multi-server...")

    # Run the three apps concurrently
    await asyncio.gather(
        run_server("Main.app:app", 8000, "Main"),
        run_server("op.app:app", 8001, "op"),
        run_server("aqua.app:app", 8002, "aqua")
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down Evolv.Platform.")
        sys.exit(0)

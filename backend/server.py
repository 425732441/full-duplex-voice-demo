#
# Copyright (c) 2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#
import asyncio
import os
from contextlib import asynccontextmanager
from typing import Any, Dict

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables
load_dotenv(override=True)

from bot_fast_api import run_bot


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles FastAPI startup and shutdown."""
    yield  # Run app


# Initialize FastAPI app with lifespan manager
app = FastAPI(lifespan=lifespan)

# Configure CORS to allow requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket connection accepted")
    try:
        await run_bot(websocket)
    except Exception as e:
        print(f"Exception in run_bot: {e}")


@app.post("/connect")
async def bot_connect(request: Request) -> Dict[Any, Any]:
    host = request.headers["host"]
    # 判断本地地址
    local_hosts = ["localhost", "127.0.0.1", "0.0.0.0"]
    hostname = host.split(":")[0]
    if hostname in local_hosts:
        ws_scheme = "ws"
    else:
        ws_scheme = "wss"
    print(f"request url:{request.url}, host:{host}, ws_scheme:{ws_scheme}")

    server_mode = os.getenv("WEBSOCKET_SERVER", "fast_api")
    if server_mode == "websocket_server":
        hostname = host.split(":")[0]
        ws_url = f"ws://{hostname}:8765"
    else:
        ws_url = f"{ws_scheme}://{host}/ws"
    return {"ws_url": ws_url}


async def main():
    server_mode = os.getenv("WEBSOCKET_SERVER", "fast_api")
    tasks = []
    try:
        if server_mode == "websocket_server":
            pass
            # tasks.append(run_bot_websocket_server())

        config = uvicorn.Config(app, host="0.0.0.0", port=7860)
        server = uvicorn.Server(config)
        tasks.append(server.serve())

        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        print("Tasks cancelled (probably due to shutdown).")


if __name__ == "__main__":
    asyncio.run(main())

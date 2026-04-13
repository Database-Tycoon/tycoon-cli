"""WebSocket endpoint for real-time subprocess log streaming."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from tycoon.server.subprocess_manager import subprocess_manager

router = APIRouter()


@router.websocket("/ws/logs/{run_id}")
async def stream_logs(websocket: WebSocket, run_id: str) -> None:
    """Stream stdout lines from a tracked subprocess to the WebSocket client."""
    await websocket.accept()

    run = subprocess_manager.get_run(run_id)
    if run is None:
        await websocket.send_text(f"[error] unknown run_id: {run_id}")
        await websocket.close()
        return

    # Send any lines that were already captured before the client connected.
    for line in run.log_lines:
        await websocket.send_text(line)

    # If the process has already finished, close immediately.
    if run.finished or run.process.returncode is not None:
        await websocket.send_text("[done]")
        await websocket.close()
        return

    # Stream new lines as they arrive.
    try:
        stdout = run.process.stdout
        if stdout is None:
            await websocket.send_text("[error] no stdout pipe")
            await websocket.close()
            return

        while True:
            raw = await stdout.readline()
            if raw == b"":
                # Process has ended.
                break
            line = raw.decode("utf-8", errors="replace").rstrip("\n")
            run.log_lines.append(line)
            await websocket.send_text(line)

        run.finished = True
        await websocket.send_text("[done]")
    except WebSocketDisconnect:
        pass
    except asyncio.CancelledError:
        pass

#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Mock hydraulics controller for the Flower Power sculpture.

Emulates the real Controllino-based HTTP API (controller.ino):
    GET /status          -> JSON with current position
    GET /move?band=N     -> move to band N (0-9), target = N*100+50 mm
    GET /stop            -> stop movement

Physics:
    0 mm  = flower fully closed
    1000 mm = flower fully opened
    0 -> 1000 mm takes 10 seconds (10 steps x 1 s each, 100 mm/step)

Usage:
    uv run mock_controller.py
    uv run mock_controller.py --host 0.0.0.0 --port 8080
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

# ── Simulation constants ─────────────────────────────────────────────────────
VELOCITY_MM_PER_S = 100.0  # full stroke (1000 mm) in 10 s
TICK_S            = 0.05   # physics tick: 20 Hz
STEP_MM           = VELOCITY_MM_PER_S * TICK_S  # 5 mm per tick
DEADBAND_MM       = 3.0

# ADC calibration mirrored from controller.ino
_CAL_ADC_0MM    = 807
_CAL_ADC_1000MM = 761


def _mm_to_adc(mm: float) -> int:
    t = max(0.0, min(1.0, mm / 1000.0))
    return round(_CAL_ADC_0MM + t * (_CAL_ADC_1000MM - _CAL_ADC_0MM))


# ── ASCII hand-fan frames (11 stages: 0, 100, 200, …, 1000 mm) ──────────────
#
#  Ribs radiate from the pivot  *  just like a folding hand fan.
#  The fan opens symmetrically; extra rib lines appear every 200 mm.
#
#    closed          half open         fully open
#      |              \   |   /        \ \ \  |  / / /
#      |               \  |  /          \ \ \ | / / /
#      |                \ | /            \ \ \|/ / /
#      *                 \|/              \ \\|// /
#      |                  *               \\|//
#                          |               \|/
#                                           *
#                                           |

_FRAMES: list[list[str]] = [
    # 0 mm – closed (fan furled)
    ["  |  ",
     "  |  ",
     "  |  ",
     "  *  ",
     "  |  "],

    # 100 mm
    [" \\|/ ",
     "  |  ",
     "  |  ",
     "  *  ",
     "  |  "],

    # 200 mm
    ["\\ | /",
     " \\|/ ",
     "  |  ",
     "  *  ",
     "  |  "],

    # 300 mm
    ["\\ | /",
     "\\ | /",
     " \\|/ ",
     "  *  ",
     "  |  "],

    # 400 mm
    ["\\  |  /",
     " \\ | / ",
     "  \\|/  ",
     "   *   ",
     "   |   "],

    # 500 mm – half open
    ["\\   |   /",
     " \\  |  / ",
     "  \\ | /  ",
     "   \\|/   ",
     "    *    ",
     "    |    "],

    # 600 mm
    ["\\    |    /",
     " \\   |   / ",
     "  \\  |  /  ",
     "   \\ | /   ",
     "    \\|/    ",
     "     *     ",
     "     |     "],

    # 700 mm – second rib appears
    ["\\ \\   |   / /",
     " \\ \\  |  / / ",
     "  \\ \\ | / /  ",
     "   \\ \\|/ /   ",
     "    \\\\|//    ",
     "     \\|/     ",
     "      *      ",
     "      |      "],

    # 800 mm
    ["\\ \\    |    / /",
     " \\ \\   |   / / ",
     "  \\ \\  |  / /  ",
     "   \\ \\ | / /   ",
     "    \\ \\|/ /    ",
     "     \\\\|//     ",
     "      \\|/      ",
     "       *       ",
     "       |       "],

    # 900 mm – third rib appears
    ["\\ \\ \\   |   / / /",
     " \\ \\ \\  |  / / / ",
     "  \\ \\ \\ | / / /  ",
     "   \\ \\ \\|/ / /   ",
     "    \\ \\\\|// /    ",
     "     \\ \\|/ /     ",
     "      \\\\|//      ",
     "       \\|/       ",
     "        *        ",
     "        |        "],

    # 1000 mm – fully open
    ["\\ \\ \\   |   / / /",
     " \\ \\ \\  |  / / / ",
     "  \\ \\ \\ | / / /  ",
     "   \\ \\ \\|/ / /   ",
     "    \\ \\\\|// /    ",
     "     \\\\\\|///     ",
     "      \\\\|//      ",
     "       \\|/       ",
     "        *        ",
     "        |        "],
]

_LABELS: list[str] = [
    "   0 mm  -  Fan furled (closed)    ",
    " 100 mm  -  First crease ...       ",
    " 200 mm  -  One rib showing        ",
    " 300 mm  -  Spreading open         ",
    " 400 mm  -  Quarter open           ",
    " 500 mm  -  Half open              ",
    " 600 mm  -  Two thirds open        ",
    " 700 mm  -  Second rib out         ",
    " 800 mm  -  Three quarters open    ",
    " 900 mm  -  Third rib out          ",
    "1000 mm  -  Fully open             ",
]

_BOX_W = 60  # total box width incl. border chars


def _box(text: str = "") -> str:
    return "|" + text.center(_BOX_W - 2) + "|"


def _render(pos: float, target: float | None, moving: bool) -> str:
    idx = min(10, max(0, round(pos / 100)))
    rows: list[str] = []

    rows.append("+" + "=" * (_BOX_W - 2) + "+")
    rows.append(_box("FLOWER POWER  -  Hydraulic Controller Mock"))
    rows.append("+" + "-" * (_BOX_W - 2) + "+")
    rows.append(_box())

    for line in _FRAMES[idx]:
        rows.append(_box(line))

    rows.append(_box())
    rows.append(_box(_LABELS[idx]))
    rows.append(_box())

    # Status line
    if moving and target is not None:
        direction = "EXTENDING" if target > pos else "RETRACTING"
        status = f"{direction}  {pos:6.1f} mm  ->  {target:.0f} mm"
    else:
        status = f"STOPPED  at  {pos:6.1f} mm"
    rows.append(_box(status))

    # Progress bar  0 mm ──────────────── 1000 mm
    # inner width = BOX_W - 2 borders - 2+2 padding - 2 brackets = BOX_W - 8
    bar_w = _BOX_W - 8
    fill  = int((pos / 1000.0) * bar_w)
    bar   = "[" + "#" * fill + "." * (bar_w - fill) + "]"
    rows.append("|  " + bar + "  |")
    # ruler spans same bar_w + 2 brackets = BOX_W - 6 chars total
    ruler_w = _BOX_W - 6
    ruler = f"{'0 mm':<{ruler_w - 7}}{'1000 mm':>7}"
    rows.append("|  " + ruler + "  |")
    rows.append("+" + "=" * (_BOX_W - 2) + "+")

    return "\n".join(rows)


# ── Shared simulation state ───────────────────────────────────────────────────

class _State:
    def __init__(self) -> None:
        self._lock     = threading.Lock()
        self.pos_mm: float   = 0.0
        self.target_mm: float = 0.0
        self.moving: bool    = False

    def snapshot(self) -> tuple[float, float, bool]:
        with self._lock:
            return self.pos_mm, self.target_mm, self.moving

    def set_target(self, target: float) -> None:
        with self._lock:
            self.target_mm = max(0.0, min(1000.0, target))
            self.moving    = True

    def stop(self) -> None:
        with self._lock:
            self.moving = False

    def tick(self) -> bool:
        """Advance position by one simulation tick. Returns True while moving."""
        with self._lock:
            if not self.moving:
                return False
            error = self.target_mm - self.pos_mm
            if abs(error) <= DEADBAND_MM:
                self.pos_mm = self.target_mm
                self.moving = False
                return False
            step = min(STEP_MM, abs(error))
            self.pos_mm += step if error > 0 else -step
            return True


_state = _State()

# ── Terminal renderer ─────────────────────────────────────────────────────────

_print_lock        = threading.Lock()
_last_frame_lines  = 0


def _print_frame(pos: float, target: float | None, moving: bool) -> None:
    global _last_frame_lines
    screen = _render(pos, target, moving)
    line_count = screen.count("\n") + 1
    with _print_lock:
        if _last_frame_lines:
            # Move cursor up and clear to end of screen
            sys.stdout.write(f"\033[{_last_frame_lines}A\033[J")
        sys.stdout.write(screen + "\n")
        sys.stdout.flush()
        _last_frame_lines = line_count


def _movement_loop() -> None:
    """Background thread: drives physics simulation and terminal animation."""
    prev_idx    = -1
    prev_moving = None

    while True:
        _state.tick()
        pos, target, moving = _state.snapshot()
        idx = min(10, max(0, round(pos / 100)))

        # Only redraw when the flower stage or movement status changes
        if idx != prev_idx or moving != prev_moving:
            _print_frame(pos, target if moving else None, moving)
            prev_idx    = idx
            prev_moving = moving

        time.sleep(TICK_S)


# ── HTTP request handler ──────────────────────────────────────────────────────

class _Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: object) -> None:
        # Suppress the default access log; the terminal display is our feedback
        pass

    def _send_json(self, code: int, data: dict) -> None:
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _build_status(
        self, pos: float, target: float | None, moving: bool
    ) -> dict:
        data: dict = {
            "stroke_mm": round(pos, 1),
            "adc": _mm_to_adc(pos),
            "auto": moving,
        }
        if moving and target is not None:
            data["target_mm"] = round(target, 0)
        return data

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        pos, target, moving = _state.snapshot()

        if parsed.path == "/status":
            self._send_json(200, self._build_status(pos, target, moving))

        elif parsed.path == "/move":
            if "band" not in params:
                self._send_json(400, {"error": "missing band parameter"})
                return
            try:
                band = int(params["band"][0])
            except ValueError:
                self._send_json(400, {"error": "band must be an integer"})
                return
            if not 0 <= band <= 9:
                self._send_json(400, {"error": "band must be 0-9"})
                return
            new_target = band * 100.0 + 50.0
            _state.set_target(new_target)
            self._send_json(
                200,
                self._build_status(pos, new_target, True),
            )

        elif parsed.path == "/stop":
            _state.stop()
            pos, target, moving = _state.snapshot()
            self._send_json(200, self._build_status(pos, None, False))

        else:
            self._send_json(404, {"error": "not found"})


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Flower Power mock hydraulic controller"
    )
    parser.add_argument("--host", default="0.0.0.0", help="bind address")
    parser.add_argument("--port", type=int, default=8080, help="TCP port")
    args = parser.parse_args()

    display_host = "127.0.0.1" if args.host == "0.0.0.0" else args.host

    print("Flower Power - Mock Hydraulic Controller")
    print(f"  http://{display_host}:{args.port}")
    print()
    print("  GET /status          current position (JSON)")
    print("  GET /move?band=N     move to band N (0-9) -> N*100+50 mm")
    print("  GET /stop            stop movement")
    print()
    print("  Ctrl-C to quit")
    print()

    # Draw initial (static) flower state
    _print_frame(0.0, None, False)

    # Start physics + display thread
    threading.Thread(target=_movement_loop, daemon=True).start()

    server = HTTPServer((args.host, args.port), _Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        sys.exit(0)


if __name__ == "__main__":
    main()

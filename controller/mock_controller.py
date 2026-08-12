#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Mock hydraulics controller for the Flower Power sculpture.

Emulates the real Controllino-based HTTP API (controller.ino):
    GET /status               -> JSON with position, fire and pattern state
    GET /move?band=N          -> move to band N (0-9), target = N*100+50 mm
    GET /stop                 -> stop movement
    GET /fire?n=0,2,4&ms=250  -> pulse those fire relays for 250 ms
    GET /fire?n=all&on=1      -> hold on (on=0 switches off again)
    GET /swirl?on=1           -> start/stop the swirl sequence
    GET /bloom?on=1           -> start/stop the bloom sequence

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

# ── Fire relays and patterns, mirrored from controller.ino ───────────────────
FIRE_COUNT   = 5
FIRE_ALL     = (1 << FIRE_COUNT) - 1
FIRE_HOLD    = float("inf")  # "on until switched off"

SWIRL_PULSE_S     = 0.150
SWIRL_GAP_START_S = 2.0
SWIRL_GAP_STEP_S  = 0.5
SWIRL_RECHARGE_S  = 6.0
SWIRL_FINALE_S    = 2.0

BLOOM_PULSE_S  = 0.250
BLOOM_HYST_MM  = 25.0
BLOOM_RINGS    = ((2, 2), (1, 3), (0, 4))

# ADC calibration mirrored from controller.ino
_CAL_ADC_0MM    = 807
_CAL_ADC_1000MM = 761


def _mm_to_adc(mm: float) -> int:
    t = max(0.0, min(1.0, mm / 1000.0))
    return round(_CAL_ADC_0MM + t * (_CAL_ADC_1000MM - _CAL_ADC_0MM))


def _parse_fire_mask(v: str) -> int | None:
    """"0,2,4" or "all" / "*" -> bitmask, None if unparsable."""
    if v in ("all", "*"):
        return FIRE_ALL
    mask = 0
    for part in v.replace("+", ",").split(","):
        if not part.isdigit() or int(part) >= FIRE_COUNT:
            return None
        mask |= 1 << int(part)
    return mask or None


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


def _render(
    pos: float,
    target: float | None,
    moving: bool,
    fire: tuple[bool, ...] = (False,) * FIRE_COUNT,
    swirl: bool = False,
    bloom: bool = False,
) -> str:
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

    # Fire relays, plus whichever pattern is driving them
    flames = "  ".join("(*)" if f else "( )" for f in fire)
    pattern = "  ".join(p for p, on in (("SWIRL", swirl), ("BLOOM", bloom)) if on)
    rows.append(_box(f"FIRE  {flames}"))
    rows.append(_box(pattern))

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
        # Reentrant: tick() holds the lock while calling the fire helpers
        self._lock     = threading.RLock()
        self.pos_mm: float   = 0.0
        self.target_mm: float = 0.0
        self.moving: bool    = False

        # Requested state per relay: 0 = off, FIRE_HOLD, or the monotonic
        # deadline at which it goes off again
        self.fire_until: list[float] = [0.0] * FIRE_COUNT

        self.swirl_running = False
        self.swirl_reverse = False
        self.swirl_finale  = False
        self.swirl_step    = 0
        self.swirl_gap     = SWIRL_GAP_START_S
        self.swirl_next_at = 0.0

        self.bloom_active = False
        self.bloom_ring   = -1

    def snapshot(self) -> tuple[float, float, bool]:
        with self._lock:
            return self.pos_mm, self.target_mm, self.moving

    def fire_snapshot(self) -> tuple[tuple[bool, ...], bool, bool]:
        with self._lock:
            now = time.monotonic()
            fire = tuple(u > now for u in self.fire_until)
            return fire, self.swirl_running, self.bloom_active

    def set_target(self, target: float) -> None:
        with self._lock:
            self.target_mm = max(0.0, min(1000.0, target))
            self.moving    = True

    def stop(self) -> None:
        with self._lock:
            self.moving = False

    # ── Fire ────────────────────────────────────────────────────────────────
    def fire(self, mask: int, seconds: float) -> None:
        with self._lock:
            until = FIRE_HOLD if seconds == FIRE_HOLD else time.monotonic() + seconds
            for i in range(FIRE_COUNT):
                if mask & (1 << i):
                    self.fire_until[i] = until

    def stop_fire(self, mask: int) -> None:
        with self._lock:
            for i in range(FIRE_COUNT):
                if mask & (1 << i):
                    self.fire_until[i] = 0.0

    def fire_all_off(self) -> None:
        with self._lock:
            self.swirl_start(False)
            self.bloom_start(False)
            self.fire_until = [0.0] * FIRE_COUNT

    # ── Patterns ────────────────────────────────────────────────────────────
    def swirl_start(self, on: bool = True) -> None:
        with self._lock:
            if on:
                self.swirl_running = True
                self.swirl_finale  = False
                self.swirl_step    = 0
                self.swirl_gap     = SWIRL_GAP_START_S
                self.swirl_next_at = time.monotonic()
            elif self.swirl_running:
                self.swirl_running = False
                self.swirl_finale  = False
                self.swirl_reverse = not self.swirl_reverse

    def bloom_start(self, on: bool = True) -> None:
        with self._lock:
            self.bloom_active = on
            if on:
                self.bloom_ring = -1

    def _update_swirl(self, now: float) -> None:
        if not self.swirl_running or now < self.swirl_next_at:
            return

        if self.swirl_finale:
            self.fire(FIRE_ALL, SWIRL_FINALE_S)
            self.swirl_start(False)
            return

        if self.swirl_step >= FIRE_COUNT:
            if self.swirl_gap <= SWIRL_GAP_STEP_S:
                self.swirl_finale  = True
                self.swirl_next_at = now + SWIRL_RECHARGE_S
                return
            self.swirl_gap -= SWIRL_GAP_STEP_S
            self.swirl_step = 0

        # Hop 2 of 5 nodes = 144 deg, the closest this ring gets to the golden angle
        stride = FIRE_COUNT - 2 if self.swirl_reverse else 2
        self.fire(1 << ((self.swirl_step * stride) % FIRE_COUNT), SWIRL_PULSE_S)
        self.swirl_next_at = now + SWIRL_PULSE_S + self.swirl_gap
        self.swirl_step += 1

    def _update_bloom(self) -> None:
        if not self.bloom_active:
            return

        width = 1000.0 / len(BLOOM_RINGS)
        r = max(0, self.bloom_ring)
        while r < len(BLOOM_RINGS) - 1 and self.pos_mm > (r + 1) * width + BLOOM_HYST_MM:
            r += 1
        while r > 0 and self.pos_mm < r * width - BLOOM_HYST_MM:
            r -= 1
        if r == self.bloom_ring:
            return
        self.bloom_ring = r

        a, b = BLOOM_RINGS[r]
        self.fire((1 << a) | (1 << b), BLOOM_PULSE_S)

    def tick(self) -> bool:
        """Advance one simulation tick. Returns True while moving."""
        with self._lock:
            now = time.monotonic()
            for i, until in enumerate(self.fire_until):
                if until != FIRE_HOLD and now >= until:
                    self.fire_until[i] = 0.0
            self._update_swirl(now)
            self._update_bloom()

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


def _print_frame(
    pos: float,
    target: float | None,
    moving: bool,
    fire: tuple[bool, ...] = (False,) * FIRE_COUNT,
    swirl: bool = False,
    bloom: bool = False,
) -> None:
    global _last_frame_lines
    screen = _render(pos, target, moving, fire, swirl, bloom)
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
    prev_fire: tuple[object, ...] = ()

    while True:
        _state.tick()
        pos, target, moving = _state.snapshot()
        fire, swirl, bloom = _state.fire_snapshot()
        idx = min(10, max(0, round(pos / 100)))

        # Only redraw when the flower stage, movement or fire state changes
        if idx != prev_idx or moving != prev_moving or (*fire, swirl, bloom) != prev_fire:
            _print_frame(pos, target if moving else None, moving, fire, swirl, bloom)
            prev_idx    = idx
            prev_moving = moving
            prev_fire   = (*fire, swirl, bloom)

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
        fire, swirl, bloom = _state.fire_snapshot()
        data: dict = {
            "stroke_mm": round(pos, 1),
            "adc": _mm_to_adc(pos),
            "auto": moving,
        }
        if moving and target is not None:
            data["target_mm"] = round(target, 0)
        data["fire"] = [int(f) for f in fire]
        data["swirl"] = swirl
        data["bloom"] = bloom
        return data

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        # keep_blank_values so value-less flags like ?on / ?off survive
        params = parse_qs(parsed.query, keep_blank_values=True)
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

        elif parsed.path == "/fire":
            mask = _parse_fire_mask(params.get("n", [""])[0])
            if mask is None:
                self._send_json(
                    400, {"error": f"n must be 0-{FIRE_COUNT - 1} list or all"}
                )
                return
            if "off" in params:
                # clearing everything also clears the patterns feeding it
                _state.fire_all_off() if mask == FIRE_ALL else _state.stop_fire(mask)
            elif "on" in params:
                _state.fire(mask, FIRE_HOLD)
            else:
                try:
                    seconds = int(params.get("ms", [""])[0]) / 1000.0
                except ValueError:
                    seconds = SWIRL_PULSE_S
                _state.fire(mask, seconds)
            self._send_json(200, self._build_status(pos, target, moving))

        elif parsed.path in ("/swirl", "/bloom"):
            start = _state.swirl_start if parsed.path == "/swirl" else _state.bloom_start
            start("on" in params)
            self._send_json(200, self._build_status(pos, target, moving))

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
    print("  GET /status               current state (JSON)")
    print("  GET /move?band=N          move to band N (0-9) -> N*100+50 mm")
    print("  GET /stop                 stop movement")
    print("  GET /fire?n=0,2,4[&ms=X]  pulse those relays (default 150 ms)")
    print("  GET /fire?n=all&on        latch on   (&off switches off again)")
    print("  GET /swirl?on             swirl sequence (?off to stop)")
    print("  GET /bloom?on             bloom sequence (?off to stop)")
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

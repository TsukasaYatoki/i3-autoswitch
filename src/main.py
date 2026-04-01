#!/usr/bin/env python3
"""Auto-switch to a window's workspace on window open/move events in i3."""

from __future__ import annotations

import argparse
import json
import sys

import i3ipc

WINDOW_EVENTS = ("window::new", "window::move")
INTERNAL_WORKSPACE_PREFIX = "__"


def node_name(node: object) -> str | None:
    name = getattr(node, "name", None)
    return name if isinstance(name, str) else None


def workspace_name_for_container(con: i3ipc.Con | None) -> str | None:
    """Return the workspace name that owns this container, if any."""
    if con is None:
        return None

    workspace = con.workspace()
    if workspace is not None:
        name = node_name(workspace)
        if name:
            return name

    # Fallback: walk ancestors in case workspace() returns None.
    current = con.parent
    while current is not None:
        if current.type == "workspace":
            name = node_name(current)
            if name:
                return name
        current = current.parent

    return None


def focused_workspace_name(i3: i3ipc.Connection) -> str | None:
    focused = i3.get_tree().find_focused()
    if focused is None:
        return None

    workspace = focused.workspace()
    if workspace is None:
        return None

    return node_name(workspace)


def debug_log(enabled: bool, message: str) -> None:
    if not enabled:
        return
    print(f"[i3-autoswitch][DEBUG] {message}", file=sys.stderr, flush=True)


def switch_to_workspace(
    i3: i3ipc.Connection, workspace_name: str, debug: bool = False
) -> None:
    # json.dumps safely quotes workspace names for i3 commands.
    debug_log(debug, f"switching to workspace: {workspace_name}")
    i3.command(f"workspace --no-auto-back-and-forth {json.dumps(workspace_name)}")


def resolve_event_workspace(
    i3: i3ipc.Connection, container: i3ipc.Con | None, debug: bool
) -> str | None:
    """Resolve workspace from event container, preferring live tree lookup by id."""
    container_id = getattr(container, "id", None)
    if isinstance(container_id, int):
        live_container = i3.get_tree().find_by_id(container_id)
        target_workspace = workspace_name_for_container(live_container)
        debug_log(
            debug,
            f"tree lookup by id={container_id} -> target_workspace={target_workspace!r}",
        )
        if target_workspace:
            return target_workspace

    target_workspace = workspace_name_for_container(container)
    debug_log(
        debug,
        f"fallback event container lookup -> target_workspace={target_workspace!r}",
    )
    return target_workspace


def on_window_event(i3: i3ipc.Connection, event: object, debug: bool = False) -> None:
    container: i3ipc.Con | None = getattr(event, "container", None)
    event_change = getattr(event, "change", "unknown")
    container_id = getattr(container, "id", None)
    target_workspace = resolve_event_workspace(i3, container, debug)

    container_name = node_name(container)
    debug_log(
        debug,
        f"window::{event_change} received, container_id={container_id!r}, container={container_name!r}, target_workspace={target_workspace!r}",
    )

    if not target_workspace:
        debug_log(debug, "event ignored: no target workspace")
        return

    # Ignore internal/special workspaces such as scratchpad.
    if target_workspace.startswith(INTERNAL_WORKSPACE_PREFIX):
        debug_log(debug, f"event ignored: internal workspace {target_workspace!r}")
        return

    current_workspace = focused_workspace_name(i3)
    if current_workspace == target_workspace:
        debug_log(debug, f"event ignored: already on workspace {target_workspace!r}")
        return

    debug_log(debug, f"current workspace is {current_workspace!r}, will switch")
    switch_to_workspace(i3, target_workspace, debug=debug)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Auto-switch to a window's workspace on i3 window open/move events."
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logs to stderr.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    i3 = i3ipc.Connection()

    def handler(conn: i3ipc.Connection, event: object) -> None:
        on_window_event(conn, event, debug=args.debug)

    for event_name in WINDOW_EVENTS:
        i3.on(event_name, handler)

    debug_log(args.debug, f"listening on {', '.join(WINDOW_EVENTS)}")

    i3.main()


if __name__ == "__main__":
    main()

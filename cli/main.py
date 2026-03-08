#!/usr/bin/env python3
"""Star Office CLI — manage agents from the terminal."""

import argparse
import sys
import os

# Allow running from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.office import Office

DEFAULT_STORE = "office-state.json"


def cmd_add(args):
    office = Office(args.store)
    agent = office.add_agent(args.id, args.name, args.ttl)
    print(f"Added: {agent}")


def cmd_remove(args):
    office = Office(args.store)
    office.remove_agent(args.id)
    print(f"Removed agent '{args.id}'")


def cmd_set(args):
    office = Office(args.store)
    agent = office.set_state(args.id, args.state, args.message or "")
    print(f"Updated: {agent}")


def cmd_list(args):
    office = Office(args.store)
    print(office.summary())


def cmd_status(args):
    office = Office(args.store)
    agent = office.get_agent(args.id)
    agent.check_ttl()
    d = agent.to_dict()
    for k, v in d.items():
        print(f"  {k}: {v}")


def cmd_reset(args):
    office = Office(args.store)
    for agent in office.agents.values():
        agent.set_state("idle", "")
    office.save()
    print(f"All {len(office.agents)} agent(s) reset to idle.")


def main():
    parser = argparse.ArgumentParser(prog="star-office", description="Star Office CLI")
    parser.add_argument("--store", default=DEFAULT_STORE, help="State file path")
    sub = parser.add_subparsers(dest="command")

    # add
    p = sub.add_parser("add", help="Add a new agent")
    p.add_argument("id", help="Agent ID")
    p.add_argument("name", help="Display name")
    p.add_argument("--ttl", type=int, default=300, help="TTL in seconds (default: 300)")

    # remove
    p = sub.add_parser("remove", help="Remove an agent")
    p.add_argument("id", help="Agent ID")

    # set
    p = sub.add_parser("set", help="Set agent state")
    p.add_argument("id", help="Agent ID")
    p.add_argument("state", help="State: idle, writing, researching, executing, syncing, error")
    p.add_argument("message", nargs="?", default="", help="Optional status message")

    # list
    sub.add_parser("list", help="List all agents")

    # status
    p = sub.add_parser("status", help="Show single agent details")
    p.add_argument("id", help="Agent ID")

    # reset
    sub.add_parser("reset", help="Reset all agents to idle")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    try:
        {
            "add": cmd_add,
            "remove": cmd_remove,
            "set": cmd_set,
            "list": cmd_list,
            "status": cmd_status,
            "reset": cmd_reset,
        }[args.command](args)
    except (ValueError, KeyError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

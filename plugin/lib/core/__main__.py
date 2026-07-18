"""Contract CLI - the only supported write path for item status and approvals.

Never edit brain frontmatter directly; skills and humans both go through
this entry point, which routes every write through the same contract checks
(legal transitions, recorded approvals) the executor gates rely on.

Usage (PYTHONPATH must point at the plugin's lib/ directory):
    python3 -m core approve <item-path> --actor NAME --channel CH [--note TEXT]
    python3 -m core reject  <item-path> --actor NAME --channel CH [--note TEXT]
    python3 -m core status  <item-path> <new-status> --actor NAME [--note TEXT]

Prints the resulting status line on success. A refused write (illegal
transition, missing item) exits nonzero with the ContractError message on
stderr.

`approve` also re-confirms an expired approval: when a gate blocks because
the latest approved record is older than the site TTL (approvals.ttl_days
in site-profile.yaml, default 30), running `approve` on the same item
appends a fresh approval entry and the gates open again. The item's status
never changes on expiry - expiry means re-confirm, not rejection.
"""
import argparse
import sys
from pathlib import Path

from . import approval as A
from . import contracts as C


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python3 -m core",
        description="Record item decisions and status changes through the contracts.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name, help_text in (
            ("approve", "record an approval (also re-confirms an expired one)"),
            ("reject", "record a rejection")):
        p = sub.add_parser(name, help=help_text)
        p.add_argument("item_path", help="path to the brief/proposal .md file")
        p.add_argument("--actor", required=True)
        p.add_argument("--channel", required=True)
        p.add_argument("--note", default=None)
    p = sub.add_parser("status", help="move an item to a new lifecycle status")
    p.add_argument("item_path", help="path to the brief/proposal .md file")
    p.add_argument("new_status")
    p.add_argument("--actor", required=True)
    p.add_argument("--channel", default=None)
    p.add_argument("--note", default=None)
    return parser


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)
    path = Path(args.item_path)
    root = path.resolve().parent.parent  # items live at <root>/{briefs,proposals}/
    try:
        if args.cmd in ("approve", "reject"):
            item_id = C.load_item(path)["meta"]["id"]
            A.record_decision(root, item_id,
                              "approved" if args.cmd == "approve" else "rejected",
                              actor=args.actor, channel=args.channel,
                              note=args.note)
        else:
            C.set_status(path, args.new_status, actor=args.actor,
                         channel=args.channel, note=args.note)
            C.rebuild_queue(root)
        meta = C.load_item(path)["meta"]
        print(f"{meta['id']}: {meta['status']}")
        return 0
    except C.ContractError as e:
        print(str(e), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

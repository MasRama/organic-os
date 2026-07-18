"""Channel-neutral approval operations over the brain repo."""
from pathlib import Path
from . import contracts as C


def pending(root):
    items = []
    for folder in ("briefs", "proposals"):
        for f in sorted((Path(root) / folder).glob("*.md")):
            item = C.load_item(f)
            if item["meta"]["status"] == "proposed":
                item["path"] = f
                items.append(item)
    return items


def find(root, item_id: str):
    for folder in ("briefs", "proposals"):
        for f in (Path(root) / folder).glob("*.md"):
            if C.load_item(f)["meta"]["id"] == item_id:
                return f
    raise C.ContractError(f"no item {item_id}")


def record_decision(root, item_id: str, decision: str, actor: str, channel: str) -> None:
    C.set_status(find(root, item_id), decision, actor=actor, channel=channel)
    C.rebuild_queue(root)

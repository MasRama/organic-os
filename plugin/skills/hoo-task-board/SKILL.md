---
name: hoo-task-board
description: Use to view or mirror the work queue - "task board", "show the queue", /organic-os:task-board. Mirrors to Notion when that connector exists; local queue.md is the source of truth.
---

# Task board

1. Rebuild queue (`core.contracts.rebuild_queue`) and show pending items,
   in-flight items (approved/drafted/partially-applied - the last with its
   human-follow-up note, mirrored from the queue's PARTIAL rows), and
   recently completed (published/measured, last 14 days).
2. If the Notion connector is available and site-profile connectors.notion is
   "available": upsert a page per item into the "organic-os board" database
   (create it on first run: properties Status, Kind, Target, Created, ItemId).
   One-way mirror: repo -> Notion. Approvals never flow back through Notion.
3. Without Notion: print the board and stop. No degradation warnings needed;
   the local board IS the product.

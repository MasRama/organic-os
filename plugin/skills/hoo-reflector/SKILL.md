---
name: hoo-reflector
description: Use to distill lessons from recent signals and outcomes - "run the reflector", weekly routine step 4, or "what did we learn". Proposes skillbook deltas; the curator merge is gated.
---

# Reflector (weekly) - propose deltas, never write directly

1. Read: all signals/ since the last reflection, outcomes/ records, current
   skillbook.md, the last reflections/ file.
2. Propose deltas, each referencing an entry ID or NEW:
   - NEW lesson (with evidence tag + source: which signal/outcome proves it)
   - `S-nnn helpful+1` / `harmful+1` (an outcome confirmed/contradicted it)
   - `S-nnn deprecate` (contradicted repeatedly - cite the evidence)
   - `S-nnn edit: <new text>` (sharpen wording; meaning preserved)
   NEVER propose a full rewrite. NEVER propose deleting lines.
3. Write reflections/YYYY-Www.md listing every delta + evidence.
4. Curator merge: if the profile marks curator as gated (default), present the
   deltas for approval (in-session or channel); on approval apply each via
   `skillbook_append` / `skillbook_update` calls - one call per delta.
5. Commit "reflection: YYYY-Www" if git.

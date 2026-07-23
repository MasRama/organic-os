# Reproducing our own results

Every claim organic-os makes about a site is a number in a file you own.
This page is how anyone recomputes one, including someone who does not
trust the tool that wrote it. You do not need the plugin, an account, or
our cooperation to do it: the raw data is in your Search Console property
and the windows are named in the record.

The posture is borrowed from [gstack](https://github.com/garrytan/gstack),
which ships the script that reproduces its results instead of asking a
reader to take the result on faith. Applied here, it means our claims come
with the windows they were measured over and a command that recomputes
them.

## What a claim looks like

When organic-os applies an approved change, it writes a record in the
brain repo at `outcomes/<item-id>.md`: what changed, the URL, when it was
applied, the measurement windows, and later the before/after numbers and
the delta. That record is the claim. It is plain markdown in your git
repo, readable without the plugin, and its history is the repo's history.

## Option 1: run the check

```
/organic-os:verify-outcome <item-slug>
```

The skill (`plugin/skills/hoo-verify-outcome`) reads only the item
identity, the URL, and the windows from the record, pulls those windows
fresh from the configured search-data and analytics connectors, computes
the delta from what it pulled, and compares that against the claimed
numbers last. Reading the claim first would make the recomputation
worthless, so the order is fixed. The run report lands in
`runs/<UTCdate>-verify-outcome/REPORT.md` with the raw pulls, the
recomputed delta, the claim, and the comparison side by side.

If the connectors are unreachable, it reports the claim as unverified. It
does not fall back to the numbers already in the brain: checking a claim
against the same run that produced it verifies nothing.

## Option 2: do it by hand in Search Console

No plugin involved. Ten minutes with the record open.

1. Open the record. Note the URL, the before window, and the after
   window. If the record has no `windows` block, the applied date plus 28
   days each way is the default the tooling uses.
2. In Search Console, open Performance, then Search results.
3. Filter by page, exact URL, set to the record's URL.
4. Set the date range to the before window. Note clicks, impressions,
   CTR, and average position.
5. Set the date range to the after window. Note the same four.
6. Subtract. That is the delta the record should be claiming.

A difference under a few percent is rounding, a partial day, or the two
to three day reporting lag. A difference of tens of percent is not, and
we want to hear about it: open an issue with the record and both sets of
numbers.

## What this proves, and what it does not

Reproducing a result proves the claim is consistent with the data. That
is the whole of it.

- **It does not prove the change caused the move.** Nothing in a
  before/after comparison can. Seasonality, an algorithm update, a
  competitor's change, a link that landed the same week, and the site's
  own trend all sit inside the same window. organic-os states this in
  every outcome it writes: where no comparison against the site-wide
  trend was run, the record reads `cause: unknown` and keeps the number.
  A measured number with an honest unknown is worth more than a confident
  story nobody checked.
- **It does not make the connector's data ground truth.** Search Console
  drops queries below a privacy threshold, averages position across
  every impression including ones far down page two, and revises recent
  days. Two people pulling the same window on different days can get
  slightly different numbers. That is a property of the source, not of
  the record.
- **It cannot recover a window that has aged out.** Search Console keeps
  16 months. A claim older than that is not reproducible from the source
  any more, and we would rather say so than point at a cached copy of our
  own working.
- **Agreement is not endorsement of the tactic.** That a title rewrite
  moved a page is one site, once. Whether the tactic generalizes is what
  `plugin/docs/evidence.md` tracks, with the evidence tier stated.

## Why the claims stay checkable

The brain is your git repo, so a claim cannot be edited after the fact
without the edit appearing in the history. Nothing is stored on a server
we control, because there is no server. The verification path reads the
same public connector you can read yourself. None of that makes the tool
trustworthy on its own, and it is not meant to: it makes the tool
checkable, which is the part we can actually offer.

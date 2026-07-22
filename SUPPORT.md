# Getting help

organic-os is a young open-source project maintained in the open. Here is
where to go, fastest path first.

## Start with the docs

Most questions are answered in the shipped docs:

- [Getting started](plugin/docs/getting-started.md) - install, first run, the
  audit-first setup flow.
- [Connectors](plugin/docs/connectors.md) - GA4, GSC, and the rest, and why
  organic-os cannot trigger an OAuth prompt itself.
- [Routines and runtimes](plugin/docs/routines.md) - scheduling the daily,
  weekly, and monthly loops.
- [Updating](plugin/docs/updating.md) - what an update touches and what it
  cannot, and what to do when an update reports success but the running
  version does not change.
- [README](README.md) - the overview, the three modules, and the FAQ.

## Ask in Discussions

If the docs did not settle it and you are not sure it is a bug, ask in
[Discussions](https://github.com/shalintripathi/organic-os/discussions):

- [Q&A](https://github.com/shalintripathi/organic-os/discussions/categories/q-a)
  - you are stuck or want to check whether you set something up correctly.
  Answers stay searchable for the next person.
- [Ideas](https://github.com/shalintripathi/organic-os/discussions/categories/ideas)
  - a capability that does not exist yet. Check
  [ROADMAP.md](ROADMAP.md) first, including what this project deliberately
  will not build.
- [Show and tell](https://github.com/shalintripathi/organic-os/discussions/categories/show-and-tell)
  - you ran it on a real site. Results that did not move are as useful to
  post as results that did.

## Open an issue

If you have a reproducible bug or a concrete request, skip the discussion and
open an issue with the right form:

- **Bug report** - something worked differently than documented.
- **Feature request** - a capability you want, or a reprioritization of the
  roadmap. Both are welcome.
- **Setup help** - stuck installing, connecting, or configuring.

The forms ask for the few details needed to help you without a round trip.

## Collect the details in one step

`/organic-os:diagnose` prints your runtime, the plugin version, the brain's
schema version, connector statuses and where each was probed, the last setup
scorecard, and the last routine outcome. It PRINTS that report and nothing
else: it never transmits, uploads, or files anything, credentials appear only
as present or absent, and paths are shown in their `~/organic-hq/<slug>`
shape rather than as your real home directory. You read it, cut anything you
would rather not share, and paste what is left into the issue. See
[the skill](plugin/skills/diagnose/SKILL.md) for exactly what it gathers.

## How this project reads its own signals

There is no telemetry in organic-os and there will not be
([THREAT-MODEL.md](THREAT-MODEL.md)), so the maintainer sees only what
GitHub itself reports and what you choose to say:

- **GitHub's own traffic API** - clone counts, unique visitors, and referrer
  sources for the repository, aggregated by GitHub and visible to the
  maintainer for a rolling two-week window. No code in this project produces
  any of it.
- **Issues and Discussions themselves** - what people actually ask, in their
  own words.

That is the whole feedback loop. If something is broken and you say nothing,
nothing here will tell us.

## What to expect

This is a solo-maintained project, so treat every response time as best
effort, not a commitment. There is no SLA, no paid support tier, and no
guarantee of a fix on any timeline. A clear repro (bug reports) or a concrete
use case (feature requests) is the single biggest thing that moves an issue
forward. Issues that fit the project's scope get a maintainer read; ones that
do not get an honest note saying so rather than silence, per
[CONTRIBUTING.md](CONTRIBUTING.md).

## Security issues

Do not open a public issue for a security or credential-handling problem.
Follow [SECURITY.md](SECURITY.md): open a private security advisory on the
repository and keep any secret value out of the report.

## Be kind

All of the above happens under our [Code of Conduct](CODE_OF_CONDUCT.md).

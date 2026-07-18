# WordPress credentials setup

This doc covers how to connect organic-os to a WordPress site: the dedicated
user, the Application Password, the RankMath plugin, the REST bridge that
exposes RankMath fields to the API, and a verification step. Follow the
sections in order; each one depends on the previous.

## 1. Create a dedicated Editor user

Do not connect organic-os with an Administrator account. Create a separate
WordPress user named `organic-agent` with the Editor role. Editor is enough
to create and update posts and their meta; it cannot install plugins, change
site settings, or manage other users, so a leaked Application Password stays
contained.

## 2. Generate an Application Password

In wp-admin, go to Users -> Profile (for the `organic-agent` user) ->
Application Passwords, name the new password (for example `organic-os`), and
click Add New Application Password. WordPress shows the password once; copy
it immediately.

Store it using the standard organic-os credential pattern: one env file per
site at `~/.config/organic-os/<site>.env`, containing at minimum:

```
WP_ENDPOINT=https://SITE/wp-json
WP_USERNAME=organic-agent
WP_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx
```

Lock the file down so only the owner can read it:

```
chmod 600 ~/.config/organic-os/<site>.env
```

Never commit this file or paste the password into the repo, chat, or logs.

## 3. Install RankMath

Install and activate the free RankMath SEO plugin on the target WordPress
site. RankMath is what owns the on-page SEO fields (title, description,
canonical, focus keyword) that organic-os reads and writes.

## 4. Install the bridge

RankMath's SEO meta fields are not exposed to the REST API by default. Pick
one of two ways to expose them:

- Copy `playground/wp-extras/organic-os-bridge.php` from this repo to
  `wp-content/mu-plugins/` on the target site. Must-use plugins load
  automatically with no activation step. Do this with either a one-line
  `wp eval` command run through WP-CLI, or a plain SFTP upload of the file
  into that directory.
- Or install Devora's `rank-math-api-manager` plugin from the WordPress
  plugin directory, which exposes the same fields without a custom file.

Either path achieves the same result: `rank_math_title`,
`rank_math_description`, `rank_math_canonical_url`, `rank_math_focus_keyword`,
and `agent_jsonld` become readable and writable through
`wp-json/wp/v2/posts/<id>`.

## 5. Enable RankMath Headless CMS Support

In RankMath's settings, turn on Headless CMS Support. This adds the
`rankmath/v1/getHead` REST route, which returns the fully rendered `<head>`
for a given URL. organic-os uses this route as the source of truth for
verifying that a write actually took effect, since it reflects RankMath's
final output rather than the raw meta value.

## 6. Verify

Confirm the connection works with a direct curl call using the Application
Password from step 2:

```
curl -u 'organic-agent:APP_PASSWORD' 'https://SITE/wp-json/wp/v2/posts?per_page=1&context=edit'
```

The URL must stay single-quoted: an unquoted `&` makes the shell background
the command and drop `context=edit`.

A working setup returns JSON for one post that includes a `meta` object
containing `rank_math_title`. If `meta` is missing or empty, recheck step 4
(the bridge plugin or api-manager plugin is not active) before troubleshooting
anything else.

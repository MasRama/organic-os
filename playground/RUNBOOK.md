# Playground deployment runbook

This is the reference runbook for standing up the live organic-os demo at
`playground.shivaatripathi.com`. It is built by a separate WordPress
session working from spec §10, on `hq-fsn1-01` per the locked personal-infra
stack (Hetzner FSN1 + Ubuntu + Caddy + Cloudflare). The organic-os build
itself does not depend on this deployment existing; it only needs the
resulting WordPress endpoint and an Application Password once the
playground session hands them off (see `plugin/docs/credentials/wordpress.md`).

The files this runbook deploys - `docker-compose.yml`, `uploads.ini`,
`Caddyfile.snippet`, `wp-extras/organic-os-bridge.php` - live in this
directory and stay in sync with spec §10. Copy them to the host; do not
hand-retype them.

## Deploy steps

1. **DNS.** Add an A record for `playground.shivaatripathi.com` pointing at
   the `hq-fsn1-01` host, proxied through Cloudflare (orange cloud), same
   pattern as every other domain on that box.

2. **Copy the compose stack to the host.**
   ```
   scp -r playground/ hq-fsn1-01:/opt/playground
   ```
   The `wp-extras/` directory (containing `organic-os-bridge.php`) travels
   with it - it gets bind-mounted straight into `wp-content/mu-plugins/`.

3. **Bring the stack up.** Generate a strong random password once and reuse
   it for every subsequent compose invocation on this host:
   ```
   cd /opt/playground
   DB_PASSWORD=$(openssl rand -base64 24) docker compose up -d
   echo "DB_PASSWORD=$DB_PASSWORD" >> .env   # keep out of git; .env stays local to the host
   ```

4. **Add the Caddy block and reload.** Append the contents of
   `Caddyfile.snippet` to the host's Caddyfile, then:
   ```
   caddy reload --config /etc/caddy/Caddyfile
   ```
   Caddy sets `X-Forwarded-Proto` and the official WordPress image consumes
   it, so there is no redirect loop behind Cloudflare's Full (strict) mode.

5. **Install WordPress core.**
   ```
   docker compose run --rm wp-cli core install \
     --url=https://playground.shivaatripathi.com \
     --title="organic-os playground" \
     --admin_user=<admin-user> \
     --admin_password=<generated> \
     --admin_email=<owner-email>
   ```
   Use the default theme (Twenty Twenty-Five); no custom theme is part of
   the demo.

6. **Install and configure RankMath.**
   ```
   docker compose run --rm wp-cli plugin install seo-by-rank-math --activate
   ```
   In RankMath's settings, turn on Headless CMS Support (this adds the
   `rankmath/v1/getHead` route organic-os uses for write verification - see
   `plugin/docs/credentials/wordpress.md` step 5).

7. **Confirm the bridge mu-plugin loaded.** `organic-os-bridge.php` is
   already mounted into `wp-content/mu-plugins/` by the compose file (step
   2-3); must-use plugins need no activation step. Confirm it loaded:
   ```
   docker compose run --rm wp-cli plugin list --status=must-use
   ```

8. **Create the dedicated agent user and Application Password.**
   ```
   docker compose run --rm wp-cli user create organic-agent agent@example.invalid --role=editor
   docker compose run --rm wp-cli user application-password create organic-agent organic-os
   ```
   Store the endpoint, username, and printed password in
   `~/.config/organic-os/playground.env` per
   `plugin/docs/credentials/wordpress.md` step 2. Never commit this file.

9. **Seed content.** Create 4-6 posts covering a spread of topics so agents
   have real material to audit and propose against:
   ```
   docker compose run --rm wp-cli post generate --count=6 --post_status=publish
   ```
   Replace generated placeholder content with real seed posts if better
   demo material is available; generated posts are a placeholder floor, not
   the final state.

10. **Wire WordPress cron via the host, not the request cycle.**
    `DISABLE_WP_CRON` is set in the compose file's `WORDPRESS_CONFIG_EXTRA`,
    so add a host crontab entry to drive it explicitly:
    ```
    */15 * * * * cd /opt/playground && docker compose run --rm wp-cli cron event run --due-now
    ```

11. **Search Console and Analytics.** Verify the property in Google Search
    Console (HTML tag or DNS verification), submit the sitemap
    (`https://playground.shivaatripathi.com/sitemap_index.xml`, RankMath's
    default), and create a GA4 property for the domain. These feed
    `plugin/docs/credentials/gsc-ga4.md`'s connector path once authorized.

## Verification checklist

Run every check below before handing the endpoint back to the organic-os
build. All must pass.

- [ ] `https://playground.shivaatripathi.com` loads over HTTPS with a valid
      certificate and no redirect loop.
- [ ] REST auth works with the app password, using the exact curl from
      `plugin/docs/credentials/wordpress.md` step 6:
      ```
      curl -u 'organic-agent:APP_PASSWORD' 'https://playground.shivaatripathi.com/wp-json/wp/v2/posts?per_page=1&context=edit'
      ```
      and the response's `meta` object contains `rank_math_title`.
- [ ] `rankmath/v1/getHead` returns a populated head for a real post URL:
      ```
      curl 'https://playground.shivaatripathi.com/wp-json/rankmath/v1/getHead?url=https%3A%2F%2Fplayground.shivaatripathi.com%2F%3Fp%3D1'
      ```
- [ ] WordPress Site Health (Tools -> Site Health -> Status) shows no
      loopback-request failure - a failing loopback check breaks WP-Cron
      and some REST-to-REST calls, and is worth fixing before declaring the
      playground ready rather than discovering it mid-demo.
- [ ] The host crontab entry from step 10 is present and has run at least
      once (`docker compose run --rm wp-cli cron event list` shows recent
      activity, not a backlog).

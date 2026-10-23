# Documate

Electronic contract signing for Dollar Loanz, served at **https://documate.dontgetbroke.com**.

Documate is a rebranded build of the open-source [Documenso](https://github.com/documenso/documenso) Community
Edition. This repository holds everything needed to rebuild the exact image that runs in production: the pinned
upstream release, the rebrand script, the brand assets and the build pipeline.

## Licence and source (AGPL-3.0)

Documenso is © Documenso, Inc. and licensed under the GNU Affero General Public License v3. Documate is a modified
version and is distributed under the same licence (see [LICENSE](LICENSE)). The complete corresponding source of the
running service is this repository at the commit named in the image label `org.opencontainers.image.revision`,
together with the upstream commit pinned in [UPSTREAM](UPSTREAM). The app links here from its footer and signing
badge. Code under upstream `packages/ee` is covered by Documenso's commercial licence; the rebrand never modifies it.

## What the rebrand changes

| Area | Change |
|---|---|
| Name | Every user-visible "Documenso" in the app, emails, PDFs, page titles, translations (12 languages) → Documate |
| Logo | Documate mark + wordmark (same family as Chatmate) in the header, signing pages, emails, PDF certificate |
| Colours | Documenso lime → Documate teal (`#0D9488`), light and dark themes, field cards, Tailwind palette |
| Icons | Favicons, Apple/Android icons, PWA manifest, social preview, share card, sign-in background |
| Links | documenso.com links, docs links and sample addresses → this repository / `example.com` |
| Signer pages | "Check out Documenso" promo removed; "Powered by" badge links to this source |
| Emails | Documenso, Inc. postal address removed from footers; support address → contracts@dollarloanz.com |
| Privacy | Pages served `noindex, nofollow`; `robots.txt` disallows everything; own `security.txt` |
| One sign-in | Staff are signed in with the identity Cloudflare Access already verified (`Cf-Access-Jwt-Assertion`, checked against the team's keys, issuer, app audience and expiry; `DOCUMATE_CF_ACCESS_TEAM_DOMAIN` + `DOCUMATE_CF_ACCESS_AUD`); "Sign out" ends the Access session |
| Sign-in fallback | OIDC logins without a `name` claim (Cloudflare Access one-time PIN) get a name from the profile or email instead of failing; `NEXT_PRIVATE_OIDC_PROMPT=omit` sends no `prompt`, so Access reuses the session from the front door instead of asking for another code |

Kept on purpose (wire-level names other systems depend on): `X-Documenso-*` webhook/email headers, the
`recipient.N@documenso.com` template placeholders, the licence-server URL, seeded service-account emails and code
identifiers such as `@documenso/*` package names.

## Build

```sh
bash build.sh                               # -> documate:local
IMAGE=ghcr.io/myklwcs/documate:dev bash build.sh
```

`build.sh` clones the upstream tag in `UPSTREAM`, refuses if the tag no longer points at the pinned commit, runs
`rebrand.py` in a pinned Alpine container, builds with upstream's own `docker/Dockerfile`, then fails if the shipped
client bundle still mentions Documenso. GitHub Actions runs the same script on every push to `main`, then
`test/oidc-no-name.sh` (staff sign-in through a provider that, like Cloudflare Access, sends no name) and
`test/cloudflare-access.sh` (one sign-in with the Access identity token), and only then
publishes `ghcr.io/myklwcs/documate:<commit>` and `:<upstream-tag>`.

To move to a newer Documenso release: change `UPSTREAM`, push, and fix whatever `rebrand.py` reports — every edit
asserts its match count, so a changed upstream file fails the build instead of shipping half-branded.

Brand assets: `brand/gen.py` is the single source of the mark, wordmark and colour tokens. The build runs it (with
fontTools and Inter Display Bold in the pinned Alpine container) to write the SVGs and the two React logo components,
then renders every PNG/ICO/JPG from those SVGs.

## Deploy

See [deploy/README.md](deploy/README.md).

## Documentation

Product and API documentation for the underlying platform: <https://docs.documenso.com>. Documate's API is the
same API at `https://documate.dontgetbroke.com/api/v2`.

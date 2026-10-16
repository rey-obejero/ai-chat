# ADR-0051: External images in replies are fetched through the application's own proxy

- **Status:** Accepted
- **Date:** 2026-10-17
- **Deciders:** Rey Obejero
- **Supersedes:** —
- **Superseded by:** —

## TL;DR

An image in a rendered reply is embedded through `GET /api/v1/media/image`, which
fetches it server-side under SSRF guards and streams it back, so the reader's
browser never contacts the third-party origin.

## Context

A reply can contain `![alt](https://somewhere/x.png)`. Rendering that as a plain
`<img src>` makes the reader's browser fetch the third party directly, which
leaks the reader's IP, User-Agent, and referring URL to that origin, and lets a
reply probe addresses reachable only from the reader's network. GitHub's Camo and
Gmail's image proxy both avoid this by fetching server-side; rendering external
images as links instead is not the industry pattern.

## Decision

Add a `media` slice exposing `GET /api/v1/media/image?url=<percent-encoded
absolute URL>`, authenticated (never public), guarded in this order:

1. parse and require `http`/`https`;
2. reject literal private, loopback, link-local, multicast, and cloud-metadata
   addresses (normalising IPv4-mapped IPv6 so `::ffff:10.0.0.1` cannot slip by);
3. resolve DNS and reject any private address in the answer;
4. connect to the validated IP with the original `Host` header (pinning defeats
   DNS rebinding);
5. follow at most `media_max_redirects` (4) redirects, re-running every check per
   hop;
6. require an image content type (png, jpeg, gif, webp);
7. stream with a `media_max_bytes` (5 MB) cap, applied to the decoded body, and
   abort past it;
8. cache in-process (64 MB, 24 h, keyed by URL) and serve with a forced validated
   `Content-Type`, `X-Content-Type-Options: nosniff`, and `Cache-Control:
   private, max-age=86400`.

The fetch client holds no cookies or credentials, uses a 10 s timeout, and
disables automatic redirects so each hop is re-validated. Any failure returns
502 with no body; the `<img>` shows its alt text and the transcript never breaks.
The markdown image rule drops every non-http(s) source, including `data:` URIs.
`media_proxy_enabled=false` removes the route (404).

## Consequences

- **Easier:** the reader's browser never talks to the third party; a `<img>` can
  be rendered directly with no client-side signing or CSP exception.
- **Harder:** the app now makes outbound requests on a user's behalf, so the
  guard list is security-critical code with its own tests.
- **We now live with:** an in-process, single-process cache; no SVG support (not
  in the content-type allowlist); and a response that is only as trustworthy as
  the guards — a compromise of the API host could still reach internal networks,
  which the guards bound but do not eliminate.

## Alternatives considered

- **Linkify external images** — leaks the reader to the third party; not the
  industry pattern.
- **Client-side signing (Camo-style URL HMAC)** — the reader's browser still
  fetches; a shared secret in the front-end does not exist by design.
- **Allow SVG** — SVG can carry script; excluded from the allowlist.
- **No cache** — re-fetches every view, and re-exposes the origin to load
  tracking.
- **A dedicated image proxy service** — more infrastructure than a single-origin
  app needs; the in-process slice is proportionate at this scale.

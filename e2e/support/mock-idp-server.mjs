// A minimal, standards-shaped OIDC provider for end-to-end tests.
//
// It is a real implementation of the parts that matter to the flow — discovery,
// a JWKS document, an RS256-signed id_token, and a token exchange — so the
// SuperTokens SDK performs real discovery and real signature verification
// rather than being stubbed past them (ADR-0033). It is deliberately not an
// interactive login UI: /authorize issues a code immediately, which is what
// makes the suite deterministic.
//
// Specs steer it through /_control before starting a sign-in:
//   POST /_control { email, emailVerified, behaviour }
// where `behaviour` is one of:
//   "ok"      (default) — sign in with `email`
//   "no_email"          — succeed but share no email address
//   "cancelled"         — return to the app as if consent was refused
//
// It uses only Node built-ins (no new dependency).
import { createHash, createSign, generateKeyPairSync, randomUUID } from "node:crypto";
import { createServer } from "node:http";

const port = Number(process.env.MOCK_IDP_PORT ?? 4011);
const issuer = process.env.MOCK_IDP_ISSUER ?? `http://localhost:${port}`;

const CLIENT_ID = process.env.MOCK_IDP_CLIENT_ID ?? "test-idp-client";
const CLIENT_SECRET = process.env.MOCK_IDP_CLIENT_SECRET ?? "test-idp-secret";

const { privateKey, publicKey } = generateKeyPairSync("rsa", { modulusLength: 2048 });
const jwk = publicKey.export({ format: "jwk" });
const kid = "e2e-key";

// Authorization codes and the access tokens they are exchanged for. Both map to
// the subject the provider settled on, which /userinfo echoes back.
const codes = new Map();
const tokens = new Map();

let control = { email: "social@example.com", emailVerified: true, behaviour: "ok" };

function base64url(input) {
  return Buffer.from(input).toString("base64url");
}

// A stable subject per email, so signing in twice as the same address is the
// same identity — as a real provider would report.
function subjectFor(email) {
  return `idp-${createHash("sha256").update(email).digest("hex").slice(0, 16)}`;
}

function signIdToken({ sub, email, emailVerified }) {
  const header = base64url(JSON.stringify({ alg: "RS256", typ: "JWT", kid }));
  const payload = { sub, aud: CLIENT_ID, iat: 0, exp: 4102444800 };
  if (email !== undefined) {
    payload.email = email;
    payload.email_verified = emailVerified;
  }
  const body = `${header}.${base64url(JSON.stringify(payload))}`;
  const signature = createSign("RSA-SHA256").update(body).sign(privateKey, "base64url");
  return `${body}.${signature}`;
}

function json(response, status, body) {
  const payload = JSON.stringify(body);
  response.writeHead(status, {
    "content-type": "application/json",
    "content-length": Buffer.byteLength(payload),
  });
  response.end(payload);
}

async function readBody(request) {
  let body = "";
  for await (const chunk of request) {
    body += chunk;
  }
  return body;
}

const server = createServer(async (request, response) => {
  const url = new URL(request.url, issuer);

  if (request.method === "GET" && url.pathname === "/health") {
    json(response, 200, { status: "ok" });
    return;
  }

  if (request.method === "POST" && url.pathname === "/_control") {
    control = { ...control, ...JSON.parse((await readBody(request)) || "{}") };
    json(response, 200, { status: "ok" });
    return;
  }

  if (request.method === "GET" && url.pathname === "/.well-known/openid-configuration") {
    json(response, 200, {
      issuer,
      authorization_endpoint: `${issuer}/authorize`,
      token_endpoint: `${issuer}/token`,
      userinfo_endpoint: `${issuer}/userinfo`,
      jwks_uri: `${issuer}/jwks`,
      response_types_supported: ["code"],
      subject_types_supported: ["public"],
      id_token_signing_alg_values_supported: ["RS256"],
      scopes_supported: ["openid", "email"],
    });
    return;
  }

  if (request.method === "GET" && url.pathname === "/jwks") {
    json(response, 200, { keys: [{ ...jwk, kid, use: "sig", alg: "RS256" }] });
    return;
  }

  if (request.method === "GET" && url.pathname === "/authorize") {
    const redirectUri = url.searchParams.get("redirect_uri");
    const state = url.searchParams.get("state") ?? "";
    if (!redirectUri) {
      json(response, 400, { error: "invalid_request" });
      return;
    }

    const target = new URL(redirectUri);
    target.searchParams.set("state", state);
    if (control.behaviour === "cancelled") {
      target.searchParams.set("error", "access_denied");
      response.writeHead(302, { location: target.toString() });
      response.end();
      return;
    }

    const code = randomUUID();
    codes.set(code, { sub: subjectFor(control.email) });
    target.searchParams.set("code", code);
    response.writeHead(302, { location: target.toString() });
    response.end();
    return;
  }

  if (request.method === "POST" && url.pathname === "/token") {
    const params = new URLSearchParams(await readBody(request));
    if (params.get("client_id") !== CLIENT_ID || params.get("client_secret") !== CLIENT_SECRET) {
      json(response, 401, { error: "invalid_client" });
      return;
    }

    const code = params.get("code");
    const entry = code ? codes.get(code) : undefined;
    if (!entry) {
      json(response, 400, { error: "invalid_grant" });
      return;
    }
    codes.delete(code);

    const accessToken = `access-${randomUUID()}`;
    tokens.set(accessToken, entry);
    json(response, 200, {
      access_token: accessToken,
      token_type: "Bearer",
      expires_in: 3600,
      id_token: signIdToken({
        sub: entry.sub,
        email: control.behaviour === "no_email" ? undefined : control.email,
        emailVerified: control.emailVerified,
      }),
    });
    return;
  }

  if (request.method === "GET" && url.pathname === "/userinfo") {
    const token = (request.headers.authorization ?? "").replace(/^Bearer\s+/i, "");
    const entry = tokens.get(token);
    if (!entry) {
      json(response, 401, { error: "invalid_token" });
      return;
    }

    const body = { sub: entry.sub };
    if (control.behaviour !== "no_email") {
      body.email = control.email;
      body.email_verified = control.emailVerified;
    }
    json(response, 200, body);
    return;
  }

  json(response, 404, { error: "not_found" });
});

server.listen(port, () => {
  console.log(`mock idp listening on ${issuer}`);
});

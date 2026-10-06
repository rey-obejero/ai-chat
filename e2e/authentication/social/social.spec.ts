import { randomUUID } from "node:crypto";

import { expect, test } from "../fixtures";
import { seedUser } from "../support/test-user";

// The specs share one mock identity provider whose behaviour is set through a
// control endpoint, so they must not overlap — two running at once would race
// the control. `serial` keeps them ordered on one worker.
test.describe.configure({ mode: "serial" });

const IDP = process.env.E2E_IDP_BASE_URL ?? "http://localhost:4011";

async function configureIdp(body: Record<string, unknown>): Promise<void> {
  const response = await fetch(`${IDP}/_control`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  expect(response.ok).toBe(true);
}

async function startSocialSignIn(page: import("@playwright/test").Page): Promise<void> {
  await page.goto("/authentication/sign-in");
  await page.getByRole("button", { name: "Continue with Test" }).click();
}

// Read `/me` from inside the page so the request carries the browser's session
// cookies and goes through the same origin as the app.
async function currentUser(page: import("@playwright/test").Page) {
  const result = await page.evaluate(async () => {
    const response = await fetch("/api/v1/me");
    return { status: response.status, body: await response.text() };
  });
  expect(result.status, result.body).toBe(200);
  return JSON.parse(result.body) as { id: string; email: string };
}

test("signs in through the provider and creates the account", async ({ page }) => {
  const email = `social-${randomUUID()}@example.com`;
  await configureIdp({ email, behaviour: "ok", emailVerified: true });

  await startSocialSignIn(page);

  await expect(page).toHaveURL(/\/application\/conversations$/);

  expect((await currentUser(page)).email).toBe(email);
});

test("a second sign-in reuses the same account rather than duplicating it", async ({ page }) => {
  const email = `social-${randomUUID()}@example.com`;
  await configureIdp({ email, behaviour: "ok", emailVerified: true });

  await startSocialSignIn(page);
  await expect(page).toHaveURL(/\/application\/conversations$/);
  const first = (await currentUser(page)).id;

  await page.evaluate(() => fetch("/api/auth/signout", { method: "POST" }));
  await startSocialSignIn(page);
  await expect(page).toHaveURL(/\/application\/conversations$/);
  const second = (await currentUser(page)).id;

  expect(second).toBe(first);
});

test("reports when the provider shares no email", async ({ page }) => {
  await configureIdp({ email: `social-${randomUUID()}@example.com`, behaviour: "no_email" });

  await startSocialSignIn(page);

  await expect(page).toHaveURL(/\/authentication\/callback/);
  await expect(page.getByText(/did not share an email/i)).toBeVisible();
});

test("refuses to create a second account for an existing email", async ({ page }) => {
  // ADR-0034: a social sign-in presenting an email that already belongs to a
  // password account is refused, and no account is created or merged.
  const existing = await seedUser();
  await configureIdp({ email: existing.email, behaviour: "ok", emailVerified: true });

  await startSocialSignIn(page);

  await expect(page).toHaveURL(/\/authentication\/callback/);
  await expect(page.getByText(/already has an account/i)).toBeVisible();
});

test("returns to the app when the provider refuses consent", async ({ page }) => {
  await configureIdp({ email: `social-${randomUUID()}@example.com`, behaviour: "cancelled" });

  await startSocialSignIn(page);

  // The provider sends the browser back with an error, and the app reports it
  // rather than hanging on the callback.
  await expect(page).toHaveURL(/\/authentication\/callback/);
  await expect(page.getByText(/could not complete the sign-in/i)).toBeVisible();
  await expect(page.getByRole("link", { name: "Back to sign in" })).toBeVisible();
});

test("keeps the destination across the full round trip", async ({ page }) => {
  const email = `social-${randomUUID()}@example.com`;
  await configureIdp({ email, behaviour: "ok", emailVerified: true });

  await page.goto("/authentication/sign-in?redirectTo=/application/conversations/deep-link");
  await page.getByRole("button", { name: "Continue with Test" }).click();

  await expect
    .poll(() => new URL(page.url()).pathname)
    .toBe("/application/conversations/deep-link");
});

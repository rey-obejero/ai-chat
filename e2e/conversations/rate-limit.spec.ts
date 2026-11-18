import { expect, test } from "../authentication/fixtures";
import { SignUpPage } from "../authentication/sign-up/SignUpPage";
import { uniqueEmail } from "../authentication/support/test-user";

const VALID_PASSWORD = "Passw0rd!123";
const BASE_URL = process.env.E2E_BASE_URL ?? "http://localhost:5173";

test("shows the rate-limit copy when the chat request is refused", async ({
  signUpPage,
  page,
  browser,
}) => {
  await signUpPage.goto();
  await signUpPage.signUp(uniqueEmail(), VALID_PASSWORD);

  await page.getByRole("button", { name: "New conversation" }).click();
  await expect(page).toHaveURL(/\/application\/conversations\/[\w-]+$/);

  // The e2e stack runs with rate limiting off, so the refusal is synthesized
  // at the browser boundary. The body mirrors the middleware's problem+json.
  await page.route("**/api/v1/conversations/*/messages", async (route) => {
    if (route.request().method() !== "POST") {
      await route.continue();
      return;
    }
    await route.fulfill({
      status: 429,
      headers: {
        "content-type": "application/problem+json",
        "retry-after": "60",
      },
      body: JSON.stringify({
        type: "about:blank",
        title: "Too Many Requests",
        status: 429,
        detail: "Too many requests.",
        instance: "/api/v1/conversations",
        code: "RATE_LIMITED",
      }),
    });
  });

  await page.getByLabel("Message").fill("Refused by the limiter");
  await page.getByRole("button", { name: "Send" }).click();

  await expect(page.getByRole("alert")).toContainText("Too many messages");

  // The refusal is per browser context: a separate session still talks to the
  // mock provider and renders its reply.
  const secondContext = await browser.newContext({ baseURL: BASE_URL });
  const secondPage = await secondContext.newPage();
  const secondSignUpPage = new SignUpPage(secondPage);
  await secondSignUpPage.goto();
  await secondSignUpPage.signUp(uniqueEmail(), VALID_PASSWORD);

  await secondPage.getByRole("button", { name: "New conversation" }).click();
  await secondPage.getByLabel("Message").fill("Unaffected session");
  await secondPage.getByRole("button", { name: "Send" }).click();
  await expect(
    secondPage.getByRole("log").getByText("Mock reply: Unaffected session", { exact: true }),
  ).toBeVisible();

  await secondContext.close();
});

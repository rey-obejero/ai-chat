import { expect, test } from "../authentication/fixtures";
import { SignUpPage } from "../authentication/sign-up/SignUpPage";
import { uniqueEmail } from "../authentication/support/test-user";

const VALID_PASSWORD = "Passw0rd!123";

async function signUpFreshAccount(signUpPage: SignUpPage): Promise<void> {
  await signUpPage.goto();
  await signUpPage.signUp(uniqueEmail(), VALID_PASSWORD);
}

test("sends a message and renders the streamed reply", async ({ signUpPage, page }) => {
  await signUpFreshAccount(signUpPage);

  await page.getByRole("button", { name: "New conversation" }).click();
  await expect(page).toHaveURL(/\/application\/conversations\/[\w-]+$/);

  await page.getByLabel("Message").fill("Hello from e2e");
  await page.getByRole("button", { name: "Send" }).click();

  // The header shows the conversation title, which is the first user message, so
  // assertions are scoped to the transcript rather than to the whole page.
  const transcript = page.getByRole("log");
  await expect(transcript.getByText("Hello from e2e", { exact: true })).toBeVisible();
  await expect(transcript.getByText("Mock reply: Hello from e2e", { exact: true })).toBeVisible();

  // The server names the conversation after its first user message.
  await expect(page.getByRole("button", { name: "Hello from e2e" })).toBeVisible();
});

test("persists the conversation across a reload", async ({ signUpPage, page }) => {
  await signUpFreshAccount(signUpPage);

  await page.getByRole("button", { name: "New conversation" }).click();
  await page.getByLabel("Message").fill("Persisted turn");
  await page.getByRole("button", { name: "Send" }).click();

  const transcript = page.getByRole("log");
  await expect(transcript.getByText("Mock reply: Persisted turn", { exact: true })).toBeVisible();

  await page.reload();

  await expect(transcript.getByText("Persisted turn", { exact: true })).toBeVisible();
  await expect(transcript.getByText("Mock reply: Persisted turn", { exact: true })).toBeVisible();
});

test("creates the conversation from the first message on the empty state", async ({
  signUpPage,
  page,
}) => {
  await signUpFreshAccount(signUpPage);
  await expect(page).toHaveURL(/\/application\/conversations$/);

  await page.getByLabel("Message").fill("Straight to it");
  await page.getByRole("button", { name: "Send" }).click();

  await expect(page).toHaveURL(/\/application\/conversations\/[\w-]+$/);
  await expect(
    page.getByRole("log").getByText("Mock reply: Straight to it", { exact: true }),
  ).toBeVisible();
});

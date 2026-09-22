import { expect, test } from "../authentication/fixtures";
import { SignUpPage } from "../authentication/sign-up/SignUpPage";
import { uniqueEmail } from "../authentication/support/test-user";

const VALID_PASSWORD = "Passw0rd!123";

async function signUpFreshAccount(signUpPage: SignUpPage): Promise<void> {
  await signUpPage.goto();
  await signUpPage.signUp(uniqueEmail(), VALID_PASSWORD);
}

test("shows the usage and provider settings", async ({ signUpPage, page }) => {
  await signUpFreshAccount(signUpPage);

  // Spend a little so the usage panel has a figure to report.
  await page.getByRole("button", { name: "New conversation" }).click();
  await page.getByLabel("Message").fill("Settings check");
  await page.getByRole("button", { name: "Send" }).click();
  await expect(page.getByText("Mock reply: Settings check", { exact: true })).toBeVisible();

  await page.getByRole("button", { name: "Account" }).click();
  await page.getByRole("menuitem", { name: "Settings" }).click();

  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible();
  await expect(dialog.getByRole("heading", { name: "Usage" })).toBeVisible();
  await expect(dialog.getByRole("heading", { name: "Provider" })).toBeVisible();
  await expect(dialog.getByText(/tokens left/)).toBeVisible();

  // The server-provided model is the default; a personal key is not in use.
  await expect(dialog.getByLabel("AI Chat (server-provided)")).toBeChecked();
  await expect(dialog.getByLabel("Your own API key")).not.toBeChecked();
  await expect(dialog.getByLabel("API key", { exact: true })).toBeHidden();
});

test("reveals the personal key field when selected", async ({ signUpPage, page }) => {
  await signUpFreshAccount(signUpPage);

  await page.getByRole("button", { name: "Account" }).click();
  await page.getByRole("menuitem", { name: "Settings" }).click();

  const dialog = page.getByRole("dialog");
  await dialog.getByLabel("Your own API key").check();

  await expect(dialog.getByLabel("API key", { exact: true })).toBeVisible();
  await expect(dialog.getByText("Not wired up yet — keys are not stored.")).toBeVisible();
});

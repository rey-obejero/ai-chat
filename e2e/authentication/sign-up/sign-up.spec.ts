import { expect, test } from "../fixtures";
import { uniqueEmail } from "../support/test-user";

const VALID_PASSWORD = "Passw0rd!123";

test("signs up a new account and lands in chat", async ({ signUpPage, page }) => {
  await signUpPage.goto();
  await signUpPage.signUp(uniqueEmail(), VALID_PASSWORD);

  await expect(page).toHaveURL(/\/chat$/);
  await expect(page.getByRole("heading", { name: "Chat" })).toBeVisible();
});

test("shows an error when the email already exists", async ({ signUpPage, user, page }) => {
  await signUpPage.goto();
  await signUpPage.signUp(user.email, VALID_PASSWORD);

  await expect(signUpPage.alert).toBeVisible();
  await expect(page).toHaveURL(/\/sign-up$/);
});

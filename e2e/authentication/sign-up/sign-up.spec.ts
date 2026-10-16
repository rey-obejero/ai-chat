import { expect, test } from "../fixtures";
import { uniqueEmail } from "../support/test-user";

const VALID_PASSWORD = "Passw0rd!123";

test("signs up a new account and lands in conversations", async ({ signUpPage, page }) => {
  await signUpPage.goto();
  await signUpPage.signUp(uniqueEmail(), VALID_PASSWORD);

  await expect(page).toHaveURL(/\/application\/conversations$/);
  await expect(page.getByRole("button", { name: "New conversation" })).toBeVisible();
});

test("shows an error when the email already exists", async ({ signUpPage, user, page }) => {
  await signUpPage.goto();
  await signUpPage.signUp(user.email, VALID_PASSWORD);

  await expect(signUpPage.alert).toBeVisible();
  await expect(page).toHaveURL(/\/authentication\/sign-up$/);
});

test("refuses a weak password before the account is created", async ({ signUpPage, page }) => {
  // "password1" is both common and in the breach data (the check itself is off
  // in this stack, as it is for rate limiting).
  await signUpPage.goto();
  await signUpPage.signUp(uniqueEmail(), "password1");

  await expect(signUpPage.alert).toBeVisible();
  await expect(page).toHaveURL(/\/authentication\/sign-up$/);
});

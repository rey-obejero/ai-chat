import { expect, test } from "../fixtures";

const WRONG_PASSWORD = "definitely-not-the-password";

test("signs in an existing account and lands in conversations", async ({
  signInPage,
  user,
  page,
}) => {
  await signInPage.goto();
  await signInPage.signIn(user.email, user.password);

  await expect(page).toHaveURL(/\/conversations$/);
  await expect(page.getByRole("button", { name: "New conversation" })).toBeVisible();
});

test("shows an error for the wrong password", async ({ signInPage, user, page }) => {
  await signInPage.goto();
  await signInPage.signIn(user.email, WRONG_PASSWORD);

  await expect(signInPage.alert).toBeVisible();
  await expect(page).toHaveURL(/\/sign-in$/);
});

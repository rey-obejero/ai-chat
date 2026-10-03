import { expect, test } from "../fixtures";

test("guarded conversations route redirects to sign in when signed out", async ({
  signInPage,
  page,
}) => {
  await page.goto("/application/conversations");

  await expect(page).toHaveURL(/\/authentication\/sign-in(\?.*)?$/);
  await expect(signInPage.heading).toBeVisible();
});

test("returns the user to the requested URL after signing in", async ({
  signInPage,
  user,
  page,
}) => {
  await page.goto("/application/conversations");
  await signInPage.signIn(user.email, user.password);

  await expect(page).toHaveURL(/\/application\/conversations$/);
});

test("ignores a protocol-relative redirectTo instead of leaving the origin", async ({
  signInPage,
  user,
  page,
}) => {
  await page.goto("/authentication/sign-in?redirectTo=//evil.example");
  await signInPage.signIn(user.email, user.password);

  await expect(page).toHaveURL(/\/application\/conversations$/);
  await expect(page).toHaveURL(/^(?!.*evil\.example)/);
});

import { expect, test } from "../fixtures";

test("guarded conversations route redirects to sign in when signed out", async ({
  signInPage,
  page,
}) => {
  await page.goto("/app/conversations");

  await expect(page).toHaveURL(/\/auth\/sign-in(\?.*)?$/);
  await expect(signInPage.heading).toBeVisible();
});

test("returns the user to the requested URL after signing in", async ({
  signInPage,
  user,
  page,
}) => {
  await page.goto("/app/conversations");
  await signInPage.signIn(user.email, user.password);

  await expect(page).toHaveURL(/\/app\/conversations$/);
});

test("ignores a protocol-relative redirectTo instead of leaving the origin", async ({
  signInPage,
  user,
  page,
}) => {
  await page.goto("/auth/sign-in?redirectTo=//evil.example");
  await signInPage.signIn(user.email, user.password);

  await expect(page).toHaveURL(/\/app\/conversations$/);
  await expect(page).toHaveURL(/^(?!.*evil\.example)/);
});

test("keeps the destination when an already signed-in user opens sign-in", async ({
  signInPage,
  user,
  page,
}) => {
  await signInPage.goto();
  await signInPage.signIn(user.email, user.password);
  await expect(page).toHaveURL(/\/app\/conversations$/);

  // Following a link that names a specific destination while already signed in
  // should land there, not on the conversation list.
  await page.goto("/auth/sign-in?redirectTo=/app/conversations/deep-link");

  // Asserted on the path, not the whole URL: the query string literally
  // contains the destination, so a URL-keyed assertion would pass even if the
  // app stayed on the sign-in page and redirected nowhere.
  await expect.poll(() => new URL(page.url()).pathname).toBe(
    "/app/conversations/deep-link",
  );
});

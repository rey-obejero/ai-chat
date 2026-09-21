import { expect, test } from "../fixtures";

test("guarded conversations route redirects to sign in when signed out", async ({
  signInPage,
  page,
}) => {
  await page.goto("/conversations");

  await expect(page).toHaveURL(/\/sign-in(\?.*)?$/);
  await expect(signInPage.heading).toBeVisible();
});

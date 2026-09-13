import { expect, test } from "../fixtures";

test("guarded chat route redirects to sign in when signed out", async ({ signInPage, page }) => {
  await page.goto("/chat");

  await expect(page).toHaveURL(/\/sign-in(\?.*)?$/);
  await expect(signInPage.heading).toBeVisible();
});

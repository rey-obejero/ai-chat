import { expect, test } from "../authentication/fixtures";
import { SignUpPage } from "../authentication/sign-up/SignUpPage";
import { uniqueEmail } from "../authentication/support/test-user";

const VALID_PASSWORD = "Passw0rd!123";

async function signUpFreshAccount(signUpPage: SignUpPage): Promise<void> {
  await signUpPage.goto();
  await signUpPage.signUp(uniqueEmail(), VALID_PASSWORD);
}

test("reveals the group chevron on hover and on keyboard focus", async ({ signUpPage, page }) => {
  await signUpFreshAccount(signUpPage);

  const header = page.getByRole("button", { name: "Projects" });
  const chevron = page.locator("section.sidebar-group", { has: header }).locator("svg.group-chevron");

  // Hidden at rest: a collapsed group must not advertise itself. The reveal is a
  // scoped :hover/:focus-within rule, not a `group-*` utility (which is inert).
  await expect(chevron).toHaveCSS("opacity", "0");

  await header.hover();
  await expect(chevron).toHaveCSS("opacity", "1");

  // Keyboard focus reveals it too, independent of the pointer.
  await page.mouse.move(0, 0);
  await expect(chevron).toHaveCSS("opacity", "0");
  await header.focus();
  await expect(chevron).toHaveCSS("opacity", "1");
});

test("reveals the collapsed-rail expand toggle on hover and expands the rail", async ({
  signUpPage,
  page,
}) => {
  await signUpFreshAccount(signUpPage);

  await page.getByRole("button", { name: "Collapse sidebar" }).click();

  const expand = page.getByRole("button", { name: "Expand sidebar" });
  await expect(expand).toHaveCSS("opacity", "0");

  await page.locator(".logo-slot").hover();
  await expect(expand).toHaveCSS("opacity", "1");

  await expand.click();
  await expect(page.getByRole("button", { name: "Collapse sidebar" })).toBeVisible();
});

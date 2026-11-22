import { test as base } from "@playwright/test";

import { SignInPage } from "./sign-in/SignInPage";
import { SignUpPage } from "./sign-up/SignUpPage";
import { seedUser, type TestUser } from "./support/test-user";

type Fixtures = {
  signInPage: SignInPage;
  signUpPage: SignUpPage;
  user: TestUser;
};

export const test = base.extend<Fixtures>({
  signInPage: async ({ page }, use) => {
    await use(new SignInPage(page));
  },
  signUpPage: async ({ page }, use) => {
    await use(new SignUpPage(page));
  },
  user: async ({}, use) => {
    await use(await seedUser());
  },
});

export { expect } from "@playwright/test";

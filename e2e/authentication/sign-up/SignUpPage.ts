import type { Locator, Page } from "@playwright/test";

/**
 * A fresh account is asked for a display name once, and that modal cannot be
 * dismissed except by Save or Skip. Most specs are about something else, so the
 * prompt is answered for them; pass `{ answerNamePrompt: false }` in the spec
 * that asserts the prompt itself.
 */
export async function answerNamePromptIfShown(page: Page): Promise<void> {
  const prompt = page.getByRole("dialog");
  await prompt.waitFor({ state: "visible", timeout: 5_000 }).catch(() => {});
  if (await prompt.isVisible().catch(() => false)) {
    await prompt.getByRole("button", { name: "Skip" }).click();
    await prompt.waitFor({ state: "hidden" }).catch(() => {});
  }
}

export class SignUpPage {
  readonly heading: Locator;
  readonly email: Locator;
  readonly password: Locator;
  readonly submit: Locator;
  readonly alert: Locator;

  constructor(private readonly page: Page) {
    this.heading = page.getByRole("heading", { name: "Sign Up" });
    this.email = page.getByLabel("Email", { exact: true });
    this.password = page.getByLabel("Password", { exact: true });
    this.submit = page.getByRole("button", { name: "Continue", exact: true });
    this.alert = page.getByRole("alert");
  }

  async goto(): Promise<void> {
    await this.page.goto("/authentication/sign-up");
  }

  async signUp(
    email: string,
    password: string,
    options: { answerNamePrompt?: boolean } = {},
  ): Promise<void> {
    await this.email.fill(email);
    await this.password.fill(password);
    await this.submit.click();
    if (options.answerNamePrompt !== false) {
      await answerNamePromptIfShown(this.page);
    }
  }
}

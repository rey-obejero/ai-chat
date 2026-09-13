import type { Locator, Page } from "@playwright/test";

export class SignInPage {
  readonly heading: Locator;
  readonly email: Locator;
  readonly password: Locator;
  readonly submit: Locator;
  readonly alert: Locator;

  constructor(private readonly page: Page) {
    this.heading = page.getByRole("heading", { name: "Sign In" });
    this.email = page.getByLabel("Email", { exact: true });
    this.password = page.getByLabel("Password", { exact: true });
    this.submit = page.getByRole("button", { name: "Sign in" });
    this.alert = page.getByRole("alert");
  }

  async goto(): Promise<void> {
    await this.page.goto("/sign-in");
  }

  async signIn(email: string, password: string): Promise<void> {
    await this.email.fill(email);
    await this.password.fill(password);
    await this.submit.click();
  }
}

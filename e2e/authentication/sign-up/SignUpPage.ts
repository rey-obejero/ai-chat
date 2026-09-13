import type { Locator, Page } from "@playwright/test";

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
    this.submit = page.getByRole("button", { name: "Create account" });
    this.alert = page.getByRole("alert");
  }

  async goto(): Promise<void> {
    await this.page.goto("/sign-up");
  }

  async signUp(email: string, password: string): Promise<void> {
    await this.email.fill(email);
    await this.password.fill(password);
    await this.submit.click();
  }
}

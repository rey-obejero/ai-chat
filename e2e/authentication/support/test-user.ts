const CORE_URL = process.env.E2E_SUPERTOKENS_CORE_URL ?? "http://localhost:3567";
const API_KEY = process.env.E2E_SUPERTOKENS_API_KEY ?? "dev-key-change-me";

export interface TestUser {
  email: string;
  password: string;
}

let counter = 0;

export function uniqueEmail(): string {
  counter += 1;
  return `e2e-${Date.now()}-${counter}@example.com`;
}

export async function seedUser(overrides: Partial<TestUser> = {}): Promise<TestUser> {
  const user: TestUser = {
    email: overrides.email ?? uniqueEmail(),
    password: overrides.password ?? "Passw0rd!123",
  };

  const response = await fetch(`${CORE_URL}/recipe/signup?rid=emailpassword`, {
    method: "POST",
    headers: { "api-key": API_KEY, "content-type": "application/json" },
    body: JSON.stringify({ email: user.email, password: user.password }),
  });

  if (!response.ok) {
    throw new Error(`Failed to seed user (${response.status}): ${await response.text()}`);
  }

  const body = (await response.json()) as { status: string };
  if (body.status !== "OK") {
    throw new Error(`Failed to seed user: ${body.status}`);
  }

  return user;
}

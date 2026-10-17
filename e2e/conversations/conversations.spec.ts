import { expect, test } from "../authentication/fixtures";
import { SignUpPage } from "../authentication/sign-up/SignUpPage";
import { uniqueEmail } from "../authentication/support/test-user";

const VALID_PASSWORD = "Passw0rd!123";

async function signUpFreshAccount(signUpPage: SignUpPage): Promise<void> {
  await signUpPage.goto();
  await signUpPage.signUp(uniqueEmail(), VALID_PASSWORD);
}

test("sends a message and renders the streamed reply", async ({ signUpPage, page }) => {
  await signUpFreshAccount(signUpPage);

  await page.getByRole("button", { name: "New conversation" }).click();
  await expect(page).toHaveURL(/\/application\/conversations\/[\w-]+$/);

  await page.getByLabel("Message").fill("Hello from e2e");
  await page.getByRole("button", { name: "Send" }).click();

  // The header shows the conversation title, which is the first user message, so
  // assertions are scoped to the transcript rather than to the whole page.
  const transcript = page.getByRole("log");
  await expect(transcript.getByText("Hello from e2e", { exact: true })).toBeVisible();
  await expect(transcript.getByText("Mock reply: Hello from e2e", { exact: true })).toBeVisible();

  // The server names the conversation after its first user message.
  await expect(page.getByRole("button", { name: "Hello from e2e" })).toBeVisible();
});

test("persists the conversation across a reload", async ({ signUpPage, page }) => {
  await signUpFreshAccount(signUpPage);

  await page.getByRole("button", { name: "New conversation" }).click();
  await page.getByLabel("Message").fill("Persisted turn");
  await page.getByRole("button", { name: "Send" }).click();

  const transcript = page.getByRole("log");
  await expect(transcript.getByText("Mock reply: Persisted turn", { exact: true })).toBeVisible();

  await page.reload();

  await expect(transcript.getByText("Persisted turn", { exact: true })).toBeVisible();
  await expect(transcript.getByText("Mock reply: Persisted turn", { exact: true })).toBeVisible();
});

test("creates the conversation from the first message on the empty state", async ({
  signUpPage,
  page,
}) => {
  await signUpFreshAccount(signUpPage);
  await expect(page).toHaveURL(/\/application\/conversations$/);

  await page.getByLabel("Message").fill("Straight to it");
  await page.getByRole("button", { name: "Send" }).click();

  await expect(page).toHaveURL(/\/application\/conversations\/[\w-]+$/);
  await expect(
    page.getByRole("log").getByText("Mock reply: Straight to it", { exact: true }),
  ).toBeVisible();
});

test("renders the assistant's markdown as elements", async ({ signUpPage, page }) => {
  await signUpFreshAccount(signUpPage);

  await page.getByRole("button", { name: "New conversation" }).click();
  await page.getByLabel("Message").fill("**bold**");
  await page.getByRole("button", { name: "Send" }).click();

  await expect(page.getByRole("log").locator("strong")).toHaveText("bold");
});

test("highlights a code block and copies it", async ({ signUpPage, page }) => {
  await signUpFreshAccount(signUpPage);

  await page.getByRole("button", { name: "New conversation" }).click();
  // The mock prefixes "Mock reply: ", so the fence has to start on its own line;
  // an internal newline survives the send-time trim, a leading one does not.
  await page.getByLabel("Message").fill("intro\n```js\nconst x = 1\n```");
  const send = page.getByRole("button", { name: "Send" });
  await expect(send).toBeEnabled();
  await send.click();

  const block = page.getByRole("log").locator(".md-code");
  await expect(block.locator(".md-code__lang")).toHaveText("js");
  await expect(block.locator(".hljs-keyword")).toHaveCount(1);

  // The containerized stack serves the app over http://caddy, which is not a
  // secure origin: the async Clipboard API is absent, so the clipboard cannot be
  // read back from the page. The control's copied state is the observable
  // behaviour here; the exact text written is asserted in the component's unit
  // test (where the clipboard is stubbed).
  await block.getByRole("button", { name: "Copy code" }).click();
  await expect(block.locator(".md-code__copy[data-copied]")).toHaveCount(1);
});

test("expands a code block longer than the line threshold", async ({ signUpPage, page }) => {
  await signUpFreshAccount(signUpPage);

  const lines = Array.from({ length: 25 }, (_, index) => `line ${index}`).join("\n");
  await page.getByRole("button", { name: "New conversation" }).click();
  await page.getByLabel("Message").fill(`intro\n\`\`\`\n${lines}\n\`\`\``);
  const send = page.getByRole("button", { name: "Send" });
  await expect(send).toBeEnabled();
  await send.click();

  const transcript = page.getByRole("log");
  const expand = transcript.getByRole("button", { name: "Show more" });
  await expect(expand).toHaveAttribute("aria-expanded", "false");

  await expand.click();
  await expect(transcript.getByRole("button", { name: "Show less" })).toHaveAttribute(
    "aria-expanded",
    "true",
  );
});

test("routes an image in a reply through the media proxy", async ({ signUpPage, page }) => {
  await signUpFreshAccount(signUpPage);

  await page.getByRole("button", { name: "New conversation" }).click();
  await page.getByLabel("Message").fill("![diagram](https://example.invalid/d.png)");
  await page.getByRole("button", { name: "Send" }).click();

  // The proxy's own tests cover the fetch; here the element and its proxied
  // src are what matter.
  const image = page.getByRole("log").locator("img");
  await expect(image).toHaveAttribute("alt", "diagram");
  await expect(image).toHaveAttribute("src", /^\/api\/v1\/media\/image\?url=/);
});

test("copies and quotes a message from the action row", async ({ signUpPage, page }) => {
  await signUpFreshAccount(signUpPage);

  await page.getByRole("button", { name: "New conversation" }).click();
  await page.getByLabel("Message").fill("original turn");
  const send = page.getByRole("button", { name: "Send" });
  await expect(send).toBeEnabled();
  await send.click();

  const transcript = page.getByRole("log");
  await expect(transcript.getByText("Mock reply: original turn", { exact: true })).toBeVisible();

  // The row is hidden at rest and revealed by hovering the turn.
  await transcript.locator(".turn").first().hover();
  await transcript.getByRole("button", { name: "Copy message" }).first().click();
  await expect(transcript.getByRole("button", { name: "Copied" }).first()).toBeVisible();

  await transcript.getByRole("button", { name: "Quote message" }).first().click();
  // `getByLabel('Message')` also matches the action buttons once a turn exists,
  // so address the composer by role.
  await expect(page.getByRole("textbox", { name: "Message" })).toHaveValue(
    /^> You: original turn/,
  );
});

test("regenerates a reply without duplicating the turn", async ({ signUpPage, page }) => {
  await signUpFreshAccount(signUpPage);

  await page.getByRole("button", { name: "New conversation" }).click();
  await page.getByLabel("Message").fill("regenerate me");
  const send = page.getByRole("button", { name: "Send" });
  await expect(send).toBeEnabled();
  await send.click();

  const transcript = page.getByRole("log");
  await expect(transcript.getByText("Mock reply: regenerate me", { exact: true })).toBeVisible();

  const assistantTurn = transcript.locator(".turn").filter({ hasText: "Assistant" }).first();
  await assistantTurn.hover();
  await assistantTurn.getByRole("button", { name: "Regenerate response" }).click();

  // The old reply is replaced, not appended to.
  await expect(transcript.getByText("Mock reply: regenerate me", { exact: true })).toHaveCount(1);
  await expect(transcript.getByText("regenerate me", { exact: true })).toHaveCount(1);
});

test("searches, renames and deletes a conversation", async ({ signUpPage, page }) => {
  await signUpFreshAccount(signUpPage);

  for (const text of ["alpha note", "beta note"]) {
    // The header carries its own New conversation button once a conversation is
    // open, so scope to the sidebar.
    await page.getByRole("navigation").getByRole("button", { name: "New conversation" }).click();
    await page.getByRole("textbox", { name: "Message" }).fill(text);
    const send = page.getByRole("button", { name: "Send" });
    await expect(send).toBeEnabled();
    await send.click();
    await expect(
      page.getByRole("log").getByText(`Mock reply: ${text}`, { exact: true }),
    ).toBeVisible();
  }

  // Search narrows the sidebar to matching conversations.
  const search = page.getByRole("textbox", { name: "Search conversations" });
  await search.fill("alpha");
  await expect(page.getByRole("button", { name: "alpha note" })).toBeVisible();
  await expect(page.getByRole("button", { name: "beta note" })).toHaveCount(0);
  await search.press("Escape");
  await expect(page.getByRole("button", { name: "beta note" })).toBeVisible();

  // Rename inline from the row's context menu.
  const row = page.locator("li", { has: page.getByRole("button", { name: "beta note" }) });
  await row.hover();
  await row.getByRole("button", { name: "Conversation actions" }).click();
  await page.getByRole("menuitem", { name: "Rename" }).click();
  // The title button is replaced by the input, so the row locator above no
  // longer matches; address the field by its own label.
  const renameInput = page.getByRole("textbox", { name: "Conversation title" });
  await renameInput.fill("renamed beta");
  await renameInput.press("Enter");
  await expect(page.getByRole("button", { name: "renamed beta" })).toBeVisible();

  // Delete asks first, then removes the row.
  const renamedRow = page.locator("li", { has: page.getByRole("button", { name: "renamed beta" }) });
  await renamedRow.hover();
  await renamedRow.getByRole("button", { name: "Conversation actions" }).click();
  await page.getByRole("menuitem", { name: "Delete" }).click();
  await page.getByRole("button", { name: "Delete" }).click();
  await expect(page.getByRole("button", { name: "renamed beta" })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "alpha note" })).toBeVisible();
});

test("edits a user message without duplicating turns", async ({ signUpPage, page }) => {
  await signUpFreshAccount(signUpPage);

  await page.getByRole("button", { name: "New conversation" }).click();
  await page.getByLabel("Message").fill("edit me");
  const send = page.getByRole("button", { name: "Send" });
  await expect(send).toBeEnabled();
  await send.click();

  const transcript = page.getByRole("log");
  await expect(transcript.getByText("Mock reply: edit me", { exact: true })).toBeVisible();

  const userTurn = transcript.locator(".turn").filter({ hasText: "You" }).first();
  await userTurn.hover();
  await userTurn.getByRole("button", { name: "Edit message" }).click();

  // Editing replaces the affected turn and everything after it, then streams a
  // fresh reply — so the transcript still holds exactly one user turn and one
  // assistant reply.
  await expect(transcript.getByText("edit me", { exact: true })).toHaveCount(1);
  await expect(transcript.getByText("Mock reply: edit me", { exact: true })).toHaveCount(1);
  await expect(transcript.locator(".turn")).toHaveCount(2);
});

test("opens the command palette on a slash and inserts without sending", async ({
  signUpPage,
  page,
}) => {
  await signUpFreshAccount(signUpPage);
  await page.getByRole("button", { name: "New conversation" }).click();

  const composer = page.getByRole("textbox", { name: "Message" });
  const palette = page.getByRole("listbox", { name: "Commands" });

  // A lone slash opens the palette and never sends. `fill` sets the value
  // without keystrokes, so type it the way a user does.
  await composer.click();
  await composer.pressSequentially("/");
  await expect(palette).toBeVisible();

  // Escape dismisses it and leaves the draft alone.
  await composer.press("Escape");
  await expect(palette).toHaveCount(0);
  await expect(composer).toHaveValue("/");

  // Arrow keys move the highlight; Enter inserts the template into the draft.
  await composer.pressSequentially("e");
  await expect(palette).toBeVisible();
  await composer.press("Enter");
  await expect(palette).toHaveCount(0);
  expect((await composer.inputValue()).length).toBeGreaterThan(1);

  // Nothing reached the provider.
  await expect(page.getByRole("log").getByText(/^Mock reply/)).toHaveCount(0);
});

test("cannot send an invocation, and follows the caret", async ({ signUpPage, page }) => {
  await signUpFreshAccount(signUpPage);
  await page.getByRole("button", { name: "New conversation" }).click();

  const composer = page.getByRole("textbox", { name: "Message" });
  const palette = page.getByRole("listbox", { name: "Commands" });
  const send = page.getByRole("button", { name: "Send" });

  await composer.click();
  await composer.pressSequentially("/");
  await expect(palette).toBeVisible();
  // A lone slash is the palette's text, not a message: Send is not a way around
  // the rule that Enter belongs to the palette.
  await expect(send).toBeDisabled();

  // The caret leaving closes the palette and leaves the draft alone; coming back
  // reopens it, because the draft still invokes a command.
  await composer.blur();
  await expect(palette).toHaveCount(0);
  await expect(composer).toHaveValue("/");
  await composer.focus();
  await expect(palette).toBeVisible();

  // With an argument in the draft it is ordinary text, and it sends.
  await composer.pressSequentially("translate hello");
  await expect(send).toBeEnabled();
  await send.click();
  await expect(page.getByRole("log").getByText("/translate hello", { exact: true })).toBeVisible();
});

test("switches the model and discloses the switch", async ({ signUpPage, page }) => {
  await signUpFreshAccount(signUpPage);
  await page.getByRole("button", { name: "New conversation" }).click();

  await page.getByRole("textbox", { name: "Message" }).fill("pick a model");
  const send = page.getByRole("button", { name: "Send" });
  await expect(send).toBeEnabled();
  await send.click();

  const transcript = page.getByRole("log");
  await expect(transcript.getByText("Mock reply: pick a model", { exact: true })).toBeVisible();

  // The picker names the model in force and lists the served set.
  await page.getByRole("button", { name: /e2e\/mock/ }).click();
  await page.getByRole("menuitem", { name: /e2e\/mock-alt/ }).click();

  // The switch is disclosed in the transcript, never silent.
  await expect(transcript.getByText(/Model set to/)).toBeVisible();
});

test("asks for a display name once and never again", async ({ signUpPage, page }) => {
  // The sign-up helper answers the prompt for every other spec; this is the one
  // that asserts it.
  await signUpPage.goto();
  await signUpPage.signUp(uniqueEmail(), VALID_PASSWORD, { answerNamePrompt: false });

  const prompt = page.getByRole("dialog");
  await expect(prompt).toBeVisible();

  // Prefilled with the derived name — the email local part, never blank.
  const field = prompt.getByRole("textbox");
  await expect(field).not.toHaveValue("");

  await field.fill("Ada Lovelace");
  await prompt.getByRole("button", { name: "Save" }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);

  // Answered once: a reload does not ask again, and the account button now
  // shows the name. The button's accessible name is "Account"; the display name
  // is its visible label.
  await page.reload();
  // Prove the account was re-read first: `toHaveCount(0)` passes the moment the
  // count matches, so asserting it before hydration would pass for a build that
  // never persisted the answer.
  await expect(page.getByRole("button", { name: "Account" })).toContainText("Ada Lovelace");
  await expect(page.getByRole("dialog")).toHaveCount(0);
});

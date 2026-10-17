import { expect, test } from "../authentication/fixtures";
import { SignUpPage } from "../authentication/sign-up/SignUpPage";
import { uniqueEmail } from "../authentication/support/test-user";

const VALID_PASSWORD = "Passw0rd!123";

/**
 * The empty state anchors the composer near the top of a scroll container, so a
 * popup opening upward from it reaches past that container's top edge and is
 * clipped — the first row survives as a sliver, unclickable. This is the check
 * that `toBeVisible()` cannot make: it ignores ancestor clipping, so the row is
 * measured and then hit-tested at its own centre.
 */
test("the command palette opens where it is not clipped", async ({ signUpPage, page }) => {
  await signUpPage.goto();
  await signUpPage.signUp(uniqueEmail(), VALID_PASSWORD);

  await page.getByLabel("Message").fill("/");
  const palette = page.getByRole("listbox", { name: "Commands" });
  await expect(palette).toBeVisible();

  const first = palette.getByRole("option").first();
  await expect(first).toBeVisible();
  const box = await first.boundingBox();
  expect(box, "the first row has a box").not.toBeNull();

  const hitAtCentre = await page.evaluate(
    ({ x, y }) => {
      const hit = document.elementFromPoint(x, y);
      return hit === null ? null : (hit.closest('[role="option"]')?.id ?? null);
    },
    { x: (box?.x ?? 0) + (box?.width ?? 0) / 2, y: (box?.y ?? 0) + (box?.height ?? 0) / 2 },
  );

  // The point at the row's own centre belongs to the row: nothing clips it away
  // and nothing paints over it.
  expect(hitAtCentre).toBe(await first.getAttribute("id"));
});

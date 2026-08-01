import { expect, test } from "@playwright/test";

test("editor supports the first vocal-note workflow", async ({ page }, testInfo) => {
  await page.goto("/");
  await expect(page.locator(".brand")).toContainText("mini-svs");
  await expect(page.locator(".note-block")).toHaveCount(3);

  const initialNoteBox = await page.locator(".note-block").first().boundingBox();
  const editorBox = await page.locator(".editor-area").boundingBox();
  expect(initialNoteBox).not.toBeNull();
  expect(editorBox).not.toBeNull();
  expect(initialNoteBox!.y).toBeGreaterThanOrEqual(editorBox!.y);
  expect(initialNoteBox!.y + initialNoteBox!.height).toBeLessThanOrEqual(
    editorBox!.y + editorBox!.height,
  );

  await page.locator(".note-block").first().click();
  const lyric = page.getByLabel("Lyric");
  await lyric.fill("ka");
  await expect(page.locator(".note-block").first()).toContainText("ka");

  await page.locator(".roll-canvas").dblclick({ position: { x: 500, y: 400 } });
  await expect(page.locator(".note-block")).toHaveCount(4);

  const bodyOverflow = await page.evaluate(() => document.body.scrollWidth > document.body.clientWidth);
  expect(bodyOverflow).toBe(false);
  await page.screenshot({ path: testInfo.outputPath("editor.png"), fullPage: true });
});

test("frontend proxy reaches the backend health endpoint", async ({ request }) => {
  const response = await request.get("/api/health");
  expect(response.ok()).toBe(true);
  await expect(response.json()).resolves.toEqual({ status: "ok", version: "0.1.0" });
});

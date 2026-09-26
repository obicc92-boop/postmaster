// Per-platform composer details. These sites change their markup without notice,
// so when posting breaks, this file is almost always the thing to update.
export const PLATFORMS = {
  x: {
    url: "https://x.com/compose/post",
    editor: ['[data-testid="tweetTextarea_0"]'],
    submit: ['[data-testid="tweetButton"]'],
  },
  linkedin: {
    url: "https://www.linkedin.com/feed/?shareActive=true",
    editor: ['.share-creation-state .ql-editor[contenteditable="true"]', 'div[role="textbox"][contenteditable="true"]'],
    submit: ["button.share-actions__primary-action"],
  },
};

// Injected into the platform tab with chrome.scripting.executeScript, so it must be
// self-contained: no closures over module scope, only its arguments.
export async function fillComposer({ editor, submit, text, autoSubmit }) {
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const find = (selectors) => {
    for (const s of selectors) {
      const el = document.querySelector(s);
      if (el) return el;
    }
    return null;
  };
  const waitFor = async (check, timeoutMs, what) => {
    const deadline = Date.now() + timeoutMs;
    while (Date.now() < deadline) {
      const value = check();
      if (value) return value;
      await sleep(250);
    }
    throw new Error(`Timed out waiting for ${what}`);
  };

  try {
    return await fill();
  } catch (err) {
    return { ok: false, message: err.message };
  }

  async function fill() {
    const box = await waitFor(() => find(editor), 20_000, "the composer (are you logged in?)");
    box.focus();

    // Rich-text editors (Draft.js on X, Quill on LinkedIn) ignore direct DOM edits, so hand
    // them the text the way a user would: as a paste, falling back to a typed insert.
    const data = new DataTransfer();
    data.setData("text/plain", text);
    box.dispatchEvent(new ClipboardEvent("paste", { clipboardData: data, bubbles: true, cancelable: true }));
    await sleep(300);
    if (!box.innerText.trim()) document.execCommand("insertText", false, text);

    const normalize = (s) => s.replace(/\s+/g, " ").trim();
    await waitFor(() => normalize(box.innerText).includes(normalize(text).slice(0, 40)), 5_000, "the text to appear");

    const button = await waitFor(
      () => {
        const b = find(submit);
        return b && !b.disabled && b.getAttribute("aria-disabled") !== "true" ? b : null;
      },
      10_000,
      "the Post button to enable",
    );

    if (!autoSubmit) {
      button.scrollIntoView({ block: "center" });
      return { ok: true, mode: "review", message: "Composer filled; waiting for the user to click Post." };
    }

    button.click();
    // Both composers are removed from the page once the post goes through.
    await waitFor(() => !box.isConnected || !find(editor), 20_000, "the post to be submitted");
    return { ok: true, mode: "auto", message: "Posted." };
  }
}

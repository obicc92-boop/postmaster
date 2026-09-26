const $ = (id) => document.getElementById(id);

async function load() {
  const { token = "", port = 17893, autoSubmit = false, status = "Unknown" } = await chrome.storage.local.get();
  $("token").value = token;
  $("port").value = port;
  $("autoSubmit").checked = autoSubmit;
  $("status").textContent = status;
}

$("save").addEventListener("click", async () => {
  await chrome.storage.local.set({
    token: $("token").value.trim(),
    port: Number($("port").value) || 17893,
    autoSubmit: $("autoSubmit").checked,
  });
  $("save").textContent = "Saved";
  setTimeout(() => ($("save").textContent = "Save"), 1200);
});

chrome.storage.onChanged.addListener((changes) => {
  if (changes.status) $("status").textContent = changes.status.newValue;
});

load();

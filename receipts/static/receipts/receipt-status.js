(() => {
  const list = document.querySelector("#receipt-list");
  if (!list || !list.querySelector("[data-receipt-id]")) return;
  const endpoint = "/api/receipts/";
  async function refreshStatuses() {
    try {
      const response = await fetch(endpoint, { headers: { Accept: "application/json" }, credentials: "same-origin" });
      if (!response.ok) return;
      const data = await response.json();
      for (const receipt of data.results) {
        const row = list.querySelector(`[data-receipt-id="${receipt.id}"]`);
        if (!row) continue;
        const status = row.querySelector("[data-status]");
        status.textContent = receipt.status_display;
        status.className = `status-pill status-${receipt.status}`;
        const reason = row.querySelector("[data-reason]");
        const defaultInfo = row.querySelector("[data-default-info]");
        if (receipt.rejection_reason) {
          reason.hidden = false;
          reason.textContent = receipt.rejection_reason;
          if (defaultInfo) defaultInfo.hidden = true;
        } else {
          reason.hidden = true;
          if (defaultInfo) {
            defaultInfo.hidden = false;
            defaultInfo.textContent = receipt.status === "pending" ? "Чек на проверке" : "Чек принят";
          }
        }
      }
    } catch {
    }
  }
  window.setInterval(refreshStatuses, 30000);
})();

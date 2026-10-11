(() => {
  const form = document.querySelector("#receipt-form");
  if (!form) return;

  const fields = ["fn", "fd", "fp", "purchase_at", "amount"];
  const startDate = form.dataset.campaignStart;
  const endDate = form.dataset.campaignEnd;
  const responseBox = document.querySelector("#form-response");
  const submitButton = form.querySelector('button[type="submit"]');
  const submitLabel = submitButton?.querySelector("span:first-child");
  const defaultSubmitText = submitLabel?.textContent || "Зарегистрировать чек";

  function setError(name, message = "") {
    const input = form.elements.namedItem(name);
    const error = document.querySelector(`#error-${name}`);
    if (!input || !error) return;
    error.textContent = message;
    error.hidden = !message;
    input.closest(".field-group")?.classList.toggle("has-error", Boolean(message));
    input.setAttribute("aria-invalid", message ? "true" : "false");
  }

  function clearMessages() {
    fields.forEach((name) => setError(name));
    const general = document.querySelector("#error-general");
    general.textContent = "";
    general.hidden = true;
    responseBox.hidden = true;
    responseBox.textContent = "";
    responseBox.className = "form-response";
  }

  function validate() {
    clearMessages();
    let valid = true;
    for (const name of fields) {
      const input = form.elements.namedItem(name);
      const value = input.value.trim();
      let error = "";
      if (!value) error = "Заполните это поле.";
      else if (["fn", "fd", "fp"].includes(name) && !/^\d{1,32}$/.test(value)) error = "Укажите только цифры (до 32 знаков).";
      else if (name === "purchase_at" && !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(value)) error = "Укажите дату и время покупки.";
      else if (name === "purchase_at" && Number.isNaN(Date.parse(value))) error = "Проверьте дату и время.";
      else if (name === "purchase_at" && (value.slice(0, 10) < startDate || value.slice(0, 10) > endDate)) error = `Дата покупки должна быть в периоде акции: ${startDate} — ${endDate}.`;
      else if (name === "amount" && (!/^\d+(?:[.,]\d{1,2})?$/.test(value.replace(/[ \u00a0]/g, "").replace(",", ".")) || Number(value.replace(/[ \u00a0]/g, "").replace(",", ".")) < 1000)) error = "Сумма должна быть не меньше 1 000 ₽.";
      if (error) {
        setError(name, error);
        valid = false;
      }
    }
    return valid;
  }

  function csrfToken() {
    return form.querySelector('input[name="csrfmiddlewaretoken"]')?.value || document.cookie.split(";").map((part) => part.trim()).find((part) => part.startsWith("csrftoken="))?.split("=").slice(1).join("=") || "";
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!validate()) {
      form.querySelector('[aria-invalid="true"]')?.focus();
      return;
    }
    submitButton.disabled = true;
    submitButton.classList.add("is-loading");
    if (submitLabel) submitLabel.textContent = "Отправляем…";
    try {
      const result = await fetch(form.dataset.endpoint, {
        method: "POST",
        body: new FormData(form),
        headers: { "X-CSRFToken": csrfToken(), "X-Requested-With": "XMLHttpRequest", "Accept": "application/json" },
        credentials: "same-origin",
      });
      const payload = await result.json();
      if (result.ok && payload.ok) {
        responseBox.className = "form-response is-success";
        responseBox.innerHTML = `${payload.message} <a href="${payload.account_url || form.dataset.accountUrl}">Открыть личный кабинет →</a>`;
        responseBox.hidden = false;
        form.reset();
      } else {
        responseBox.className = "form-response is-error";
        responseBox.textContent = payload.message || "Не удалось зарегистрировать чек. Проверьте данные.";
        responseBox.hidden = false;
        for (const [name, errors] of Object.entries(payload.errors || {})) {
          const message = Array.isArray(errors) ? errors.map((item) => item.message).join(" ") : String(errors);
          if (fields.includes(name)) setError(name, message);
          else {
            const general = document.querySelector("#error-general");
            general.textContent = message;
            general.hidden = false;
          }
        }
      }
    } catch {
      responseBox.className = "form-response is-error";
      responseBox.textContent = "Не удалось связаться с сервером. Проверьте подключение и попробуйте ещё раз.";
      responseBox.hidden = false;
    } finally {
      submitButton.disabled = false;
      submitButton.classList.remove("is-loading");
      if (submitLabel) submitLabel.textContent = defaultSubmitText;
    }
  });

  fields.forEach((name) => form.elements.namedItem(name).addEventListener("input", () => setError(name)));

  document.querySelector("#parse-qr").addEventListener("click", () => {
    const feedback = document.querySelector("#qr-feedback");
    const raw = document.querySelector("#qr-string").value.trim();
    try {
      const query = raw.includes("?") ? raw.slice(raw.indexOf("?") + 1) : raw.replace(/^\?/, "");
      const params = new URLSearchParams(query);
      const values = { fn: params.get("fn"), fd: params.get("i"), fp: params.get("fp"), amount: params.get("s"), purchase_at: params.get("t") };
      if (!values.fn || !values.fd || !values.fp || !values.amount || !values.purchase_at) throw new Error("missing");
      let stamp = values.purchase_at.replace(/[-:]/g, "");
      stamp = stamp.replace(/^(\d{8})[tT ]?(\d{4})(\d{2})?$/, (_, day, hm, sec = "00") => `${day}T${hm}${sec}`);
      if (!/^\d{8}T\d{6}$/.test(stamp)) throw new Error("date");
      const dateValue = `${stamp.slice(0, 4)}-${stamp.slice(4, 6)}-${stamp.slice(6, 8)}T${stamp.slice(9, 11)}:${stamp.slice(11, 13)}`;
      const amountValue = values.amount.replace(",", ".");
      for (const name of ["fn", "fd", "fp"]) form.elements.namedItem(name).value = values[name];
      form.elements.namedItem("purchase_at").value = dateValue;
      form.elements.namedItem("amount").value = amountValue;
      fields.forEach((name) => setError(name));
      feedback.textContent = "Готово! Проверь данные перед отправкой.";
      feedback.className = "qr-feedback is-success";
    } catch {
      feedback.textContent = "Не получилось распознать строку. Проверь формат QR-кода.";
      feedback.className = "qr-feedback is-error";
    }
  });
})();

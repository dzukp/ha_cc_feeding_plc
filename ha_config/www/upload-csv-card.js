class UploadCsvCard extends HTMLElement {
  set hass(hass) {
    this._hass = hass;
  }

  setConfig(config) {
    const root = this.attachShadow({ mode: "open" });

    const card = document.createElement("ha-card");
    card.header = "Загрузка расписания кормления";

    const content = document.createElement("div");
    content.className = "card-content";

    content.innerHTML = `
      <p>Выберите CSV-файл и нажмите "Загрузить"</p>
      <input type="file" id="csvFile" accept=".csv" hidden />
      <div id="status"></div>
      <style>
        .card-content { display: flex; flex-direction: column; gap: 16px; }
      </style>
    `;

    const btnOpen = document.createElement("mwc-button");
    btnOpen.setAttribute("raised", "");
    btnOpen.label = "Открыть";

    const btnUpload = document.createElement("mwc-button");
    btnUpload.setAttribute("raised", "");
    btnUpload.label = "Загрузить";

    content.appendChild(btnOpen);
    content.appendChild(btnUpload);
    card.appendChild(content);
    root.appendChild(card);

    this.querySelector("#uploadBtn").addEventListener("click", async () => {
      const fileInput = this.querySelector("#csvFile");
      const statusEl = this.querySelector("#status");

      if (!fileInput.files.length) {
        statusEl.textContent = "Файл не выбран";
        return;
      }

      const file = fileInput.files[0];
      const reader = new FileReader();

      reader.onload = async (e) => {
        const csvText = e.target.result;
        try {
          const response = await this._hass.fetchWithAuth("/api/pool/recipe_csv", {
            method: "POST",
            headers: {
              "Content-Type": "application/json"
            },
            body: JSON.stringify({ csv: csvText }),
          });

          if (response.ok) {
            const resp_data = await response.json();
            const success_cnt = resp_data.results.filter(item => !item.errors || item.errors.length === 0).length;
            const failed_cnt = resp_data.results.filter(item => item.errors && item.errors.length > 0).length;
            statusEl.textContent = `Загружено для ${success_cnt} кормушек(-ки). С ошибками ${failed_cnt} кормушек(-ки)`;
          }
          else {
            statusEl.textContent = `Ошибка загрузки данных ${response.status}`;
          }
        } catch (err) {
          statusEl.textContent = `Ошибка: ${err}`;
        }
      };

      reader.readAsText(file);
    });

    this.querySelector("#openFileBtn").addEventListener("click", async () => {
      const input = this.querySelector("#csvFile");
      const statusEl = this.querySelector("#status");
      input.click();
    });

    this.querySelector("#csvFile").addEventListener("change", (e) => {
      const statusEl = this.querySelector("#status");
      if (e.target.files.length > 0) {
        statusEl.textContent = e.target.files[0].name;
      } else {
        statusEl.textContent = "";
      }
    });
  }

  getCardSize() {
    return 3;
  }
}

customElements.define("upload-csv-card", UploadCsvCard);

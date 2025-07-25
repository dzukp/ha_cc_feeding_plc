class UploadCsvCard extends HTMLElement {
  set hass(hass) {
    this._hass = hass;
  }

  setConfig(config) {
    this.config = config;
    this.innerHTML = `
      <ha-card header="Загрузка расписания кормления">
        <div class="card-content">
          <p>Выберите CSV-файл и нажмите "Загрузить"</p>
          <input type="file" id="csvFile" accept=".csv" hidden />
          <mwc-button raised label="Открыть" id="openFileBtn"></mwc-button>
          <mwc-button raised label="Загрузить" id="uploadBtn"></mwc-button>
          <div id="status"></div>
        </div>
      </ha-card>
      <style>
        ha-card {
          max-width: 500px;
          margin: auto;
        }
        .card-content {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }
        #status {
          font-size: 14px;
          color: var(--primary-text-color);
        }
      </style>
    `;

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

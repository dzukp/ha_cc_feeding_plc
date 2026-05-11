class ParamsCsvCard extends HTMLElement {
  set hass(hass) {
    this._hass = hass;
  }

  setConfig(config) {
    this.config = config;
    this.innerHTML = `
      <ha-card header="Параметры">
        <div class="card-content">
          <p>Сохранить текущие параметры в файл</p>
          <input type="file" id="csvFile" accept=".csv" hidden />
          <ha-button raised id="downloadBtn">Сохранить в файл</ha-button>
          <p>Загрузить параметры из файла</p>
          <ha-button raised id="openFileBtn">Выбрать файл</ha-button>
          <ha-button raised id="uploadBtn">Загрузить из файла</ha-button>
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

    this.querySelector("#downloadBtn").addEventListener("click", async () => {
      const statusEl = this.querySelector("#status");
      try {
        const response = await this._hass.fetchWithAuth("/api/pool/parameters_csv", {
          method: "GET",
        });
        if (response.ok) {
          const csvText = await response.text();
          const blob = new Blob([csvText], { type: "text/csv" });
          const url = URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          a.download = `feeding_plc_parameters_${new Date().toISOString().slice(0, 19).replace(/:/g, "-")}.csv`;
          a.click();
          URL.revokeObjectURL(url);
          statusEl.textContent = "Параметры сохранены";
        } else {
          statusEl.textContent = `Ошибка сохранения параметров ${response.status}`;
        }
      } catch (err) {
        statusEl.textContent = `Ошибка: ${err}`;
      }
    });

    this.querySelector("#openFileBtn").addEventListener("click", async () => {
      this.querySelector("#csvFile").click();
    });

    this.querySelector("#csvFile").addEventListener("change", (e) => {
      const statusEl = this.querySelector("#status");
      if (e.target.files.length > 0) {
        statusEl.textContent = e.target.files[0].name;
      } else {
        statusEl.textContent = "";
      }
    });

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
          const response = await this._hass.fetchWithAuth("/api/pool/parameters_csv_upload", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ csv: csvText }),
          });

          if (response.ok) {
            const respData = await response.json();
            const okCnt = (respData.results || []).filter((x) => x.ok).length;
            const errCnt = (respData.results || []).filter((x) => x.errors && x.errors.length > 0).length;
            statusEl.textContent = `Загружено: ${okCnt}, ошибок: ${errCnt}`;
          } else {
            statusEl.textContent = `Ошибка загрузки параметров ${response.status}`;
          }
        } catch (err) {
          statusEl.textContent = `Ошибка: ${err}`;
        }
      };

      reader.readAsText(file);
    });
  }

  getCardSize() {
    return 3;
  }
}

customElements.define("params-csv-card", ParamsCsvCard);

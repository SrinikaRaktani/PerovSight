const API_BASE = "http://127.0.0.1:8000";

const features = [
  "ID","Cs","FA","MA","Br","Cl","I","t","BG (eV)","H (eV)","L (eV)",
  "hm","em","Phm","Pem","Gr. Size"
];

// Feature units / dimensions for display
const featureMeta = {
  "ID":       { unit: "",      dim: "—"    },
  "Cs":       { unit: "mol%",  dim: "Composition" },
  "FA":       { unit: "mol%",  dim: "Composition" },
  "MA":       { unit: "mol%",  dim: "Composition" },
  "Br":       { unit: "mol%",  dim: "Halide" },
  "Cl":       { unit: "mol%",  dim: "Halide" },
  "I":        { unit: "mol%",  dim: "Halide" },
  "t":        { unit: "",      dim: "Tolerance" },
  "BG (eV)":  { unit: "eV",    dim: "Energy" },
  "H (eV)":   { unit: "eV",    dim: "Energy" },
  "L (eV)":   { unit: "eV",    dim: "Energy" },
  "hm":       { unit: "cm²/Vs",dim: "Mobility" },
  "em":       { unit: "cm²/Vs",dim: "Mobility" },
  "Phm":      { unit: "cm²/Vs",dim: "Mobility" },
  "Pem":      { unit: "cm²/Vs",dim: "Mobility" },
  "Gr. Size": { unit: "nm",    dim: "Morphology" },
};

// Output dimensions
const outputDims = {
  pce: { label:"PCE",  unit:"%",      dim:"Efficiency" },
  voc: { label:"Voc",  unit:"V",      dim:"Voltage" },
  jsc: { label:"Jsc",  unit:"mA/cm²", dim:"Current density" },
  ff:  { label:"FF",   unit:"%",      dim:"Fill Factor" },
};

// ── INIT ──
window.onload = () => {
  const container = document.getElementById("manualFields");
  features.forEach(f => {
    const meta = featureMeta[f] || { unit:"", dim:"" };
    container.innerHTML += `
      <div class="input-group">
        <label>${f}${meta.unit ? ` <span style="color:var(--teal);font-size:9px;">(${meta.unit})</span>` : ""}</label>
        <input id="${f}" type="number" step="any" value="0.000000" min="0">
      </div>
    `;
  });
};

// ── RUN PREDICTION ──
async function runPrediction() {
  let formData = new FormData();
  let type = document.getElementById("inputType").value;

  if (type === "image") {
    let file = document.getElementById("file").files[0];
    if (!file) return alert("Please upload an image");
    formData.append("file", file);
  } else {
    let data = {};
    let hasNegative = false;
    features.forEach(f => {
      const val = parseFloat(document.getElementById(f).value) || 0;
      if (val < 0) hasNegative = true;
      data[f] = val;
    });
    if (hasNegative) {
      alert("All input values must be non-negative.");
      return;
    }
    formData.append("data", JSON.stringify(data));
  }

  const btn = document.querySelector('.btn-primary');
  btn.textContent = "⏳ Analysing…";
  btn.disabled = true;

  try {
    let res = await fetch(`${API_BASE}/predict/full`, {
      method: "POST", body: formData
    });
    let out = await res.json();
    displayResults(out);
  } catch (err) {
    console.error("Prediction Error:", err);
    alert("Error connecting to backend");
  } finally {
    btn.textContent = "🚀 Run Prediction";
    btn.disabled = false;
  }
}

// ── DISPLAY RESULTS ──
function displayResults(data) {
  let div = document.getElementById("results");
  div.style.display = "block";
  div.scrollIntoView({ behavior: "smooth", block: "start" });

  if (data.status === "error" || !data.initial_results) {
    alert(data.message || "Error");
    return;
  }

  let r = data.initial_results;
  window.lastPCE = r.pce;
  window.lastVoc = r.voc;
  window.lastJsc = r.jsc;
  window.lastFF  = r.ff;

  let html = `
    <div class="card-title">
      <div class="icon icon-teal">📊</div>
      Analysis Results
    </div>
  `;

  // ── IMAGE OUTPUT ──
  if (data.model_used === "image") {
    html += `
      <div class="section-label">Defect Analysis</div>
      <div class="grid-2" style="margin-bottom:16px;">
        <div>
          <div style="font-size:11px;font-weight:600;color:var(--text-soft);margin-bottom:6px;text-transform:uppercase;letter-spacing:1px;">Original</div>
          <img class="img-result" src="data:image/png;base64,${r.original_image}">
        </div>
        <div>
          <div style="font-size:11px;font-weight:600;color:var(--text-soft);margin-bottom:6px;text-transform:uppercase;letter-spacing:1px;">Defect Map</div>
          <img class="img-result" src="data:image/png;base64,${r.defect_image}">
        </div>
      </div>
      <div class="grid-2" style="margin-bottom:16px;">
        <div class="metric">
          <div class="label">Defect Area</div>
          <div class="value">${r.defect_percentage.toFixed(2)}</div>
          <div class="unit">% of surface <span class="dim-chip">Spatial</span></div>
        </div>
        <div class="metric">
          <div class="label">Condition</div>
          <div class="value" style="font-size:20px;">
            <span class="condition-badge"
              style="background:${r.condition_color ? r.condition_color+'22' : '#d4ead922'};
                     color:${r.condition_color || 'var(--sage)'};">
              ${r.condition}
            </span>
          </div>
        </div>
      </div>
      <div class="divider"></div>
    `;
  }

  // ── PERFORMANCE METRICS ──
  html += `<div class="section-label">Performance Metrics</div>`;
  html += `<div class="grid-4">`;
  Object.entries(outputDims).forEach(([key, meta]) => {
    html += `
      <div class="metric">
        <div class="label">${meta.label}</div>
        <div class="value">${r[key].toFixed(3)}</div>
        <div class="unit">${meta.unit} <span class="dim-chip">${meta.dim}</span></div>
      </div>
    `;
  });
  html += `</div>`;

  // ── DEGRADATION TOGGLE ──
  html += `
    <div class="divider"></div>

    <div class="toggle-row">
      <label for="envToggle">🌡 Enable Degradation Simulation</label>
      <label class="toggle-switch">
        <input type="checkbox" id="envToggle" onchange="toggleEnvInputs()">
        <span class="slider"></span>
      </label>
    </div>

    <div id="envInputs" style="display:none; margin-top:20px;">
      <div class="section-label">Environmental Conditions</div>

      <div class="range-group">
        <div class="range-label">
          <span>Temperature</span>
          <span class="val"><span id="tval">30</span> °C</span>
        </div>
        <input type="range" id="temp" min="20" max="80" value="30" oninput="tval.innerText=this.value">
      </div>

      <div class="range-group">
        <div class="range-label">
          <span>Humidity</span>
          <span class="val"><span id="hval">50</span> %</span>
        </div>
        <input type="range" id="hum" min="10" max="95" value="50" oninput="hval.innerText=this.value">
      </div>

      <div class="range-group">
        <div class="range-label">
          <span>Time</span>
          <span class="val"><span id="timeval">1000</span> hrs</span>
        </div>
        <input type="range" id="time" min="0" max="5000" value="1000" oninput="timeval.innerText=this.value">
      </div>

      <div class="input-group" style="margin-top:8px;">
        <label>ISOS Condition</label>
        <select id="isos">
          <option>ISOS-D-1</option>
          <option>ISOS-D-2</option>
          <option>ISOS-L-1</option>
          <option>ISOS-L-2</option>
          <option>ISOS-O-1</option>
        </select>
      </div>

      <button class="btn btn-secondary" onclick="runDegradation()" style="margin-top:16px;">
        📉 Run Degradation Simulation
      </button>
    </div>

    <div id="degradationSection" style="display:none; margin-top:20px;">
      <div id="degMetrics"></div>
      <div class="chart-wrap">
        <h4>PCE over Time</h4>
        <canvas id="pceChart"></canvas>
      </div>
      <div class="chart-wrap">
        <h4>Normalised Parameters</h4>
        <canvas id="normChart"></canvas>
      </div>
      <div id="tableDiv" style="margin-top:20px;"></div>
    </div>
  `;

  div.innerHTML = html;
}

// ── TOGGLE ENV ──
function toggleEnvInputs() {
  const show = document.getElementById("envToggle").checked;
  document.getElementById("envInputs").style.display = show ? "block" : "none";
}

// ── RUN DEGRADATION ──
async function runDegradation() {
  document.getElementById("degradationSection").style.display = "block";

  const btn = document.querySelector('.btn-secondary');
  btn.textContent = "⏳ Simulating…";
  btn.disabled = true;

  let res = await fetch(`${API_BASE}/predict/degradation`, {
    method: "POST",
    body: new URLSearchParams({
      pce: window.lastPCE,
      voc: window.lastVoc,
      jsc: window.lastJsc,
      ff:  window.lastFF,
      temperature: document.getElementById("temp").value,
      humidity:    document.getElementById("hum").value,
      time:        document.getElementById("time").value,
      isos:        document.getElementById("isos").value
    })
  });

  let d = await res.json();
  btn.textContent = "📉 Run Degradation Simulation";
  btn.disabled = false;

  if (!d.curves) return alert("No degradation data");

  // ── DEG METRICS ──
  const degFields = [
    { key:"final_pce",       label:"Final PCE",  unit:"%",   dim:"Efficiency" },
    { key:"efficiency_loss", label:"Loss",        unit:"%",   dim:"Δ Efficiency" },
    { key:"deg_rate",        label:"Deg. Rate",   unit:"/hr", dim:"Kinetics",  decimals:5 },
    { key:"T90",             label:"T90",         unit:"hr",  dim:"Lifetime" },
    { key:"T80",             label:"T80",         unit:"hr",  dim:"Lifetime" },
    { key:"T50",             label:"T50",         unit:"hr",  dim:"Lifetime" },
    { key:"RUL",             label:"RUL",         unit:"hr",  dim:"Remaining life" },
  ];

  let mHtml = `<div class="section-label">Degradation Metrics</div><div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:10px;margin-bottom:16px;">`;
  degFields.forEach(f => {
    const v = d[f.key];
    const dec = f.decimals ?? 2;
    const display = v != null ? (typeof v === 'number' ? v.toFixed(dec) : v) : "—";
    mHtml += `
      <div class="metric">
        <div class="label">${f.label}</div>
        <div class="value" style="font-size:20px;">${display}</div>
        <div class="unit">${f.unit} <span class="dim-chip">${f.dim}</span></div>
      </div>
    `;
  });
  mHtml += `</div>`;
  document.getElementById("degMetrics").innerHTML = mHtml;

  plotPCE(d.curves);
  plotNorm(d.curves);
  renderTable(d, d.curves);
}

// ── CHARTS ──
const chartDefaults = {
  responsive: true,
  plugins: { legend: { labels: { color:"#6b4c3b", font:{ family:"DM Sans" } } } },
  scales: {
    x: { ticks:{ color:"#a0816e", font:{family:"DM Sans",size:11} }, grid:{ color:"#e8d8cc" } },
    y: { ticks:{ color:"#a0816e", font:{family:"DM Sans",size:11} }, grid:{ color:"#e8d8cc" } }
  }
};

function plotPCE(curves) {
  new Chart(document.getElementById("pceChart"), {
    type: 'line',
    data: {
      labels: curves.time,
      datasets: [{
        label: "PCE (%)",
        data: curves.pce,
        borderColor: "#e8836a",
        backgroundColor: "rgba(232,131,106,0.08)",
        tension: 0.4, fill: true, pointRadius: 0
      }]
    },
    options: chartDefaults
  });
}

function plotNorm(curves) {
  const palette = ["#4a9e8e","#e8836a","#7aab8a"];
  const keys = ["voc","jsc","ff"];
  const labels = ["Voc (V)","Jsc (mA/cm²)","FF (%)"];
  new Chart(document.getElementById("normChart"), {
    type: 'line',
    data: {
      labels: curves.time,
      datasets: keys.map((k,i) => ({
        label: labels[i],
        data: curves[k],
        borderColor: palette[i],
        tension: 0.4, fill: false, pointRadius: 0
      }))
    },
    options: chartDefaults
  });
}

// ── TABLE ──
function renderTable(d, curves) {
  const start = curves.pce[0];
  const rows = [
    { name:"T90", threshold:(start*0.9).toFixed(3), time: d.T90||"—" },
    { name:"T80", threshold:(start*0.8).toFixed(3), time: d.T80||"—" },
    { name:"T50", threshold:(start*0.5).toFixed(3), time: d.T50||"—" },
  ];

  document.getElementById("tableDiv").innerHTML = `
    <div class="section-label">Lifetime Metrics</div>
    <table class="lifetime-table">
      <thead>
        <tr>
          <th>Milestone</th>
          <th>PCE Threshold (%)</th>
          <th>Time (hr) <span class="dim-chip">Lifetime</span></th>
        </tr>
      </thead>
      <tbody>
        ${rows.map(r => `
          <tr>
            <td><strong>${r.name}</strong></td>
            <td>${r.threshold}</td>
            <td>${r.time}</td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;
}
from __future__ import annotations


def render_index_page() -> str:
    return """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Job Agent</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap');

    :root {
      color-scheme: light;
      --bg: #f4efe7;
      --bg-2: #e8f1ee;
      --panel: rgba(255, 255, 255, 0.78);
      --panel-strong: #ffffff;
      --text: #142027;
      --muted: #60707d;
      --accent: #0f766e;
      --accent-2: #b45309;
      --border: rgba(20, 32, 39, 0.12);
      --shadow: 0 20px 60px rgba(16, 24, 40, 0.14);
    }

    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      font-family: 'Space Grotesk', 'Segoe UI', sans-serif;
      color: var(--text);
      background:
        radial-gradient(circle at top left, rgba(15, 118, 110, 0.16), transparent 30%),
        radial-gradient(circle at top right, rgba(180, 83, 9, 0.12), transparent 25%),
        linear-gradient(135deg, var(--bg) 0%, var(--bg-2) 100%);
    }

    .shell {
      width: min(1400px, calc(100% - 32px));
      margin: 0 auto;
      padding: 24px 0 40px;
    }

    .hero {
      display: grid;
      grid-template-columns: 1.2fr 0.8fr;
      gap: 18px;
      align-items: stretch;
      margin-bottom: 18px;
    }

    .hero-card, .panel, .metric, .mini-card {
      background: var(--panel);
      backdrop-filter: blur(18px);
      border: 1px solid var(--border);
      box-shadow: var(--shadow);
    }

    .hero-card {
      border-radius: 28px;
      padding: 28px;
      position: relative;
      overflow: hidden;
      animation: rise 700ms ease both;
    }

    .hero-card::after {
      content: '';
      position: absolute;
      inset: auto -60px -120px auto;
      width: 240px;
      height: 240px;
      border-radius: 50%;
      background: linear-gradient(135deg, rgba(15,118,110,.16), rgba(180,83,9,.10));
      filter: blur(8px);
      pointer-events: none;
    }

    .eyebrow {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 14px;
      border-radius: 999px;
      background: rgba(15, 118, 110, 0.10);
      color: var(--accent);
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.12em;
      text-transform: uppercase;
    }

    h1 {
      margin: 18px 0 12px;
      font-size: clamp(2.4rem, 4vw, 4.8rem);
      line-height: 0.95;
      letter-spacing: -0.05em;
      max-width: 11ch;
    }

    .hero p {
      margin: 0;
      max-width: 62ch;
      color: var(--muted);
      font-size: 1rem;
      line-height: 1.7;
    }

    .hero-stats {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 18px;
    }

    .metric {
      border-radius: 24px;
      padding: 20px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      min-height: 150px;
      animation: rise 700ms ease both;
    }

    .metric strong {
      font-size: 2.1rem;
      letter-spacing: -0.05em;
    }

    .metric span {
      color: var(--muted);
      line-height: 1.5;
    }

    .grid {
      display: grid;
      grid-template-columns: 1.05fr 0.95fr;
      gap: 18px;
      align-items: start;
    }

    .panel {
      border-radius: 28px;
      padding: 22px;
      animation: rise 800ms ease both;
    }

    .panel h2 {
      margin: 0 0 12px;
      font-size: 1.25rem;
      letter-spacing: -0.04em;
    }

    .field-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
      margin-bottom: 14px;
    }

    label {
      display: grid;
      gap: 8px;
      font-size: 0.9rem;
      font-weight: 600;
      color: var(--text);
    }

    input, textarea, select {
      width: 100%;
      border: 1px solid rgba(20, 32, 39, 0.12);
      border-radius: 18px;
      background: rgba(255, 255, 255, 0.92);
      color: var(--text);
      padding: 13px 14px;
      font: inherit;
      outline: none;
      transition: border-color 140ms ease, box-shadow 140ms ease, transform 140ms ease;
    }

    textarea {
      min-height: 180px;
      resize: vertical;
    }

    input:focus, textarea:focus, select:focus {
      border-color: rgba(15, 118, 110, 0.55);
      box-shadow: 0 0 0 4px rgba(15, 118, 110, 0.12);
    }

    .full {
      grid-column: 1 / -1;
    }

    .actions {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin-top: 14px;
    }

    button {
      border: 0;
      border-radius: 999px;
      padding: 13px 18px;
      font: inherit;
      font-weight: 700;
      cursor: pointer;
      transition: transform 140ms ease, box-shadow 140ms ease, opacity 140ms ease;
    }

    button:hover { transform: translateY(-1px); }
    button:disabled { opacity: 0.6; cursor: wait; }

    .primary {
      background: linear-gradient(135deg, var(--accent), #155e75);
      color: white;
      box-shadow: 0 14px 34px rgba(15, 118, 110, 0.28);
    }

    .ghost {
      background: rgba(255, 255, 255, 0.7);
      color: var(--text);
      border: 1px solid rgba(20, 32, 39, 0.12);
    }

    .aside {
      display: grid;
      gap: 18px;
    }

    .mini-card {
      border-radius: 24px;
      padding: 18px;
    }

    .mini-card h3 {
      margin: 0 0 10px;
      font-size: 1rem;
    }

    .status {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      border-radius: 999px;
      background: rgba(15, 118, 110, 0.10);
      color: var(--accent);
      font-weight: 700;
      font-size: 0.85rem;
    }

    .dot {
      width: 9px;
      height: 9px;
      border-radius: 50%;
      background: var(--accent);
      box-shadow: 0 0 0 5px rgba(15, 118, 110, 0.12);
    }

    .results {
      display: grid;
      gap: 16px;
      margin-top: 16px;
    }

    .result-box {
      background: var(--panel-strong);
      border: 1px solid var(--border);
      border-radius: 22px;
      padding: 18px;
      box-shadow: 0 8px 24px rgba(16, 24, 40, 0.08);
    }

    .result-box h3 {
      margin: 0 0 10px;
      font-size: 1rem;
    }

    pre {
      margin: 0;
      white-space: pre-wrap;
      word-break: break-word;
      font-family: 'SFMono-Regular', Consolas, monospace;
      font-size: 0.92rem;
      line-height: 1.6;
      color: #1b2730;
    }

    .questions {
      display: grid;
      gap: 10px;
      margin: 0;
      padding-left: 18px;
      color: #1b2730;
    }

    .loading {
      display: none;
      align-items: center;
      gap: 10px;
      color: var(--muted);
      font-weight: 600;
      margin-top: 12px;
    }

    .spinner {
      width: 16px;
      height: 16px;
      border-radius: 50%;
      border: 2px solid rgba(15, 118, 110, 0.22);
      border-top-color: var(--accent);
      animation: spin 900ms linear infinite;
    }

    .footer-note {
      margin-top: 14px;
      color: var(--muted);
      font-size: 0.9rem;
    }

    @keyframes rise {
      from { opacity: 0; transform: translateY(14px); }
      to { opacity: 1; transform: translateY(0); }
    }

    @keyframes spin {
      to { transform: rotate(360deg); }
    }

    @media (max-width: 1080px) {
      .hero, .grid { grid-template-columns: 1fr; }
    }

    @media (max-width: 720px) {
      .shell { width: min(100% - 18px, 1400px); }
      .hero-card, .panel, .mini-card, .metric { border-radius: 22px; }
      .field-grid, .hero-stats { grid-template-columns: 1fr; }
      h1 { max-width: none; }
    }
  </style>
</head>
<body>
  <div class="shell">
    <section class="hero">
      <div class="hero-card">
        <div class="eyebrow">Job Agent / Meta Llama</div>
        <h1>投研求职多智能体工作台</h1>
        <p>把简历、JD 和目标城市放进来，直接生成岗位解析、候选人诊断、简历改写、面试追问和 networking 草稿。默认支持本地 Ollama 的免费 Meta Llama 路线，也能回退到 mock 模式。</p>
      </div>
      <div class="hero-stats">
        <div class="metric">
          <strong>6</strong>
          <span>个 agent 串联 JD 解析、诊断、改写、训练、网络与案例检索。</span>
        </div>
        <div class="metric">
          <strong>0</strong>
          <span>外部付费门槛。Meta Llama 可以通过本地 Ollama 免费运行。</span>
        </div>
        <div class="metric">
          <strong>1</strong>
          <span>个页面完成输入、运行与结果查看，不需要额外前端工程。</span>
        </div>
        <div class="metric">
          <strong>10</strong>
          <span>道面试题默认输出，适合直接做 stock pitch 和 behavior drill。</span>
        </div>
      </div>
    </section>

    <section class="grid">
      <div class="panel">
        <h2>输入区</h2>
        <div class="field-grid">
          <label>
            LLM Provider
            <select id="provider">
              <option value="mock">mock</option>
              <option value="ollama">ollama / meta-llama</option>
            </select>
          </label>
          <label>
            Model
            <input id="model" value="llama3.1:8b" />
          </label>
          <label>
            Target City
            <input id="targetCity" placeholder="Shanghai / Hong Kong" />
          </label>
          <label>
            Target Sector
            <input id="targetSector" placeholder="healthcare / TMT / macro" />
          </label>
          <label class="full">
            Resume Text
            <textarea id="resumeText" placeholder="Paste resume text here or load a .txt file..."></textarea>
          </label>
          <label class="full">
            JD Text
            <textarea id="jdText" placeholder="Paste the job description here or load a .txt file..."></textarea>
          </label>
        </div>
        <div class="actions">
          <button class="primary" id="runBtn">Run analysis</button>
          <button class="ghost" id="sampleBtn">Load sample data</button>
          <label class="ghost" style="display:inline-flex;align-items:center;gap:10px;cursor:pointer;">
            Resume file
            <input id="resumeFile" type="file" accept=".txt,.md,.csv,.json" style="display:none;" />
          </label>
          <label class="ghost" style="display:inline-flex;align-items:center;gap:10px;cursor:pointer;">
            JD file
            <input id="jdFile" type="file" accept=".txt,.md,.csv,.json" style="display:none;" />
          </label>
        </div>
        <div class="loading" id="loading"><div class="spinner"></div> Running LangGraph flow...</div>
        <div class="footer-note">Tip: if Ollama is running locally, switch provider to <b>ollama</b> for the free Meta Llama route.</div>
      </div>

      <div class="aside">
        <div class="mini-card">
          <div class="status"><span class="dot"></span><span id="healthText">Waiting for input</span></div>
          <h3 style="margin-top:14px;">Live output</h3>
          <div class="results">
            <div class="result-box">
              <h3>Final report</h3>
              <pre id="finalReport">Run the analysis to see a summary here.</pre>
            </div>
            <div class="result-box">
              <h3>Diagnosis</h3>
              <pre id="diagnosis">No result yet.</pre>
            </div>
            <div class="result-box">
              <h3>Interview questions</h3>
              <ol class="questions" id="questions"></ol>
            </div>
            <div class="result-box">
              <h3>Resume versions</h3>
              <pre id="resumeVersions">No result yet.</pre>
            </div>
            <div class="result-box">
              <h3>Networking drafts</h3>
              <pre id="networkingDrafts">No result yet.</pre>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>

  <script>
    const sampleResume = `Analyst intern in healthcare research\n- Built DCF and comp models in Python and Excel\n- Summarized policy impact on revenue and margin\n- Wrote 2 deep-dive reports and 1 pitch deck`;
    const sampleJd = `Shanghai buy-side equity research analyst role\nHealthcare coverage\nMust have financial modeling, stock pitch, and bilingual communication`;

    const elements = {
      provider: document.getElementById('provider'),
      model: document.getElementById('model'),
      targetCity: document.getElementById('targetCity'),
      targetSector: document.getElementById('targetSector'),
      resumeText: document.getElementById('resumeText'),
      jdText: document.getElementById('jdText'),
      runBtn: document.getElementById('runBtn'),
      sampleBtn: document.getElementById('sampleBtn'),
      resumeFile: document.getElementById('resumeFile'),
      jdFile: document.getElementById('jdFile'),
      loading: document.getElementById('loading'),
      healthText: document.getElementById('healthText'),
      finalReport: document.getElementById('finalReport'),
      diagnosis: document.getElementById('diagnosis'),
      questions: document.getElementById('questions'),
      resumeVersions: document.getElementById('resumeVersions'),
      networkingDrafts: document.getElementById('networkingDrafts'),
    };

    const setLoading = (flag) => {
      elements.loading.style.display = flag ? 'flex' : 'none';
      elements.runBtn.disabled = flag;
    };

    const pretty = (value) => JSON.stringify(value, null, 2);

    const readFileAsText = (file) => new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(String(reader.result || ''));
      reader.onerror = () => reject(reader.error);
      reader.readAsText(file, 'utf-8');
    });

    elements.resumeFile.addEventListener('change', async () => {
      const file = elements.resumeFile.files && elements.resumeFile.files[0];
      if (!file) return;
      elements.resumeText.value = await readFileAsText(file);
      elements.healthText.textContent = `Loaded resume: ${file.name}`;
    });

    elements.jdFile.addEventListener('change', async () => {
      const file = elements.jdFile.files && elements.jdFile.files[0];
      if (!file) return;
      elements.jdText.value = await readFileAsText(file);
      elements.healthText.textContent = `Loaded JD: ${file.name}`;
    });

    elements.sampleBtn.addEventListener('click', () => {
      elements.resumeText.value = sampleResume;
      elements.jdText.value = sampleJd;
      elements.targetCity.value = 'Shanghai';
      elements.targetSector.value = 'healthcare';
      elements.provider.value = 'mock';
      elements.healthText.textContent = 'Sample data loaded';
    });

    elements.runBtn.addEventListener('click', async () => {
      setLoading(true);
      elements.healthText.textContent = 'Running analysis...';
      try {
        const response = await fetch('/run', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            resume_text: elements.resumeText.value,
            jd_text: elements.jdText.value,
            target_city: elements.targetCity.value,
            target_sector: elements.targetSector.value,
            llm_provider: elements.provider.value,
            llm_model: elements.model.value,
          }),
        });

        if (!response.ok) {
          throw new Error(`Request failed: ${response.status}`);
        }

        const data = await response.json();
        elements.finalReport.textContent = data.final_report || 'No final report returned.';
        elements.diagnosis.textContent = pretty(data.diagnosis || {});
        elements.resumeVersions.textContent = pretty(data.resume_versions || {});
        elements.networkingDrafts.textContent = pretty(data.networking_drafts || {});
        elements.questions.innerHTML = '';
        (data.interview_questions || []).forEach((question) => {
          const li = document.createElement('li');
          li.textContent = question;
          elements.questions.appendChild(li);
        });
        elements.healthText.textContent = 'Analysis complete';
      } catch (error) {
        elements.healthText.textContent = 'Run failed';
        elements.finalReport.textContent = String(error);
      } finally {
        setLoading(false);
      }
    });

    elements.provider.addEventListener('change', () => {
      elements.healthText.textContent = elements.provider.value === 'ollama'
        ? 'Ollama / Meta Llama selected'
        : 'Mock mode selected';
    });
  </script>
</body>
</html>"""
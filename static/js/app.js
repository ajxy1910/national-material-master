/**
 * National Unified Material Master (NUMM) Portal Controller
 * "One Nation – One Material Code" (National CPSE Harmonization)
 */

document.addEventListener('DOMContentLoaded', () => {
  // Global State
  const state = {
    currentTab: 'overview',
    overviewMetrics: null,
    clusters: [],
    crosswalk: [],
    auditTrail: [],
    selectedMasterForDiff: null,
    activeCpseFilter: 'ALL',
    searchTerm: ''
  };

  // DOM Elements
  const tabButtons = document.querySelectorAll('.nav-tab-btn');
  const sections = document.querySelectorAll('.view-section');

  // Initialize
  initTabs();
  loadOverviewData();
  loadClusters();
  loadCrosswalk();
  loadGovernanceData();
  initAiStudio();
  initSavingsCalculator();
  initMigrationWorkbench();
  initSapConsole();

  // Tab Navigation Handling
  function initTabs() {
    tabButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        const tabId = btn.getAttribute('data-tab');
        switchTab(tabId);
      });
    });
  }

  function switchTab(tabId) {
    state.currentTab = tabId;
    tabButtons.forEach(b => b.classList.toggle('active', b.getAttribute('data-tab') === tabId));
    sections.forEach(s => s.classList.toggle('active', s.id === `section-${tabId}`));
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  // Expose switchTab globally for internal buttons
  window.switchTab = switchTab;

  // -------------------------------------------------------------
  // 1. Overview Dashboard
  // -------------------------------------------------------------
  async function loadOverviewData() {
    try {
      const res = await fetch('/api/overview');
      const data = await res.json();
      if (data.status === 'success') {
        state.overviewMetrics = data.metrics;
        renderOverviewKPIs(data.metrics);
        renderCpseDistribution(data.metrics.cpse_item_counts);
      }
    } catch (err) {
      console.error('Failed to load overview data:', err);
    }
  }

  function renderOverviewKPIs(m) {
    document.getElementById('kpi-total-raw').textContent = m.total_raw_materials_ingested.toLocaleString();
    document.getElementById('kpi-national-codes').textContent = m.total_national_master_codes.toLocaleString();
    document.getElementById('kpi-rationalization').textContent = `${m.rationalization_rate_pct}%`;
    document.getElementById('kpi-savings').textContent = `₹ ${m.total_procurement_savings_crores} Cr`;
    document.getElementById('kpi-surplus-stock').textContent = m.total_surplus_stock_visible.toLocaleString();

    // Match counts
    document.getElementById('cnt-exact-dups').textContent = m.match_distribution.exact_duplicates;
    document.getElementById('cnt-near-dups').textContent = m.match_distribution.near_duplicates;
    document.getElementById('cnt-functional-equiv').textContent = m.match_distribution.functional_equivalents;
  }

  function renderCpseDistribution(counts) {
    const container = document.getElementById('cpse-bar-container');
    if (!container) return;
    container.innerHTML = '';

    const maxCount = Math.max(...Object.values(counts));
    for (const [cpse, count] of Object.entries(counts)) {
      const pct = (count / maxCount) * 100;
      const row = document.createElement('div');
      row.className = 'cpse-bar-row';
      row.innerHTML = `
        <span class="cpse-bar-label"><span class="cpse-badge cpse-${cpse}">${cpse}</span></span>
        <div class="cpse-bar-track">
          <div class="cpse-bar-fill" style="width:${pct}%"></div>
        </div>
        <span class="cpse-bar-count">${count}</span>
      `;
      container.appendChild(row);
    }
  }

  // -------------------------------------------------------------
  // 2. AI Matching & Recommendation Studio
  // -------------------------------------------------------------
  function initAiStudio() {
    const btnSearch = document.getElementById('btn-ai-search');
    const inputQuery = document.getElementById('ai-query-input');
    const thresholdSlider = document.getElementById('threshold-slider');
    const thresholdVal = document.getElementById('threshold-val');

    if (thresholdSlider) {
      thresholdSlider.addEventListener('input', (e) => {
        thresholdVal.textContent = `${e.target.value}%`;
      });
    }

    if (btnSearch && inputQuery) {
      btnSearch.addEventListener('click', () => {
        runAiMatch(inputQuery.value.trim());
      });
      inputQuery.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') runAiMatch(inputQuery.value.trim());
      });
    }

    // Quick demo chips
    document.querySelectorAll('.quick-chip').forEach(chip => {
      chip.addEventListener('click', () => {
        const text = chip.getAttribute('data-query');
        if (inputQuery) {
          inputQuery.value = text;
          runAiMatch(text);
        }
      });
    });
  }

  async function runAiMatch(query) {
    if (!query) return;
    const resultsContainer = document.getElementById('ai-results-container');
    const attrContainer = document.getElementById('parsed-attrs-container');
    const threshold = document.getElementById('threshold-slider') ? parseFloat(document.getElementById('threshold-slider').value) : 60;

    resultsContainer.innerHTML = '<div style="padding:2rem; text-align:center; color:var(--text-muted);"><span class="pulse-dot" style="display:inline-block; margin-right:8px; background:var(--navy-accent);"></span>Analyzing natural language attributes & computing semantic vectors...</div>';

    try {
      const res = await fetch('/api/match', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query_text: query, threshold })
      });
      const data = await res.json();

      if (data.status === 'success') {
        renderParsedAttributes(data.extracted_attributes, data.standardized_descriptions, data.recommended_national_code);
        renderMatchCards(data.matches, data.input_query, data.extracted_attributes);
      }
    } catch (err) {
      resultsContainer.innerHTML = `<div style="color:var(--red-alert); padding:1rem; background:#FEE2E2; border:1px solid #FCA5A5; border-radius:var(--radius-sm);">Error performing AI match: ${err.message}</div>`;
    }
  }

  function renderParsedAttributes(attrs, descs, recommendedCode) {
    const container = document.getElementById('parsed-attrs-container');
    if (!container) return;

    container.innerHTML = `
      <div style="background:#EFF6FF; border:1px solid #BFDBFE; border-radius:var(--radius-md); padding:1.1rem; margin-bottom:1.5rem;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.75rem;">
          <span style="font-size:0.83rem; font-weight:700; color:var(--navy-dark); text-transform:uppercase; letter-spacing:0.04em;">NLP Parametric Extraction:</span>
          <span class="cnmc-tag"><span style="color:var(--saffron); margin-right:4px;">Proposed CNMC:</span> ${recommendedCode}</span>
        </div>
        <div class="attr-chip-grid">
          <span class="attr-chip"><strong>Category:</strong> ${attrs.category}</span>
          <span class="attr-chip"><strong>Item Type:</strong> ${attrs.item_type}</span>
          <span class="attr-chip"><strong>Size:</strong> ${attrs.size}</span>
          <span class="attr-chip"><strong>Rating / Class:</strong> ${attrs.rating}</span>
          <span class="attr-chip"><strong>Material Grade:</strong> ${attrs.material_grade}</span>
          <span class="attr-chip"><strong>End Connection:</strong> ${attrs.end_connection}</span>
          <span class="attr-chip"><strong>Standard:</strong> ${attrs.standard}</span>
        </div>
        <div style="margin-top:0.85rem; font-size:0.8rem; background:var(--bg-white); border:1px solid var(--border); padding:0.65rem 0.9rem; border-radius:var(--radius-sm);">
          <strong style="color:var(--navy-accent);">SAP 40-char (MARA-MAKTX):</strong> <code style="font-family:var(--font-mono); font-size:0.78rem;">${descs.sap_short_desc}</code><br/>
          <strong style="color:var(--saffron); margin-top:4px; display:inline-block;">Master Long Desc:</strong> <span style="color:var(--text-muted);">${descs.gem_long_desc}</span>
        </div>
      </div>
    `;
  }

  function renderMatchCards(matches, queryText, queryAttrs) {
    const container = document.getElementById('ai-results-container');
    if (!container) return;

    if (!matches || matches.length === 0) {
      container.innerHTML = `
        <div style="padding:2.5rem; text-align:center; background:rgba(255,255,255,0.02); border-radius:var(--radius-md); border:1px dashed var(--border-glass);">
          <div style="font-size:2rem; margin-bottom:0.5rem;">🔍</div>
          <h4 style="margin-bottom:0.5rem;">No Existing National Master Above Threshold</h4>
          <p style="color:var(--text-secondary); font-size:0.85rem; max-width:500px; margin:0 auto 1.25rem;">
            This appears to be a distinct item. You can create a new National Unified Material Master record or lower the similarity threshold.
          </p>
          <button class="btn btn-saffron" onclick="switchTab('governance')">Propose New National Code</button>
        </div>
      `;
      return;
    }

    container.innerHTML = `<h3 style="font-size:0.92rem; margin-bottom:1rem; color:var(--text-muted); font-weight:600; text-transform:uppercase; letter-spacing:0.04em;">Identified Matching National Material Masters (${matches.length})</h3>`;

    matches.forEach((m, idx) => {
      const master = m.national_master;
      const card = document.createElement('div');
      card.className = 'match-card';

      let badgeClass = 'status-AI_RECOMMENDED';
      if (m.match_type === 'EXACT_DUPLICATE') badgeClass = 'status-APPROVED_NATIONAL_CODE';
      else if (m.match_type === 'FUNCTIONAL_EQUIVALENT') badgeClass = 'status-COMMITTEE_EVALUATION';

      card.innerHTML = `
        <div class="match-header">
          <div>
            <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.35rem;">
              <span class="cnmc-tag">${master.cnmc}</span>
              <span class="status-pill ${badgeClass}">${m.match_type.replace('_', ' ')}</span>
            </div>
            <h4 style="font-size:0.95rem; font-weight:700; color:var(--navy-dark)">${master.standard_short_desc}</h4>
            <p style="font-size:0.8rem; color:var(--text-muted); margin-top:0.25rem;">${master.standard_long_desc}</p>
          </div>
          <div class="confidence-gauge">
            <div class="confidence-pct">${m.confidence_pct}%</div>
            <div class="confidence-label">Match Score</div>
          </div>
        </div>

        <div style="display:grid; grid-template-columns: repeat(3, 1fr); gap:0.5rem; margin:0.75rem 0; font-size:0.75rem; background:var(--bg-stripe); border:1px solid var(--border-light); padding:0.6rem 0.85rem; border-radius:var(--radius-sm);">
          <div><span style="color:var(--text-muted);">Spec Attribute Match:</span> <strong style="color:var(--navy-dark);">${m.score_breakdown.attribute_compatibility}%</strong></div>
          <div><span style="color:var(--text-muted);">Vector Cosine Sim:</span> <strong style="color:var(--navy-dark);">${m.score_breakdown.semantic_cosine}%</strong></div>
          <div><span style="color:var(--text-muted);">Fuzzy Overlap:</span> <strong style="color:var(--navy-dark);">${m.score_breakdown.string_fuzzy}%</strong></div>
        </div>

        <div style="display:flex; justify-content:space-between; align-items:center; margin-top:0.75rem; padding-top:0.75rem; border-top:1px solid var(--border-light);">
          <div style="font-size:0.8rem; color:var(--text-muted);">
            <strong style="color:var(--emerald);">AI Action:</strong> ${m.recommendation}
          </div>
          <div style="display:flex; gap:0.5rem;">
            <button class="btn btn-secondary btn-diff" data-index="${idx}">Compare Specs</button>
            <button class="btn btn-outline-emerald btn-map" data-cnmc="${master.cnmc}">Approve Mapping</button>
          </div>
        </div>
      `;

      // Event listener for diff inspection
      card.querySelector('.btn-diff').addEventListener('click', () => {
        openDiffModal(queryText, queryAttrs, master);
      });

      card.querySelector('.btn-map').addEventListener('click', () => {
        openGovernanceModal(master.cnmc, master.standard_short_desc);
      });

      container.appendChild(card);
    });
  }

  // -------------------------------------------------------------
  // 3. Side-by-Side Diff Modal
  // -------------------------------------------------------------
  function openDiffModal(queryText, queryAttrs, master) {
    const modal = document.getElementById('diff-modal');
    if (!modal) return;

    document.getElementById('diff-query-title').textContent = queryText;
    document.getElementById('diff-master-code').textContent = master.cnmc;
    document.getElementById('diff-master-title').textContent = master.standard_short_desc;

    const tAttrs = master.attributes || {};
    const tbody = document.getElementById('diff-table-body');
    tbody.innerHTML = '';

    const paramRows = [
      { label: 'Category', q: queryAttrs.category, t: master.category },
      { label: 'Item Type', q: queryAttrs.item_type, t: tAttrs.item_type },
      { label: 'Nominal Size', q: queryAttrs.size, t: tAttrs.size },
      { label: 'Rating / Class', q: queryAttrs.rating, t: tAttrs.rating },
      { label: 'Material Grade', q: queryAttrs.material_grade, t: tAttrs.material_grade },
      { label: 'End Connection', q: queryAttrs.end_connection, t: tAttrs.end_connection },
      { label: 'Standard / Code', q: queryAttrs.standard, t: tAttrs.standard }
    ];

    paramRows.forEach(row => {
      const qVal = row.q || 'N/A';
      const tVal = row.t || 'N/A';
      const isMatch = qVal.toUpperCase() === tVal.toUpperCase() ||
        (qVal !== 'N/A' && tVal !== 'N/A' && (qVal.includes(tVal) || tVal.includes(qVal)));

      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td style="font-weight:600; color:var(--text-muted);">${row.label}</td>
        <td>${qVal}</td>
        <td>${tVal}</td>
        <td>
          <span class="${isMatch ? 'diff-match' : 'diff-mismatch'}">
            ${isMatch ? '✓ COMPATIBLE' : '⚠ DIVERGENT'}
          </span>
        </td>
      `;
      tbody.appendChild(tr);
    });

    modal.classList.add('active');
  }

  // Close modals
  document.querySelectorAll('.modal-close-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.modal-overlay').forEach(m => m.classList.remove('active'));
    });
  });

  // -------------------------------------------------------------
  // 4. Duplicate Clusters & Demand Aggregation
  // -------------------------------------------------------------
  async function loadClusters() {
    try {
      const res = await fetch('/api/clusters');
      const data = await res.json();
      if (data.status === 'success') {
        state.clusters = data.clusters;
        renderClusters(data.clusters);
      }
    } catch (err) {
      console.error('Failed to load clusters:', err);
    }
  }

  function renderClusters(clusters) {
    const container = document.getElementById('clusters-accordion');
    if (!container) return;
    container.innerHTML = '';

    clusters.forEach((c, idx) => {
      const card = document.createElement('div');
      card.className = 'cluster-item';

      const itemsHtml = c.items.map(item => `
        <tr>
          <td><span class="cpse-badge cpse-${item.cpse}">${item.cpse}</span></td>
          <td><code style="font-family:var(--font-mono); font-size:0.8rem;">${item.legacy_code}</code></td>
          <td style="max-width:320px;">${item.description}</td>
          <td>${item.uom}</td>
          <td><strong>₹ ${item.unit_price_inr.toLocaleString()}</strong></td>
          <td>${item.annual_procurement_qty.toLocaleString()}</td>
          <td><span style="color:var(--emerald); font-weight:600;">${item.stock_on_hand}</span></td>
          <td><span class="status-pill status-${item.match_type}">${item.match_type.replace('_', ' ')}</span></td>
        </tr>
      `).join('');

      card.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:1rem;">
          <div>
            <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.25rem;">
              <span class="cnmc-tag">${c.cnmc}</span>
              <span class="status-pill status-${c.harmonization_status}">${c.harmonization_status.replace('_', ' ')}</span>
              <span style="font-size:0.75rem; color:var(--text-secondary); background:rgba(255,255,255,0.06); padding:0.15rem 0.5rem; border-radius:var(--radius-full);">${c.items_count} CPSE Master Records</span>
            </div>
            <h3 style="font-size:1.05rem; font-weight:700;">${c.standard_short_desc}</h3>
            <p style="font-size:0.8rem; color:var(--text-secondary);">${c.standard_long_desc}</p>
          </div>
          <div style="text-align:right;">
            <div style="font-size:1.1rem; font-weight:800; color:var(--saffron);">₹ ${c.procurement_analytics.potential_savings_crores} Cr</div>
            <div style="font-size:0.7rem; color:var(--text-muted);">Demand Aggregation Savings</div>
          </div>
        </div>

        <div style="display:grid; grid-template-columns: repeat(4, 1fr); gap:0.75rem; background:rgba(0,0,0,0.3); border-radius:var(--radius-md); padding:0.85rem; margin-bottom:1rem; font-size:0.8rem;">
          <div><span style="color:var(--text-secondary);">Min Price Paid:</span> <strong style="color:var(--accent-emerald);">₹ ${c.price_stats.min_price_inr.toLocaleString()}</strong></div>
          <div><span style="color:var(--text-secondary);">Max Price Paid:</span> <strong style="color:var(--accent-rose);">₹ ${c.price_stats.max_price_inr.toLocaleString()}</strong></div>
          <div><span style="color:var(--text-secondary);">CPSE Price Variance:</span> <strong style="color:var(--accent-saffron);">${c.price_stats.variance_pct}%</strong></div>
          <div><span style="color:var(--text-secondary);">Cross-CPSE Surplus Stock:</span> <strong style="color:var(--accent-cyan);">${c.procurement_analytics.total_stock_on_hand} Units</strong></div>
        </div>

        <div class="data-table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>CPSE</th>
                <th>Legacy Code</th>
                <th>Local Description</th>
                <th>UOM</th>
                <th>Unit PO Price</th>
                <th>Annual Qty</th>
                <th>On-Hand Stock</th>
                <th>Classification</th>
              </tr>
            </thead>
            <tbody>
              ${itemsHtml}
            </tbody>
          </table>
        </div>
      `;
      container.appendChild(card);
    });
  }

  // -------------------------------------------------------------
  // 5. CPSE Cross-Walk Matrix
  // -------------------------------------------------------------
  async function loadCrosswalk() {
    try {
      const res = await fetch('/api/crosswalk');
      const data = await res.json();
      if (data.status === 'success') {
        state.crosswalk = data.crosswalk;
        renderCrosswalk(data.crosswalk);
      }
    } catch (err) {
      console.error('Failed to load crosswalk:', err);
    }
  }

  function renderCrosswalk(items) {
    const tbody = document.getElementById('crosswalk-table-body');
    if (!tbody) return;
    tbody.innerHTML = '';

    const filterCpse = state.activeCpseFilter;
    const search = state.searchTerm.toLowerCase();

    items.forEach(cw => {
      // Check search match
      const searchBlob = `${cw.cnmc} ${cw.standard_short_desc} ${cw.category}`.toLowerCase();
      if (search && !searchBlob.includes(search)) return;

      const mappings = cw.cpse_mappings;
      const cpsePills = Object.keys(mappings)
        .filter(k => mappings[k] !== null)
        .map(k => `<span class="cpse-badge cpse-${k}">${k}: ${mappings[k].legacy_code}</span>`)
        .join(' ');

      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><span class="cnmc-tag">${cw.cnmc}</span></td>
        <td><strong style="font-size:0.85rem;">${cw.standard_short_desc}</strong></td>
        <td><span class="status-pill status-${cw.harmonization_status}">${cw.harmonization_status.replace('_', ' ')}</span></td>
        <td>${cw.standard_uom}</td>
        <td>₹ ${cw.benchmark_price_inr.toLocaleString()}</td>
        <td><div style="display:flex; flex-wrap:wrap; gap:4px;">${cpsePills}</div></td>
        <td>
          <button class="btn btn-secondary" style="padding:0.35rem 0.65rem; font-size:0.75rem;" onclick="viewCrosswalkDetail('${cw.cnmc}')">Inspect</button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  }

  // Crosswalk filters & search
  const cwSearchInput = document.getElementById('crosswalk-search');
  if (cwSearchInput) {
    cwSearchInput.addEventListener('input', (e) => {
      state.searchTerm = e.target.value.trim();
      renderCrosswalk(state.crosswalk);
    });
  }

  window.viewCrosswalkDetail = function (cnmc) {
    const item = state.crosswalk.find(x => x.cnmc === cnmc);
    if (!item) return;
    alert(`Common National Material Code: ${item.cnmc}\nStandard Description: ${item.standard_long_desc}\nNational Demand: ${item.annual_national_demand} ${item.standard_uom}\nBenchmark Price: ₹ ${item.benchmark_price_inr}`);
  };

  // -------------------------------------------------------------
  // 6. Savings Calculator
  // -------------------------------------------------------------
  function initSavingsCalculator() {
    const sliderQty = document.getElementById('calc-slider-qty');
    const sliderDiscount = document.getElementById('calc-slider-discount');
    const lblQty = document.getElementById('lbl-calc-qty');
    const lblDiscount = document.getElementById('lbl-calc-discount');
    const resSpend = document.getElementById('calc-res-spend');
    const resSavings = document.getElementById('calc-res-savings');
    const resPct = document.getElementById('calc-res-pct');

    function updateCalc() {
      if (!sliderQty || !sliderDiscount) return;
      const qtyMultiplier = parseFloat(sliderQty.value);
      const discountPct = parseFloat(sliderDiscount.value);

      lblQty.textContent = `${qtyMultiplier}x`;
      lblDiscount.textContent = `${discountPct}%`;

      const baseSpendCrores = 92.4; // Base overlapping PO spend across CPSEs
      const effectiveSpend = baseSpendCrores * qtyMultiplier;
      const savingsCrores = effectiveSpend * (discountPct / 100);

      resSpend.textContent = `₹ ${(effectiveSpend - savingsCrores).toFixed(2)} Cr`;
      resSavings.textContent = `₹ ${savingsCrores.toFixed(2)} Cr`;
      resPct.textContent = `${discountPct}% Net Reduction`;
    }

    if (sliderQty && sliderDiscount) {
      sliderQty.addEventListener('input', updateCalc);
      sliderDiscount.addEventListener('input', updateCalc);
      updateCalc();
    }
  }

  // -------------------------------------------------------------
  // 7. Legacy CSV Migration Workbench
  // -------------------------------------------------------------
  function initMigrationWorkbench() {
    const dropzone = document.getElementById('csv-dropzone');
    const fileInput = document.getElementById('csv-file-input');
    const btnSample = document.getElementById('btn-load-sample-csv');

    if (dropzone && fileInput) {
      dropzone.addEventListener('click', () => fileInput.click());
      dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.classList.add('dragover');
      });
      dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));
      dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
          uploadCsv(e.dataTransfer.files[0]);
        }
      });
      fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
          uploadCsv(fileInput.files[0]);
        }
      });
    }

    if (btnSample) {
      btnSample.addEventListener('click', loadSampleCsv);
    }
  }

  async function loadSampleCsv() {
    try {
      const res = await fetch('/static/../data/sample_legacy_upload.csv');
      const text = await res.text();
      const blob = new Blob([text], { type: 'text/csv' });
      const file = new File([blob], 'sample_legacy_upload.csv', { type: 'text/csv' });
      uploadCsv(file);
    } catch (err) {
      console.error('Failed to load sample csv:', err);
    }
  }

  async function uploadCsv(file) {
    const reportContainer = document.getElementById('migration-results-container');
    reportContainer.innerHTML = `
      <div style="padding:2rem; text-align:center; color:var(--text-muted);">
        <span class="pulse-dot" style="display:inline-block; margin-right:8px; background:var(--navy-accent);"></span>
        Parsing CPSE file: <strong>${file.name}</strong> (${(file.size / 1024).toFixed(1)} KB)... Running batch AI harmonization...
      </div>
    `;

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('/api/upload', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();

      if (data.status === 'success') {
        renderMigrationReport(data);
      } else {
        reportContainer.innerHTML = `<div style="color:var(--accent-rose); padding:1rem;">Upload failed: ${data.message}</div>`;
      }
    } catch (err) {
      reportContainer.innerHTML = `<div style="color:var(--accent-rose); padding:1rem;">Error during migration processing: ${err.message}</div>`;
    }
  }

  function renderMigrationReport(data) {
    const container = document.getElementById('migration-results-container');
    if (!container) return;

    const rowsHtml = data.results.map(r => `
      <tr>
        <td><strong>#${r.row_index}</strong></td>
        <td><span class="cpse-badge cpse-${r.cpse}">${r.cpse}</span></td>
        <td><code>${r.legacy_code}</code></td>
        <td style="max-width:280px; font-size:0.8rem;">${r.original_description}</td>
        <td><span class="cnmc-tag">${r.assigned_cnmc}</span></td>
        <td><span class="status-pill status-${r.harmonization_status === 'MAPPED_EXISTING_CNMC' ? 'APPROVED_NATIONAL_CODE' : 'AI_RECOMMENDED'}">${r.harmonization_status.replace(/_/g, ' ')}</span></td>
        <td><strong style="color:var(--emerald);">${r.confidence_pct}%</strong></td>
      </tr>
    `).join('');

    container.innerHTML = `
      <div style="margin-top:1.5rem;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
          <h3 style="font-size:1.1rem; font-weight:700;">Harmonization Execution Report: ${data.file_name}</h3>
          <a href="/api/export?format=csv" class="btn btn-saffron" style="padding:0.4rem 0.85rem; font-size:0.75rem;">Download Mapped Catalog CSV</a>
        </div>

        <div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:1rem; margin-bottom:1.5rem;">
          <div class="kpi-card emerald" style="padding:1rem;">
            <div style="font-size:0.75rem; color:var(--text-muted);">Mapped to Existing Masters</div>
            <div style="font-size:1.6rem; font-weight:800; color:var(--emerald);">${data.statistics.mapped_to_existing_exact + data.statistics.mapped_to_existing_near}</div>
          </div>
          <div class="kpi-card saffron" style="padding:1rem;">
            <div style="font-size:0.75rem; color:var(--text-muted);">New Common Codes Proposed</div>
            <div style="font-size:1.6rem; font-weight:800; color:var(--saffron);">${data.statistics.new_national_codes_generated}</div>
          </div>
          <div class="kpi-card cyan" style="padding:1rem;">
            <div style="font-size:0.75rem; color:var(--text-muted);">Total Records Processed</div>
            <div style="font-size:1.6rem; font-weight:800; color:var(--navy-accent);">${data.total_records_processed}</div>
          </div>
        </div>

        <div class="data-table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>Row</th>
                <th>CPSE</th>
                <th>Legacy Code</th>
                <th>Original Description</th>
                <th>Assigned National Code (CNMC)</th>
                <th>Harmonization Status</th>
                <th>Confidence</th>
              </tr>
            </thead>
            <tbody>
              ${rowsHtml}
            </tbody>
          </table>
        </div>
      </div>
    `;
  }

  // -------------------------------------------------------------
  // 8. Governance & Committee Review
  // -------------------------------------------------------------
  async function loadGovernanceData() {
    try {
      const resStatus = await fetch('/api/governance/status');
      const dataStatus = await resStatus.json();
      if (dataStatus.status === 'success') {
        renderGovernanceQueue(dataStatus.items);
      }

      const resAudit = await fetch('/api/governance/audit');
      const dataAudit = await resAudit.json();
      if (dataAudit.status === 'success') {
        renderAuditTrail(dataAudit.audit_trail);
      }
    } catch (err) {
      console.error('Failed to load governance data:', err);
    }
  }

  function renderGovernanceQueue(items) {
    const tbody = document.getElementById('governance-queue-body');
    if (!tbody) return;
    tbody.innerHTML = '';

    items.forEach(itm => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><span class="cnmc-tag">${itm.cnmc}</span></td>
        <td><strong>${itm.standard_short_desc}</strong></td>
        <td>${itm.category}</td>
        <td><span class="status-pill status-${itm.harmonization_status}">${itm.harmonization_status.replace('_', ' ')}</span></td>
        <td>${itm.mapped_cpse_count} Enterprises</td>
        <td>
          <button class="btn btn-primary" style="padding:0.35rem 0.75rem; font-size:0.75rem;" onclick="openGovernanceModal('${itm.cnmc}', '${itm.standard_short_desc}')">Review / Ratify</button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  }

  function renderAuditTrail(logs) {
    const container = document.getElementById('audit-trail-timeline');
    if (!container) return;
    container.innerHTML = '';

    logs.forEach(log => {
      const item = document.createElement('div');
      item.className = 'audit-item';

      const dot = document.createElement('div');
      dot.className = 'audit-dot';

      const content = document.createElement('div');
      content.className = 'audit-content';
      content.innerHTML = `
        <div class="audit-ts">${log.timestamp.replace('T', ' ')}</div>
        <div style="font-size:0.88rem; font-weight:600; color:var(--navy-dark); margin-bottom:0.2rem;">
          <span class="cnmc-tag" style="margin-right:6px;">${log.cnmc}</span>
          ${log.remarks}
        </div>
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <div style="font-size:0.78rem; color:var(--text-muted);">Actor: <strong style="color:var(--navy-dark);">${log.actor}</strong> (${log.actor_org})</div>
          <span class="status-pill status-${log.new_status}">${log.action}</span>
        </div>
      `;

      item.appendChild(dot);
      item.appendChild(content);
      container.appendChild(item);
    });
  }

  window.openGovernanceModal = function (cnmc, title) {
    const modal = document.getElementById('gov-action-modal');
    if (!modal) return;

    document.getElementById('gov-modal-cnmc').textContent = cnmc;
    document.getElementById('gov-modal-title').textContent = title;
    document.getElementById('gov-hidden-cnmc').value = cnmc;

    modal.classList.add('active');
  };

  const btnSubmitGov = document.getElementById('btn-submit-gov-action');
  if (btnSubmitGov) {
    btnSubmitGov.addEventListener('click', async () => {
      const cnmc = document.getElementById('gov-hidden-cnmc').value;
      const newStatus = document.getElementById('gov-select-status').value;
      const actor = document.getElementById('gov-input-actor').value.trim() || 'Data Steward';
      const actorOrg = document.getElementById('gov-input-org').value.trim() || 'Ministry of Petroleum & Natural Gas';
      const remarks = document.getElementById('gov-input-remarks').value.trim() || 'Ratification recorded via National Portal';

      try {
        const res = await fetch('/api/governance/update', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            cnmc,
            new_status: newStatus,
            actor,
            actor_org: actorOrg,
            remarks
          })
        });
        const data = await res.json();
        if (data.status === 'success') {
          document.getElementById('gov-action-modal').classList.remove('active');
          loadGovernanceData();
          loadCrosswalk();
          loadClusters();
          alert(`Successfully updated status for ${cnmc} to ${newStatus}`);
        } else {
          alert(`Failed: ${data.message}`);
        }
      } catch (err) {
        alert(`Error updating governance status: ${err.message}`);
      }
    });
  }

  // -------------------------------------------------------------
  // 9. SAP / ERP Integration Console
  // -------------------------------------------------------------
  function initSapConsole() {
    const selectCnmc = document.getElementById('sap-select-cnmc');
    const selectCpse = document.getElementById('sap-select-cpse');
    const selectType = document.getElementById('sap-select-type');
    const btnGenPayload = document.getElementById('btn-gen-sap-payload');
    const btnSimSync = document.getElementById('btn-sim-sap-sync');
    const previewBox = document.getElementById('sap-preview-box');

    async function generatePayload() {
      const cnmc = selectCnmc.value;
      const cpse = selectCpse.value;
      const type = selectType.value;

      try {
        const res = await fetch(`/api/sap/payload?cnmc=${encodeURIComponent(cnmc)}&cpse=${encodeURIComponent(cpse)}&type=${type}`);
        if (type === 'idoc') {
          const text = await res.text();
          previewBox.textContent = text;
        } else {
          const json = await res.json();
          previewBox.textContent = JSON.stringify(json, null, 2);
        }
      } catch (err) {
        previewBox.textContent = `Error generating payload: ${err.message}`;
      }
    }

    async function simulateSync() {
      const cnmc = selectCnmc.value;
      const cpse = selectCpse.value;
      previewBox.textContent = `Initiating RFC / IDoc connection to ${cpse} SAP S/4HANA instance...\nHandshaking with SAP Gateway RFC port 3300...`;

      try {
        const res = await fetch('/api/sap/sync', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ cnmc, cpse })
        });
        const data = await res.json();
        previewBox.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        previewBox.textContent = `Sync failed: ${err.message}`;
      }
    }

    if (btnGenPayload) btnGenPayload.addEventListener('click', generatePayload);
    if (btnSimSync) btnSimSync.addEventListener('click', simulateSync);
  }
});

// -------------------------------------------------------------
// 10. Global Language Switcher Functions (Google Translate API)
// -------------------------------------------------------------

// Google Translate Widget Initialization
function googleTranslateElementInit() {
  new google.translate.TranslateElement({
    pageLanguage: 'en',
    includedLanguages: 'en,hi',
    autoDisplay: false
  }, 'google_translate_element');
}

// Global Function to trigger translation on pill button click
window.translatePage = function (langCode) {
  // 1. Update Active Highlight Class on Custom Buttons
  const buttons = document.querySelectorAll('.lang-pill, .lang-tab, .lang-btn');
  buttons.forEach(btn => btn.classList.remove('active'));

  const selectedBtn = document.getElementById(`btn-${langCode}`);
  if (selectedBtn) {
    selectedBtn.classList.add('active');
  }

  // 2. Trigger Google Translate Dropdown
  const selectElement = document.querySelector('.goog-te-combo');
  if (selectElement) {
    selectElement.value = langCode;
    selectElement.dispatchEvent(new Event('change'));
  } else {
    console.warn('Google Translate element is initializing...');
  }
};
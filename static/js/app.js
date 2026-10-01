/* ═══════════════════════════════════════════════════════════════
   SolidGuard — Smart Contract Vulnerability Scanner & Showcase
   JavaScript — UI Logic, Chart.js Metrics, Samples & Audit Modal
   ═══════════════════════════════════════════════════════════════ */

// ── DOM References ─────────────────────────────────────────────
const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('fileInput');
const fileInfo = document.getElementById('fileInfo');
const fileName = document.getElementById('fileName');
const fileSize = document.getElementById('fileSize');
const removeBtn = document.getElementById('removeBtn');
const analyzeBtn = document.getElementById('analyzeBtn');
const codePreview = document.getElementById('codePreview');
const uploadCard = document.getElementById('uploadCard');
const scanner = document.getElementById('scanner');
const scanProgressBar = document.getElementById('scanProgressBar');
const scanStatus = document.getElementById('scanStatus');
const results = document.getElementById('results');
const scanAgainBtn = document.getElementById('scanAgainBtn');
const exportReportBtn = document.getElementById('exportReportBtn');
const printAuditBtn = document.getElementById('printAuditBtn');
const auditModal = document.getElementById('auditModal');
const closeAuditModal = document.getElementById('closeAuditModal');

let selectedFile = null;
let lastAnalysisData = null;
let sampleContractsCache = {};
let chartsInitialized = false;
let chartInstances = {};

// ── Color map for vulnerability classes (GitHub Security Palette) ──
const PROB_COLORS = {
    'Safe': '#238636',
    'Reentrancy': '#f85149',
    'Denial of Service': '#db6d28',
    'Integer Overflow/Underflow': '#db6d28',
    'Access Control': '#f85149',
    'Unchecked External Call': '#db6d28',
    'Bad Randomness': '#d29922',
    'Race Condition (Front-Running)': '#db6d28',
    'Honeypot': '#d29922',
    'Forced Ether Reception': '#d29922',
    'Incorrect Interface': '#58a6ff',
    'Variable Shadowing': '#58a6ff',
    'Dangerous Delegatecall': '#f85149',
    'Ether Strict Equality': '#d29922',
    'Ether Frozen': '#d29922',
};

// ── Vector SVG Helpers (Zero Emoji Architecture) ───────────────
function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function getSeveritySvg(severity, iconType) {
    const s = (severity || '').toLowerCase();
    const t = (iconType || '').toLowerCase();

    if (s === 'safe' || t === 'safe') {
        return `<svg class="verdict-svg safe" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            <polyline points="9 12 11 14 15 10"/>
        </svg>`;
    } else if (s === 'critical' || t === 'critical') {
        return `<svg class="verdict-svg critical" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="12 2 2 22 22 22 12 2"/>
            <line x1="12" y1="9" x2="12" y2="13"/>
            <line x1="12" y1="17" x2="12.01" y2="17"/>
        </svg>`;
    } else if (s === 'high' || t === 'high') {
        return `<svg class="verdict-svg high" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
            <line x1="12" y1="9" x2="12" y2="13"/>
            <line x1="12" y1="17" x2="12.01" y2="17"/>
        </svg>`;
    } else if (s === 'low' || t === 'low') {
        return `<svg class="verdict-svg low" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="16" x2="12" y2="12"/>
            <line x1="12" y1="8" x2="12.01" y2="8"/>
        </svg>`;
    } else {
        // Medium / warning
        return `<svg class="verdict-svg medium" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>`;
    }
}

// ── Showcase Navigation Tabs ───────────────────────────────────
document.querySelectorAll('.nav-tab').forEach(tab => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

        tab.classList.add('active');
        const targetId = tab.getAttribute('data-tab');
        const targetContent = document.getElementById(targetId);
        if (targetContent) {
            targetContent.classList.add('active');
        }

        if (targetId === 'tab-analytics') {
            loadAnalyticsCharts();
        }
    });
});

// ── Drag & Drop ────────────────────────────────────────────────
dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.classList.add('drag-over');
});

dropzone.addEventListener('dragleave', () => {
    dropzone.classList.remove('drag-over');
});

dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('drag-over');
    const files = e.dataTransfer.files;
    if (files.length > 0) handleFile(files[0]);
});

dropzone.addEventListener('click', (e) => {
    if (e.target.closest('.browse-btn')) return;
    fileInput.click();
});

fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) handleFile(fileInput.files[0]);
});

removeBtn.addEventListener('click', resetUpload);

// ── File Handling ──────────────────────────────────────────────
function handleFile(file) {
    if (!file.name.endsWith('.sol')) {
        alert('Please select a Solidity (.sol) file.');
        return;
    }

    selectedFile = file;
    fileName.textContent = file.name;
    fileSize.textContent = formatBytes(file.size);
    fileInfo.classList.add('visible');
    analyzeBtn.classList.add('visible');
    dropzone.style.display = 'none';

    // Read & show code preview
    const reader = new FileReader();
    reader.onload = (e) => {
        const code = e.target.result;
        codePreview.textContent = code.length > 5000
            ? code.substring(0, 5000) + '\n\n... (truncated)'
            : code;
        codePreview.classList.add('visible');
    };
    reader.readAsText(file);
}

function resetUpload() {
    selectedFile = null;
    fileInput.value = '';
    fileInfo.classList.remove('visible');
    analyzeBtn.classList.remove('visible');
    codePreview.classList.remove('visible');
    dropzone.style.display = '';
    results.classList.remove('visible');
    uploadCard.style.display = '';
    scanner.classList.remove('visible');
}

function formatBytes(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1048576).toFixed(1) + ' MB';
}

// ── Pre-loaded Sample Contracts (1-Click Demo) ──────────────────
async function loadPreloadedSamples() {
    try {
        const resp = await fetch('/api/samples');
        const data = await resp.json();
        if (data.samples) {
            data.samples.forEach(s => {
                sampleContractsCache[s.id] = s;
            });
        }
    } catch (err) {
        console.warn('Could not load samples:', err);
    }
}
loadPreloadedSamples();

document.querySelectorAll('.sample-pill').forEach(pill => {
    pill.addEventListener('click', () => {
        const sampleId = pill.getAttribute('data-sample');
        const sample = sampleContractsCache[sampleId];
        if (!sample) {
            alert('Loading sample contracts, please retry in a second...');
            return;
        }

        // Create a File object from the sample code
        const blob = new Blob([sample.code], { type: 'text/plain' });
        const file = new File([blob], sample.name, { type: 'text/plain' });

        handleFile(file);

        // Scroll smoothly to code preview / analyze button
        analyzeBtn.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    });
});

// ── Analysis Execution ─────────────────────────────────────────
analyzeBtn.addEventListener('click', () => {
    if (!selectedFile) return;
    startScan();
});

async function startScan() {
    // Show scanner animation
    uploadCard.style.display = 'none';
    scanner.classList.add('visible');
    results.classList.remove('visible');
    scanProgressBar.style.width = '0%';

    // Animate progress phases
    const phases = [
        { pct: 20, msg: 'Reading Solidity AST & tokens…' },
        { pct: 40, msg: 'Extracting 33 vulnerability features…' },
        { pct: 65, msg: 'Running Random Forest ensemble (200 trees)…' },
        { pct: 85, msg: 'Calculating Bayesian confidence & gating…' },
        { pct: 95, msg: 'Compiling security audit report…' },
    ];

    let phaseIdx = 0;
    const phaseInterval = setInterval(() => {
        if (phaseIdx < phases.length) {
            scanProgressBar.style.width = phases[phaseIdx].pct + '%';
            scanStatus.textContent = phases[phaseIdx].msg;
            phaseIdx++;
        }
    }, 350);

    // Send multipart request
    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
        const resp = await fetch('/api/analyze', { method: 'POST', body: formData });
        const data = await resp.json();

        clearInterval(phaseInterval);
        scanProgressBar.style.width = '100%';
        scanStatus.textContent = 'Audit complete!';

        if (data.error) {
            alert('Error: ' + data.error);
            resetUpload();
            return;
        }

        lastAnalysisData = data;
        setTimeout(() => showResults(data), 450);
    } catch (err) {
        clearInterval(phaseInterval);
        alert('Network error: ' + err.message);
        resetUpload();
    }
}

// ── Render Results ─────────────────────────────────────────────
function showResults(data) {
    scanner.classList.remove('visible');
    results.classList.add('visible');

    // Verdict card
    const verdict = document.getElementById('verdict');
    const verdictIcon = document.getElementById('verdictIcon');
    const verdictTitle = document.getElementById('verdictTitle');
    const severityBadge = document.getElementById('severityBadge');
    const modelMethod = document.getElementById('modelMethod');

    verdict.className = 'verdict';
    if (data.severity === 'Safe') {
        verdict.classList.add('safe');
    } else if (data.severity === 'Critical' || data.severity === 'High') {
        verdict.classList.add('danger');
    } else if (data.severity === 'Low') {
        verdict.classList.add('info');
    } else {
        verdict.classList.add('warning');
    }

    verdictIcon.innerHTML = getSeveritySvg(data.severity, data.severity_icon);
    verdictTitle.textContent = data.vulnerability;
    severityBadge.textContent = data.severity;

    if (modelMethod) {
        modelMethod.innerHTML = `
            <svg class="engine-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="3"/>
                <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
            </svg>
            <span>Model: ${escapeHtml(data.model_method || 'Random Forest Classifier (200 Trees)')}</span>
        `;
    }

    // Confidence
    document.getElementById('confidenceValue').textContent = data.confidence.toFixed(1) + '%';
    setTimeout(() => {
        document.getElementById('confidenceBar').style.width = data.confidence + '%';
    }, 100);

    // Class Probabilities
    const probContainer = document.getElementById('probabilities');
    probContainer.innerHTML = '';

    if (data.class_probabilities) {
        Object.entries(data.class_probabilities)
            .sort((a, b) => b[1] - a[1])
            .forEach(([name, prob]) => {
                const color = PROB_COLORS[name] || '#6366f1';
                const item = document.createElement('div');
                item.className = 'prob-item';
                item.innerHTML = `
                    <span class="prob-name">${escapeHtml(name)}</span>
                    <div class="prob-bar-container">
                        <div class="prob-bar-fill" style="width:0%;background:${color}"></div>
                    </div>
                    <span class="prob-value">${prob.toFixed(1)}%</span>
                `;
                probContainer.appendChild(item);

                setTimeout(() => {
                    item.querySelector('.prob-bar-fill').style.width = prob + '%';
                }, 200);
            });
    }

    // Features breakdown
    const featuresGrid = document.getElementById('featuresGrid');
    featuresGrid.innerHTML = '';
    data.features.forEach(f => {
        const chip = document.createElement('div');
        chip.className = 'feature-chip ' + (f.detected ? 'detected' : '');
        chip.innerHTML = `
            ${f.detected 
                ? '<svg class="feat-icon alert" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>'
                : '<svg class="feat-icon ok" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>'
            }
            <span class="feat-name">${escapeHtml(f.name)}</span>
        `;
        featuresGrid.appendChild(chip);
    });

    // Recommendation
    const rec = document.getElementById('recommendation');
    rec.innerHTML = data.recommendation.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
}

scanAgainBtn.addEventListener('click', resetUpload);

// ── Formal Audit Certificate Modal ─────────────────────────────
function openAuditCertificate() {
    if (!lastAnalysisData) {
        alert('Please analyze a smart contract first to generate an audit report.');
        return;
    }

    const data = lastAnalysisData;
    document.getElementById('certFileName').textContent = data.filename || 'Contract.sol';
    document.getElementById('certDate').textContent = new Date().toLocaleString();
    document.getElementById('certVerdict').textContent = data.vulnerability;
    document.getElementById('certSeverity').textContent = data.severity;
    document.getElementById('certConfidence').textContent = data.confidence.toFixed(1) + '%';

    const box = document.getElementById('certVerdictBox');
    box.className = 'cert-verdict-box ' + (data.severity || 'Safe');

    // Probabilities
    const probsEl = document.getElementById('certProbsContainer');
    probsEl.innerHTML = '';
    if (data.class_probabilities) {
        Object.entries(data.class_probabilities)
            .sort((a, b) => b[1] - a[1])
            .forEach(([name, prob]) => {
                const pill = document.createElement('div');
                pill.className = 'cert-prob-pill';
                pill.innerHTML = `<span>${escapeHtml(name)}</span><strong>${prob.toFixed(1)}%</strong>`;
                probsEl.appendChild(pill);
            });
    }

    // Features checklist
    const featsEl = document.getElementById('certFeaturesContainer');
    featsEl.innerHTML = '';
    data.features.forEach(f => {
        const item = document.createElement('div');
        item.className = 'cert-feat-item' + (f.detected ? ' detected' : '');
        const iconSvg = f.detected
            ? `<svg class="cert-svg-warn" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 2 22 22 22 12 2"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`
            : `<svg class="cert-svg-check" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>`;
        item.innerHTML = `${iconSvg}<span>${escapeHtml(f.name)}</span>`;
        featsEl.appendChild(item);
    });

    // Recommendation
    document.getElementById('certRecommendation').innerHTML = data.recommendation.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    auditModal.classList.add('active');
}

exportReportBtn.addEventListener('click', openAuditCertificate);
printAuditBtn.addEventListener('click', openAuditCertificate);
closeAuditModal.addEventListener('click', () => auditModal.classList.remove('active'));

auditModal.addEventListener('click', (e) => {
    if (e.target === auditModal) auditModal.classList.remove('active');
});

document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && auditModal.classList.contains('active')) {
        auditModal.classList.remove('active');
    }
});

// ── Interactive Chart.js Metrics ───────────────────────────────
async function loadAnalyticsCharts() {
    if (chartsInitialized) return;

    try {
        const resp = await fetch('/api/metrics');
        const data = await resp.json();

        // 1. Feature Importance Horizontal Bar Chart
        const featCtx = document.getElementById('chartFeatureImportance');
        if (featCtx && data.feature_importances) {
            const topFeats = data.feature_importances.slice(0, 10);
            const labels = topFeats.map(f => f.label || f.feature);
            const values = topFeats.map(f => f.importance);

            chartInstances.featureImportance = new Chart(featCtx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Gini Importance (%)',
                        data: values,
                        backgroundColor: 'rgba(35, 134, 54, 0.75)',
                        borderColor: '#2ea043',
                        borderWidth: 1,
                        borderRadius: 4,
                    }]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: (ctx) => `Importance: ${ctx.parsed.x.toFixed(2)}%`
                            }
                        }
                    },
                    scales: {
                        x: {
                            grid: { color: 'rgba(255, 255, 255, 0.05)' },
                            ticks: { color: '#94a3b8' }
                        },
                        y: {
                            grid: { display: false },
                            ticks: { color: '#f1f5f9', font: { size: 11 } }
                        }
                    }
                }
            });
        }

        // 2. Ablation Comparison Bar Chart (14 vs 33 Features)
        const abCtx = document.getElementById('chartAblation');
        if (abCtx && data.comparison) {
            chartInstances.ablation = new Chart(abCtx, {
                type: 'bar',
                data: {
                    labels: ['5-Fold CV Accuracy', 'Training Accuracy'],
                    datasets: [
                        {
                            label: 'Baseline (14 Features)',
                            data: [85.93, 89.58],
                            backgroundColor: 'rgba(100, 116, 139, 0.65)',
                            borderColor: '#94a3b8',
                            borderWidth: 1,
                            borderRadius: 6,
                        },
                        {
                            label: 'SolidGuard Enhanced (33 Features)',
                            data: [92.65, 95.71],
                            backgroundColor: 'rgba(16, 185, 129, 0.75)',
                            borderColor: '#34d399',
                            borderWidth: 1,
                            borderRadius: 6,
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            labels: { color: '#cbd5e1' }
                        }
                    },
                    scales: {
                        y: {
                            min: 80,
                            max: 100,
                            grid: { color: 'rgba(255, 255, 255, 0.05)' },
                            ticks: {
                                color: '#94a3b8',
                                callback: (v) => v + '%'
                            }
                        },
                        x: {
                            grid: { display: false },
                            ticks: { color: '#f1f5f9' }
                        }
                    }
                }
            });
        }

        // 3. Class Distribution Donut Chart
        const distCtx = document.getElementById('chartDistribution');
        if (distCtx && data.class_distribution) {
            chartInstances.distribution = new Chart(distCtx, {
                type: 'doughnut',
                data: {
                    labels: data.class_distribution.labels,
                    datasets: [{
                        data: data.class_distribution.counts,
                        backgroundColor: data.class_distribution.colors,
                        borderColor: '#161b22',
                        borderWidth: 2,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: { color: '#cbd5e1', boxWidth: 12, padding: 14 }
                        },
                        tooltip: {
                            callbacks: {
                                label: (ctx) => `${ctx.label}: ${ctx.parsed} contracts`
                            }
                        }
                    },
                    cutout: '62%'
                }
            });
        }

        chartsInitialized = true;
    } catch (err) {
        console.error('Error loading analytics metrics:', err);
    }
}

/* ═══════════════════════════════════════════════════════════════
   SolidGuard — Smart Contract Vulnerability Scanner
   JavaScript — UI Logic
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

let selectedFile = null;

// ── Color map for vulnerability classes ────────────────────────
const PROB_COLORS = {
    'Safe': '#10b981',
    'Reentrancy': '#ef4444',
    'Denial of Service': '#f97316',
    'Integer Overflow/Underflow': '#f97316',
    'Access Control': '#ef4444',
    'Unchecked External Call': '#f97316',
    'Bad Randomness': '#eab308',
    'Race Condition (Front-Running)': '#f97316',
    'Honeypot': '#eab308',
    'Forced Ether Reception': '#eab308',
    'Incorrect Interface': '#3b82f6',
    'Variable Shadowing': '#3b82f6',
};

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

// ── Analysis ───────────────────────────────────────────────────
analyzeBtn.addEventListener('click', () => {
    if (!selectedFile) return;
    startScan();
});

async function startScan() {
    // Show scanner
    uploadCard.style.display = 'none';
    scanner.classList.add('visible');
    results.classList.remove('visible');
    scanProgressBar.style.width = '0%';

    // Animate progress
    const phases = [
        { pct: 20, msg: 'Reading Solidity source code…' },
        { pct: 40, msg: 'Extracting 14 vulnerability features…' },
        { pct: 65, msg: 'Running Random Forest model inference…' },
        { pct: 85, msg: 'Calculating confidence scores…' },
        { pct: 95, msg: 'Generating security report…' },
    ];

    let phaseIdx = 0;
    const phaseInterval = setInterval(() => {
        if (phaseIdx < phases.length) {
            scanProgressBar.style.width = phases[phaseIdx].pct + '%';
            scanStatus.textContent = phases[phaseIdx].msg;
            phaseIdx++;
        }
    }, 350);

    // Send request
    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
        const resp = await fetch('/api/analyze', { method: 'POST', body: formData });
        const data = await resp.json();

        clearInterval(phaseInterval);
        scanProgressBar.style.width = '100%';
        scanStatus.textContent = 'Analysis complete!';

        if (data.error) {
            alert('Error: ' + data.error);
            resetUpload();
            return;
        }

        setTimeout(() => showResults(data), 500);
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

    // Verdict
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

    verdictIcon.textContent = data.severity_icon;
    verdictTitle.textContent = data.vulnerability;
    severityBadge.textContent = data.severity;

    // Show which ML method was used
    if (modelMethod) {
        modelMethod.textContent = '⚙ ' + (data.model_method || 'Random Forest Classifier');
    }

    // Confidence
    document.getElementById('confidenceValue').textContent = data.confidence.toFixed(1) + '%';
    setTimeout(() => {
        document.getElementById('confidenceBar').style.width = data.confidence + '%';
    }, 100);

    // Probabilities
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
                    <span class="prob-name">${name}</span>
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

    // Features
    const featuresGrid = document.getElementById('featuresGrid');
    featuresGrid.innerHTML = '';
    data.features.forEach(f => {
        const chip = document.createElement('div');
        chip.className = 'feature-chip';
        chip.innerHTML = `
            <span class="indicator ${f.detected ? 'on' : 'off'}"></span>
            <span>${f.name}</span>
        `;
        featuresGrid.appendChild(chip);
    });

    // Recommendation — render markdown bold
    const rec = document.getElementById('recommendation');
    rec.innerHTML = data.recommendation.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
}

scanAgainBtn.addEventListener('click', resetUpload);

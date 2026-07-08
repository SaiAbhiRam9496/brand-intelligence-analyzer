// ============================================================
// dashboard.js - UI interaction, Chart.js, and API sync
// ============================================================

// Verify session
Auth.requireAuth();

let sentimentPie = null;
let sourceBar = null;
let currentReportId = null;
let currentBrandName = "";

document.addEventListener('DOMContentLoaded', () => {
    loadHistory();
    
    document.getElementById('btnAnalyze').addEventListener('click', runBrandAnalysis);
    document.getElementById('btnPdf').addEventListener('click', downloadPdfReport);
});

async function loadHistory() {
    const listEl = document.getElementById('historyList');
    listEl.innerHTML = '';
    
    try {
        const history = await API.getHistory();
        if (history.length === 0) {
            listEl.innerHTML = '<li style="color: var(--text-muted); font-size: 0.85rem; padding: 1rem 0;">No past analysis runs found.</li>';
            return;
        }
        
        history.forEach(item => {
            const li = document.createElement('li');
            li.className = 'history-item';
            
            // Format date short
            const dateStr = item.createdAt ? item.createdAt.substring(0, 10) : '';
            li.innerHTML = `
                <span><strong>${item.brandName}</strong></span>
                <span style="color: var(--text-muted); font-size: 0.75rem;">${dateStr}</span>
            `;
            
            li.addEventListener('click', () => fetchCachedAnalysis(item.id, item.brandName));
            listEl.appendChild(li);
        });
    } catch (e) {
        console.error("Failed to load history:", e);
    }
}

async function runBrandAnalysis() {
    const brandInput = document.getElementById('brandSearch');
    const brand = brandInput.value.trim();
    if (!brand) return;

    const overlay = document.getElementById('loadingOverlay');
    overlay.style.display = 'flex';

    try {
        const res = await API.analyze(brand);
        displayResults(brand, res);
        await loadHistory(); // Reload side history
        
        // Auto-select the newly generated report for PDF download
        const history = await API.getHistory();
        if (history && history.length > 0) {
            currentReportId = history[0].id;
            currentBrandName = history[0].brandName;
            document.getElementById('btnPdf').style.display = 'inline-flex';
        }
    } catch (err) {
        alert(err.message || "Pipeline error running brand analysis.");
    } finally {
        overlay.style.display = 'none';
    }
}

async function fetchCachedAnalysis(reportId, brandName) {
    const overlay = document.getElementById('loadingOverlay');
    overlay.style.display = 'flex';
    document.getElementById('loadingText').textContent = "Loading cached analysis...";

    try {
        // Reuse same analyze API (it fetches cached automatically in Spring Boot)
        const res = await API.analyze(brandName);
        displayResults(brandName, res);
        
        // Find report ID in sidebar matching
        currentReportId = reportId;
        currentBrandName = brandName;
        document.getElementById('btnPdf').style.display = 'inline-flex';
    } catch (err) {
        alert(err.message || "Failed to load cached report.");
    } finally {
        overlay.style.display = 'none';
        document.getElementById('loadingText').textContent = "Scraping and analyzing brand metrics...";
    }
}

function displayResults(brand, data) {
    document.getElementById('resultsWrapper').style.display = 'block';
    document.getElementById('brandTitle').textContent = `${brand.toUpperCase()} Brand Insights`;
    
    // Set metrics
    const summary = data.sentiment_summary || {};
    document.getElementById('valTotal').textContent = summary.total_docs || 0;
    document.getElementById('valPositive').textContent = `${summary.positive_pct || 0}%`;
    document.getElementById('valNegative').textContent = `${summary.negative_pct || 0}%`;
    
    const tone = data.tone_result || {};
    document.getElementById('valTone').textContent = tone.primary_tone || "Neutral";

    // Setup charts
    renderCharts(summary);

    // Populate common topics
    const topicsEl = document.getElementById('topicsList');
    topicsEl.innerHTML = '';
    const topicsData = data.topics_result || {};
    
    if (topicsData.status === 'skipped' || !topicsData.topics || topicsData.topics.length === 0) {
        topicsEl.innerHTML = `<div class="topic-pill"><span style="color: var(--text-secondary);">${topicsData.reason || "Insufficient negative comments to group."}</span></div>`;
    } else {
        topicsData.topics.forEach(t => {
            const div = document.createElement('div');
            div.className = 'topic-pill';
            div.innerHTML = `
                <span><strong>Theme ${t.topic_id + 1}:</strong> ${t.label}</span>
                <span class="btn btn-secondary" style="font-size: 0.75rem; padding: 0.2rem 0.6rem;">${t.document_count} items</span>
            `;
            topicsEl.appendChild(div);
        });
    }

    // Populate Critical Complaints
    const complaintsEl = document.getElementById('complaintsList');
    complaintsEl.innerHTML = '';
    const worst = data.worst_docs || [];
    
    if (worst.length === 0) {
        complaintsEl.innerHTML = '<div style="color: var(--text-muted); font-size: 0.9rem;">No major negative feedback parsed.</div>';
    } else {
        worst.slice(0, 4).forEach(doc => {
            const div = document.createElement('div');
            div.className = 'complaint-item';
            div.innerHTML = `
                <div style="display:flex; justify-content:space-between; font-size:0.8rem; color:var(--text-secondary); margin-bottom:0.4rem;">
                    <span>Source: <strong>${doc.source}</strong></span>
                    <span>Date: ${doc.date}</span>
                </div>
                <p style="font-size:0.9rem; line-height:1.5;">"${doc.text}"</p>
            `;
            complaintsEl.appendChild(div);
        });
    }

    // Render Strategy markdown text
    const strategyEl = document.getElementById('strategyReportText');
    const strategyMarkdown = data.strategy_report || "No strategy recommendations generated.";
    // Simple markdown format render
    strategyEl.innerHTML = formatMarkdown(strategyMarkdown);

    // Show PDF download button only if we have active cache ID
    // Check if we can extract it from the latest item in sidebar
    setTimeout(() => {
        const items = document.querySelectorAll('.history-item');
        if (items.length > 0) {
            // Assume the first one is the matching item we just ran or requested
            const firstItem = items[0];
            firstItem.click; // Let it set active if not set
        }
    }, 100);
}

function renderCharts(summary) {
    const pieCtx = document.getElementById('sentimentPieChart').getContext('2d');
    const barCtx = document.getElementById('sourceBarChart').getContext('2d');

    // Destroy existing instances if they exist
    if (sentimentPie) sentimentPie.destroy();
    if (sourceBar) sourceBar.destroy();

    // 1. Sentiment Pie Chart
    sentimentPie = new Chart(pieCtx, {
        type: 'doughnut',
        data: {
            labels: ['Positive', 'Negative', 'Neutral'],
            datasets: [{
                data: [summary.positive_pct || 0, summary.negative_pct || 0, summary.neutral_pct || 0],
                backgroundColor: ['#10b981', '#ef4444', '#f59e0b'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#f3f4f6', font: { family: 'Outfit' } }
                }
            }
        }
    });

    // 2. Source Bar Chart
    const sources = summary.by_source || {};
    const labels = Object.keys(sources);
    const posData = [];
    const negData = [];
    const neuData = [];

    labels.forEach(s => {
        const counts = sources[s] || {};
        posData.push(counts.Positive || 0);
        negData.push(counts.Negative || 0);
        neuData.push(counts.Neutral || 0);
    });

    sourceBar = new Chart(barCtx, {
        type: 'bar',
        data: {
            labels: labels.map(l => l.toUpperCase()),
            datasets: [
                { label: 'Positive', data: posData, backgroundColor: '#10b981' },
                { label: 'Negative', data: negData, backgroundColor: '#ef4444' },
                { label: 'Neutral', data: neuData, backgroundColor: '#f59e0b' }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { ticks: { color: '#9ca3af' }, grid: { display: false } },
                y: { ticks: { color: '#9ca3af' }, grid: { color: 'rgba(255,255,255,0.05)' } }
            },
            plugins: {
                legend: {
                    labels: { color: '#f3f4f6', font: { family: 'Outfit' } }
                }
            }
        }
    });
}

function downloadPdfReport() {
    if (!currentReportId || !currentBrandName) {
        alert("Please select a completed analysis report first.");
        return;
    }
    API.downloadPdf(currentReportId, currentBrandName).catch(err => alert("PDF download failed."));
}

function formatMarkdown(text) {
    if (typeof text !== 'string') {
        if (text && typeof text === 'object') {
            return formatStrategyJson(text); // Handle the JSON object natively
        } else {
            return "No strategy recommendations generated.";
        }
    }
    return text
        .replace(/\n/g, '<br>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/### (.*?)(<br>|$)/g, '<h4 style="font-size:1.1rem; margin-top:1.2rem; color:var(--text-primary); font-weight:600;">$1</h4>')
        .replace(/## (.*?)(<br>|$)/g, '<h3 style="font-size:1.3rem; margin-top:1.5rem; color:var(--text-primary); font-weight:700;">$1</h3>')
        .replace(/- (.*?)(<br>|$)/g, '<div style="margin-left: 1rem; margin-top: 0.3rem;">• $1</div>');
}

function formatStrategyJson(data) {
    let html = '';
    
    if (data.current_strategy) {
        html += '<h3 style="font-size:1.3rem; margin-top:1.5rem; color:var(--text-primary); font-weight:700;">Current Marketing Strategy</h3>';
        html += `<p style="line-height:1.6;">${data.current_strategy}</p>`;
    }
    
    if (data.strengths && data.strengths.length > 0) {
        html += '<h3 style="font-size:1.3rem; margin-top:1.5rem; color:var(--text-primary); font-weight:700;">Strengths</h3>';
        html += '<ul style="margin-left: 1.5rem; margin-top: 0.5rem; list-style-type: disc;">';
        data.strengths.forEach(s => html += `<li style="margin-bottom:0.3rem;">${s}</li>`);
        html += '</ul>';
    }
    
    if (data.weaknesses && data.weaknesses.length > 0) {
        html += '<h3 style="font-size:1.3rem; margin-top:1.5rem; color:var(--text-primary); font-weight:700;">Weaknesses</h3>';
        html += '<ul style="margin-left: 1.5rem; margin-top: 0.5rem; list-style-type: disc;">';
        data.weaknesses.forEach(w => html += `<li style="margin-bottom:0.3rem;">${w}</li>`);
        html += '</ul>';
    }
    
    if (data.recommendations && data.recommendations.length > 0) {
        html += '<h3 style="font-size:1.3rem; margin-top:1.5rem; color:var(--text-primary); font-weight:700;">Actionable Recommendations</h3>';
        data.recommendations.forEach((r, i) => {
            html += `<h4 style="font-size:1.1rem; margin-top:1.2rem; color:var(--text-primary); font-weight:600;">${i+1}. ${r.title}</h4>`;
            html += `<p style="margin-left: 1rem; margin-top: 0.3rem;">${r.explanation}</p>`;
        });
    }
    
    return html || "No structured strategy generated.";
}

// Example prompts
const examples = [
    "Compare Python and JavaScript for backend web development",
    "Plan a 3-day trip to Paris including budget breakdown, top attractions, and restaurant recommendations",
    "Research the history of artificial intelligence and then write a comprehensive summary based on that research"
];

// Navigation
function navigate(page) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.getElementById(page).classList.add('active');
    document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'));
    event.target.closest('.nav-item').classList.add('active');
}

// Load example
function loadExample(index) {
    document.getElementById('prompt-input').value = examples[index];
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadMetrics();
    loadBenchmarks();
    document.getElementById('prompt-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && e.ctrlKey) runDemo();
    });
});

// Load Metrics
async function loadMetrics() {
    try {
        const response = await fetch('/metrics');
        const data = await response.json();
        if (data.error) return;

        document.getElementById('m-success').textContent = `${data.success_rate.toFixed(0)}%`;
        document.getElementById('m-speedup').textContent = `${data.avg_speedup}x`;
        document.getElementById('m-latency').textContent = `${data.avg_latency}s`;
        document.getElementById('m-total').textContent = data.total_prompts;
    } catch (error) {
        console.error('Failed to load metrics:', error);
    }
}

// Run Demo
async function runDemo() {
    const prompt = document.getElementById('prompt-input').value.trim();
    const model = document.getElementById('model-select').value;
    const count = document.getElementById('agent-count').value;

    if (!prompt) {
        alert('Please enter a prompt first!');
        return;
    }

    document.getElementById('loading').style.display = 'flex';
    document.getElementById('plan-display').style.display = 'none';
    document.getElementById('results-display').style.display = 'none';
    document.getElementById('results-container').innerHTML = '';

    try {
        // Step 1: Analyze Prompt
        const analyzeRes = await fetch('/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                prompt: prompt,
                model: model || null,
                agent_count: count ? parseInt(count) : null
            })
        });
        const plan = await analyzeRes.json();
        displayPlan(plan);

        // Step 2: Execute Plan (with visual simulation)
        const executePromise = fetch('/execute', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode: plan.mode, plan: plan.plan, prompt: prompt })
        });

        // Run simulation concurrently
        const simulationPromise = simulateExecution(plan);

        // Wait for both (so user sees the full animation at least, or waits for result)
        const [executeRes, _] = await Promise.all([executePromise, simulationPromise]);

        const results = await executeRes.json();
        displayResults(results);
    } catch (error) {
        alert('Error: ' + error.message);
    } finally {
        document.getElementById('loading').style.display = 'none';
    }
}

// Display Plan
function displayPlan(plan) {
    console.log("displayPlan called with:", plan);
    const display = document.getElementById('plan-display');
    display.style.display = 'block';

    // Clear previous content
    display.innerHTML = `
        <h3>📋 Execution Plan</h3>
        <div class="plan-badge" id="mode-badge">Mode ${plan.mode}</div>
        <div id="visual-plan-container"></div>
        <button class="view-json-btn" onclick="toggleJsonPlan()">Show Raw JSON</button>
        <div id="plan-details" class="plan-details-container" style="display: none;">${JSON.stringify(plan, null, 2)}</div>
    `;

    renderVisualPlan(plan);
}

function toggleJsonPlan() {
    const details = document.getElementById('plan-details');
    const btn = document.querySelector('.view-json-btn');
    if (details.style.display === 'none') {
        details.style.display = 'block';
        btn.textContent = 'Hide Raw JSON';
    } else {
        details.style.display = 'none';
        btn.textContent = 'Show Raw JSON';
    }
}

function renderVisualPlan(plan) {
    console.log("renderVisualPlan called");
    const container = document.getElementById('visual-plan-container');

    // Create Flow Container
    const flow = document.createElement('div');
    flow.className = 'execution-flow';

    // Step 1: Prompt
    flow.innerHTML += `
        <div class="flow-step active">
            <div class="flow-icon">⌨️</div>
            <div class="flow-label">Prompt</div>
        </div>
        <div class="flow-connector active"></div>
    `;

    // Step 2: Planner
    flow.innerHTML += `
        <div class="flow-step active">
            <div class="flow-icon">🧠</div>
            <div class="flow-label">Planner</div>
        </div>
        <div class="flow-connector active"></div>
    `;

    // Step 3: Execution (DAG or Parallel)
    flow.innerHTML += `
        <div class="flow-step active">
            <div class="flow-icon">⚡</div>
            <div class="flow-label">Execution</div>
        </div>
        <div class="flow-connector"></div>
    `;

    // Step 4: Results
    flow.innerHTML += `
        <div class="flow-step" id="flow-result-step">
            <div class="flow-icon">📝</div>
            <div class="flow-label">Results</div>
        </div>
    `;

    container.appendChild(flow);

    // Create Detailed DAG View Container (Below the flow)
    const dagContainer = document.createElement('div');
    dagContainer.className = 'dag-detail-view';
    dagContainer.id = 'dag-detail-view';
    dagContainer.style.marginTop = '2rem';
    dagContainer.style.padding = '1rem';
    dagContainer.style.background = 'rgba(17, 24, 39, 0.5)';
    dagContainer.style.borderRadius = '12px';
    dagContainer.style.border = '1px solid rgba(148, 163, 184, 0.1)';
    container.appendChild(dagContainer);

    // Render Mode Specific Visuals in the new container
    if (plan.mode === 'B' && plan.plan && plan.plan.subtasks) {
        // Mode B: DAG Visualization
        const layers = organizeIntoLayers(plan.plan.subtasks);

        dagContainer.innerHTML = '<h4 style="color: #94a3b8; margin-bottom: 1rem;">Real-Time DAG Monitor</h4>';

        layers.forEach((layer, layerIdx) => {
            const layerDiv = document.createElement('div');
            layerDiv.className = 'dag-layer';

            layer.forEach(task => {
                const node = document.createElement('div');
                node.className = 'agent-node pending';
                node.id = `node-${task.id}`;
                node.innerHTML = `
                    <div class="node-icon">🤖</div>
                    <div class="node-info">
                        <div class="node-id">Agent ${task.id}</div>
                        <div class="node-desc">${task.description}</div>
                        <div class="node-model">${task.model}</div>
                        <div class="node-status">Pending</div>
                    </div>
                `;
                layerDiv.appendChild(node);
            });

            dagContainer.appendChild(layerDiv);

            // Add arrow if not last layer
            if (layerIdx < layers.length - 1) {
                const arrow = document.createElement('div');
                arrow.className = 'dag-arrow';
                arrow.innerHTML = '⬇️';
                dagContainer.appendChild(arrow);
            }
        });

    } else {
        // Mode A: Simple Parallel
        const models = plan.plan && plan.plan.models ? plan.plan.models : ['1', '2'];

        dagContainer.innerHTML = '<h4 style="color: #94a3b8; margin-bottom: 1rem;">Parallel Execution Monitor</h4>';

        const layerDiv = document.createElement('div');
        layerDiv.className = 'dag-layer';

        models.forEach((model, idx) => {
            const node = document.createElement('div');
            node.className = 'agent-node pending';
            node.id = `node-a-${idx}`;
            node.innerHTML = `
                <div class="node-icon">⚡</div>
                <div class="node-info">
                    <div class="node-id">Agent ${idx + 1}</div>
                    <div class="node-desc">Processing user prompt with ${model}</div>
                    <div class="node-model">${model}</div>
                    <div class="node-status">Pending</div>
                </div>
            `;
            layerDiv.appendChild(node);
        });

        dagContainer.appendChild(layerDiv);
    }
}

// Helper: Topological Sort into Layers
function organizeIntoLayers(subtasks) {
    const layers = [];
    let remaining = [...subtasks];
    let processedIds = new Set();

    while (remaining.length > 0) {
        const currentLayer = [];
        const nextRemaining = [];

        remaining.forEach(task => {
            const deps = task.depends_on || [];
            if (deps.every(d => processedIds.has(d))) {
                currentLayer.push(task);
            } else {
                nextRemaining.push(task);
            }
        });

        if (currentLayer.length === 0) {
            // Cycle detected or error, just dump rest
            layers.push(remaining);
            break;
        }

        layers.push(currentLayer);
        currentLayer.forEach(t => processedIds.add(t.id));
        remaining = nextRemaining;
    }
    return layers;
}

// Simulate Real-Time Progress (Visual only, while waiting for backend)
async function simulateExecution(plan) {
    if (plan.mode === 'B' && plan.plan && plan.plan.subtasks) {
        const layers = organizeIntoLayers(plan.plan.subtasks);

        for (let i = 0; i < layers.length; i++) {
            const layer = layers[i];

            // Mark layer as processing
            layer.forEach(task => {
                const node = document.getElementById(`node-${task.id}`);
                if (node) {
                    node.classList.remove('pending');
                    node.classList.add('processing');
                    node.querySelector('.node-status').textContent = 'Processing...';
                }
            });

            // Wait random time to simulate work (1.5s - 3s per layer)
            await new Promise(r => setTimeout(r, 1500 + Math.random() * 1500));

            // Mark layer as complete
            layer.forEach(task => {
                const node = document.getElementById(`node-${task.id}`);
                if (node) {
                    node.classList.remove('processing');
                    node.classList.add('completed');
                    node.querySelector('.node-status').textContent = 'Done';
                }
            });
        }
    } else {
        // Mode A Simulation
        const models = plan.plan && plan.plan.models ? plan.plan.models : ['1', '2'];

        // Start all
        models.forEach((_, idx) => {
            const node = document.getElementById(`node-a-${idx}`);
            if (node) {
                node.classList.remove('pending');
                node.classList.add('processing');
                node.querySelector('.node-status').textContent = 'Thinking...';
            }
        });

        await new Promise(r => setTimeout(r, 2000));

        // End all
        models.forEach((_, idx) => {
            const node = document.getElementById(`node-a-${idx}`);
            if (node) {
                node.classList.remove('processing');
                node.classList.add('completed');
                node.querySelector('.node-status').textContent = 'Done';
            }
        });
    }
}

// Display Results - WITH PREMIUM FORMATTING
let currentResultsData = [];

function displayResults(data) {
    currentResultsData = data.results; // Store for toggling
    const container = document.getElementById('results-container');
    container.innerHTML = '';

    // Activate the Results step in the flow
    const resultStep = document.getElementById('flow-result-step');
    if (resultStep) {
        resultStep.classList.add('active');
    }

    // Update Performance Metrics
    if (data.metrics) {
        const seq = data.metrics.sequential_baseline || 0;
        const maxParallel = Math.max(...data.results.map(r => r.latency || 0));
        const speedup = maxParallel > 0 ? seq / maxParallel : 0;

        document.getElementById('demo-sequential').textContent = `${seq.toFixed(2)}s`;
        document.getElementById('demo-parallel').textContent = `${maxParallel.toFixed(2)}s`;
        document.getElementById('demo-speedup').textContent = `${speedup.toFixed(2)}x`;
    } else {
        // Fallback if metrics missing
        document.getElementById('demo-sequential').textContent = '--s';
        document.getElementById('demo-parallel').textContent = '--s';
        document.getElementById('demo-speedup').textContent = '--x';
    }

    // 1. Display Combined Result (if available) - Full Width
    if (data.combined) {
        const combinedCard = document.createElement('div');
        combinedCard.className = 'result-card combined-result';
        combinedCard.style.border = '2px solid #8b5cf6'; // Violet border for emphasis
        combinedCard.style.background = 'linear-gradient(to bottom right, rgba(139, 92, 246, 0.1), rgba(17, 24, 39, 0.8))';
        combinedCard.style.marginBottom = '2rem'; // Spacing below combined result

        const formattedCombined = marked.parse(data.combined);

        combinedCard.innerHTML = `
            <div class="result-header">
                <span class="model-badge" style="background: #8b5cf6; color: white;">✨ Combined Result</span>
                <div class="result-meta">
                    <span>Synthesized from ${data.results.length} agents</span>
                </div>
            </div>
            <div class="result-content">
                <div class="result-text">${formattedCombined}</div>
            </div>
        `;
        container.appendChild(combinedCard);
    }

    // 2. Display Individual Results
    const agentsHeader = document.createElement('h4');
    agentsHeader.textContent = 'Individual Agent Outputs';
    agentsHeader.style.marginTop = '1rem';
    agentsHeader.style.marginBottom = '1rem';
    agentsHeader.style.color = '#94a3b8';
    container.appendChild(agentsHeader);

    // Create Grid for Individual Results
    const gridContainer = document.createElement('div');
    gridContainer.className = 'results-grid';
    container.appendChild(gridContainer);

    data.results.forEach((result, idx) => {
        const card = document.createElement('div');
        card.className = 'result-card';

        const modelName = result.model || 'Unknown';
        let response = result.response || result.error || 'No response';
        const latency = result.latency ? result.latency.toFixed(2) : '0.00';
        const tokens = result.tokens || 0;

        // Task Description (if available)
        const taskDesc = result.description ? `<div style="font-size: 0.9rem; color: #94a3b8; margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 1px dashed rgba(148, 163, 184, 0.2);"><strong>Task:</strong> ${result.description}</div>` : '';

        // Truncate long responses
        const MAX_LENGTH = 600;
        const isTruncated = response.length > MAX_LENGTH;
        const displayText = isTruncated ? response.substring(0, MAX_LENGTH) + '...' : response;

        // Format text using marked.js
        const formattedText = marked.parse(displayText);

        card.innerHTML = `
            <div class="result-header">
                <span class="model-badge">${modelName}</span>
                <div class="result-meta">
                    <span title="Latency (seconds)">⏱️ ${latency}s</span>
                    <span title="Token Usage">🪙 ${tokens}</span>
                </div>
            </div>
            <div class="result-content">
                ${taskDesc}
                <div class="result-text" id="text-${idx}">${formattedText}</div>
                ${isTruncated ? `
                    <button class="example-btn" style="margin-top: 1rem; font-size: 0.8rem;" onclick="toggleText(${idx})">
                        Show Full Response
                    </button>
                ` : ''}
            </div>
        `;

        gridContainer.appendChild(card);
    });

    document.getElementById('results-display').style.display = 'block';
}

// Toggle full text
function toggleText(idx) {
    const elem = document.getElementById(`text-${idx}`);
    const btn = event.target;
    const fullText = currentResultsData[idx].response || currentResultsData[idx].error || '';

    if (btn.textContent.includes('Show Full')) {
        elem.innerHTML = marked.parse(fullText);
        btn.textContent = 'Show Less';
    } else {
        const short = fullText.substring(0, 600) + '...';
        elem.innerHTML = marked.parse(short);
        btn.textContent = 'Show Full Response';
    }
}

// Load Benchmarks
async function loadBenchmarks() {
    try {
        const response = await fetch('/metrics');
        const data = await response.json();
        if (data.error || !data.details) return;

        const tbody = document.querySelector('#benchmark-table tbody');
        tbody.innerHTML = '';

        data.details.forEach(item => {
            const row = tbody.insertRow();

            // Truncate prompt for display
            const promptText = item.prompt || '';
            const shortPrompt = promptText.length > 50 ? promptText.substring(0, 50) + '...' : promptText;

            row.innerHTML = `
                <td>${item.prompt_id}</td>
                <td>${item.category}</td>
                <td title="${promptText.replace(/"/g, '&quot;')}">${shortPrompt}</td>
                <td><span class="mode-badge">Mode ${item.mode_detected}</span></td>
                <td>${item.total_latency.toFixed(2)}s</td>
                <td>${item.speedup.toFixed(2)}x</td>
                <td>${item.success_rate}%</td>
            `;
        });

        createChart(data.details);
    } catch (error) {
        console.error('Failed to load benchmarks:', error);
    }
}

// Create Chart
function createChart(data) {
    const categories = {};
    data.forEach(item => {
        if (!categories[item.category]) categories[item.category] = [];
        categories[item.category].push(item.speedup);
    });

    const labels = Object.keys(categories);
    const values = labels.map(cat => {
        const arr = categories[cat];
        return arr.reduce((a, b) => a + b, 0) / arr.length;
    });

    const ctx = document.getElementById('speedupChart').getContext('2d');

    // Destroy existing chart if it exists
    if (window.myChart) window.myChart.destroy();

    window.myChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Average Speedup',
                data: values,
                backgroundColor: 'rgba(99, 102, 241, 0.5)', // Indigo with opacity
                borderColor: '#6366f1', // Indigo solid
                borderWidth: 2,
                borderRadius: 8,
                hoverBackgroundColor: '#8b5cf6' // Violet on hover
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    labels: {
                        color: '#94a3b8',
                        font: { family: "'Space Grotesk', sans-serif" }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: '#94a3b8',
                        font: { family: "'Space Grotesk', sans-serif" }
                    },
                    grid: { color: 'rgba(148, 163, 184, 0.1)' }
                },
                x: {
                    ticks: {
                        color: '#94a3b8',
                        font: { family: "'Space Grotesk', sans-serif" }
                    },
                    grid: { display: false }
                }
            }
        }
    });
}

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

        // Step 2: Human-in-the-Loop Review
        document.getElementById('loading').style.display = 'none';
        document.getElementById('plan-review-container').style.display = 'block';

        // Store plan globally
        window.currentPlan = plan;
        window.currentPrompt = prompt;

        // Generate Review Cards
        const container = document.getElementById('review-cards-container');
        container.innerHTML = '';

        if (plan.mode === 'B') {
            plan.plan.subtasks.forEach((task, index) => {
                const card = document.createElement('div');
                card.className = 'review-card';
                card.innerHTML = `
                    <div class="review-card-header">
                        <span class="review-agent-id">Agent ${task.id}</span>
                    </div>
                    <div class="review-input-group">
                        <label class="review-label">Task Description</label>
                        <input type="text" class="review-input task-desc-input" data-id="${task.id}" value="${task.description}">
                    </div>
                    <div class="review-input-group">
                        <label class="review-label">LLM Model</label>
                        <select class="review-select task-model-input" data-id="${task.id}">
                            <option value="llama-3.3-70b-versatile" ${task.model === 'llama-3.3-70b-versatile' ? 'selected' : ''}>Llama 3.3 70B</option>
                            <option value="llama-3.1-8b-instant" ${task.model === 'llama-3.1-8b-instant' ? 'selected' : ''}>Llama 3.1 8B</option>
                        </select>
                    </div>
                `;
                container.appendChild(card);
            });
        } else {
            // Mode A
            const models = plan.plan.models || ['llama-3.1-8b-instant', 'llama-3.1-8b-instant'];
            models.forEach((model, index) => {
                const card = document.createElement('div');
                card.className = 'review-card';
                card.innerHTML = `
                    <div class="review-card-header">
                        <span class="review-agent-id">Agent ${index + 1}</span>
                    </div>
                    <div class="review-input-group">
                        <label class="review-label">LLM Model</label>
                        <select class="review-select mode-a-model-input" data-index="${index}">
                            <option value="llama-3.3-70b-versatile" ${model === 'llama-3.3-70b-versatile' ? 'selected' : ''}>Llama 3.3 70B</option>
                            <option value="llama-3.1-8b-instant" ${model === 'llama-3.1-8b-instant' ? 'selected' : ''}>Llama 3.1 8B</option>
                        </select>
                    </div>
                `;
                container.appendChild(card);
            });
        }

    } catch (error) {
        alert('Error: ' + error.message);
        document.getElementById('loading').style.display = 'none';
    }
}

// Execute Approved Plan
async function executeApprovedPlan() {
    try {
        const plan = window.currentPlan;

        // Update plan with values from UI
        if (plan.mode === 'B') {
            const descInputs = document.querySelectorAll('.task-desc-input');
            const modelInputs = document.querySelectorAll('.task-model-input');

            descInputs.forEach(input => {
                const id = input.dataset.id;
                // Use loose equality (==) to handle string/number mismatch
                const task = plan.plan.subtasks.find(t => t.id == id);
                if (task) {
                    console.log(`Updating task ${id} description: ${input.value}`);
                    task.description = input.value;
                }
            });

            modelInputs.forEach(input => {
                const id = input.dataset.id;
                // Use loose equality (==) to handle string/number mismatch
                const task = plan.plan.subtasks.find(t => t.id == id);
                if (task) {
                    console.log(`Updating task ${id} model: ${input.value}`);
                    task.model = input.value;
                }
            });
        } else {
            // Mode A
            const modelInputs = document.querySelectorAll('.mode-a-model-input');
            const newModels = [];
            modelInputs.forEach(input => {
                newModels.push(input.value);
            });
            plan.plan.models = newModels;
        }

        // Hide review, show loading
        document.getElementById('plan-review-container').style.display = 'none';
        document.getElementById('loading').style.display = 'flex';

        // Re-render visual plan in case it changed
        displayPlan(plan);

        // Execute Plan
        const executePromise = fetch('/execute', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode: plan.mode, plan: plan.plan, prompt: window.currentPrompt })
        });

        // Run simulation
        const simulationPromise = simulateExecution(plan);

        const [executeRes, _] = await Promise.all([executePromise, simulationPromise]);
        const results = await executeRes.json();
        displayResults(results);

    } catch (error) {
        alert('Error during execution: ' + error.message);
    } finally {
        document.getElementById('loading').style.display = 'none';
    }
}


// Cancel Execution
function cancelExecution() {
    document.getElementById('plan-review-container').style.display = 'none';
    document.getElementById('plan-display').style.display = 'none';
    document.getElementById('results-display').style.display = 'none';
    document.getElementById('loading').style.display = 'none';
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
                const arrowDiv = document.createElement('div');
                arrowDiv.className = 'dag-arrow';
                arrowDiv.innerHTML = '➜';
                dagContainer.appendChild(arrowDiv);
            }
        });

    } else {
        // Mode A: Parallel Visualization
        dagContainer.innerHTML = '<h4 style="color: #94a3b8; margin-bottom: 1rem;">Parallel Agent Monitor</h4>';
        const agentGrid = document.createElement('div');
        agentGrid.className = 'agent-grid';

        const models = plan.plan.models || ['llama-3.1-8b-instant', 'llama-3.1-8b-instant'];
        models.forEach((model, index) => {
            const node = document.createElement('div');
            node.className = 'agent-node pending';
            node.id = `node-${index + 1}`;
            node.innerHTML = `
                <div class="node-icon">🤖</div>
                <div class="node-info">
                    <div class="node-id">Agent ${index + 1}</div>
                    <div class="node-desc">Processing full prompt</div>
                    <div class="node-model">${model}</div>
                    <div class="node-status">Pending</div>
                </div>
            `;
            agentGrid.appendChild(node);
        });
        dagContainer.appendChild(agentGrid);
    }
}

// Helper to organize tasks into layers for DAG
function organizeIntoLayers(tasks) {
    const layers = [];
    const visited = new Set();
    let currentLayer = tasks.filter(t => !t.dependencies || t.dependencies.length === 0);

    while (currentLayer.length > 0) {
        layers.push(currentLayer);
        currentLayer.forEach(t => visited.add(t.id));

        // Find next layer: tasks whose dependencies are all visited
        currentLayer = tasks.filter(t =>
            !visited.has(t.id) &&
            t.dependencies &&
            t.dependencies.every(depId => visited.has(depId))
        );
    }
    return layers;
}

// Simulate Execution (Visuals only)
async function simulateExecution(plan) {
    const steps = document.querySelectorAll('.flow-step');
    const connectors = document.querySelectorAll('.flow-connector');

    // Step 3: Execution Active
    steps[2].classList.add('active');
    if (connectors[2]) connectors[2].classList.add('active');

    // Simulate Agent Progress
    if (plan.mode === 'B') {
        const tasks = plan.plan.subtasks;
        // Simple simulation: iterate through layers
        const layers = organizeIntoLayers(tasks);

        for (const layer of layers) {
            await new Promise(r => setTimeout(r, 1000)); // Simulate work
            layer.forEach(task => {
                const node = document.getElementById(`node-${task.id}`);
                if (node) {
                    node.classList.remove('pending');
                    node.classList.add('completed');
                    node.querySelector('.node-status').textContent = 'Completed';
                }
            });
        }
    } else {
        // Mode A
        const count = (plan.plan.models || []).length;
        for (let i = 1; i <= count; i++) {
            await new Promise(r => setTimeout(r, 800));
            const node = document.getElementById(`node-${i}`);
            if (node) {
                node.classList.remove('pending');
                node.classList.add('completed');
                node.querySelector('.node-status').textContent = 'Completed';
            }
        }
    }

    // Step 4: Results Active
    steps[3].classList.add('active');
}

// Display Results
function displayResults(results) {
    const container = document.getElementById('results-container');
    document.getElementById('results-display').style.display = 'block';

    // Update Metrics
    if (results.metrics) {
        document.getElementById('demo-sequential').textContent = `${results.metrics.sequential_time.toFixed(2)}s`;
        document.getElementById('demo-parallel').textContent = `${results.metrics.parallel_time.toFixed(2)}s`;
        document.getElementById('demo-speedup').textContent = `${results.metrics.speedup.toFixed(1)}x`;
    }

    // Render Result Cards
    if (results.mode === 'B') {
        // Combined Result
        container.innerHTML = `
            <div class="result-card">
                <div class="result-header">
                    <h3>🎉 Final Aggregated Result</h3>
                    <span class="model-badge">Consensus</span>
                </div>
                <div class="result-content">${marked.parse(results.final_result)}</div>
            </div>
        `;

        // Individual Results (Mode B)
        const subtasksHeader = document.createElement('h3');
        subtasksHeader.style.marginTop = '2rem';
        subtasksHeader.style.marginBottom = '1rem';
        subtasksHeader.style.color = '#e2e8f0';
        subtasksHeader.textContent = 'Individual Agent Contributions';
        container.appendChild(subtasksHeader);

        const gridContainer = document.createElement('div');
        gridContainer.className = 'results-grid';
        container.appendChild(gridContainer);

        results.responses.forEach((res) => {
            const card = document.createElement('div');
            card.className = 'result-card';
            card.innerHTML = `
                <div class="result-header">
                    <div>
                        <h3>Agent ${res.id}: ${res.task || 'Task'}</h3>
                        <div class="result-metrics">
                            <span>⏱️ ${res.latency}s</span>
                            <span>📝 ${res.tokens} tokens</span>
                        </div>
                    </div>
                    <span class="model-badge">${res.model}</span>
                </div>
                <div class="result-content">${marked.parse(res.response)}</div>
            `;
            gridContainer.appendChild(card);
        });

    } else {
        // Individual Results (Mode A)

        // Combined Result (Synthesis)
        container.innerHTML = `
            <div class="result-card">
                <div class="result-header">
                    <h3>🎉 Final Aggregated Result</h3>
                    <span class="model-badge">Synthesis</span>
                </div>
                <div class="result-content">${marked.parse(results.final_result)}</div>
            </div>
        `;

        const subtasksHeader = document.createElement('h3');
        subtasksHeader.style.marginTop = '2rem';
        subtasksHeader.style.marginBottom = '1rem';
        subtasksHeader.style.color = '#e2e8f0';
        subtasksHeader.textContent = 'Individual Model Responses';
        container.appendChild(subtasksHeader);

        const gridContainer = document.createElement('div');
        gridContainer.className = 'results-grid';
        container.appendChild(gridContainer);

        results.responses.forEach((res, index) => {
            const card = document.createElement('div');
            card.className = 'result-card';
            card.innerHTML = `
                <div class="result-header">
                    <div>
                        <h3>Agent ${index + 1} Response</h3>
                        <div class="result-metrics">
                            <span>⏱️ ${res.latency}s</span>
                            <span>📝 ${res.tokens} tokens</span>
                        </div>
                    </div>
                    <span class="model-badge">${res.model}</span>
                </div>
                <div class="result-content">${marked.parse(res.response)}</div>
            `;
            gridContainer.appendChild(card);
        });
    }

    // Refresh global metrics
    loadMetrics();
    loadBenchmarks();
}

// Load Benchmarks Table
async function loadBenchmarks() {
    try {
        const response = await fetch('/benchmarks');
        const data = await response.json();
        const tbody = document.querySelector('#benchmark-table tbody');
        tbody.innerHTML = '';

        // Sort by timestamp desc
        data.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

        data.forEach(run => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>#${run.prompt_id}</td>
                <td>${run.category}</td>
                <td>${run.prompt.substring(0, 50)}...</td>
                <td>${run.mode_detected}</td>
                <td>${run.total_latency.toFixed(2)}s</td>
                <td>${run.speedup.toFixed(1)}x</td>
                <td><span class="status-dot" style="display:inline-block"></span></td>
            `;
            tbody.appendChild(row);
        });

        renderChart(data);
    } catch (error) {
        console.error('Failed to load benchmarks:', error);
    }
}

function renderChart(data) {
    const ctx = document.getElementById('speedupChart').getContext('2d');

    // Prepare data (show all runs in chronological order)
    const chronological = [...data].reverse();
    const labels = chronological.map(d => `#${d.prompt_id}`);
    const speedups = chronological.map(d => d.speedup);

    if (window.myChart) {
        window.myChart.destroy();
    }

    window.myChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Speedup Factor',
                data: speedups,
                borderColor: '#8b5cf6',
                backgroundColor: 'rgba(139, 92, 246, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#94a3b8' }
                }
            },
            scales: {
                y: {
                    grid: { color: 'rgba(148, 163, 184, 0.1)' },
                    ticks: { color: '#94a3b8' }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#94a3b8' }
                }
            }
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('scraper-form');
    const resultsContainer = document.getElementById('results-container');
    const pipelineTracker = document.getElementById('pipeline-tracker');
    
    let pollInterval = null;
    let currentTaskId = null;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const url = document.getElementById('url').value;
        const businessModel = document.getElementById('business-model').value;
        const agentRole = document.getElementById('agent-role').value;

        // Reset UI
        resultsContainer.style.display = 'none';
        resetPipeline();
        
        const submitBtn = document.getElementById('submit-btn');
        submitBtn.disabled = true;
        submitBtn.innerText = 'Orchestrating Agents...';

        try {
            const response = await fetch('/api/crawl-site', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    url,
                    max_pages: 30,
                    max_depth: 1,
                    business_model: businessModel,
                    agent_role: agentRole,
                    task_type: 'both'
                })
            });

            const data = await response.json();
            currentTaskId = data.task_id;
            startPolling(data.task_id);
        } catch (err) {
            alert('Error starting orchestrator: ' + err.message);
            submitBtn.disabled = false;
        }
    });

    function startPolling(taskId) {
        if (pollInterval) clearInterval(pollInterval);
        
        pollInterval = setInterval(async () => {
            try {
                const response = await fetch(`/api/crawl-status/${taskId}`);
                const data = await response.json();
                
                updateStatusUI(data.status);

                if (data.status === 'completed') {
                    clearInterval(pollInterval);
                    showResults(data);
                    document.getElementById('submit-btn').disabled = false;
                    document.getElementById('submit-btn').innerText = 'Run Multi-Agent Orchestrator';
                } else if (data.status === 'failed') {
                    clearInterval(pollInterval);
                    alert('Orchestration failed: ' + data.error);
                    document.getElementById('submit-btn').disabled = false;
                }
            } catch (err) {
                console.error('Polling error:', err);
            }
        }, 2000);
    }

    function updateStatusUI(status) {
        const steps = {
            'crawling': 'step-scrape',
            'building_kb': 'step-kb',
            'auditing_kb': 'step-audit',
            'generating_instructions': 'step-refine',
            'generating_qa': 'step-qa',
            'completed': 'step-qa'
        };

        const targetId = steps[status];
        if (targetId) {
            const stepEl = document.getElementById(targetId);
            // Mark previous steps as completed
            Object.values(steps).forEach(id => {
                const el = document.getElementById(id);
                if (el) el.classList.remove('active');
            });
            
            stepEl.classList.add('active');
            
            // Mark predecessors as completed
            const stepIds = Object.values(steps);
            const currentIndex = stepIds.indexOf(targetId);
            for(let i=0; i < currentIndex; i++) {
                document.getElementById(stepIds[i]).classList.add('completed');
            }
        }
    }

    function resetPipeline() {
        document.querySelectorAll('.pipeline-step').forEach(el => {
            el.classList.remove('active', 'completed');
        });
    }

    function showResults(data) {
        resultsContainer.style.display = 'block';
        
        // 1. Profile Content (Expanded)
        if (data.lead_analysis) {
            const profile = data.lead_analysis.company_profile;
            const fit = data.lead_analysis.ai_voice_agent_fit;
            const pain = data.lead_analysis.pain_points;

            document.getElementById('profile-content').innerHTML = `
                <!-- Overview Row -->
                <div class="stat-card" style="grid-column: span 2;">
                    <div class="stat-label">Company Summary</div>
                    <div class="stat-value" style="font-size: 1rem; line-height: 1.6; font-weight: 400;">${profile.short_summary}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">AI Readiness</div>
                    <div class="stat-value" style="color: var(--success)">${fit.fit_level} (${fit.fit_score}%)</div>
                </div>

                <!-- Details Grid -->
                <div class="stat-card">
                    <div class="stat-label">Industry</div>
                    <div class="stat-value" style="font-size: 0.9rem;">${profile.industry.join(', ')}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Target Customers</div>
                    <div class="stat-value" style="font-size: 0.9rem;">${profile.target_customers.join(', ')}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Business Type / Model</div>
                    <div class="stat-value">${profile.business_type}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Location & Size</div>
                    <div class="stat-value" style="font-size: 0.9rem;">${profile.location} ${profile.team_size ? ' | ' + profile.team_size : ''}</div>
                </div>

                <!-- Pain Points Section -->
                <div class="stat-card" style="grid-column: span 3; background: rgba(239, 68, 68, 0.05); border-color: rgba(239, 68, 68, 0.2);">
                    <div class="stat-label" style="color: var(--danger)">Detected Pain Points</div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-top: 1rem;">
                        <div>
                            <h4 style="font-size: 0.8rem; margin-bottom: 0.5rem; opacity: 0.8;">Customer Pain Points</h4>
                            <ul style="font-size: 0.85rem; padding-left: 1rem; color: #cbd5e1;">
                                ${pain.customer_pain_points.map(p => `<li style="margin-bottom: 0.4rem;">${p}</li>`).join('')}
                            </ul>
                        </div>
                        <div>
                            <h4 style="font-size: 0.8rem; margin-bottom: 0.5rem; opacity: 0.8;">Operational Inefficiencies</h4>
                            <ul style="font-size: 0.85rem; padding-left: 1rem; color: #cbd5e1;">
                                ${pain.operational_pain_points.map(p => `<li style="margin-bottom: 0.4rem;">${p}</li>`).join('')}
                            </ul>
                        </div>
                    </div>
                </div>
            `;
        }

        // 2. KB Editor
        document.getElementById('kb-editor').value = data.kb_content || '';
        if (data.kb_evaluation) {
            document.getElementById('kb-score-badge').innerText = `Score: ${data.kb_evaluation.score}`;
        }

        // 3. Instructions Editor
        if (data.agent_instructions) {
            document.getElementById('instruction-editor').value = data.agent_instructions.final_instructions;
            document.getElementById('refine-badge').style.display = data.agent_instructions.was_refined ? 'inline' : 'none';
        }

        // 4. QA List
        renderQA(data.qa_list || []);
    }

    function renderQA(qaList) {
        const qaContent = document.getElementById('qa-content');
        qaContent.innerHTML = qaList.map((qa, index) => `
            <div class="stat-card qa-item" data-index="${index}">
                <div class="field-group" style="margin-bottom: 0.5rem;">
                    <label style="font-size: 0.7rem; color: var(--accent-secondary);">Question</label>
                    <textarea class="qa-q-edit" style="width: 100%; background: transparent; border: 1px solid rgba(255,255,255,0.1); color: white; border-radius: 4px; padding: 0.5rem; font-size: 0.9rem;">${qa.question}</textarea>
                </div>
                <div class="field-group" style="margin-bottom: 0.5rem;">
                    <label style="font-size: 0.7rem; color: var(--success);">Answer</label>
                    <textarea class="qa-a-edit" style="width: 100%; background: transparent; border: 1px solid rgba(255,255,255,0.1); color: white; border-radius: 4px; padding: 0.5rem; font-size: 0.85rem;">${qa.answer}</textarea>
                </div>
                <div class="field-group">
                    <label style="font-size: 0.7rem; opacity: 0.5;">Category</label>
                    <input type="text" class="qa-t-edit" value="${qa.type_of_question}" style="width: 100%; background: transparent; border: 1px solid rgba(255,255,255,0.1); color: white; border-radius: 4px; padding: 0.2rem 0.5rem; font-size: 0.7rem; text-transform: uppercase;">
                </div>
                <button class="btn-secondary delete-qa" data-index="${index}" style="margin-top: 0.5rem; background: var(--danger); font-size: 0.7rem; padding: 0.2rem 0.5rem; border: none;">Delete</button>
            </div>
        `).join('');

        // Attach delete handlers
        document.querySelectorAll('.delete-qa').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const index = e.target.dataset.index;
                qaList.splice(index, 1);
                renderQA(qaList);
            });
        });
    }

    // Tab Switching
    document.querySelectorAll('.tab-link').forEach(link => {
        link.addEventListener('click', () => {
            document.querySelectorAll('.tab-link').forEach(l => l.classList.remove('active'));
            document.querySelectorAll('.tab-pane').forEach(p => p.style.display = 'none');
            
            link.classList.add('active');
            document.getElementById(link.dataset.tab).style.display = 'block';
        });
    });

    // Copy Buttons
    document.getElementById('copy-kb').addEventListener('click', () => {
        navigator.clipboard.writeText(document.getElementById('kb-editor').value);
        alert('KB copied!');
    });
    
    document.getElementById('copy-instructions').addEventListener('click', () => {
        navigator.clipboard.writeText(document.getElementById('instruction-editor').value);
        alert('Instructions copied!');
    });

    // Save Buttons
    document.getElementById('save-kb').addEventListener('click', async () => {
        if (!currentTaskId) return alert('No active task to save to.');
        const content = document.getElementById('kb-editor').value;
        
        try {
            const response = await fetch('/api/update-kb', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ task_id: currentTaskId, kb_content: content })
            });
            if (response.ok) {
                const btn = document.getElementById('save-kb');
                btn.innerText = 'Save KB';
                btn.style.boxShadow = 'none';
                alert('Knowledge Base saved successfully!');
            }
            else alert('Failed to save KB.');
        } catch (err) {
            alert('Error saving KB: ' + err.message);
        }
    });

    document.getElementById('save-instructions').addEventListener('click', async () => {
        if (!currentTaskId) return alert('No active task to save to.');
        const content = document.getElementById('instruction-editor').value;
        
        try {
            const response = await fetch('/api/update-instructions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ task_id: currentTaskId, instructions: content })
            });
            if (response.ok) {
                const btn = document.getElementById('save-instructions');
                btn.innerText = 'Save Instructions';
                btn.style.boxShadow = 'none';
                alert('Instructions saved successfully!');
            }
            else alert('Failed to save instructions.');
        } catch (err) {
            alert('Error saving instructions: ' + err.message);
        }
    });

    // Visual feedback for edits
    document.getElementById('kb-editor').addEventListener('input', () => {
        const btn = document.getElementById('save-kb');
        btn.innerText = 'Save KB (Unsaved Changes)';
        btn.style.boxShadow = '0 0 15px rgba(34, 197, 94, 0.5)';
    });

    document.getElementById('instruction-editor').addEventListener('input', () => {
        const btn = document.getElementById('save-instructions');
        btn.innerText = 'Save Instructions (Unsaved Changes)';
        btn.style.boxShadow = '0 0 15px rgba(34, 197, 94, 0.5)';
    });

    document.getElementById('add-qa').addEventListener('click', () => {
        const qaContent = document.getElementById('qa-content');
        const newIdx = document.querySelectorAll('.qa-item').length;
        const newHtml = `
            <div class="stat-card qa-item" data-index="${newIdx}">
                <div class="field-group" style="margin-bottom: 0.5rem;">
                    <label style="font-size: 0.7rem; color: var(--accent-secondary);">Question</label>
                    <textarea class="qa-q-edit" placeholder="Enter question..." style="width: 100%; background: transparent; border: 1px solid rgba(255,255,255,0.1); color: white; border-radius: 4px; padding: 0.5rem; font-size: 0.9rem;"></textarea>
                </div>
                <div class="field-group" style="margin-bottom: 0.5rem;">
                    <label style="font-size: 0.7rem; color: var(--success);">Answer</label>
                    <textarea class="qa-a-edit" placeholder="Enter answer..." style="width: 100%; background: transparent; border: 1px solid rgba(255,255,255,0.1); color: white; border-radius: 4px; padding: 0.5rem; font-size: 0.85rem;"></textarea>
                </div>
                <div class="field-group">
                    <label style="font-size: 0.7rem; opacity: 0.5;">Category</label>
                    <input type="text" class="qa-t-edit" placeholder="GENERAL" style="width: 100%; background: transparent; border: 1px solid rgba(255,255,255,0.1); color: white; border-radius: 4px; padding: 0.2rem 0.5rem; font-size: 0.7rem; text-transform: uppercase;">
                </div>
            </div>
        `;
        qaContent.insertAdjacentHTML('afterbegin', newHtml);
    });

    document.getElementById('save-qa').addEventListener('click', async () => {
        if (!currentTaskId) return alert('No active task to save to.');
        
        const qaItems = [];
        document.querySelectorAll('.qa-item').forEach(el => {
            qaItems.push({
                question: el.querySelector('.qa-q-edit').value,
                answer: el.querySelector('.qa-a-edit').value,
                type_of_question: el.querySelector('.qa-t-edit').value || 'General'
            });
        });

        try {
            const response = await fetch('/api/update-qa', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ task_id: currentTaskId, qa_list: qaItems })
            });
            if (response.ok) alert('Q&A pairs saved successfully!');
            else alert('Failed to save Q&A.');
        } catch (err) {
            alert('Error saving Q&A: ' + err.message);
        }
    });
});

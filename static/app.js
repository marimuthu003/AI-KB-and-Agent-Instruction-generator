document.addEventListener('DOMContentLoaded', () => {
    const currentCategoryTitle = document.getElementById('current-category');

    const scraperContainer = document.getElementById('scraper-container');
    const toolScraper = document.getElementById('tool-scraper');
    const scraperForm = document.getElementById('scraper-form');
    const scraperResults = document.getElementById('scraper-results');
    const scrapeBtn = document.getElementById('scrape-btn');
    const scraperStatus = document.getElementById('scraper-status');
    const scraperStatusText = document.getElementById('scraper-status-text');
    const scraperCount = document.getElementById('scraper-count');
    const scraperDisc = document.getElementById('scraper-disc');

    const kbContainer = document.getElementById('kb-container');
    const toolKb = document.getElementById('tool-kb');
    const kbForm = document.getElementById('kb-form');
    const kbResults = document.getElementById('kb-results');
    const scrapeKbBtn = document.getElementById('scrape-kb-btn');
    const kbTextarea = document.getElementById('kb-textarea');
    const kbDownloadBtn = document.getElementById('kb-download-btn');
    const kbStatus = document.getElementById('kb-status');
    const kbStatusText = document.getElementById('kb-status-text');
    const kbCount = document.getElementById('kb-count');
    const kbDisc = document.getElementById('kb-disc');

    // Tool navigation
    toolScraper.addEventListener('click', () => {
        toolScraper.classList.add('active');
        toolScraper.style.background = 'rgba(255,255,255,0.1)';
        toolKb.classList.remove('active');
        toolKb.style.background = 'transparent';
        scraperContainer.style.display = 'block';
        kbContainer.style.display = 'none';
        currentCategoryTitle.textContent = 'AI Web Scraper';
    });

    toolKb.addEventListener('click', () => {
        toolKb.classList.add('active');
        toolKb.style.background = 'rgba(255,255,255,0.1)';
        toolScraper.classList.remove('active');
        toolScraper.style.background = 'transparent';
        scraperContainer.style.display = 'none';
        kbContainer.style.display = 'block';
        currentCategoryTitle.textContent = 'Knowledge Base Scraper';
    });

    // Initial styles
    toolScraper.style.background = 'rgba(255,255,255,0.1)';

    // Scraper logic
    let pollIntervalScraper;
    scraperForm.onsubmit = async (e) => {
        e.preventDefault();
        const url = document.getElementById('scraper-url').value;
        const maxPages = parseInt(document.getElementById('scraper-max-pages').value);
        const maxDepth = parseInt(document.getElementById('scraper-max-depth').value);
        const businessModel = document.getElementById('scraper-business-model').value;
        const agentRole = document.getElementById('scraper-agent-role').value;

        scrapeBtn.disabled = true;
        scraperStatus.style.display = 'block';
        scraperResults.style.display = 'none';
        scraperStatusText.textContent = 'Initializing crawl...';
        
        try {
            const res = await fetch('/api/crawl-site', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    url, max_pages: maxPages, max_depth: maxDepth,
                    include_blog: true, include_docs: true, include_legal: false,
                    task_type: "lead_analysis",
                    business_model: businessModel,
                    agent_role: agentRole
                })
            });
            const data = await res.json();
            if(!res.ok) throw new Error(data.detail || 'Failed to start');
            
            const taskId = data.task_id;
            
            pollIntervalScraper = setInterval(async () => {
                try {
                    const statusRes = await fetch(`/api/crawl-status/${taskId}`);
                    const statusData = await statusRes.json();
                    
                    scraperCount.textContent = statusData.pages_crawled || 0;
                    scraperDisc.textContent = statusData.pages_discovered || 0;
                    scraperStatusText.textContent = `Status: ${statusData.status}`;
                    
                    if(statusData.status === 'completed' || statusData.status.startsWith('failed')) {
                        clearInterval(pollIntervalScraper);
                        scrapeBtn.disabled = false;
                        
                        if(statusData.status === 'completed') {
                            const lead = statusData.lead_analysis || {};
                            const core = lead.core || lead;
                            const profile = core.company_profile || core;
                            const pain = core.pain_points || {};
                            const fit = core.ai_voice_agent_fit || core.dakini_fit || {};

                            // 1. Profile Tab
                            document.getElementById('tab-profile').innerHTML = `
                                <div class="result-card">
                                    <h4 style="margin-bottom: 1.5rem; color: var(--accent);">Company Identity</h4>
                                    <div class="data-row"><span class="data-label">Name</span><span class="data-value">${profile.company_name || 'N/A'}</span></div>
                                    <div class="data-row"><span class="data-label">Website</span><span class="data-value"><a href="${profile.website}" target="_blank" style="color: var(--accent);">${profile.website || 'N/A'}</a></span></div>
                                    <div class="data-row"><span class="data-label">Location</span><span class="data-value">${profile.location || 'N/A'}</span></div>
                                    <div class="data-row"><span class="data-label">Size</span><span class="data-value">${profile.team_size || 'N/A'}</span></div>
                                    <div class="data-row"><span class="data-label">Model</span><span class="data-value">${profile.business_type || 'N/A'}</span></div>
                                    
                                    <div style="margin-top: 1.5rem;">
                                        <span class="data-label" style="display: block; margin-bottom: 0.5rem;">Industry & Sectors</span>
                                        <div>${(Array.isArray(profile.industry) ? profile.industry : [profile.industry || 'N/A']).map(i => `<span class="tag-pill">${i}</span>`).join('')}</div>
                                    </div>
                                </div>
                                <div class="result-card">
                                    <h4 style="margin-bottom: 1rem; color: var(--accent);">Target Audience</h4>
                                    <div>${(Array.isArray(profile.target_customers) ? profile.target_customers : [profile.target_customers || 'N/A']).map(t => `<span class="tag-pill" style="background: rgba(108, 99, 255, 0.1); border-color: var(--accent);">${t}</span>`).join('')}</div>
                                </div>
                                <div class="result-card">
                                    <h4 style="margin-bottom: 1rem; color: var(--accent);">Executive Summary</h4>
                                    <p style="color: var(--text-secondary); line-height: 1.6;">${profile.short_summary || 'N/A'}</p>
                                </div>
                            `;

                            // 2. Pain Points Tab
                            document.getElementById('tab-pain-points').innerHTML = `
                                <div class="result-card">
                                    <h4 style="margin-bottom: 1rem; color: var(--danger);">Customer Challenges</h4>
                                    ${(Array.isArray(pain.customer_pain_points) ? pain.customer_pain_points : []).map(p => `<div class="pain-point-item">${p}</div>`).join('') || '<p>N/A</p>'}
                                </div>
                                <div class="result-card">
                                    <h4 style="margin-bottom: 1rem; color: var(--warning);">Operational Bottlenecks</h4>
                                    ${(Array.isArray(pain.operational_pain_points) ? pain.operational_pain_points : []).map(p => `<div class="pain-point-item" style="border-left-color: var(--warning); background: rgba(255, 193, 7, 0.05);">${p}</div>`).join('') || '<p>N/A</p>'}
                                </div>
                                <div class="result-card">
                                    <h4 style="margin-bottom: 1rem;">Process Inefficiencies</h4>
                                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                                        <div>
                                            <strong style="font-size: 0.8rem; color: var(--text-secondary); display: block; margin-bottom: 0.5rem;">Manual Workflows</strong>
                                            ${(Array.isArray(pain.main_manual_workflows) ? pain.main_manual_workflows : []).map(w => `<div style="font-size: 0.85rem; margin-bottom: 0.4rem; color: #ccc;">• ${w}</div>`).join('') || 'N/A'}
                                        </div>
                                        <div>
                                            <strong style="font-size: 0.8rem; color: var(--text-secondary); display: block; margin-bottom: 0.5rem;">Comm-Heavy Tasks</strong>
                                            ${(Array.isArray(pain.communication_heavy_processes) ? pain.communication_heavy_processes : []).map(w => `<div style="font-size: 0.85rem; margin-bottom: 0.4rem; color: #ccc;">• ${w}</div>`).join('') || 'N/A'}
                                        </div>
                                    </div>
                                </div>
                            `;

                            // 3. AI Fit Tab
                            const score = fit.fit_score || 0;
                            document.getElementById('tab-ai-fit').innerHTML = `
                                <div class="fit-score-container">
                                    <div class="fit-score-gauge" data-score="${score}" style="--score-percent: ${score}%"></div>
                                    <div>
                                        <h3 style="color: #fff; margin-bottom: 0.5rem;">AI Readiness: ${fit.fit_level || 'N/A'}</h3>
                                        <p style="color: var(--text-secondary); font-size: 0.9rem;">${fit.fit_reason || fit.reason || 'No specific reason provided.'}</p>
                                    </div>
                                </div>
                                <div class="result-card">
                                    <h4 style="margin-bottom: 1rem; color: var(--success);">Recommended Solutions</h4>
                                    ${(Array.isArray(fit.problems_we_can_solve) ? fit.problems_we_can_solve : []).map(s => `<div class="solution-item">${s}</div>`).join('') || '<p>N/A</p>'}
                                </div>
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem;">
                                    <div class="result-card">
                                        <h4 style="margin-bottom: 1rem; font-size: 0.9rem;">Primary Use Cases</h4>
                                        <ul style="padding-left: 1rem; color: var(--text-secondary); font-size: 0.85rem;">
                                            ${(Array.isArray(fit.recommended_use_cases) ? fit.recommended_use_cases : []).map(u => `<li>${u}</li>`).join('') || 'N/A'}
                                        </ul>
                                    </div>
                                    <div class="result-card">
                                        <h4 style="margin-bottom: 1rem; font-size: 0.9rem;">Expected Benefits</h4>
                                        <ul style="padding-left: 1rem; color: var(--text-secondary); font-size: 0.85rem;">
                                            ${(Array.isArray(fit.expected_benefits) ? fit.expected_benefits : []).map(u => `<li>${u}</li>`).join('') || 'N/A'}
                                        </ul>
                                    </div>
                                </div>
                            `;

                            // 4. Raw Tab
                            document.getElementById('tab-raw').innerHTML = `
                                <pre style="background: rgba(0,0,0,0.3); padding: 1.5rem; border-radius: 12px; color: #00ff88; font-family: monospace; font-size: 0.85rem; overflow-x: auto; border: 1px solid var(--border-color);">${JSON.stringify(lead, null, 2)}</pre>
                            `;
                            
                            scraperResults.style.display = 'block';
                        } else {
                            alert('Crawl failed: ' + statusData.error);
                        }
                    }
                } catch(e) {
                    console.error("Polling error", e);
                }
            }, 2000);
            
        } catch (error) {
            alert(error.message);
            scrapeBtn.disabled = false;
            scraperStatus.style.display = 'none';
        }
    };

    // KB Scraper logic
    let pollIntervalKb;
    kbForm.onsubmit = async (e) => {
        e.preventDefault();
        const url = document.getElementById('kb-url').value;
        const maxPages = parseInt(document.getElementById('kb-max-pages').value);
        const maxDepth = parseInt(document.getElementById('kb-max-depth').value);
        const businessModel = document.getElementById('kb-business-model').value;
        const agentRole = document.getElementById('kb-agent-role').value;

        scrapeKbBtn.disabled = true;
        kbStatus.style.display = 'block';
        kbResults.style.display = 'none';
        kbStatusText.textContent = 'Initializing crawl...';
        
        try {
            const res = await fetch('/api/crawl-site', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    url, max_pages: maxPages, max_depth: maxDepth,
                    include_blog: true, include_docs: true, include_legal: false,
                    task_type: "kb_generation",
                    business_model: businessModel,
                    agent_role: agentRole
                })
            });
            const data = await res.json();
            if(!res.ok) throw new Error(data.detail || 'Failed to start');
            
            const taskId = data.task_id;
            
            pollIntervalKb = setInterval(async () => {
                try {
                    const statusRes = await fetch(`/api/crawl-status/${taskId}`);
                    const statusData = await statusRes.json();
                    
                    kbCount.textContent = statusData.pages_crawled || 0;
                    kbDisc.textContent = statusData.pages_discovered || 0;
                    kbStatusText.textContent = `Status: ${statusData.status}`;
                    
                    if(statusData.status === 'completed' || statusData.status.startsWith('failed')) {
                        clearInterval(pollIntervalKb);
                        scrapeKbBtn.disabled = false;
                        
                        if(statusData.status === 'completed') {
                            kbTextarea.value = statusData.kb_preview || "No KB generated";
                            kbResults.style.display = 'block';
                            
                            kbDownloadBtn.onclick = () => {
                                window.location.href = `/api/download-kb/${taskId}`;
                            };
                        } else {
                            alert('Crawl failed: ' + statusData.error);
                        }
                    }
                } catch(e) {
                    console.error("Polling error", e);
                }
            }, 2000);
            
        } catch (error) {
            alert(error.message);
            scrapeKbBtn.disabled = false;
            kbStatus.style.display = 'none';
        }
    };
});

window.switchTab = function(tabId) {
    // Update buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
        if(btn.getAttribute('onclick').includes(tabId)) {
            btn.classList.add('active');
        }
    });
    
    // Update panels
    document.querySelectorAll('.tab-panel').forEach(panel => {
        panel.classList.remove('active');
    });
    const targetPanel = document.getElementById(`tab-${tabId}`);
    if (targetPanel) targetPanel.classList.add('active');
};

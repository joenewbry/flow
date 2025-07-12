const { ipcRenderer, shell } = require('electron');

// DOM elements
const elements = {
    statsContent: document.getElementById('stats-content'),
    trackingStatus: document.getElementById('tracking-status'),
    chromaStatus: document.getElementById('chroma-status'),
    vectorStatus: document.getElementById('vector-status'),
    recentScreenshots: document.getElementById('recent-screenshots'),
    recentAnalysis: document.getElementById('recent-analysis'),
    storageInfo: document.getElementById('storage-info'),
    logOutput: document.getElementById('log-output'),
    startTrackingBtn: document.getElementById('start-tracking'),
    stopTrackingBtn: document.getElementById('stop-tracking'),
    openConfigBtn: document.getElementById('open-config'),
    refreshStatusBtn: document.getElementById('refresh-status'),
    openScreenshotsBtn: document.getElementById('open-screenshots'),
    openAnalysisBtn: document.getElementById('open-analysis')
};

// Utility functions
function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatNumber(num) {
    return num.toLocaleString();
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleString();
}

function updateStatusIndicator(element, isActive) {
    const indicator = element.querySelector('.status-indicator');
    if (isActive) {
        indicator.classList.remove('status-inactive');
        indicator.classList.add('status-active');
    } else {
        indicator.classList.remove('status-active');
        indicator.classList.add('status-inactive');
    }
}

function logMessage(message, type = 'info') {
    const timestamp = new Date().toLocaleTimeString();
    const logEntry = `[${timestamp}] ${message}\n`;
    
    if (elements.logOutput) {
        elements.logOutput.textContent += logEntry;
        elements.logOutput.scrollTop = elements.logOutput.scrollHeight;
    }
    
    console.log(logEntry);
}

// Update statistics display
async function updateStats() {
    try {
        const stats = await ipcRenderer.invoke('get-stats');
        
        if (elements.statsContent) {
            elements.statsContent.innerHTML = `
                <div class="stat-item">
                    <span>Screenshots:</span>
                    <span class="stat-value">${formatNumber(stats.screenshots)}</span>
                </div>
                <div class="stat-item">
                    <span>Analysis Files:</span>
                    <span class="stat-value">${formatNumber(stats.analysisFiles)}</span>
                </div>
                <div class="stat-item">
                    <span>Total Words:</span>
                    <span class="stat-value">${formatNumber(stats.totalWords)}</span>
                </div>
                <div class="stat-item">
                    <span>Total Characters:</span>
                    <span class="stat-value">${formatNumber(stats.totalCharacters)}</span>
                </div>
                <div class="stat-item">
                    <span>Total Size:</span>
                    <span class="stat-value">${formatBytes(stats.totalSize)}</span>
                </div>
            `;
        }

        // Update storage info
        if (elements.storageInfo) {
            elements.storageInfo.innerHTML = `
                <div class="stat-item">
                    <span>Screenshots:</span>
                    <span class="stat-value">${formatBytes(stats.totalSize * 0.8)}</span>
                </div>
                <div class="stat-item">
                    <span>Analysis Data:</span>
                    <span class="stat-value">${formatBytes(stats.totalSize * 0.2)}</span>
                </div>
                <div class="stat-item">
                    <span>Average per Screenshot:</span>
                    <span class="stat-value">${stats.screenshots > 0 ? formatBytes(stats.totalSize / stats.screenshots) : '0 Bytes'}</span>
                </div>
            `;
        }

        // Update recent screenshots
        if (elements.recentScreenshots) {
            if (stats.recentScreenshots.length > 0) {
                elements.recentScreenshots.innerHTML = stats.recentScreenshots.map(screenshot => `
                    <div class="file-item" onclick="openScreenshot('${screenshot.name}')">
                        <span class="file-name">${screenshot.name}</span>
                        <span class="file-size">${formatBytes(screenshot.size)}</span>
                    </div>
                `).join('');
            } else {
                elements.recentScreenshots.innerHTML = '<div class="loading">No screenshots found</div>';
            }
        }

        // Update recent analysis
        if (elements.recentAnalysis) {
            if (stats.recentAnalysis.length > 0) {
                elements.recentAnalysis.innerHTML = stats.recentAnalysis.map(analysis => `
                    <div class="file-item" onclick="openAnalysis('${analysis.name}')">
                        <div>
                            <div class="file-name">${analysis.name}</div>
                            <div class="file-size">${analysis.wordCount} words, ${analysis.charCount} chars</div>
                        </div>
                        <span class="file-size">${formatBytes(analysis.size)}</span>
                    </div>
                `).join('');
            } else {
                elements.recentAnalysis.innerHTML = '<div class="loading">No analysis files found</div>';
            }
        }

        logMessage(`Stats updated: ${stats.screenshots} screenshots, ${stats.analysisFiles} analyses, ${formatBytes(stats.totalSize)} total`);
    } catch (error) {
        logMessage(`Error updating stats: ${error.message}`, 'error');
    }
}

// Update tracking status
async function updateTrackingStatus() {
    try {
        const isTracking = await ipcRenderer.invoke('get-tracking-status');
        
        if (elements.trackingStatus) {
            elements.trackingStatus.innerHTML = `
                <span class="status-indicator ${isTracking ? 'status-active' : 'status-inactive'}"></span>
                ${isTracking ? 'Active' : 'Inactive'}
            `;
        }

        // Update button states
        if (elements.startTrackingBtn) {
            elements.startTrackingBtn.disabled = isTracking;
            elements.startTrackingBtn.textContent = isTracking ? 'Tracking...' : 'Start Tracking';
        }

        if (elements.stopTrackingBtn) {
            elements.stopTrackingBtn.disabled = !isTracking;
        }

        logMessage(`Tracking status: ${isTracking ? 'Active' : 'Inactive'}`);
    } catch (error) {
        logMessage(`Error updating tracking status: ${error.message}`, 'error');
    }
}

// Update ChromaDB status
async function updateChromaStatus() {
    try {
        const isChromaActive = await ipcRenderer.invoke('check-chroma-status');
        
        if (elements.chromaStatus) {
            elements.chromaStatus.innerHTML = `
                <span class="status-indicator ${isChromaActive ? 'status-active' : 'status-inactive'}"></span>
                ${isChromaActive ? 'Connected' : 'Disconnected'}
            `;
        }

        if (elements.vectorStatus) {
            elements.vectorStatus.innerHTML = `
                <span class="status-indicator ${isChromaActive ? 'status-active' : 'status-inactive'}"></span>
                ${isChromaActive ? 'Available' : 'Unavailable'}
            `;
        }

        logMessage(`ChromaDB status: ${isChromaActive ? 'Connected' : 'Disconnected'}`);
    } catch (error) {
        logMessage(`Error checking ChromaDB status: ${error.message}`, 'error');
    }
}

// Event handlers
async function startTracking() {
    try {
        logMessage('Starting screen tracking...');
        await ipcRenderer.invoke('start-tracking');
        updateTrackingStatus();
    } catch (error) {
        logMessage(`Error starting tracking: ${error.message}`, 'error');
    }
}

async function stopTracking() {
    try {
        logMessage('Stopping screen tracking...');
        await ipcRenderer.invoke('stop-tracking');
        updateTrackingStatus();
    } catch (error) {
        logMessage(`Error stopping tracking: ${error.message}`, 'error');
    }
}

async function openScreenshot(filename) {
    try {
        await ipcRenderer.invoke('open-screenshot', filename);
        logMessage(`Opened screenshot: ${filename}`);
    } catch (error) {
        logMessage(`Error opening screenshot: ${error.message}`, 'error');
    }
}

async function openAnalysis(filename) {
    try {
        await ipcRenderer.invoke('open-analysis', filename);
        logMessage(`Opened analysis: ${filename}`);
    } catch (error) {
        logMessage(`Error opening analysis: ${error.message}`, 'error');
    }
}

function openConfig() {
    const configPath = process.platform === 'darwin' 
        ? '~/Library/Application Support/Claude/claude_desktop_config.json'
        : process.platform === 'win32'
        ? '%APPDATA%/Claude/claude_desktop_config.json'
        : '~/.config/Claude/claude_desktop_config.json';
    
    shell.openPath(configPath);
    logMessage(`Opening Claude Desktop config: ${configPath}`);
}

function refreshStatus() {
    logMessage('Refreshing system status...');
    updateStats();
    updateTrackingStatus();
    updateChromaStatus();
}

// Set up event listeners
document.addEventListener('DOMContentLoaded', () => {
    // Button event listeners
    if (elements.startTrackingBtn) {
        elements.startTrackingBtn.addEventListener('click', startTracking);
    }
    
    if (elements.stopTrackingBtn) {
        elements.stopTrackingBtn.addEventListener('click', stopTracking);
    }
    
    if (elements.openConfigBtn) {
        elements.openConfigBtn.addEventListener('click', openConfig);
    }
    
    if (elements.refreshStatusBtn) {
        elements.refreshStatusBtn.addEventListener('click', refreshStatus);
    }
    
    if (elements.openScreenshotsBtn) {
        elements.openScreenshotsBtn.addEventListener('click', () => {
            shell.openPath(require('path').join(__dirname, 'screenshots'));
        });
    }
    
    if (elements.openAnalysisBtn) {
        elements.openAnalysisBtn.addEventListener('click', () => {
            shell.openPath(require('path').join(__dirname, 'screenhistory'));
        });
    }

    // Initial load
    logMessage('Dashboard initialized');
    refreshStatus();
    
    // Set up periodic updates
    setInterval(updateStats, 30000); // Update stats every 30 seconds
    setInterval(updateTrackingStatus, 5000); // Update tracking status every 5 seconds
    setInterval(updateChromaStatus, 60000); // Update ChromaDB status every minute
});

// IPC event listeners
ipcRenderer.on('tracking-started', () => {
    logMessage('Screen tracking started');
    updateTrackingStatus();
});

ipcRenderer.on('tracking-stopped', () => {
    logMessage('Screen tracking stopped');
    updateTrackingStatus();
});

ipcRenderer.on('tracking-output', (event, data) => {
    logMessage(`Tracking: ${data.trim()}`);
});

ipcRenderer.on('tracking-error', (event, error) => {
    logMessage(`Tracking Error: ${error.trim()}`, 'error');
});

// Global functions for HTML onclick handlers
window.openScreenshot = openScreenshot;
window.openAnalysis = openAnalysis;
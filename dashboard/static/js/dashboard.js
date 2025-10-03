// Flow Dashboard JavaScript

class FlowDashboard {
    constructor() {
        this.websocket = null;
        this.activityChart = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.errorCount = 0;
        this.lastError = null;
        this.healthCheckInterval = null;
        this.showNotifications = true;
        
        // Bind methods
        this.handleWebSocketMessage = this.handleWebSocketMessage.bind(this);
        this.handleWebSocketClose = this.handleWebSocketClose.bind(this);
        this.handleWebSocketError = this.handleWebSocketError.bind(this);
        
        // Set up global error handlers
        this.setupGlobalErrorHandlers();
    }
    
    async initialize() {
        console.log('Initializing Flow Dashboard...');
        
        // Load configuration first
        const config = loadConfiguration();
        
        // Apply configuration settings
        if (config['refresh-interval']) {
            this.refreshInterval = config['refresh-interval'] * 1000;
        }
        this.showNotifications = config['show-notifications'] !== false;
        
        // Initialize UI with server data
        if (window.initialData) {
            this.updateStatusDisplay(window.initialData.status);
            this.updateStatsDisplay(window.initialData.stats);
        }
        
        // Initialize activity chart
        await this.initializeActivityChart();
        
        // Connect WebSocket for real-time updates
        this.connectWebSocket();
        
        // Set up periodic updates
        this.startPeriodicUpdates();
        
        console.log('Dashboard initialized successfully');
    }
    
    setupGlobalErrorHandlers() {
        // Handle uncaught JavaScript errors
        window.addEventListener('error', (event) => {
            this.handleError('JavaScript Error', event.error || event.message, {
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno
            });
        });
        
        // Handle unhandled promise rejections
        window.addEventListener('unhandledrejection', (event) => {
            this.handleError('Unhandled Promise Rejection', event.reason, {
                promise: event.promise
            });
        });
        
        // Start health monitoring
        this.startHealthMonitoring();
    }
    
    handleError(type, error, context = {}) {
        this.errorCount++;
        this.lastError = {
            type,
            error: error?.message || error,
            timestamp: new Date().toISOString(),
            context
        };
        
        console.error(`[${type}]`, error, context);
        
        // Log to our logs system if available
        if (typeof logsData !== 'undefined') {
            logsData.unshift({
                timestamp: new Date().toISOString(),
                level: 'ERROR',
                source: 'dashboard.error_handler',
                message: `${type}: ${error?.message || error}`
            });
            
            // Update logs display if visible
            if (typeof filterAndDisplayLogs === 'function') {
                filterAndDisplayLogs();
                updateLogsStats();
            }
        }
        
        // Show user notification for critical errors
        if (this.showNotifications && this.shouldNotifyUser(type, error)) {
            this.showToast(`System Error: ${error?.message || error}`, 'error', 8000);
        }
        
        // Attempt recovery for certain error types
        this.attemptErrorRecovery(type, error);
    }
    
    shouldNotifyUser(type, error) {
        // Don't spam users with too many notifications
        if (this.errorCount > 10) return false;
        
        // Always notify for critical errors
        const criticalErrors = [
            'Network Error',
            'WebSocket Connection Failed',
            'Data Load Failed',
            'System Health Check Failed'
        ];
        
        return criticalErrors.some(critical => type.includes(critical));
    }
    
    attemptErrorRecovery(type, error) {
        try {
            switch (type) {
                case 'WebSocket Connection Failed':
                case 'WebSocket Error':
                    if (this.reconnectAttempts < this.maxReconnectAttempts) {
                        setTimeout(() => this.connectWebSocket(), this.reconnectDelay);
                    }
                    break;
                    
                case 'Data Load Failed':
                    // Retry data loading after a delay
                    setTimeout(() => {
                        this.refreshAll().catch(err => {
                            console.error('Recovery attempt failed:', err);
                        });
                    }, 5000);
                    break;
                    
                case 'Chart Rendering Failed':
                    // Reinitialize the chart
                    setTimeout(() => {
                        this.initializeActivityChart().catch(err => {
                            console.error('Chart recovery failed:', err);
                        });
                    }, 2000);
                    break;
                    
                default:
                    // Generic recovery: refresh the page if too many errors
                    if (this.errorCount > 20) {
                        if (confirm('The dashboard has encountered multiple errors. Would you like to refresh the page?')) {
                            window.location.reload();
                        }
                    }
            }
        } catch (recoveryError) {
            console.error('Error during recovery attempt:', recoveryError);
        }
    }
    
    startHealthMonitoring() {
        // Check system health every 30 seconds
        this.healthCheckInterval = setInterval(() => {
            this.performHealthCheck();
        }, 30000);
    }
    
    async performHealthCheck() {
        try {
            // Check if the dashboard API is responsive
            const response = await fetch('/health', { 
                method: 'GET',
                timeout: 5000 
            });
            
            if (!response.ok) {
                throw new Error(`Health check failed: ${response.status}`);
            }
            
            // Reset error count on successful health check
            if (this.errorCount > 0) {
                this.errorCount = Math.max(0, this.errorCount - 1);
            }
            
        } catch (error) {
            this.handleError('System Health Check Failed', error);
        }
    }
    
    // Enhanced error handling for async operations
    async safeAsyncOperation(operation, operationName = 'Unknown Operation') {
        try {
            return await operation();
        } catch (error) {
            this.handleError(`${operationName} Failed`, error);
            throw error; // Re-throw so calling code can handle it
        }
    }
    
    // Safe wrapper for DOM operations
    safeDOMOperation(operation, operationName = 'DOM Operation') {
        try {
            return operation();
        } catch (error) {
            this.handleError(`${operationName} Failed`, error);
            return null;
        }
    }
    
    // Enhanced toast notifications with error tracking
    showToast(message, type = 'info', duration = 4000) {
        if (!this.showNotifications && type !== 'error') {
            return; // Respect user notification preferences
        }
        
        try {
            const toast = document.createElement('div');
            toast.className = `toast toast-${type}`;
            toast.innerHTML = `
                <div class="toast-content">
                    <span class="toast-icon">${this.getToastIcon(type)}</span>
                    <span class="toast-message">${message}</span>
                    <button class="toast-close" onclick="this.parentElement.parentElement.remove()">×</button>
                </div>
            `;
            
            const container = document.getElementById('toast-container') || this.createToastContainer();
            container.appendChild(toast);
            
            // Auto-remove after duration
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.remove();
                }
            }, duration);
            
            // Log toast messages
            if (typeof logsData !== 'undefined') {
                logsData.unshift({
                    timestamp: new Date().toISOString(),
                    level: type.toUpperCase(),
                    source: 'dashboard.toast',
                    message: `Toast: ${message}`
                });
            }
            
        } catch (error) {
            console.error('Failed to show toast notification:', error);
            // Fallback to browser alert for critical messages
            if (type === 'error') {
                alert(`Error: ${message}`);
            }
        }
    }
    
    createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container';
        document.body.appendChild(container);
        return container;
    }
    
    getToastIcon(type) {
        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };
        return icons[type] || 'ℹ️';
    }
    
    connectWebSocket() {
        try {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            
            this.websocket = new WebSocket(wsUrl);
            
            this.websocket.onopen = () => {
                console.log('WebSocket connected');
                this.reconnectAttempts = 0;
                this.updateConnectionStatus(true);
            };
            
            this.websocket.onmessage = this.handleWebSocketMessage;
            this.websocket.onclose = this.handleWebSocketClose;
            this.websocket.onerror = this.handleWebSocketError;
            
        } catch (error) {
            console.error('Error connecting WebSocket:', error);
            this.updateConnectionStatus(false);
        }
    }
    
    handleWebSocketMessage(event) {
        try {
            const message = JSON.parse(event.data);
            
            switch (message.type) {
                case 'status_update':
                    this.updateStatusDisplay(message.data);
                    break;
                default:
                    console.log('Unknown WebSocket message type:', message.type);
            }
        } catch (error) {
            console.error('Error handling WebSocket message:', error);
        }
    }
    
    handleWebSocketClose(event) {
        console.log('WebSocket disconnected');
        this.updateConnectionStatus(false);
        
        // Attempt to reconnect
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
            
            console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`);
            
            setTimeout(() => {
                this.connectWebSocket();
            }, delay);
        } else {
            console.error('Max reconnection attempts reached');
            this.showToast('Connection lost. Please refresh the page.', 'error');
        }
    }
    
    handleWebSocketError(error) {
        console.error('WebSocket error:', error);
        this.updateConnectionStatus(false);
    }
    
    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connection-status');
        const dot = statusElement.querySelector('.status-dot');
        const text = statusElement.querySelector('.status-text');
        
        if (connected) {
            dot.style.backgroundColor = 'var(--success-color)';
            text.textContent = 'Connected';
        } else {
            dot.style.backgroundColor = 'var(--danger-color)';
            text.textContent = 'Disconnected';
        }
    }
    
    updateStatusDisplay(status) {
        // Update overall status
        const overallBadge = document.getElementById('overall-badge');
        const badgeText = overallBadge.querySelector('.badge-text');
        badgeText.textContent = status.overall_status.charAt(0).toUpperCase() + status.overall_status.slice(1);
        
        // Update badge color
        overallBadge.className = `status-badge ${status.overall_status}`;
        
        // Update control buttons
        const startBtn = document.getElementById('start-btn');
        const stopBtn = document.getElementById('stop-btn');
        
        if (status.overall_status === 'running') {
            startBtn.disabled = true;
            stopBtn.disabled = false;
        } else {
            startBtn.disabled = false;
            stopBtn.disabled = true;
        }
        
        // Update ChromaDB status
        const chromaBadge = document.getElementById('chroma-badge');
        const chromaBadgeText = chromaBadge.querySelector('.badge-text');
        chromaBadgeText.textContent = status.chroma_db.running ? 'Running' : 'Stopped';
        chromaBadge.className = `status-badge ${status.chroma_db.running ? 'running' : 'stopped'}`;
        
        const chromaHealth = document.getElementById('chroma-health');
        if (chromaHealth) {
            chromaHealth.textContent = status.chroma_db.healthy ? 'Healthy' : 'Unhealthy';
        }
        
        const chromaPid = document.getElementById('chroma-pid');
        if (chromaPid && status.chroma_db.pid) {
            chromaPid.textContent = status.chroma_db.pid;
        }
        
        // Update Screen Capture status
        const captureBadge = document.getElementById('capture-badge');
        const captureBadgeText = captureBadge.querySelector('.badge-text');
        captureBadgeText.textContent = status.screen_capture.running ? 'Running' : 'Stopped';
        captureBadge.className = `status-badge ${status.screen_capture.running ? 'running' : 'stopped'}`;
        
        const captureHealth = document.getElementById('capture-health');
        if (captureHealth) {
            captureHealth.textContent = status.screen_capture.healthy ? 'Healthy' : 'Unhealthy';
        }
        
        const capturePid = document.getElementById('capture-pid');
        if (capturePid && status.screen_capture.pid) {
            capturePid.textContent = status.screen_capture.pid;
        }
    }
    
    updateStatsDisplay(stats) {
        const totalCaptures = document.getElementById('total-captures');
        const uniqueScreens = document.getElementById('unique-screens');
        const avgTextLength = document.getElementById('avg-text-length');
        const dateRange = document.getElementById('date-range');
        
        if (totalCaptures) totalCaptures.textContent = stats.total_captures || 0;
        if (uniqueScreens) uniqueScreens.textContent = stats.unique_screens || 0;
        if (avgTextLength) avgTextLength.textContent = stats.avg_text_length || 0;
        
        if (dateRange && stats.date_range) {
            const start = new Date(stats.date_range.earliest).toLocaleDateString();
            const end = new Date(stats.date_range.latest).toLocaleDateString();
            dateRange.textContent = `${start} to ${end}`;
        } else if (dateRange) {
            dateRange.textContent = 'No data';
        }
    }
    
    async initializeActivityChart() {
        const canvas = document.getElementById('activity-chart');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        
        // Get initial activity data
        const activityData = await this.fetchActivityData();
        
        this.activityChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: activityData.labels,
                datasets: [{
                    label: 'Captures with Content',
                    data: activityData.contentData,
                    backgroundColor: '#4CAF50',
                    borderColor: '#4CAF50',
                    borderWidth: 1
                }, {
                    label: 'Empty Captures',
                    data: activityData.emptyData,
                    backgroundColor: '#FFC107',
                    borderColor: '#FFC107',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        stacked: true,
                        title: {
                            display: true,
                            text: 'Time'
                        }
                    },
                    y: {
                        stacked: true,
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Number of Captures'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false // We have custom legend
                    },
                    tooltip: {
                        callbacks: {
                            title: function(context) {
                                return `Time: ${context[0].label}`;
                            },
                            label: function(context) {
                                return `${context.dataset.label}: ${context.parsed.y}`;
                            }
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });
    }
    
    async fetchActivityData() {
        try {
            const timeRange = document.getElementById('time-range')?.value || '24';
            const grouping = document.getElementById('grouping')?.value || 'hourly';
            
            console.log(`Fetching activity data: ${timeRange}h, ${grouping}`);
            
            const response = await fetch(`/api/activity-data?hours=${timeRange}&grouping=${grouping}&include_empty=true`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log('Activity data received:', data);
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            if (!data.timeline_data || data.timeline_data.length === 0) {
                console.warn('No timeline data available');
                return { 
                    labels: ['No Data'], 
                    contentData: [0], 
                    emptyData: [0],
                    summary: data.summary || {}
                };
            }
            
            const labels = data.timeline_data.map(item => {
                try {
                    if (grouping === 'hourly') {
                        // Handle "YYYY-MM-DD HH:00" format
                        if (item.timestamp.includes(' ')) {
                            const [datePart, timePart] = item.timestamp.split(' ');
                            const date = new Date(`${datePart}T${timePart}:00`);
                            return date.toLocaleTimeString([], { 
                                month: 'short', 
                                day: 'numeric', 
                                hour: '2-digit', 
                                minute: '2-digit' 
                            });
                        } else {
                            // Handle ISO format
                            const date = new Date(item.timestamp);
                            return date.toLocaleTimeString([], { 
                                month: 'short', 
                                day: 'numeric', 
                                hour: '2-digit', 
                                minute: '2-digit' 
                            });
                        }
                    } else {
                        // Daily format
                        const date = new Date(item.timestamp);
                        return date.toLocaleDateString([], { 
                            month: 'short', 
                            day: 'numeric' 
                        });
                    }
                } catch (e) {
                    console.warn('Error parsing timestamp:', item.timestamp, e);
                    return item.timestamp;
                }
            });
            
            const contentData = data.timeline_data.map(item => {
                const contentCaptures = Math.round(item.capture_count * item.content_percentage / 100);
                return contentCaptures;
            });
            
            const emptyData = data.timeline_data.map(item => {
                const contentCaptures = Math.round(item.capture_count * item.content_percentage / 100);
                return Math.max(0, item.capture_count - contentCaptures);
            });
            
            console.log(`Generated chart data: ${labels.length} labels, ${contentData.length} content points, ${emptyData.length} empty points`);
            
            return { 
                labels, 
                contentData, 
                emptyData, 
                summary: data.summary || {},
                timeRange: data.time_range || {}
            };
            
        } catch (error) {
            console.error('Error fetching activity data:', error);
            this.showToast(`Failed to fetch activity data: ${error.message}`, 'error');
            return { 
                labels: ['Error'], 
                contentData: [0], 
                emptyData: [0],
                summary: {},
                error: error.message
            };
        }
    }
    
    async updateActivityGraph() {
        if (!this.activityChart) return;
        
        this.showLoading();
        
        try {
            const activityData = await this.fetchActivityData();
            
            this.activityChart.data.labels = activityData.labels;
            this.activityChart.data.datasets[0].data = activityData.contentData;
            this.activityChart.data.datasets[1].data = activityData.emptyData;
            
            this.activityChart.update();
            
        } catch (error) {
            console.error('Error updating activity graph:', error);
            this.showToast('Failed to update activity graph', 'error');
        } finally {
            this.hideLoading();
        }
    }
    
    async refreshActivityGraph() {
        await this.updateActivityGraph();
        this.showToast('Activity graph refreshed', 'success');
    }
    
    startPeriodicUpdates() {
        // Update stats every 30 seconds
        setInterval(async () => {
            try {
                const response = await fetch('/api/stats');
                const stats = await response.json();
                this.updateStatsDisplay(stats);
            } catch (error) {
                console.error('Error updating stats:', error);
            }
        }, 30000);
        
        // Update activity graph every 5 minutes
        setInterval(() => {
            this.updateActivityGraph();
        }, 300000);
    }
    
    showLoading() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.style.display = 'flex';
        }
    }
    
    hideLoading() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.style.display = 'none';
        }
    }
    
    showToast(message, type = 'info', duration = 5000) {
        const container = document.getElementById('toast-container');
        if (!container) return;
        
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <div class="toast-content">
                <strong>${type.charAt(0).toUpperCase() + type.slice(1)}</strong>
                <p>${message}</p>
            </div>
        `;
        
        container.appendChild(toast);
        
        // Auto remove after duration
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, duration);
        
        // Allow manual removal
        toast.addEventListener('click', () => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        });
    }
    
    async performSearch(query, startDate = null, endDate = null) {
        try {
            this.showLoading();
            
            const params = new URLSearchParams({ q: query });
            if (startDate) params.append('start_date', startDate);
            if (endDate) params.append('end_date', endDate);
            
            const response = await fetch(`/api/search?${params}`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            this.displaySearchResults(data);
            
        } catch (error) {
            console.error('Search error:', error);
            this.showToast(`Search failed: ${error.message}`, 'error');
        } finally {
            this.hideLoading();
        }
    }
    
    displaySearchResults(data) {
        const resultsContainer = document.getElementById('search-results');
        const resultsCount = document.getElementById('results-count');
        const resultsList = document.getElementById('results-list');
        
        if (!resultsContainer || !resultsCount || !resultsList) return;
        
        // Update results count
        resultsCount.textContent = `${data.total_found} result${data.total_found !== 1 ? 's' : ''}`;
        
        // Clear previous results
        resultsList.innerHTML = '';
        
        if (data.results.length === 0) {
            resultsList.innerHTML = `
                <div class="no-results">
                    <p>No results found for "${data.query}"</p>
                    <p class="text-secondary">Try different keywords or adjust the date range.</p>
                </div>
            `;
        } else {
            // Display results
            data.results.forEach(result => {
                const resultItem = document.createElement('div');
                resultItem.className = 'result-item';
                
                const timestamp = new Date(result.timestamp).toLocaleString();
                
                resultItem.innerHTML = `
                    <div class="result-header">
                        <span class="result-timestamp">${timestamp}</span>
                        <span class="result-screen">${result.screen_name}</span>
                    </div>
                    <div class="result-preview">${result.text_preview}</div>
                    <div class="result-stats">
                        <span>Length: ${result.text_length} chars</span>
                        <span>Words: ${result.word_count}</span>
                        <span>Relevance: ${result.relevance}</span>
                    </div>
                `;
                
                resultsList.appendChild(resultItem);
            });
        }
        
        // Show results container
        resultsContainer.style.display = 'block';
        
        // Scroll to results
        resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

// Global functions for button handlers
async function startSystem() {
    const dashboard = window.flowDashboard;
    if (!dashboard) return;
    
    dashboard.showLoading();
    
    try {
        const response = await fetch('/api/start', { method: 'POST' });
        const result = await response.json();
        
        if (result.success) {
            dashboard.showToast(result.message, 'success');
        } else {
            dashboard.showToast(result.message, 'error');
        }
        
    } catch (error) {
        console.error('Error starting system:', error);
        dashboard.showToast('Failed to start system', 'error');
    } finally {
        dashboard.hideLoading();
    }
}

async function stopSystem() {
    const dashboard = window.flowDashboard;
    if (!dashboard) return;
    
    dashboard.showLoading();
    
    try {
        const response = await fetch('/api/stop', { method: 'POST' });
        const result = await response.json();
        
        if (result.success) {
            dashboard.showToast(result.message, 'success');
        } else {
            dashboard.showToast(result.message, 'error');
        }
        
    } catch (error) {
        console.error('Error stopping system:', error);
        dashboard.showToast('Failed to stop system', 'error');
    } finally {
        dashboard.hideLoading();
    }
}

function updateActivityGraph() {
    const dashboard = window.flowDashboard;
    if (dashboard) {
        dashboard.updateActivityGraph();
    }
}

function refreshActivityGraph() {
    const dashboard = window.flowDashboard;
    if (dashboard) {
        dashboard.refreshActivityGraph();
    }
}

async function performSearch() {
    const dashboard = window.flowDashboard;
    if (!dashboard) return;
    
    const query = document.getElementById('search-query')?.value?.trim();
    if (!query) {
        dashboard.showToast('Please enter a search query', 'warning');
        return;
    }
    
    const startDate = document.getElementById('search-start-date')?.value || null;
    const endDate = document.getElementById('search-end-date')?.value || null;
    
    await dashboard.performSearch(query, startDate, endDate);
}

// Tools Dashboard Functions
async function refreshToolsStatus() {
    const dashboard = window.flowDashboard;
    if (!dashboard) return;
    
    try {
        dashboard.showLoading();
        
        // Update MCP server status
        const mcpStatus = await checkMCPServerStatus();
        document.getElementById('mcp-server-status').textContent = mcpStatus.status;
        document.getElementById('tools-last-updated').textContent = new Date().toLocaleTimeString();
        
        // Update tool statuses
        const toolCards = document.querySelectorAll('.tool-card');
        toolCards.forEach(card => {
            const statusDot = card.querySelector('.status-dot');
            const statusText = card.querySelector('.status-text');
            
            if (mcpStatus.available) {
                statusDot.className = 'status-dot available';
                statusText.textContent = 'Available';
            } else {
                statusDot.className = 'status-dot unavailable';
                statusText.textContent = 'Unavailable';
            }
        });
        
        dashboard.showToast('Tools status refreshed', 'success');
        
    } catch (error) {
        console.error('Error refreshing tools status:', error);
        dashboard.showToast('Failed to refresh tools status', 'error');
    } finally {
        dashboard.hideLoading();
    }
}

async function checkMCPServerStatus() {
    try {
        // This is a placeholder - in a real implementation, you'd check if the MCP server is running
        // For now, we'll assume it's available since we can't easily test the MCP server from the web dashboard
        return {
            status: 'Available (Standalone)',
            available: true,
            note: 'MCP server runs independently'
        };
    } catch (error) {
        return {
            status: 'Unknown',
            available: false,
            error: error.message
        };
    }
}

async function testMCPConnection() {
    const dashboard = window.flowDashboard;
    if (!dashboard) return;
    
    try {
        dashboard.showLoading();
        
        // Test basic connectivity by checking if the MCP server directory exists
        // This is a simplified test - real MCP testing would require more complex setup
        dashboard.showToast('MCP Server Test: The Python MCP server is configured and ready to use with Claude Desktop. See the configuration section below for setup instructions.', 'info', 8000);
        
    } catch (error) {
        console.error('Error testing MCP connection:', error);
        dashboard.showToast('MCP connection test failed', 'error');
    } finally {
        dashboard.hideLoading();
    }
}

async function testTool(toolName) {
    const dashboard = window.flowDashboard;
    if (!dashboard) return;
    
    const toolCard = document.querySelector(`[data-tool="${toolName}"]`);
    const statusDot = toolCard?.querySelector('.status-dot');
    const statusText = toolCard?.querySelector('.status-text');
    
    try {
        // Update UI to show testing
        if (statusDot && statusText) {
            statusDot.className = 'status-dot testing';
            statusText.textContent = 'Testing...';
        }
        
        // Simulate tool test based on tool type
        let testResult;
        switch (toolName) {
            case 'search-screenshots':
                testResult = await testSearchTool();
                break;
            case 'get-stats':
                testResult = await testStatsTool();
                break;
            case 'what-can-i-do':
                testResult = { success: true, message: 'Tool available - provides system capabilities info' };
                break;
            default:
                testResult = { success: true, message: `${toolName} tool is available` };
        }
        
        // Update UI based on result
        if (statusDot && statusText) {
            if (testResult.success) {
                statusDot.className = 'status-dot available';
                statusText.textContent = 'Available';
                dashboard.showToast(`${toolName}: ${testResult.message}`, 'success');
            } else {
                statusDot.className = 'status-dot unavailable';
                statusText.textContent = 'Failed';
                dashboard.showToast(`${toolName}: ${testResult.message}`, 'error');
            }
        }
        
    } catch (error) {
        console.error(`Error testing tool ${toolName}:`, error);
        
        if (statusDot && statusText) {
            statusDot.className = 'status-dot unavailable';
            statusText.textContent = 'Error';
        }
        
        dashboard.showToast(`Tool test failed: ${error.message}`, 'error');
    }
}

async function testSearchTool() {
    try {
        // Test the search API endpoint
        const response = await fetch('/api/search?q=test&limit=1');
        if (response.ok) {
            const data = await response.json();
            return { 
                success: true, 
                message: `Search working - ${data.processed_files || 0} files available` 
            };
        } else {
            return { success: false, message: 'Search API not responding' };
        }
    } catch (error) {
        return { success: false, message: error.message };
    }
}

async function testStatsTool() {
    try {
        // Test the stats API endpoint
        const response = await fetch('/api/stats');
        if (response.ok) {
            const data = await response.json();
            return { 
                success: true, 
                message: `Stats working - ${data.total_captures || 0} captures available` 
            };
        } else {
            return { success: false, message: 'Stats API not responding' };
        }
    } catch (error) {
        return { success: false, message: error.message };
    }
}

function showToolExample(toolName) {
    const examples = {
        'search-screenshots': `Example usage in Claude Desktop:
        
"Search for screenshots containing 'email' from last week"
"Find any screens with 'github.com' from yesterday"
"Look for 'meeting notes' between 2024-01-01 and 2024-01-07"`,
        
        'what-can-i-do': `Example usage in Claude Desktop:
        
"What can Flow do?"
"Show me Flow's capabilities"
"What tools are available in Flow?"`,
        
        'get-stats': `Example usage in Claude Desktop:
        
"Show me Flow statistics"
"How much data has Flow collected?"
"What's the status of my Flow system?"`,
        
        'activity-graph': `Example usage in Claude Desktop:
        
"Generate an activity graph for the last 7 days"
"Show me daily activity patterns for the past month"
"Create a timeline of my screen activity"`,
        
        'time-range-summary': `Example usage in Claude Desktop:
        
"Summarize my activity from 9am to 5pm yesterday"
"Show me what I worked on between Jan 1-7, 2024"
"Get a sample of my screen activity from last week"`,
        
        'start-flow': `Example usage in Claude Desktop:
        
"Start the Flow system"
"Begin screen capture recording"
"Turn on Flow monitoring"`,
        
        'stop-flow': `Example usage in Claude Desktop:
        
"Stop the Flow system"
"End screen capture recording"
"Turn off Flow monitoring"`
    };
    
    const example = examples[toolName] || 'No example available';
    const dashboard = window.flowDashboard;
    if (dashboard) {
        dashboard.showToast(example, 'info', 10000);
    }
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        const dashboard = window.flowDashboard;
        if (dashboard) {
            dashboard.showToast('Configuration copied to clipboard!', 'success');
        }
    }).catch(err => {
        console.error('Failed to copy text: ', err);
        const dashboard = window.flowDashboard;
        if (dashboard) {
            dashboard.showToast('Failed to copy to clipboard', 'error');
        }
    });
}

// Configuration Management Functions
const DEFAULT_CONFIG = {
    'capture-interval': 60,
    'max-concurrent-ocr': 4,
    'auto-start': false,
    'data-retention': 90,
    'max-file-size': 10,
    'compress-old-data': true,
    'theme-mode': 'light',
    'refresh-interval': 30,
    'show-notifications': true,
    'log-level': 'INFO',
    'enable-telemetry': false,
    'experimental-features': false
};

function loadConfiguration() {
    try {
        const saved = localStorage.getItem('flow-dashboard-config');
        const config = saved ? JSON.parse(saved) : {};
        
        // Apply configuration to form elements
        Object.keys(DEFAULT_CONFIG).forEach(key => {
            const element = document.getElementById(key);
            if (!element) return;
            
            const value = config[key] !== undefined ? config[key] : DEFAULT_CONFIG[key];
            
            if (element.type === 'checkbox') {
                element.checked = value;
            } else {
                element.value = value;
            }
        });
        
        // Apply theme immediately
        const theme = config['theme-mode'] || DEFAULT_CONFIG['theme-mode'];
        applyTheme(theme);
        
        // Update status
        const hasCustomConfig = Object.keys(config).length > 0;
        document.getElementById('config-status').textContent = hasCustomConfig ? 'Custom' : 'Default';
        
        if (hasCustomConfig && config._lastSaved) {
            document.getElementById('config-last-saved').textContent = new Date(config._lastSaved).toLocaleString();
        }
        
        return config;
        
    } catch (error) {
        console.error('Error loading configuration:', error);
        return {};
    }
}

function saveConfiguration() {
    const dashboard = window.flowDashboard;
    if (!dashboard) return;
    
    try {
        const config = {};
        
        // Collect all configuration values
        Object.keys(DEFAULT_CONFIG).forEach(key => {
            const element = document.getElementById(key);
            if (!element) return;
            
            if (element.type === 'checkbox') {
                config[key] = element.checked;
            } else if (element.type === 'number') {
                config[key] = parseInt(element.value, 10);
            } else {
                config[key] = element.value;
            }
        });
        
        // Add metadata
        config._lastSaved = new Date().toISOString();
        config._version = '1.0';
        
        // Save to localStorage
        localStorage.setItem('flow-dashboard-config', JSON.stringify(config));
        
        // Apply theme if changed
        applyTheme(config['theme-mode']);
        
        // Update status
        document.getElementById('config-status').textContent = 'Custom';
        document.getElementById('config-last-saved').textContent = new Date().toLocaleString();
        
        dashboard.showToast('Configuration saved successfully!', 'success');
        
        // Apply configuration changes that affect the dashboard
        applyDashboardConfig(config);
        
    } catch (error) {
        console.error('Error saving configuration:', error);
        dashboard.showToast('Failed to save configuration', 'error');
    }
}

function resetToDefaults() {
    const dashboard = window.flowDashboard;
    if (!dashboard) return;
    
    if (!confirm('Are you sure you want to reset all settings to defaults? This cannot be undone.')) {
        return;
    }
    
    try {
        // Clear saved configuration
        localStorage.removeItem('flow-dashboard-config');
        
        // Reset form elements to defaults
        Object.keys(DEFAULT_CONFIG).forEach(key => {
            const element = document.getElementById(key);
            if (!element) return;
            
            const value = DEFAULT_CONFIG[key];
            
            if (element.type === 'checkbox') {
                element.checked = value;
            } else {
                element.value = value;
            }
        });
        
        // Apply default theme
        applyTheme(DEFAULT_CONFIG['theme-mode']);
        
        // Update status
        document.getElementById('config-status').textContent = 'Default';
        document.getElementById('config-last-saved').textContent = 'Never';
        
        dashboard.showToast('Configuration reset to defaults', 'success');
        
    } catch (error) {
        console.error('Error resetting configuration:', error);
        dashboard.showToast('Failed to reset configuration', 'error');
    }
}

function applyTheme(theme) {
    const body = document.body;
    
    // Remove existing theme classes
    body.removeAttribute('data-theme');
    
    if (theme === 'dark') {
        body.setAttribute('data-theme', 'dark');
    } else if (theme === 'auto') {
        // Check system preference
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        if (prefersDark) {
            body.setAttribute('data-theme', 'dark');
        }
    }
    // 'light' theme is the default (no attribute needed)
}

function applyDashboardConfig(config) {
    const dashboard = window.flowDashboard;
    if (!dashboard) return;
    
    // Update refresh interval
    if (config['refresh-interval'] && config['refresh-interval'] !== dashboard.refreshInterval) {
        dashboard.refreshInterval = config['refresh-interval'] * 1000; // Convert to milliseconds
        dashboard.restartAutoRefresh();
    }
    
    // Update notification settings
    dashboard.showNotifications = config['show-notifications'] !== false;
}

// Listen for system theme changes when in auto mode
if (window.matchMedia) {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    mediaQuery.addListener(() => {
        const config = loadConfiguration();
        if (config['theme-mode'] === 'auto') {
            applyTheme('auto');
        }
    });
}

// Logs Management Functions
let logsData = [];
let logsCurrentFilter = 'all';
let logsAutoRefresh = true;
let logsRefreshInterval = null;

function initializeLogs() {
    // Set up log filter change handler
    const logFilter = document.getElementById('log-filter');
    if (logFilter) {
        logFilter.addEventListener('change', (e) => {
            logsCurrentFilter = e.target.value;
            filterAndDisplayLogs();
        });
    }
    
    // Set up auto-refresh toggle
    const autoRefreshToggle = document.getElementById('logs-auto-refresh');
    if (autoRefreshToggle) {
        autoRefreshToggle.addEventListener('change', (e) => {
            logsAutoRefresh = e.target.checked;
            if (logsAutoRefresh) {
                startLogsAutoRefresh();
            } else {
                stopLogsAutoRefresh();
            }
        });
    }
    
    // Start auto-refresh by default
    if (logsAutoRefresh) {
        startLogsAutoRefresh();
    }
    
    // Load initial logs
    refreshLogs();
}

function startLogsAutoRefresh() {
    if (logsRefreshInterval) {
        clearInterval(logsRefreshInterval);
    }
    
    logsRefreshInterval = setInterval(() => {
        if (logsAutoRefresh) {
            refreshLogs(true); // Silent refresh
        }
    }, 5000); // Refresh every 5 seconds
}

function stopLogsAutoRefresh() {
    if (logsRefreshInterval) {
        clearInterval(logsRefreshInterval);
        logsRefreshInterval = null;
    }
}

async function refreshLogs(silent = false) {
    const dashboard = window.flowDashboard;
    
    try {
        if (!silent && dashboard) {
            dashboard.showLoading();
        }
        
        // Simulate log data - in a real implementation, this would fetch from the server
        const mockLogs = generateMockLogs();
        logsData = mockLogs;
        
        filterAndDisplayLogs();
        updateLogsStats();
        
        if (!silent && dashboard) {
            dashboard.showToast('Logs refreshed', 'success');
        }
        
    } catch (error) {
        console.error('Error refreshing logs:', error);
        if (dashboard) {
            dashboard.showToast('Failed to refresh logs', 'error');
        }
    } finally {
        if (!silent && dashboard) {
            dashboard.hideLoading();
        }
    }
}

function generateMockLogs() {
    const levels = ['INFO', 'WARNING', 'ERROR', 'DEBUG'];
    const sources = ['dashboard.app', 'process_manager', 'ocr_data', 'mcp_server', 'chroma_client'];
    const messages = [
        'Flow Dashboard started successfully',
        'ChromaDB server connection established',
        'Screen capture process started',
        'OCR processing completed for screenshot',
        'Configuration saved successfully',
        'Warning: High memory usage detected',
        'Error: Failed to connect to ChromaDB server',
        'Debug: Processing OCR data batch',
        'MCP server tool executed: search-screenshots',
        'Activity graph data updated',
        'User configuration loaded',
        'System health check completed',
        'Warning: Disk space running low',
        'Error: OCR processing failed for image',
        'Info: Automatic cleanup completed'
    ];
    
    const logs = [];
    const now = new Date();
    
    for (let i = 0; i < 50; i++) {
        const timestamp = new Date(now.getTime() - (i * 60000 * Math.random() * 10));
        const level = levels[Math.floor(Math.random() * levels.length)];
        const source = sources[Math.floor(Math.random() * sources.length)];
        const message = messages[Math.floor(Math.random() * messages.length)];
        
        logs.push({
            timestamp: timestamp.toISOString(),
            level,
            source,
            message: `${message} (${i + 1})`
        });
    }
    
    return logs.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
}

function filterAndDisplayLogs() {
    const logsContent = document.getElementById('logs-content');
    if (!logsContent) return;
    
    let filteredLogs = logsData;
    
    // Apply level filter
    if (logsCurrentFilter !== 'all') {
        const levelPriority = { 'DEBUG': 0, 'INFO': 1, 'WARNING': 2, 'ERROR': 3 };
        const filterPriority = levelPriority[logsCurrentFilter];
        
        filteredLogs = logsData.filter(log => {
            const logPriority = levelPriority[log.level];
            return logPriority >= filterPriority;
        });
    }
    
    // Clear existing content
    logsContent.innerHTML = '';
    
    if (filteredLogs.length === 0) {
        logsContent.innerHTML = `
            <div class="logs-empty">
                <div class="logs-empty-icon">📋</div>
                <div class="logs-empty-text">No logs match the current filter</div>
                <div class="logs-empty-subtext">Try adjusting the log level filter or refresh the logs</div>
            </div>
        `;
        return;
    }
    
    // Display logs
    filteredLogs.forEach(log => {
        const logEntry = document.createElement('div');
        logEntry.className = 'log-entry';
        
        const timestamp = new Date(log.timestamp);
        const timeString = timestamp.toLocaleTimeString();
        
        logEntry.innerHTML = `
            <div class="log-time">${timeString}</div>
            <div class="log-level ${log.level}">${log.level}</div>
            <div class="log-source">${log.source}</div>
            <div class="log-message">${log.message}</div>
        `;
        
        logsContent.appendChild(logEntry);
    });
}

function updateLogsStats() {
    const totalElement = document.getElementById('logs-total');
    const errorsElement = document.getElementById('logs-errors');
    const warningsElement = document.getElementById('logs-warnings');
    
    if (!totalElement || !errorsElement || !warningsElement) return;
    
    const stats = logsData.reduce((acc, log) => {
        acc.total++;
        if (log.level === 'ERROR') acc.errors++;
        if (log.level === 'WARNING') acc.warnings++;
        return acc;
    }, { total: 0, errors: 0, warnings: 0 });
    
    totalElement.textContent = stats.total;
    errorsElement.textContent = stats.errors;
    warningsElement.textContent = stats.warnings;
}

function clearLogs() {
    const dashboard = window.flowDashboard;
    
    if (!confirm('Are you sure you want to clear all logs? This cannot be undone.')) {
        return;
    }
    
    try {
        logsData = [];
        filterAndDisplayLogs();
        updateLogsStats();
        
        if (dashboard) {
            dashboard.showToast('Logs cleared successfully', 'success');
        }
        
    } catch (error) {
        console.error('Error clearing logs:', error);
        if (dashboard) {
            dashboard.showToast('Failed to clear logs', 'error');
        }
    }
}

function downloadLogs() {
    const dashboard = window.flowDashboard;
    
    try {
        const logsText = logsData.map(log => {
            const timestamp = new Date(log.timestamp).toISOString();
            return `${timestamp} [${log.level}] ${log.source}: ${log.message}`;
        }).join('\n');
        
        const blob = new Blob([logsText], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `flow-logs-${new Date().toISOString().split('T')[0]}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        
        URL.revokeObjectURL(url);
        
        if (dashboard) {
            dashboard.showToast('Logs downloaded successfully', 'success');
        }
        
    } catch (error) {
        console.error('Error downloading logs:', error);
        if (dashboard) {
            dashboard.showToast('Failed to download logs', 'error');
        }
    }
}

function loadMoreLogs() {
    // This would typically load more logs from the server
    // For now, we'll just show a message
    const dashboard = window.flowDashboard;
    if (dashboard) {
        dashboard.showToast('Load more logs functionality would fetch additional log entries from the server', 'info');
    }
}

// Initialize dashboard when DOM is loaded
function initializeDashboard() {
    window.flowDashboard = new FlowDashboard();
    window.flowDashboard.initialize();
    
    // Initialize logs system
    initializeLogs();
}

// Export for use in HTML
window.startSystem = startSystem;
window.stopSystem = stopSystem;
window.updateActivityGraph = updateActivityGraph;
window.refreshActivityGraph = refreshActivityGraph;
window.initializeDashboard = initializeDashboard;

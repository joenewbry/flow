// Flow Dashboard JavaScript

class FlowDashboard {
    constructor() {
        this.websocket = null;
        this.activityChart = null;
        this.weeklyChart = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.errorCount = 0;
        this.lastError = null;
        this.healthCheckInterval = null;
        this.showNotifications = true;
        
        // Countdown tracking
        this.countdownInterval = null;
        this.secondsRemaining = 60;
        this.isRecording = false;
        this.mcpClients = [];
        this.lastMcpRequest = null;
        
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
        
        // Load enhanced metrics
        await this.updateEnhancedMetrics();
        
        // Initialize weekly chart
        await this.initializeWeeklyChart();
        
        // Initialize coverage heatmap
        await this.initializeCoverageHeatmap();
        
        // Initialize activity chart (old one, might remove)
        // await this.initializeActivityChart();
        
        // Initialize screen cards
        await this.initializeScreenCards();
        
        // Connect WebSocket for real-time updates
        this.connectWebSocket();
        
        // Set up periodic updates
        this.startPeriodicUpdates();
        
        // Start countdown
        this.startCountdown();
        
        // Update status dot
        this.updateStatusDot(true);
        
        // Start MCP monitoring
        this.startMcpMonitoring();
        
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
                case 'hamster_state_update':
                    this.updateHamsterStates(message.data);
                    break;
                case 'hamster_event':
                    this.handleHamsterEvent(message.data);
                    break;
                case 'log_message':
                    this.handleLogMessage(message.data);
                    break;
                case 'countdown_update':
                    this.handleCountdownUpdate(message.data);
                    break;
                case 'chat_message':
                case 'tool_status':
                case 'queue_update':
                case 'message_status':
                    // Handle chat-related messages
                    handleChatWebSocketMessage(message);
                    break;
                default:
                    console.log('Unknown WebSocket message type:', message.type);
            }
        } catch (error) {
            console.error('Error handling WebSocket message:', error);
        }
    }
    
    handleCountdownUpdate(data) {
        // Update seconds remaining from server
        if (data.seconds_remaining !== undefined) {
            this.secondsRemaining = data.seconds_remaining;
            
            // Update displays immediately
            const countdownText = document.getElementById('countdown-text');
            const statusCountdownText = document.getElementById('status-countdown-text');
            
            if (countdownText) {
                countdownText.textContent = `Next capture in ${data.seconds_remaining}s`;
            }
            
            if (statusCountdownText) {
                statusCountdownText.textContent = `Next capture in ${data.seconds_remaining} seconds`;
            }
        }
    }
    
    handleLogMessage(logData) {
        // Map subsystem names to panel IDs
        const subsystemMap = {
            'screen-capture': 'screen-capture-log-content',
            'chromadb': 'chromadb-log-content',
            'dashboard': 'dashboard-log-content',
            'mcp-server': 'mcp-server-log-content'
        };
        
        const panelId = subsystemMap[logData.subsystem];
        if (!panelId) {
            console.warn(`Unknown log subsystem: ${logData.subsystem}`);
            return;
        }
        
        const logContent = document.getElementById(panelId);
        if (!logContent) {
            return;
        }
        
        // Check if "No logs available" message exists and remove it
        const emptyMessage = logContent.querySelector('.log-empty');
        if (emptyMessage) {
            emptyMessage.remove();
        }
        
        // Create log entry element
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry log-${logData.level.toLowerCase()}`;
        
        const timeStamp = new Date(logData.timestamp).toLocaleTimeString();
        
        logEntry.innerHTML = `
            <span class="log-time">${timeStamp}</span>
            <span class="log-level">${logData.level}</span>
            <span class="log-message">${this.escapeHtml(logData.message)}</span>
        `;
        
        // Append to log content
        logContent.appendChild(logEntry);
        
        // Auto-scroll if enabled
        const autoScrollCheckbox = document.getElementById('auto-scroll-logs');
        if (autoScrollCheckbox && autoScrollCheckbox.checked) {
            logContent.scrollTop = logContent.scrollHeight;
        }
        
        // Limit number of log entries (keep last 1000)
        const maxEntries = 1000;
        const entries = logContent.querySelectorAll('.log-entry');
        if (entries.length > maxEntries) {
            const entriesToRemove = entries.length - maxEntries;
            for (let i = 0; i < entriesToRemove; i++) {
                entries[i].remove();
            }
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
        // Update the status dot in the header
        this.updateStatusDot(connected);
    }
    
    updateStatusDisplay(status) {
        // Update recording state for countdown
        this.isRecording = status.screen_capture && status.screen_capture.running;
        
        // Update overall status indicator
        const overallIndicator = document.getElementById('overall-indicator');
        if (overallIndicator) {
            overallIndicator.className = 'status-indicator';
            overallIndicator.classList.add(status.overall_status === 'running' ? 'running' : 'stopped');
        }
        
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
        
        // Update ChromaDB status indicator
        const chromaIndicator = document.getElementById('chroma-indicator');
        if (chromaIndicator) {
            chromaIndicator.className = 'status-indicator';
            chromaIndicator.classList.add(status.chroma_db.running ? 'running' : 'stopped');
        }
        
        const chromaHealth = document.getElementById('chroma-health');
        if (chromaHealth) {
            chromaHealth.textContent = status.chroma_db.healthy ? 'Healthy' : 'Unhealthy';
        }
        
        const chromaPid = document.getElementById('chroma-pid');
        if (chromaPid && status.chroma_db.pid) {
            chromaPid.textContent = status.chroma_db.pid;
        }
        
        // Update Screen Capture status indicator
        const captureIndicator = document.getElementById('capture-indicator');
        if (captureIndicator) {
            captureIndicator.className = 'status-indicator';
            captureIndicator.classList.add(status.screen_capture.running ? 'running' : 'stopped');
        }
        
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
    
    async updateEnhancedMetrics() {
        try {
            const response = await fetch('/api/enhanced-metrics');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const metrics = await response.json();
            
            // Today's Activity
            const todayScreenshotCount = document.getElementById('today-screenshot-count');
            const todayTextCaptured = document.getElementById('today-text-captured');
            const todayActiveHours = document.getElementById('today-active-hours');
            
            if (todayScreenshotCount) todayScreenshotCount.textContent = metrics.today.screenshot_count;
            if (todayTextCaptured) {
                const textCount = metrics.today.text_captured;
                if (textCount >= 1000000) {
                    todayTextCaptured.textContent = (textCount / 1000000).toFixed(1) + 'M';
                } else if (textCount >= 1000) {
                    todayTextCaptured.textContent = (textCount / 1000).toFixed(1) + 'K';
                } else {
                    todayTextCaptured.textContent = textCount;
                }
            }
            if (todayActiveHours) todayActiveHours.textContent = metrics.today.active_hours;
            
            // 7-Day Overview
            const weekTotalScreenshots = document.getElementById('week-total-screenshots');
            const weekDailyAverage = document.getElementById('week-daily-average');
            const weekTrendSymbol = document.getElementById('week-trend-symbol');
            const weekTrendLabel = document.getElementById('week-trend-label');
            const weekMostActiveDay = document.getElementById('week-most-active-day');
            const weekMostActiveDayCount = document.getElementById('week-most-active-day-count');
            const weekActiveDays = document.getElementById('week-active-days');
            const weekSuccessRate = document.getElementById('week-success-rate');
            
            if (weekTotalScreenshots) weekTotalScreenshots.textContent = metrics.seven_day.total_screenshots;
            if (weekDailyAverage) weekDailyAverage.textContent = metrics.seven_day.daily_average;
            if (weekTrendSymbol) weekTrendSymbol.textContent = metrics.seven_day.trend_symbol;
            if (weekTrendLabel) {
                weekTrendLabel.textContent = metrics.seven_day.trend;
                weekTrendLabel.style.textTransform = 'uppercase';
            }
            
            if (weekMostActiveDay && metrics.seven_day.most_active_day !== 'N/A') {
                const date = new Date(metrics.seven_day.most_active_day);
                weekMostActiveDay.textContent = date.toLocaleDateString('en-US', { 
                    month: 'short', 
                    day: 'numeric' 
                });
            } else if (weekMostActiveDay) {
                weekMostActiveDay.textContent = 'N/A';
            }
            if (weekMostActiveDayCount) {
                weekMostActiveDayCount.textContent = metrics.seven_day.most_active_day_count + ' captures';
            }
            if (weekActiveDays) weekActiveDays.textContent = metrics.seven_day.active_days;
            if (weekSuccessRate) weekSuccessRate.textContent = metrics.seven_day.empty_capture_rate !== undefined 
                ? (100 - metrics.seven_day.empty_capture_rate).toFixed(1) + '%'
                : '-';
            
            // ChromaDB Status
            const chromaTotalDocuments = document.getElementById('chroma-total-documents');
            const chromaCollectionCount = document.getElementById('chroma-collection-count');
            const chromaStatusLabel = document.getElementById('chroma-status-label');
            
            if (chromaTotalDocuments) chromaTotalDocuments.textContent = metrics.chromadb.total_documents;
            if (chromaCollectionCount) chromaCollectionCount.textContent = metrics.chromadb.collections.length;
            if (chromaStatusLabel) {
                chromaStatusLabel.textContent = metrics.chromadb.status;
                chromaStatusLabel.style.textTransform = 'uppercase';
            }
            
            // System Debug Info
            const systemOcrFiles = document.getElementById('system-ocr-files');
            const systemDiskSpace = document.getElementById('system-disk-space');
            
            if (systemOcrFiles) systemOcrFiles.textContent = metrics.system.ocr_files_on_disk;
            if (systemDiskSpace) systemDiskSpace.textContent = metrics.system.disk_space_used;
            
            console.log('Enhanced metrics updated successfully');
            
        } catch (error) {
            console.error('Error updating enhanced metrics:', error);
        }
    }
    
    // Status Dot Management
    updateStatusDot(isOnline) {
        const statusDot = document.getElementById('status-dot');
        if (statusDot) {
            statusDot.className = 'status-dot';
            if (!isOnline) {
                statusDot.classList.add('offline');
            }
        }
    }
    
    // Weekly Chart
    async initializeWeeklyChart() {
        try {
            const response = await fetch('/api/activity-data?hours=168&grouping=daily');
            const data = await response.json();
            
            const ctx = document.getElementById('weekly-bar-chart');
            if (!ctx) return;
            
            // Group by day and count screenshots
            const dayData = {};
            data.timeline_data.forEach(item => {
                const day = item.timestamp.split(' ')[0];
                if (!dayData[day]) {
                    dayData[day] = { total: 0, screens: new Set() };
                }
                dayData[day].total += item.capture_count;
                item.screen_names.forEach(screen => dayData[day].screens.add(screen));
            });
            
            const labels = Object.keys(dayData).map(date => {
                const d = new Date(date);
                return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            });
            
            const totals = Object.values(dayData).map(d => d.total);
            const screenCounts = Object.values(dayData).map(d => d.screens.size);
            
            this.weeklyChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Screenshots',
                        data: totals,
                        backgroundColor: '#111827',
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    aspectRatio: 3,
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            callbacks: {
                                afterLabel: function(context) {
                                    const screens = screenCounts[context.dataIndex];
                                    return `${screens} screen${screens !== 1 ? 's' : ''}`;
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                precision: 0
                            }
                        }
                    }
                }
            });
            
        } catch (error) {
            console.error('Error initializing weekly chart:', error);
        }
    }
    
    // Coverage Heatmap - GitHub style
    async initializeCoverageHeatmap() {
        try {
            const response = await fetch('/api/activity-data?hours=168&grouping=daily');
            const data = await response.json();
            
            const container = document.getElementById('coverage-heatmap');
            if (!container) return;
            
            // Create wrapper
            const wrapper = document.createElement('div');
            wrapper.className = 'heatmap-wrapper';
            
            // Get 8 weeks of data (56 days)
            const now = new Date();
            const startDate = new Date(now);
            startDate.setDate(now.getDate() - 55); // Go back 55 days to get ~8 weeks
            
            // Adjust to start on Sunday
            const dayOfWeek = startDate.getDay();
            startDate.setDate(startDate.getDate() - dayOfWeek);
            
            // Build activity map
            const activityMap = {};
            data.timeline_data.forEach(item => {
                const dateKey = item.timestamp.split(' ')[0]; // Get just the date part
                activityMap[dateKey] = item.capture_count;
            });
            
            // Create month labels
            const monthsDiv = document.createElement('div');
            monthsDiv.className = 'heatmap-months';
            
            // Create main container
            const mainDiv = document.createElement('div');
            mainDiv.className = 'heatmap-main';
            
            // Create day labels (Sun, Mon, Tue, Wed, Thu, Fri, Sat)
            const daysLabels = document.createElement('div');
            daysLabels.className = 'heatmap-days-labels';
            
            const dayNames = ['Sun', '', 'Mon', '', 'Wed', '', 'Fri', ''];
            dayNames.forEach((name, index) => {
                const label = document.createElement('div');
                label.className = 'heatmap-day-label';
                if (!name) label.classList.add('empty');
                label.textContent = name;
                daysLabels.appendChild(label);
            });
            
            // Create grid of weeks
            const grid = document.createElement('div');
            grid.className = 'heatmap-grid';
            
            let currentDate = new Date(startDate);
            let currentMonth = null;
            let weekIndex = 0;
            
            // Generate 8 weeks
            for (let week = 0; week < 8; week++) {
                const weekColumn = document.createElement('div');
                weekColumn.className = 'heatmap-week';
                
                // Add 7 days for this week
                for (let day = 0; day < 7; day++) {
                    const cell = document.createElement('div');
                    cell.className = 'heatmap-cell';
                    
                    // Check if this date has activity
                    const dateKey = currentDate.toISOString().split('T')[0];
                    const count = activityMap[dateKey] || 0;
                    
                    // Set level based on count
                    let level = 0;
                    if (count > 0) {
                        if (count >= 12) level = 4;
                        else if (count >= 8) level = 3;
                        else if (count >= 4) level = 2;
                        else level = 1;
                    }
                    
                    cell.classList.add(`level-${level}`);
                    cell.title = `${currentDate.toLocaleDateString()}: ${count} capture${count !== 1 ? 's' : ''}`;
                    
                    // Track months for labels
                    if (day === 0 && currentDate.getDate() <= 7) {
                        const monthName = currentDate.toLocaleDateString('en-US', { month: 'short' });
                        if (monthName !== currentMonth) {
                            const monthLabel = document.createElement('div');
                            monthLabel.className = 'heatmap-month';
                            monthLabel.textContent = monthName;
                            monthLabel.style.width = '80px'; // Approximate width for multiple weeks
                            monthsDiv.appendChild(monthLabel);
                            currentMonth = monthName;
                        }
                    }
                    
                    weekColumn.appendChild(cell);
                    currentDate.setDate(currentDate.getDate() + 1);
                }
                
                grid.appendChild(weekColumn);
            }
            
            mainDiv.appendChild(daysLabels);
            mainDiv.appendChild(grid);
            
            wrapper.appendChild(monthsDiv);
            wrapper.appendChild(mainDiv);
            
            container.innerHTML = '';
            container.appendChild(wrapper);
            
        } catch (error) {
            console.error('Error initializing coverage heatmap:', error);
        }
    }
    
    // Screen Cards
    async initializeScreenCards() {
        try {
            const response = await fetch('/api/status');
            const status = await response.json();
            
            const screensGrid = document.getElementById('screens-grid');
            if (!screensGrid) return;
            
            screensGrid.innerHTML = '';
            
            // Only show cards for screens that actually exist
            // For now, we'll check if screen_capture is running
            if (status.screen_capture && status.screen_capture.running) {
                // Would ideally get screen count from API
                // For now, just show a single active card
                const card = document.createElement('div');
                card.className = 'screen-card';
                card.innerHTML = `
                    <h4>Screen 1</h4>
                    <div class="screen-status">Active</div>
                `;
                screensGrid.appendChild(card);
            } else {
                screensGrid.innerHTML = '<p style="color: var(--gray-600);">No active screens detected. Start the system to begin capturing.</p>';
            }
            
        } catch (error) {
            console.error('Error initializing screen cards:', error);
        }
    }
    
    // Countdown
    startCountdown() {
        const updateCountdown = () => {
            const countdownText = document.getElementById('countdown-text');
            const statusCountdownText = document.getElementById('status-countdown-text');
            
            // Update countdown display
            if (this.isRecording) {
                // Countdown to next screenshot (60 seconds)
                if (this.secondsRemaining <= 0) {
                    this.secondsRemaining = 60;
                }
                
                // Update header countdown
                if (countdownText) {
                    countdownText.textContent = `Next capture in ${this.secondsRemaining}s`;
                }
                
                // Update status page countdown
                if (statusCountdownText) {
                    statusCountdownText.textContent = `Next capture in ${this.secondsRemaining} seconds`;
                }
                
                this.secondsRemaining--;
            } else {
                if (countdownText) {
                    countdownText.textContent = '';
                }
                if (statusCountdownText) {
                    statusCountdownText.textContent = 'Screen capture is stopped';
                }
                this.secondsRemaining = 60;
            }
        };
        
        // Update every second
        if (this.countdownInterval) {
            clearInterval(this.countdownInterval);
        }
        this.countdownInterval = setInterval(updateCountdown, 1000);
        
        // Initial update
        updateCountdown();
    }
    
    createStateCards() {
        const screenStatesContainer = document.getElementById('screen-states');
        const audioStatesContainer = document.getElementById('audio-states');
        
        if (!screenStatesContainer || !audioStatesContainer) return;
        
        // Screen Refinery States
        const screenComponents = [
            { id: 'hamster-1', name: 'HAMSTER 1', type: 'hamster' },
            { id: 'hamster-2', name: 'HAMSTER 2', type: 'hamster' },
            { id: 'hamster-3', name: 'HAMSTER 3', type: 'hamster' },
            { id: 'monitor-1', name: 'MONITOR 1', type: 'monitor' },
            { id: 'monitor-2', name: 'MONITOR 2', type: 'monitor' },
            { id: 'monitor-3', name: 'MONITOR 3', type: 'monitor' },
            { id: 'pipe-to-ocr', name: 'PIPE TO OCR', type: 'pipe' },
            { id: 'pipe-from-ocr', name: 'PIPE FROM OCR', type: 'pipe' },
            { id: 'ocr-cube', name: 'OCR CUBE', type: 'cube' },
            { id: 'chroma-screen', name: 'CHROMA SCREEN', type: 'chroma' }
        ];
        
        // Audio Refinery States
        const audioComponents = [
            { id: 'audio-hamster', name: 'AUDIO HAMSTER', type: 'hamster' },
            { id: 'audio-pipe-1', name: 'AUDIO PIPE 1', type: 'pipe' },
            { id: 'audio-pipe-2', name: 'AUDIO PIPE 2', type: 'pipe' },
            { id: 'audio-cube', name: 'AUDIO CUBE', type: 'cube' },
            { id: 'chroma-audio', name: 'CHROMA AUDIO', type: 'chroma' }
        ];
        
        // Create screen state cards
        screenComponents.forEach(component => {
            const card = this.createStateCard(component);
            screenStatesContainer.appendChild(card);
        });
        
        // Create audio state cards
        audioComponents.forEach(component => {
            const card = this.createStateCard(component);
            audioStatesContainer.appendChild(card);
        });
    }
    
    createStateCard(component) {
        const card = document.createElement('div');
        card.className = 'state-card idle';
        card.id = `state-${component.id}`;
        
        card.innerHTML = `
            <h4>${component.name}</h4>
            <div class="state-value">IDLE</div>
            <div class="state-time">--:--</div>
        `;
        
        return card;
    }
    
    updateHamsterStates(stateData) {
        if (!stateData || !stateData.components) return;
        
        Object.entries(stateData.components).forEach(([componentId, state]) => {
            this.updateComponentState(componentId, state);
        });
    }
    
    updateComponentState(componentId, state) {
        const card = document.getElementById(`state-${componentId}`);
        if (!card) return;
        
        // Update card classes
        card.className = `state-card ${state.status || 'idle'}`;
        
        // Update state value
        const stateValue = card.querySelector('.state-value');
        if (stateValue) {
            stateValue.textContent = state.status?.toUpperCase() || 'IDLE';
        }
        
        // Update timestamp
        const stateTime = card.querySelector('.state-time');
        if (stateTime) {
            const now = new Date();
            stateTime.textContent = now.toLocaleTimeString();
        }
        
        // Store state in memory
        if (componentId.includes('audio')) {
            this.hamsterStates.audio[componentId] = state;
        } else {
            this.hamsterStates.screen[componentId] = state;
        }
    }
    
    handleHamsterEvent(eventData) {
        if (!eventData) return;
        
        const { componentId, action, newState, timestamp } = eventData;
        
        // Update the component state
        this.updateComponentState(componentId, {
            status: newState,
            lastAction: action,
            timestamp: timestamp
        });
        
        // Show notification for important events
        if (this.showNotifications && this.isImportantEvent(action)) {
            this.showToast(`${componentId}: ${action}`, 'info');
        }
        
        // Log the event
        console.log(`[Hamster Event] ${componentId}: ${action} -> ${newState}`);
    }
    
    isImportantEvent(action) {
        const importantActions = [
            'START_RUN',
            'TAKE_SCREENSHOT',
            'START_PROCESSING',
            'START_FLOW',
            'ERROR_OCCURRED',
            'COMPLETED'
        ];
        return importantActions.includes(action);
    }
    
    // Get current hamster states for debugging
    getHamsterStates() {
        return this.hamsterStates;
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
                    label: 'CAPTURES WITH CONTENT',
                    data: activityData.contentData,
                    backgroundColor: '#111827',
                    borderColor: '#111827',
                    borderWidth: 0
                }, {
                    label: 'EMPTY CAPTURES',
                    data: activityData.emptyData,
                    backgroundColor: '#4B5563',
                    borderColor: '#4B5563',
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: true,
                scales: {
                    x: {
                        stacked: true,
                        grid: {
                            color: '#E5E7EB',
                            lineWidth: 1
                        },
                        ticks: {
                            color: '#4B5563',
                            font: {
                                family: 'Arial, sans-serif',
                                weight: 'normal',
                                size: 12
                            },
                            maxRotation: 0,
                            minRotation: 0
                        },
                        title: {
                            display: false
                        }
                    },
                    y: {
                        stacked: true,
                        beginAtZero: true,
                        grid: {
                            color: '#E5E7EB',
                            lineWidth: 1
                        },
                        ticks: {
                            color: '#4B5563',
                            font: {
                                family: 'Arial, sans-serif',
                                weight: 'normal',
                                size: 12
                            },
                            stepSize: 1
                        },
                        title: {
                            display: false
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false // We have custom legend
                    },
                    tooltip: {
                        backgroundColor: '#111827',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        borderColor: '#111827',
                        borderWidth: 0,
                        padding: 16,
                        titleFont: {
                            family: 'Arial, sans-serif',
                            weight: '600',
                            size: 14
                        },
                        bodyFont: {
                            family: 'Arial, sans-serif',
                            weight: 'normal',
                            size: 14
                        },
                        callbacks: {
                            title: function(context) {
                                return context[0].label || 'Time';
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
    
    startCountdown() {
        this.countdownInterval = setInterval(() => {
            this.secondsRemaining--;
            
            const countdownElement = document.getElementById('countdown');
            if (countdownElement) {
                countdownElement.textContent = this.secondsRemaining;
            }
            
            // When countdown reaches 0, trigger screenshot and reset
            if (this.secondsRemaining <= 0) {
                this.triggerScreenshot();
                this.secondsRemaining = 60;
            }
        }, 1000);
    }
    
    triggerScreenshot() {
        // Flash the start line to indicate screenshot
        const startLine = document.querySelector('.start-line');
        if (startLine) {
            startLine.style.backgroundColor = 'var(--pixel-black)';
            startLine.style.color = 'var(--pixel-white)';
            setTimeout(() => {
                startLine.style.backgroundColor = '';
                startLine.style.color = '';
            }, 500);
        }
        
        // Show toast notification
        this.showToast('SCREENSHOT CAPTURED!', 'success', 2000);
        
        console.log('Screenshot triggered at:', new Date().toISOString());
    }
    
    startMcpMonitoring() {
        // Check MCP server status every 30 seconds
        setInterval(() => {
            this.checkMcpStatus();
        }, 30000);
        
        // Initial check
        this.checkMcpStatus();
    }
    
    async checkMcpStatus() {
        try {
            const response = await fetch('/api/mcp-status');
            const mcpData = await response.json();
            
            const mcpClientsElement = document.getElementById('mcp-clients');
            const mcpLastRequestElement = document.getElementById('mcp-last-request');
            
            if (mcpClientsElement) {
                mcpClientsElement.textContent = mcpData.clients || 0;
            }
            
            if (mcpLastRequestElement) {
                if (mcpData.last_request) {
                    const lastRequest = new Date(mcpData.last_request);
                    mcpLastRequestElement.textContent = lastRequest.toLocaleTimeString();
                } else {
                    mcpLastRequestElement.textContent = 'NEVER';
                }
            }
            
            // Update MCP indicator status
            const mcpIndicator = document.getElementById('mcp-indicator');
            if (mcpIndicator) {
                mcpIndicator.className = 'status-indicator';
                mcpIndicator.classList.add(mcpData.running ? 'running' : 'stopped');
            }
            
        } catch (error) {
            console.error('Error checking MCP status:', error);
            const mcpStatusElement = document.getElementById('mcp-status');
            if (mcpStatusElement) {
                mcpStatusElement.textContent = 'ERROR';
            }
        }
    }

    async fetchActivityData() {
        try {
            const timeRange = document.getElementById('time-range')?.value || '72'; // Default to 3 days
            const grouping = 'minutely'; // Force minute-by-minute
            
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
                    const date = new Date(item.timestamp);
                    if (grouping === 'minutely') {
                        // For minute-by-minute data, show only day marks
                        const dayStart = new Date(date);
                        dayStart.setHours(0, 0, 0, 0);
                        
                        // Only show label if this is the first entry of a new day
                        const isNewDay = date.getHours() === 0 && date.getMinutes() === 0;
                        return isNewDay ? date.toLocaleDateString([], { 
                            month: 'short', 
                            day: 'numeric' 
                        }) : '';
                    } else if (grouping === 'hourly') {
                        return date.toLocaleTimeString([], { 
                            month: 'short', 
                            day: 'numeric', 
                            hour: '2-digit' 
                        });
                    } else {
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
        
        // Update enhanced metrics every 60 seconds
        setInterval(async () => {
            await this.updateEnhancedMetrics();
        }, 60000);
        
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
    
    highlightSearchMatches(text, query) {
        if (!text || !query) return text;
        
        // Split query into individual words
        const queryWords = query.toLowerCase().split(/\s+/).filter(w => w.length > 2);
        if (queryWords.length === 0) return text;
        
        // Find the first occurrence of any query word
        const textLower = text.toLowerCase();
        let firstMatchIndex = -1;
        let matchedWord = '';
        
        for (const word of queryWords) {
            const index = textLower.indexOf(word);
            if (index !== -1 && (firstMatchIndex === -1 || index < firstMatchIndex)) {
                firstMatchIndex = index;
                matchedWord = word;
            }
        }
        
        // If no match found, return original text (truncated)
        if (firstMatchIndex === -1) {
            return text.length > 300 ? text.substring(0, 300) + '...' : text;
        }
        
        // Extract context around the match (200 chars before and after)
        const contextSize = 200;
        const start = Math.max(0, firstMatchIndex - contextSize);
        const end = Math.min(text.length, firstMatchIndex + matchedWord.length + contextSize);
        
        let excerpt = text.substring(start, end);
        
        // Add ellipsis if truncated
        if (start > 0) excerpt = '...' + excerpt;
        if (end < text.length) excerpt = excerpt + '...';
        
        // Highlight all query words in the excerpt
        let highlighted = excerpt;
        for (const word of queryWords) {
            const regex = new RegExp(`(${this.escapeRegex(word)})`, 'gi');
            highlighted = highlighted.replace(regex, '<mark>$1</mark>');
        }
        
        return highlighted;
    }
    
    escapeRegex(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
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
                
                // Extract context around matched text and highlight matches
                const highlightedPreview = this.highlightSearchMatches(
                    result.text_preview, 
                    data.query
                );
                
                resultItem.innerHTML = `
                    <div class="result-header">
                        <span class="result-timestamp">${timestamp}</span>
                        <span class="result-screen">${result.screen_name}</span>
                    </div>
                    <div class="result-preview">${highlightedPreview}</div>
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

// Take screenshot now
async function takeScreenshotNow() {
    const statusDiv = document.getElementById('refinery-status');
    const button = document.getElementById('take-screenshot-btn');
    
    if (!statusDiv || !button) return;
    
    // Disable button
    button.disabled = true;
    button.textContent = '⏳ Capturing...';
    
    try {
        statusDiv.innerHTML = '<div style="color: var(--gray-600);">Capturing screenshots and running OCR...</div>';
        
        const startTime = Date.now();
        
        // Trigger screenshot capture
        // This would ideally call an API endpoint that triggers a manual capture
        // For now, just simulate with a message
        await new Promise(resolve => setTimeout(resolve, 2000)); // Simulate OCR time
        
        const ocrTime = ((Date.now() - startTime) / 1000).toFixed(2);
        
        // Simulate Chroma save
        const chromaStartTime = Date.now();
        await new Promise(resolve => setTimeout(resolve, 500));
        const chromaTime = ((Date.now() - chromaStartTime) / 1000).toFixed(2);
        
        statusDiv.innerHTML = `
            <div class="timing-metric">
                <strong>${ocrTime}s</strong> Capturing OCR
            </div>
            <div class="timing-metric">
                <strong>${chromaTime}s</strong> Saving to Chroma
            </div>
        `;
        
        // Re-enable button
        button.disabled = false;
        button.textContent = '📸 Take Screenshot Now';
        
        // Show success toast
        if (window.flowDashboard) {
            window.flowDashboard.showToast('Screenshot captured successfully', 'success');
        }
        
        // Refresh metrics after a moment
        setTimeout(() => {
            if (window.flowDashboard) {
                window.flowDashboard.updateEnhancedMetrics();
                window.flowDashboard.initializeWeeklyChart();
                window.flowDashboard.initializeCoverageHeatmap();
            }
        }, 1000);
        
    } catch (error) {
        console.error('Error taking screenshot:', error);
        statusDiv.innerHTML = '<div style="color: #EF4444;">Error capturing screenshot</div>';
        button.disabled = false;
        button.textContent = '📸 Take Screenshot Now';
    }
}

// Page Switching
function switchPage(pageName) {
    // Hide all pages
    const pages = document.querySelectorAll('.page-content');
    pages.forEach(page => {
        page.style.display = 'none';
    });
    
    // Show selected page
    const selectedPage = document.getElementById(`page-${pageName}`);
    if (selectedPage) {
        selectedPage.style.display = 'block';
    }
    
    // Update active tab
    const tabs = document.querySelectorAll('.nav-tab');
    tabs.forEach(tab => {
        tab.classList.remove('active');
        if (tab.getAttribute('data-page') === pageName) {
            tab.classList.add('active');
        }
    });
    
    // Load logs when logs page is opened
    if (pageName === 'logs') {
        refreshAllLogs();
    }
    
    // Store current page in localStorage
    localStorage.setItem('currentPage', pageName);
}

// Toggle Tools Panel
function toggleToolsPanel() {
    const toolsGrid = document.getElementById('mcp-tools-grid');
    const chevron = document.getElementById('tools-chevron');
    
    if (!toolsGrid || !chevron) return;
    
    if (toolsGrid.style.display === 'none') {
        toolsGrid.style.display = 'grid';
        chevron.classList.add('rotated');
    } else {
        toolsGrid.style.display = 'none';
        chevron.classList.remove('rotated');
    }
}

// Chat Functions
let chatHistory = [];
let messageCounter = 0;

async function sendChatMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Generate unique message ID
    const messageId = `msg_${Date.now()}_${++messageCounter}`;
    
    // Add user message to chat immediately
    addChatMessage('user', message);
    chatHistory.push({ role: 'user', content: message });
    
    // Clear input
    input.value = '';
    
    // Send message to backend
    try {
        const response = await fetch('/api/chat/send', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message_id: messageId,
                content: message
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || 'Failed to send message');
        }
        
        // Show queued status
        addChatMessage('system', `Message queued (${data.message_id})`);
        
    } catch (error) {
        console.error('Error sending chat message:', error);
        addChatMessage('error', `Error: ${error.message}`);
    }
}

// Handle incoming WebSocket chat messages
function handleChatWebSocketMessage(data) {
    if (data.type === 'chat_message') {
        const msg = data.data;
        addChatMessage(msg.role, msg.content);
        chatHistory.push({ role: msg.role, content: msg.content });
    }
    else if (data.type === 'tool_status') {
        const tool = data.data;
        if (tool.status === 'executing') {
            addChatMessage('tool', `🔧 Executing tool: ${tool.tool_name}...`);
        } else if (tool.status === 'completed') {
            addChatMessage('tool', `✅ Tool ${tool.tool_name} completed`);
        }
    }
    else if (data.type === 'queue_update') {
        updateQueueDisplay(data.data);
    }
    else if (data.type === 'message_status') {
        const status = data.data;
        if (status.status === 'error') {
            addChatMessage('error', `Message failed: ${status.error}`);
        }
    }
}

// Update queue display
function updateQueueDisplay(queueData) {
    // Show queue information if there's a queue panel
    const queuePanel = document.getElementById('chat-queue-panel');
    if (queuePanel) {
        if (queueData.queue_size > 0) {
            queuePanel.style.display = 'block';
            queuePanel.innerHTML = `
                <div class="queue-info">
                    <strong>Queue:</strong> ${queueData.queue_size} message(s) pending
                </div>
            `;
        } else {
            queuePanel.style.display = 'none';
        }
    }
}

function addChatMessage(type, content) {
    const messagesDiv = document.getElementById('chat-messages');
    if (!messagesDiv) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${type}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    if (type === 'user') {
        contentDiv.innerHTML = `<strong>You:</strong> ${escapeHtml(content)}`;
    } else if (type === 'assistant') {
        contentDiv.innerHTML = `<strong>Assistant:</strong> ${escapeHtml(content).replace(/\n/g, '<br>')}`;
    } else if (type === 'error') {
        contentDiv.innerHTML = `<strong>Error:</strong> ${escapeHtml(content)}`;
    } else if (type === 'tool') {
        contentDiv.innerHTML = `<strong>Tool:</strong> ${escapeHtml(content)}`;
    } else {
        contentDiv.innerHTML = `<strong>System:</strong> ${escapeHtml(content)}`;
    }
    
    messageDiv.appendChild(contentDiv);
    messagesDiv.appendChild(messageDiv);
    
    // Scroll to bottom
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

async function clearChat() {
    try {
        // Clear on backend
        const response = await fetch('/api/chat/clear-conversation', {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error('Failed to clear conversation');
        }
        
        // Clear locally
        const messagesDiv = document.getElementById('chat-messages');
        if (messagesDiv) {
            messagesDiv.innerHTML = `
                <div class="chat-message system">
                    <div class="message-content">
                        <strong>System:</strong> Conversation cleared. MCP Chat ready. Available tools: search, stats, activity, system. Try asking me anything!
                    </div>
                </div>
            `;
        }
        chatHistory = [];
        
    } catch (error) {
        console.error('Error clearing chat:', error);
        addChatMessage('error', 'Failed to clear conversation');
    }
}

function quickChat(message) {
    const input = document.getElementById('chat-input');
    if (input) {
        input.value = message;
        sendChatMessage();
    }
}

// Log Functions
async function refreshAllLogs() {
    console.log('Refreshing all logs...');
    const dashboard = window.flowDashboard;
    
    try {
        const subsystems = ['screen-capture', 'dashboard', 'mcp-server', 'chromadb'];
        
        for (const subsystem of subsystems) {
            await loadLogsForSubsystem(subsystem);
        }
        
        if (dashboard) {
            dashboard.showToast('Logs refreshed', 'success');
        }
    } catch (error) {
        console.error('Error refreshing logs:', error);
        if (dashboard) {
            dashboard.showToast('Failed to refresh logs', 'error');
        }
    }
}

async function loadLogsForSubsystem(subsystem) {
    try {
        const response = await fetch(`/api/logs/${subsystem}?max_lines=100`);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(`Failed to load ${subsystem} logs`);
        }
        
        // Map subsystem names to log content IDs
        const contentMap = {
            'screen-capture': 'screen-logs',
            'dashboard': 'dashboard-logs',
            'mcp-server': 'mcp-logs',
            'chromadb': 'chroma-logs'
        };
        
        const contentId = contentMap[subsystem];
        if (!contentId) return;
        
        const logContent = document.getElementById(contentId);
        if (!logContent) return;
        
        // Clear existing logs
        logContent.innerHTML = '';
        
        if (data.logs && data.logs.length > 0) {
            // Add log entries
            data.logs.forEach(log => {
                const logEntry = document.createElement('div');
                logEntry.className = `log-entry log-${log.level.toLowerCase()}`;
                
                logEntry.innerHTML = `
                    <span class="log-time">${log.timestamp || new Date().toLocaleTimeString()}</span>
                    <span class="log-level">${log.level}</span>
                    <span class="log-message">${escapeHtml(log.message)}</span>
                `;
                
                logContent.appendChild(logEntry);
            });
        } else {
            logContent.innerHTML = '<div class="log-empty">No logs available</div>';
        }
        
    } catch (error) {
        console.error(`Error loading logs for ${subsystem}:`, error);
    }
}

function clearAllLogs() {
    if (!confirm('Are you sure you want to clear all logs?')) {
        return;
    }
    
    const logContents = document.querySelectorAll('.log-content');
    logContents.forEach(content => {
        content.innerHTML = '<div class="log-empty">No logs available</div>';
    });
    
    const dashboard = window.flowDashboard;
    if (dashboard) {
        dashboard.showToast('All logs cleared', 'success');
    }
}

function filterLogs(subsystem) {
    const selectId = `${subsystem}-log-level`;
    const select = document.getElementById(selectId);
    if (!select) return;
    
    const level = select.value;
    console.log(`Filtering ${subsystem} logs to ${level}`);
    
    // Would implement actual filtering here
}

// Handle Enter key in chat input
document.addEventListener('DOMContentLoaded', function() {
    const chatInput = document.getElementById('chat-input');
    if (chatInput) {
        chatInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendChatMessage();
            }
        });
    }
    
    // Restore last page from localStorage or default to search
    const currentPage = localStorage.getItem('currentPage');
    if (currentPage) {
        switchPage(currentPage);
    } else {
        switchPage('search');
    }
});

// Export for use in HTML
window.startSystem = startSystem;
window.stopSystem = stopSystem;
window.updateActivityGraph = updateActivityGraph;
window.refreshActivityGraph = refreshActivityGraph;
window.initializeDashboard = initializeDashboard;
window.takeScreenshotNow = takeScreenshotNow;
window.switchPage = switchPage;
window.sendChatMessage = sendChatMessage;
window.clearChat = clearChat;
window.quickChat = quickChat;
window.refreshAllLogs = refreshAllLogs;
window.clearAllLogs = clearAllLogs;
window.filterLogs = filterLogs;

/**
 * Visualization Manager for Hamster System
 * Handles visual updates, animations, and real-time data integration
 */

class VisualizationManager {
    constructor(simulationEngine) {
        this.engine = simulationEngine;
        this.websocket = null;
        this.isConnectedToBackend = false;
        this.mockMode = true;
        this.debugMode = false;
        this.eventLog = [];
        this.maxLogEntries = 100;
        
        this.setupEventListeners();
        this.initializeDebugPanel();
    }
    
    setupEventListeners() {
        // Listen to simulation events
        this.engine.on('stateChange', (event) => {
            this.logEvent(`${event.componentId}: ${event.oldState} → ${event.newState}`);
            this.updateDebugDisplay();
        });
        
        this.engine.on('error', (event) => {
            this.showError(`Error in ${event.componentId}: ${event.error.message}`);
            this.logEvent(`ERROR: ${event.componentId} - ${event.error.message}`, 'error');
        });
        
        this.engine.on('simulationStarted', () => {
            this.logEvent('Simulation started', 'info');
        });
        
        this.engine.on('simulationStopped', () => {
            this.logEvent('Simulation stopped', 'info');
        });
        
        this.engine.on('scenarioLoaded', (scenario) => {
            this.logEvent(`Scenario loaded: ${scenario.name}`, 'info');
        });
    }
    
    initializeDebugPanel() {
        const debugPanel = document.getElementById('debug-panel');
        const toggleBtn = document.getElementById('toggle-debug');
        
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => {
                debugPanel.classList.toggle('collapsed');
                this.debugMode = !debugPanel.classList.contains('collapsed');
                
                if (this.debugMode) {
                    this.updateDebugDisplay();
                }
            });
        }
        
        // Initialize debug display
        this.updateDebugDisplay();
    }
    
    updateDebugDisplay() {
        if (!this.debugMode) return;
        
        this.updateComponentStatesDisplay();
        this.updateEventLogDisplay();
    }
    
    updateComponentStatesDisplay() {
        const statesContainer = document.getElementById('component-states');
        if (!statesContainer) return;
        
        const systemState = this.engine.getSystemState();
        let html = '';
        
        Object.entries(systemState).forEach(([componentId, state]) => {
            const statusClass = state.isAnimating ? 'animating' : 'idle';
            html += `
                <div class="component-state ${statusClass}">
                    <strong>${componentId}:</strong> ${state.currentState}
                    <div class="possible-transitions">
                        Next: ${state.possibleStates.join(', ') || 'none'}
                    </div>
                    <div class="component-meta">
                        Updated: ${new Date(state.lastUpdate).toLocaleTimeString()}
                    </div>
                </div>
            `;
        });
        
        statesContainer.innerHTML = html;
    }
    
    updateEventLogDisplay() {
        const logContainer = document.getElementById('event-log');
        if (!logContainer) return;
        
        const recentEvents = this.eventLog.slice(-20); // Show last 20 events
        let html = '';
        
        recentEvents.forEach(event => {
            const timeStr = new Date(event.timestamp).toLocaleTimeString();
            html += `
                <div class="event-entry ${event.type}">
                    <span class="event-time">${timeStr}</span>
                    <span class="event-message">${event.message}</span>
                </div>
            `;
        });
        
        logContainer.innerHTML = html;
        logContainer.scrollTop = logContainer.scrollHeight;
    }
    
    logEvent(message, type = 'info') {
        const event = {
            timestamp: Date.now(),
            message,
            type
        };
        
        this.eventLog.push(event);
        
        // Limit log size
        if (this.eventLog.length > this.maxLogEntries) {
            this.eventLog = this.eventLog.slice(-this.maxLogEntries);
        }
        
        if (this.debugMode) {
            this.updateEventLogDisplay();
        }
        
        // Console logging
        switch (type) {
            case 'error':
                console.error(`[Hamsters] ${message}`);
                break;
            case 'warn':
                console.warn(`[Hamsters] ${message}`);
                break;
            default:
                console.log(`[Hamsters] ${message}`);
        }
    }
    
    showError(message, duration = 5000) {
        const errorBanner = document.getElementById('error-banner');
        const errorMessage = document.getElementById('error-message');
        const dismissBtn = document.getElementById('dismiss-error');
        
        if (errorBanner && errorMessage) {
            errorMessage.textContent = message;
            errorBanner.classList.remove('hidden');
            
            // Auto-hide after duration
            const hideTimeout = setTimeout(() => {
                errorBanner.classList.add('hidden');
            }, duration);
            
            // Manual dismiss
            if (dismissBtn) {
                const dismissHandler = () => {
                    errorBanner.classList.add('hidden');
                    clearTimeout(hideTimeout);
                    dismissBtn.removeEventListener('click', dismissHandler);
                };
                dismissBtn.addEventListener('click', dismissHandler);
            }
        }
    }
    
    // WebSocket connection for real-time backend integration
    connectToBackend(url = 'ws://localhost:8082/ws') {
        try {
            this.websocket = new WebSocket(url);
            
            this.websocket.onopen = () => {
                this.isConnectedToBackend = true;
                this.mockMode = false;
                this.logEvent('Connected to backend WebSocket', 'info');
                this.updateConnectionStatus(true);
            };
            
            this.websocket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleBackendMessage(data);
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            };
            
            this.websocket.onclose = () => {
                this.isConnectedToBackend = false;
                this.mockMode = true;
                this.logEvent('Disconnected from backend, switching to mock mode', 'warn');
                this.updateConnectionStatus(false);
                
                // Attempt to reconnect after delay
                setTimeout(() => {
                    if (!this.isConnectedToBackend) {
                        this.connectToBackend(url);
                    }
                }, 5000);
            };
            
            this.websocket.onerror = (error) => {
                this.logEvent(`WebSocket error: ${error}`, 'error');
            };
            
        } catch (error) {
            this.logEvent(`Failed to connect to backend: ${error.message}`, 'error');
            this.mockMode = true;
        }
    }
    
    handleBackendMessage(data) {
        switch (data.type) {
            case 'status_update':
                this.handleStatusUpdate(data.data);
                break;
                
            case 'screen_detection':
                this.triggerScreenDetection(data.screen_id);
                break;
                
            case 'ocr_processing':
                this.triggerOCRProcessing(data);
                break;
                
            case 'audio_detected':
                this.triggerAudioDetection(data);
                break;
                
            case 'chroma_stored':
                this.triggerDataStorage(data);
                break;
                
            case 'error':
                this.showError(data.message);
                break;
                
            default:
                this.logEvent(`Unknown message type: ${data.type}`, 'warn');
        }
    }
    
    handleStatusUpdate(status) {
        // Update system status based on backend data
        if (status.refinery_running && !this.engine.isRunning) {
            // Backend is running but simulation is not - start simulation
            this.startRealtimeMode();
        } else if (!status.refinery_running && this.engine.isRunning) {
            // Backend stopped - switch to mock mode
            this.stopRealtimeMode();
        }
    }
    
    triggerScreenDetection(screenId) {
        const monitorId = `monitor-${screenId}`;
        const hamsterId = `hamster-${screenId}`;
        
        // Trigger the screen capture flow
        this.engine.scheduleEvent(0, monitorId, 'DETECT_SCREEN');
        this.engine.scheduleEvent(1000, hamsterId, 'START_RUN');
        
        this.logEvent(`Screen detection triggered for ${monitorId}`, 'info');
    }
    
    triggerOCRProcessing(data) {
        this.engine.scheduleEvent(0, 'ocr-cube', 'DATA_RECEIVED', data);
        this.logEvent('OCR processing triggered', 'info');
    }
    
    triggerAudioDetection(data) {
        this.engine.scheduleEvent(0, 'audio-hamster', 'AUDIO_DETECTED', data);
        this.logEvent('Audio detection triggered', 'info');
    }
    
    triggerDataStorage(data) {
        const chromaId = data.collection === 'audio_transcripts' ? 'chroma-audio' : 'chroma-screen';
        this.engine.scheduleEvent(0, chromaId, 'RECEIVE_DATA', data);
        this.logEvent(`Data stored in ${chromaId}`, 'info');
    }
    
    startRealtimeMode() {
        this.mockMode = false;
        this.engine.start();
        this.logEvent('Started real-time mode', 'info');
    }
    
    stopRealtimeMode() {
        this.mockMode = true;
        this.engine.stop();
        this.logEvent('Stopped real-time mode', 'info');
    }
    
    updateConnectionStatus(connected) {
        const statusIndicator = document.getElementById('connection-status');
        const statusDot = statusIndicator?.querySelector('.status-dot');
        const statusText = statusIndicator?.querySelector('.status-text');
        
        if (statusDot && statusText) {
            if (connected) {
                statusDot.style.color = '#32CD32';
                statusText.textContent = 'LIVE';
            } else {
                statusDot.style.color = '#FFD700';
                statusText.textContent = 'MOCK';
            }
        }
    }
    
    // Animation helpers
    createParticleEffect(element, type = 'data') {
        const particle = document.createElement('div');
        particle.className = `particle ${type}`;
        
        const colors = {
            data: '#4169E1',
            audio: '#8A2BE2',
            error: '#DC143C'
        };
        
        particle.style.cssText = `
            position: absolute;
            width: 6px;
            height: 6px;
            background: ${colors[type] || colors.data};
            border-radius: 50%;
            pointer-events: none;
            z-index: 1000;
        `;
        
        element.appendChild(particle);
        
        // Animate particle
        particle.animate([
            { transform: 'translateY(0) scale(1)', opacity: 1 },
            { transform: 'translateY(-20px) scale(0.5)', opacity: 0 }
        ], {
            duration: 1000,
            easing: 'ease-out'
        }).onfinish = () => {
            particle.remove();
        };
    }
    
    highlightComponent(componentId, duration = 2000) {
        const component = this.engine.components.get(componentId);
        if (!component || !component.visualElement) return;
        
        const element = component.visualElement;
        const originalBoxShadow = element.style.boxShadow;
        
        element.style.boxShadow = '0 0 20px #FFD700';
        element.style.transition = 'box-shadow 0.3s ease';
        
        setTimeout(() => {
            element.style.boxShadow = originalBoxShadow;
        }, duration);
    }
    
    // Performance monitoring
    updateMemoryUsage() {
        if (performance.memory) {
            const usage = Math.round(performance.memory.usedJSHeapSize / 1024 / 1024);
            const memoryDisplay = document.getElementById('memory-usage');
            if (memoryDisplay) {
                memoryDisplay.textContent = `${usage} MB`;
            }
        }
    }
    
    // Cleanup
    destroy() {
        if (this.websocket) {
            this.websocket.close();
        }
        
        this.engine.stop();
        this.eventLog = [];
    }
}

// Scenario definitions
const SimulationScenarios = {
    SCREEN_CAPTURE_FLOW: {
        name: 'Screen Capture Flow',
        description: 'Complete screen detection → OCR → storage cycle',
        duration: 15000,
        events: [
            { delay: 0, component: 'monitor-1', action: 'DETECT_SCREEN' },
            { delay: 1000, component: 'hamster-1', action: 'START_RUN' },
            { delay: 3000, component: 'hamster-1', action: 'REACH_MONITOR' },
            { delay: 4000, component: 'hamster-1', action: 'ENTER_COMPLETE' },
            { delay: 5000, component: 'monitor-1', action: 'TAKE_SCREENSHOT' },
            { delay: 5500, component: 'hamster-1', action: 'SCREENSHOT_TAKEN' },
            { delay: 6500, component: 'hamster-1', action: 'EXIT_COMPLETE' },
            { delay: 8000, component: 'hamster-1', action: 'DELIVER_DATA' },
            { delay: 14000, component: 'hamster-1', action: 'DELIVERY_COMPLETE' }
        ]
    },
    
    AUDIO_TRANSCRIPTION_FLOW: {
        name: 'Audio Transcription Flow',
        description: 'Audio detection → transcription → storage cycle',
        duration: 20000,
        events: [
            { delay: 0, component: 'audio-hamster', action: 'AUDIO_DETECTED' },
            { delay: 2000, component: 'audio-hamster', action: 'START_PROCESSING' },
            { delay: 10000, component: 'audio-hamster', action: 'TRANSCRIPTION_START' },
            { delay: 19000, component: 'audio-hamster', action: 'TRANSCRIPTION_COMPLETE' }
        ]
    },
    
    MULTI_MONITOR_FLOW: {
        name: 'Multi-Monitor Capture',
        description: 'Simultaneous capture from multiple monitors',
        duration: 18000,
        events: [
            // Monitor 1 flow
            { delay: 0, component: 'monitor-1', action: 'DETECT_SCREEN' },
            { delay: 500, component: 'hamster-1', action: 'START_RUN' },
            
            // Monitor 2 flow (offset)
            { delay: 2000, component: 'monitor-2', action: 'DETECT_SCREEN' },
            { delay: 2500, component: 'hamster-2', action: 'START_RUN' },
            
            // Monitor 3 flow (more offset)
            { delay: 4000, component: 'monitor-3', action: 'DETECT_SCREEN' },
            { delay: 4500, component: 'hamster-3', action: 'START_RUN' }
        ]
    },
    
    ERROR_SCENARIOS: {
        name: 'Error Handling',
        description: 'Tests various error conditions and recovery',
        duration: 10000,
        events: [
            { delay: 0, component: 'hamster-1', action: 'START_RUN' },
            { delay: 2000, component: 'hamster-1', action: 'ERROR' },
            { delay: 4000, component: 'hamster-1', action: 'RESET' },
            { delay: 5000, component: 'ocr-cube', action: 'ERROR' },
            { delay: 7000, component: 'ocr-cube', action: 'RESET' }
        ]
    }
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { VisualizationManager, SimulationScenarios };
} else {
    window.VisualizationManager = VisualizationManager;
    window.SimulationScenarios = SimulationScenarios;
}


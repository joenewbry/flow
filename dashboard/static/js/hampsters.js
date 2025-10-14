/**
 * Main Hamster Visualization Application
 * Initializes and coordinates all components
 */

class HamsterApp {
    constructor() {
        this.simulationEngine = null;
        this.visualizationManager = null;
        this.configurationManager = null;
        this.canvasManager = null;
        this.isInitialized = false;
        
        // Bind methods
        this.init = this.init.bind(this);
        this.setupControls = this.setupControls.bind(this);
        this.registerComponents = this.registerComponents.bind(this);
    }
    
    async init() {
        try {
            console.log('🐹 Initializing Hamster Visualization System...');
            
            // Initialize simulation engine
            this.simulationEngine = new SimulationEngine();
            
            // Register all components
            this.registerComponents();
            
            // Initialize visualization manager
            this.visualizationManager = new VisualizationManager(this.simulationEngine);
            
            // Initialize configuration manager
            this.configurationManager = new ConfigurationManager(this.simulationEngine, this.visualizationManager);
            
            // Initialize canvas manager
            this.canvasManager = new CanvasManager(this.simulationEngine, this.visualizationManager);
            
            // Setup UI controls
            this.setupControls();
            
            // Try to connect to backend
            this.visualizationManager.connectToBackend();
            
            // Load default scenario
            this.loadScenario('SCREEN_CAPTURE_FLOW');
            
            this.isInitialized = true;
            console.log('✅ Hamster Visualization System initialized successfully!');
            
        } catch (error) {
            console.error('❌ Failed to initialize Hamster Visualization System:', error);
            this.showError('Failed to initialize visualization system: ' + error.message);
        }
    }
    
    registerComponents() {
        const { StateMachineFactory } = window.HamsterStateMachine;
        
        // Register hamsters
        for (let i = 1; i <= 3; i++) {
            const hamsterElement = document.getElementById(`hamster-${i}`);
            if (hamsterElement) {
                const stateMachine = StateMachineFactory.createHamster();
                this.simulationEngine.registerComponent(`hamster-${i}`, stateMachine, hamsterElement);
            }
        }
        
        // Register audio hamster
        const audioHamsterElement = document.getElementById('audio-hamster');
        if (audioHamsterElement) {
            const stateMachine = StateMachineFactory.createAudioHamster();
            this.simulationEngine.registerComponent('audio-hamster', stateMachine, audioHamsterElement);
        }
        
        // Register monitors
        for (let i = 1; i <= 3; i++) {
            const monitorElement = document.getElementById(`monitor-${i}`);
            if (monitorElement) {
                const stateMachine = StateMachineFactory.createMonitor();
                this.simulationEngine.registerComponent(`monitor-${i}`, stateMachine, monitorElement);
            }
        }
        
        // Register processing cubes
        const ocrCubeElement = document.getElementById('ocr-cube');
        if (ocrCubeElement) {
            const stateMachine = StateMachineFactory.createProcessingCube();
            this.simulationEngine.registerComponent('ocr-cube', stateMachine, ocrCubeElement);
        }
        
        const audioCubeElement = document.getElementById('audio-cube');
        if (audioCubeElement) {
            const stateMachine = StateMachineFactory.createProcessingCube();
            this.simulationEngine.registerComponent('audio-cube', stateMachine, audioCubeElement);
        }
        
        // Register pipes
        const pipes = [
            'pipe-to-ocr',
            'pipe-from-ocr',
            'audio-pipe-1',
            'audio-pipe-2'
        ];
        
        pipes.forEach(pipeId => {
            const pipeElement = document.getElementById(pipeId);
            if (pipeElement) {
                const stateMachine = StateMachineFactory.createPipe();
                this.simulationEngine.registerComponent(pipeId, stateMachine, pipeElement);
            }
        });
        
        // Register ChromaDB storage
        const chromaScreenElement = document.getElementById('chroma-screen');
        if (chromaScreenElement) {
            const stateMachine = StateMachineFactory.createChromaDB();
            this.simulationEngine.registerComponent('chroma-screen', stateMachine, chromaScreenElement);
        }
        
        const chromaAudioElement = document.getElementById('chroma-audio');
        if (chromaAudioElement) {
            const stateMachine = StateMachineFactory.createChromaDB();
            this.simulationEngine.registerComponent('chroma-audio', stateMachine, chromaAudioElement);
        }
        
        console.log(`📝 Registered ${this.simulationEngine.components.size} components`);
    }
    
    setupControls() {
        // Play/Pause button
        const playPauseBtn = document.getElementById('play-pause-btn');
        if (playPauseBtn) {
            playPauseBtn.addEventListener('click', () => {
                if (this.simulationEngine.isRunning) {
                    this.simulationEngine.stop();
                    playPauseBtn.textContent = '▶️ Play';
                    playPauseBtn.classList.remove('playing');
                } else {
                    this.simulationEngine.start();
                    playPauseBtn.textContent = '⏸️ Pause';
                    playPauseBtn.classList.add('playing');
                }
            });
        }
        
        // Step button
        const stepBtn = document.getElementById('step-btn');
        if (stepBtn) {
            stepBtn.addEventListener('click', () => {
                if (!this.simulationEngine.isRunning) {
                    this.simulationEngine.step();
                }
            });
        }
        
        // Reset button
        const resetBtn = document.getElementById('reset-btn');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => {
                this.simulationEngine.reset();
                if (playPauseBtn) {
                    playPauseBtn.textContent = '▶️ Play';
                    playPauseBtn.classList.remove('playing');
                }
            });
        }
        
        // Scenario selector
        const scenarioSelect = document.getElementById('scenario-select');
        if (scenarioSelect) {
            scenarioSelect.addEventListener('change', (e) => {
                this.loadScenario(e.target.value);
            });
        }
        
        // Speed slider
        const speedSlider = document.getElementById('speed-slider');
        const speedDisplay = document.getElementById('speed-display');
        if (speedSlider && speedDisplay) {
            speedSlider.addEventListener('input', (e) => {
                const speed = parseFloat(e.target.value);
                this.simulationEngine.setSpeed(speed);
                speedDisplay.textContent = `${speed.toFixed(1)}x`;
            });
        }
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return;
            
            switch (e.key) {
                case ' ': // Spacebar - play/pause
                    e.preventDefault();
                    playPauseBtn?.click();
                    break;
                case 'r': // R - reset
                    e.preventDefault();
                    resetBtn?.click();
                    break;
                case 's': // S - step
                    e.preventDefault();
                    stepBtn?.click();
                    break;
                case 'd': // D - toggle debug
                    e.preventDefault();
                    document.getElementById('toggle-debug')?.click();
                    break;
            }
        });
        
        console.log('🎮 Controls initialized');
    }
    
    loadScenario(scenarioName) {
        const scenario = window.SimulationScenarios[scenarioName];
        if (!scenario) {
            console.error(`Scenario not found: ${scenarioName}`);
            return;
        }
        
        this.simulationEngine.loadScenario(scenario);
        console.log(`📋 Loaded scenario: ${scenario.name}`);
        
        // Update UI
        const scenarioSelect = document.getElementById('scenario-select');
        if (scenarioSelect) {
            scenarioSelect.value = scenarioName;
        }
    }
    
    showError(message) {
        if (this.visualizationManager) {
            this.visualizationManager.showError(message);
        } else {
            alert(message);
        }
    }
    
    // Manual trigger methods for testing
    triggerScreenCapture(screenId = 1) {
        if (!this.isInitialized) return;
        
        const monitorId = `monitor-${screenId}`;
        const hamsterId = `hamster-${screenId}`;
        
        this.simulationEngine.scheduleEvent(0, monitorId, 'DETECT_SCREEN');
        this.simulationEngine.scheduleEvent(1000, hamsterId, 'START_RUN');
        
        console.log(`📸 Triggered screen capture for screen ${screenId}`);
    }
    
    triggerAudioTranscription() {
        if (!this.isInitialized) return;
        
        this.simulationEngine.scheduleEvent(0, 'audio-hamster', 'AUDIO_DETECTED');
        console.log('🎤 Triggered audio transcription');
    }
    
    triggerError(componentId) {
        if (!this.isInitialized) return;
        
        this.simulationEngine.scheduleEvent(0, componentId, 'ERROR');
        console.log(`❌ Triggered error for ${componentId}`);
    }
    
    // Utility methods
    getSystemStatus() {
        if (!this.isInitialized) return null;
        
        return {
            isRunning: this.simulationEngine.isRunning,
            isConnectedToBackend: this.visualizationManager.isConnectedToBackend,
            mockMode: this.visualizationManager.mockMode,
            componentCount: this.simulationEngine.components.size,
            eventQueueSize: this.simulationEngine.eventQueue.length,
            currentScenario: this.simulationEngine.currentScenario?.name || 'None',
            configuration: this.configurationManager.getCurrentConfig()
        };
    }
    
    exportState() {
        if (!this.isInitialized) return null;
        
        return {
            systemState: this.simulationEngine.getSystemState(),
            eventLog: this.visualizationManager.eventLog.slice(-50), // Last 50 events
            performanceStats: this.simulationEngine.performanceStats,
            timestamp: new Date().toISOString()
        };
    }
    
    // Cleanup
    destroy() {
        if (this.visualizationManager) {
            this.visualizationManager.destroy();
        }
        
        if (this.canvasManager) {
            this.canvasManager.destroy();
        }
        
        if (this.simulationEngine) {
            this.simulationEngine.stop();
        }
        
        this.isInitialized = false;
        console.log('🧹 Hamster Visualization System cleaned up');
    }
}

// Global app instance
let hamsterApp = null;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    hamsterApp = new HamsterApp();
    hamsterApp.init();
    
    // Expose app to global scope for debugging
    window.hamsterApp = hamsterApp;
    
    // Add some helpful console commands
    console.log(`
🐹 Hamster Visualization System Loaded!

Available commands:
- hamsterApp.triggerScreenCapture(1)  // Trigger screen 1 capture
- hamsterApp.triggerAudioTranscription()  // Trigger audio processing
- hamsterApp.getSystemStatus()  // Get current system status
- hamsterApp.exportState()  // Export current state for debugging

Keyboard shortcuts:
- Space: Play/Pause
- R: Reset
- S: Step
- D: Toggle Debug Panel
    `);
});

// Handle page unload
window.addEventListener('beforeunload', () => {
    if (hamsterApp) {
        hamsterApp.destroy();
    }
});

// Handle visibility change (pause when tab is hidden)
document.addEventListener('visibilitychange', () => {
    if (hamsterApp && hamsterApp.simulationEngine) {
        if (document.hidden) {
            // Page is hidden, pause simulation to save resources
            if (hamsterApp.simulationEngine.isRunning) {
                hamsterApp.simulationEngine.stop();
                hamsterApp._wasRunningBeforeHide = true;
            }
        } else {
            // Page is visible again, resume if it was running
            if (hamsterApp._wasRunningBeforeHide) {
                hamsterApp.simulationEngine.start();
                hamsterApp._wasRunningBeforeHide = false;
            }
        }
    }
});

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { HamsterApp };
}

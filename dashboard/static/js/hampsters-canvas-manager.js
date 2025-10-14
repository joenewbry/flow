/**
 * Canvas Manager for Hamster Visualizations
 * Coordinates Screen Recording and Audio Recording canvas renderers
 */

class CanvasManager {
    constructor(simulationEngine, visualizationManager) {
        this.engine = simulationEngine;
        this.visualizationManager = visualizationManager;
        
        // Canvas renderers
        this.screenRenderer = null;
        this.audioRenderer = null;
        
        // Configuration
        this.config = {
            canvasWidth: 800,
            canvasHeight: 400,
            fps: 8
        };
        
        this.init();
    }
    
    init() {
        // Initialize canvas elements
        const screenCanvas = document.getElementById('screen-canvas');
        const audioCanvas = document.getElementById('audio-canvas');
        
        if (screenCanvas) {
            this.screenRenderer = new CanvasRenderer(screenCanvas, this.config.canvasWidth, this.config.canvasHeight);
        }
        
        if (audioCanvas) {
            this.audioRenderer = new CanvasRenderer(audioCanvas, this.config.canvasWidth, this.config.canvasHeight);
        }
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Start rendering
        this.start();
        
        console.log('🎨 Canvas Manager initialized');
    }
    
    setupEventListeners() {
        // Listen to simulation events
        this.engine.on('stateChange', (event) => {
            this.handleStateChange(event);
        });
        
        this.engine.on('eventProcessed', (event) => {
            this.handleEventProcessed(event);
        });
        
        // Listen to configuration changes
        if (this.visualizationManager.configurationManager) {
            this.visualizationManager.configurationManager.on('configChanged', (config) => {
                this.updateConfiguration(config);
            });
        }
    }
    
    handleStateChange(event) {
        const { componentId, newState, oldState } = event;
        const componentType = componentId.split('_')[0];
        
        // Route to appropriate canvas
        if (componentType === 'hamster' || componentType === 'monitor' || componentType === 'pipe' || componentType === 'ocr-cube' || componentType === 'chroma') {
            this.updateScreenCanvas(componentId, newState, oldState);
        } else if (componentType === 'audio-hamster' || componentType === 'audio-cube' || componentId.includes('audio')) {
            this.updateAudioCanvas(componentId, newState, oldState);
        }
    }
    
    handleEventProcessed(event) {
        const { componentId, action, newState } = event;
        
        // Handle specific events
        switch (action) {
            case 'START_RUN':
                this.triggerHamsterRun(componentId);
                break;
            case 'TAKE_SCREENSHOT':
                this.triggerScreenshot(componentId);
                break;
            case 'START_FLOW':
                this.triggerPipeFlow(componentId);
                break;
            case 'START_PROCESSING':
                this.triggerProcessing(componentId);
                break;
        }
    }
    
    updateScreenCanvas(componentId, newState, oldState) {
        if (!this.screenRenderer) return;
        
        let object = this.screenRenderer.objects.find(obj => obj.id === componentId);
        
        if (!object) {
            // Create new object
            object = this.createScreenObject(componentId, newState);
        } else {
            // Update existing object
            this.updateScreenObject(object, newState);
        }
    }
    
    updateAudioCanvas(componentId, newState, oldState) {
        if (!this.audioRenderer) return;
        
        let object = this.audioRenderer.objects.find(obj => obj.id === componentId);
        
        if (!object) {
            // Create new object
            object = this.createAudioObject(componentId, newState);
        } else {
            // Update existing object
            this.updateAudioObject(object, newState);
        }
    }
    
    createScreenObject(componentId, state) {
        const positions = this.getScreenObjectPositions();
        const pos = positions[componentId] || { x: 100, y: 100 };
        
        let objectType = 'hamster';
        if (componentId.includes('monitor')) objectType = 'monitor';
        else if (componentId.includes('pipe')) objectType = 'pipe_empty';
        else if (componentId.includes('cube')) objectType = 'cube_idle';
        else if (componentId.includes('chroma')) objectType = 'data_particle';
        
        const object = this.screenRenderer.createObject(objectType, pos.x, pos.y, {
            state: state,
            componentId: componentId
        });
        
        return object;
    }
    
    createAudioObject(componentId, state) {
        const positions = this.getAudioObjectPositions();
        const pos = positions[componentId] || { x: 100, y: 100 };
        
        let objectType = 'audio_hamster_sleeping';
        if (componentId.includes('pipe')) objectType = 'audio_particle';
        else if (componentId.includes('cube')) objectType = 'cube_idle';
        
        const object = this.audioRenderer.createObject(objectType, pos.x, pos.y, {
            state: state,
            componentId: componentId
        });
        
        return object;
    }
    
    updateScreenObject(object, newState) {
        object.state = newState;
        
        // Update object type based on state
        switch (newState) {
            case 'waiting':
                object.type = 'hamster_idle';
                break;
            case 'running':
                object.type = 'hamster_running';
                object.speed = 2;
                break;
            case 'entering_manhole':
                object.type = 'hamster_entering';
                break;
            case 'exiting_manhole':
                object.type = 'hamster_exiting';
                break;
            case 'detected':
                object.type = 'monitor_detected';
                break;
            case 'capturing':
                object.type = 'monitor_capturing';
                break;
            case 'flowing':
                object.type = 'pipe_flowing';
                break;
            case 'processing':
                object.type = 'cube_processing';
                break;
        }
    }
    
    updateAudioObject(object, newState) {
        object.state = newState;
        
        // Update object type based on state
        switch (newState) {
            case 'sleeping':
                object.type = 'audio_hamster_sleeping';
                break;
            case 'listening':
                object.type = 'audio_hamster_listening';
                break;
            case 'processing':
            case 'transcribing':
                object.type = 'audio_hamster_processing';
                break;
            case 'flowing':
                object.type = 'audio_particle';
                object.direction = 'horizontal';
                object.speed = 2;
                break;
        }
    }
    
    // Animation triggers
    triggerHamsterRun(componentId) {
        const object = this.screenRenderer?.objects.find(obj => obj.id === componentId);
        if (object) {
            object.type = 'hamster_running';
            object.speed = 2;
            object.state = 'running';
        }
    }
    
    triggerScreenshot(componentId) {
        const object = this.screenRenderer?.objects.find(obj => obj.id === componentId);
        if (object) {
            object.type = 'monitor_capturing';
            object.state = 'capturing';
            
            // Flash effect
            setTimeout(() => {
                object.type = 'monitor_detected';
                object.state = 'detected';
            }, 200);
        }
    }
    
    triggerPipeFlow(componentId) {
        const object = this.screenRenderer?.objects.find(obj => obj.id === componentId);
        if (object) {
            object.type = 'pipe_flowing';
            object.state = 'flowing';
            
            // Create data particles
            this.createDataParticles(componentId);
        }
    }
    
    triggerProcessing(componentId) {
        const object = this.screenRenderer?.objects.find(obj => obj.id === componentId);
        if (object) {
            object.type = 'cube_processing';
            object.state = 'processing';
            object.rotation = 0;
        }
    }
    
    createDataParticles(pipeId) {
        const pipeObject = this.screenRenderer.objects.find(obj => obj.id === pipeId);
        if (!pipeObject) return;
        
        // Create multiple particles for visual effect
        for (let i = 0; i < 3; i++) {
            const particle = this.screenRenderer.createObject('data_particle', pipeObject.x, pipeObject.y, {
                direction: 'horizontal',
                speed: 3,
                life: 2000 // 2 seconds
            });
            
            // Remove particle after its lifetime
            setTimeout(() => {
                this.screenRenderer.removeObject(particle.id);
            }, particle.life);
        }
    }
    
    // Layout positioning
    getScreenObjectPositions() {
        return {
            'hamster-1': { x: 50, y: 200 },
            'hamster-2': { x: 50, y: 250 },
            'hamster-3': { x: 50, y: 300 },
            'monitor-1': { x: 200, y: 200 },
            'monitor-2': { x: 200, y: 250 },
            'monitor-3': { x: 200, y: 300 },
            'manhole-1': { x: 180, y: 200 },
            'manhole-2': { x: 180, y: 250 },
            'manhole-3': { x: 180, y: 300 },
            'pipe-to-ocr': { x: 300, y: 250 },
            'pipe-from-ocr': { x: 500, y: 250 },
            'ocr-cube': { x: 400, y: 250 },
            'chroma-screen': { x: 600, y: 250 }
        };
    }
    
    getAudioObjectPositions() {
        return {
            'audio-hamster': { x: 100, y: 200 },
            'audio-pipe-1': { x: 200, y: 200 },
            'audio-pipe-2': { x: 400, y: 200 },
            'audio-cube': { x: 300, y: 200 },
            'chroma-audio': { x: 500, y: 200 }
        };
    }
    
    // Configuration updates
    updateConfiguration(config) {
        if (config.blockSize) {
            this.config.canvasWidth = Math.max(400, config.blockSize * 20);
            this.config.canvasHeight = Math.max(300, config.blockSize * 15);
            
            // Resize canvases
            if (this.screenRenderer) {
                this.screenRenderer.canvas.width = this.config.canvasWidth;
                this.screenRenderer.canvas.height = this.config.canvasHeight;
                this.screenRenderer.canvas.style.width = `${this.config.canvasWidth}px`;
                this.screenRenderer.canvas.style.height = `${this.config.canvasHeight}px`;
                this.screenRenderer.width = this.config.canvasWidth;
                this.screenRenderer.height = this.config.canvasHeight;
            }
            
            if (this.audioRenderer) {
                this.audioRenderer.canvas.width = this.config.canvasWidth;
                this.audioRenderer.canvas.height = this.config.canvasHeight;
                this.audioRenderer.canvas.style.width = `${this.config.canvasWidth}px`;
                this.audioRenderer.canvas.style.height = `${this.config.canvasHeight}px`;
                this.audioRenderer.width = this.config.canvasWidth;
                this.audioRenderer.height = this.config.canvasHeight;
            }
        }
        
        if (config.reducedMotion) {
            this.stop();
        } else {
            this.start();
        }
    }
    
    // Control methods
    start() {
        if (this.screenRenderer) {
            this.screenRenderer.start();
        }
        if (this.audioRenderer) {
            this.audioRenderer.start();
        }
    }
    
    stop() {
        if (this.screenRenderer) {
            this.screenRenderer.stop();
        }
        if (this.audioRenderer) {
            this.audioRenderer.stop();
        }
    }
    
    reset() {
        if (this.screenRenderer) {
            this.screenRenderer.objects = [];
        }
        if (this.audioRenderer) {
            this.audioRenderer.objects = [];
        }
    }
    
    // Debug methods
    getStats() {
        return {
            screenObjects: this.screenRenderer?.objects.length || 0,
            audioObjects: this.audioRenderer?.objects.length || 0,
            screenFPS: this.screenRenderer?.currentFps || 0,
            audioFPS: this.audioRenderer?.currentFps || 0
        };
    }
    
    // Cleanup
    destroy() {
        if (this.screenRenderer) {
            this.screenRenderer.destroy();
        }
        if (this.audioRenderer) {
            this.audioRenderer.destroy();
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { CanvasManager };
} else {
    window.CanvasManager = CanvasManager;
}


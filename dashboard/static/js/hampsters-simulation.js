/**
 * Simulation Engine for Hamster Visualization
 * Handles event scheduling, component management, and scenario playback
 */

class SimulationEngine {
    constructor() {
        this.components = new Map();
        this.eventQueue = [];
        this.isRunning = false;
        this.simulationSpeed = 1.0;
        this.eventHandlers = new Map();
        this.currentScenario = null;
        this.frameId = null;
        this.lastFrameTime = 0;
        this.performanceStats = {
            fps: 0,
            frameCount: 0,
            lastFpsUpdate: 0,
            activeAnimations: 0
        };
        
        // Bind methods to preserve 'this' context
        this.step = this.step.bind(this);
        this.start = this.start.bind(this);
        this.stop = this.stop.bind(this);
    }
    
    // Register a component with its state machine
    registerComponent(id, stateMachine, visualElement) {
        const component = {
            id,
            stateMachine,
            visualElement,
            lastUpdate: Date.now(),
            isAnimating: false
        };
        
        this.components.set(id, component);
        
        // Listen to state changes for visual updates
        stateMachine.onStateChange((stateChange) => {
            this.handleStateChange(id, stateChange);
        });
        
        this.emit('componentRegistered', { id, component });
        return component;
    }
    
    // Schedule an event to occur after a delay
    scheduleEvent(delay, componentId, action, data = {}) {
        const event = {
            timestamp: Date.now() + (delay / this.simulationSpeed),
            componentId,
            action,
            data,
            id: Math.random().toString(36).substr(2, 9)
        };
        
        this.eventQueue.push(event);
        this.eventQueue.sort((a, b) => a.timestamp - b.timestamp);
        
        this.emit('eventScheduled', event);
        return event.id;
    }
    
    // Cancel a scheduled event
    cancelEvent(eventId) {
        const index = this.eventQueue.findIndex(event => event.id === eventId);
        if (index > -1) {
            const event = this.eventQueue.splice(index, 1)[0];
            this.emit('eventCancelled', event);
            return true;
        }
        return false;
    }
    
    // Process events and update components
    step(currentTime = Date.now()) {
        // Calculate FPS
        this.updatePerformanceStats(currentTime);
        
        // Process due events
        while (this.eventQueue.length > 0 && this.eventQueue[0].timestamp <= currentTime) {
            const event = this.eventQueue.shift();
            this.processEvent(event);
        }
        
        // Update component animations
        this.updateAnimations(currentTime);
        
        // Continue simulation if running
        if (this.isRunning) {
            this.frameId = requestAnimationFrame(this.step);
        }
    }
    
    processEvent(event) {
        const component = this.components.get(event.componentId);
        if (!component) {
            console.warn(`Component not found: ${event.componentId}`);
            return;
        }
        
        try {
            // Check if transition is valid
            if (!component.stateMachine.canTransition(event.action)) {
                console.warn(`Invalid transition for ${event.componentId}: ${component.stateMachine.getState()} -> ${event.action}`);
                return;
            }
            
            // Attempt state transition
            const newState = component.stateMachine.transition(event.action, event.data);
            
            // Update component timestamp
            component.lastUpdate = Date.now();
            
            // Emit event for listeners
            this.emit('eventProcessed', {
                componentId: event.componentId,
                action: event.action,
                newState,
                data: event.data
            });
            
        } catch (error) {
            console.error(`State transition error for ${event.componentId}:`, error);
            this.emit('error', { componentId: event.componentId, error, event });
        }
    }
    
    handleStateChange(componentId, stateChange) {
        const component = this.components.get(componentId);
        if (!component) return;
        
        // Update visual representation
        this.updateVisual(componentId, stateChange.newState, stateChange.data);
        
        // Trigger dependent events based on state change
        this.triggerDependentEvents(componentId, stateChange);
        
        // Emit state change event
        this.emit('stateChange', {
            componentId,
            ...stateChange
        });
    }
    
    updateVisual(componentId, newState, data) {
        const component = this.components.get(componentId);
        if (!component || !component.visualElement) return;
        
        const element = component.visualElement;
        const componentType = componentId.split('_')[0];
        
        // Remove all state classes
        element.className = element.className.replace(/\b(idle|waiting|running|entering_manhole|in_monitor|exiting_manhole|returning|delivering|detected|capturing|captured|receiving|processing|complete|sending|flowing|empty|blocked|sleeping|listening|transcribing|storing|error)\b/g, '');
        
        // Add new state class
        element.classList.add(newState);
        
        // Handle specific visual updates based on component type
        switch (componentType) {
            case 'hamster':
                this.updateHamsterVisual(element, newState, data);
                break;
            case 'audio-hamster':
                this.updateAudioHamsterVisual(element, newState, data);
                break;
            case 'monitor':
                this.updateMonitorVisual(element, newState, data);
                break;
            case 'pipe':
                this.updatePipeVisual(element, newState, data);
                break;
            case 'ocr-cube':
            case 'audio-cube':
                this.updateCubeVisual(element, newState, data);
                break;
            case 'chroma':
                this.updateChromaVisual(element, newState, data);
                break;
        }
        
        // Track animation state
        component.isAnimating = this.isStateAnimated(newState);
        this.updateAnimationCount();
    }
    
    updateHamsterVisual(element, state, data) {
        switch (state) {
            case 'running':
                // Trigger running animation
                element.style.animationDuration = `${AnimationTiming.hamster_run_duration}ms`;
                break;
            case 'entering_manhole':
                // Trigger manhole entry animation
                setTimeout(() => {
                    if (element.classList.contains('entering_manhole')) {
                        // Auto-transition to in_monitor after animation
                        const componentId = element.closest('.hamster').id;
                        this.scheduleEvent(AnimationTiming.manhole_animation, componentId, 'ENTER_COMPLETE');
                    }
                }, AnimationTiming.manhole_animation);
                break;
            case 'in_monitor':
                // Hide hamster, show in monitor
                const monitorId = data.monitorId || 'monitor-1';
                this.showHamsterInMonitor(monitorId);
                break;
            case 'exiting_manhole':
                // Show hamster exiting
                setTimeout(() => {
                    if (element.classList.contains('exiting_manhole')) {
                        const componentId = element.closest('.hamster').id;
                        this.scheduleEvent(100, componentId, 'EXIT_COMPLETE');
                    }
                }, AnimationTiming.manhole_animation);
                break;
        }
    }
    
    updateAudioHamsterVisual(element, state, data) {
        const headphones = element.querySelector('.headphones');
        
        switch (state) {
            case 'listening':
                if (headphones) {
                    headphones.classList.add('active');
                }
                break;
            case 'sleeping':
                if (headphones) {
                    headphones.classList.remove('active');
                }
                break;
        }
    }
    
    updateMonitorVisual(element, state, data) {
        switch (state) {
            case 'capturing':
                // Trigger flash effect
                setTimeout(() => {
                    if (element.classList.contains('capturing')) {
                        const componentId = element.closest('.monitor-container').id;
                        this.scheduleEvent(0, componentId, 'SCREENSHOT_COMPLETE');
                    }
                }, AnimationTiming.screenshot_flash);
                break;
        }
    }
    
    updatePipeVisual(element, state, data) {
        const dataFlow = element.querySelector('.data-flow, .audio-flow');
        
        switch (state) {
            case 'flowing':
                if (dataFlow) {
                    dataFlow.style.animationDuration = `${AnimationTiming.pipe_flow_speed}ms`;
                }
                // Auto-stop flow after animation
                setTimeout(() => {
                    if (element.classList.contains('flowing')) {
                        const componentId = element.id;
                        this.scheduleEvent(0, componentId, 'STOP_FLOW');
                    }
                }, AnimationTiming.pipe_flow_speed);
                break;
        }
    }
    
    updateCubeVisual(element, state, data) {
        switch (state) {
            case 'processing':
                // Auto-complete processing after timeout
                setTimeout(() => {
                    if (element.classList.contains('processing')) {
                        const componentId = element.id;
                        this.scheduleEvent(0, componentId, 'PROCESSING_COMPLETE');
                    }
                }, AnimationTiming.ocr_processing);
                break;
        }
    }
    
    updateChromaVisual(element, state, data) {
        switch (state) {
            case 'receiving':
                this.addDataRecord(element, data);
                // Auto-complete storage
                setTimeout(() => {
                    if (element.classList.contains('receiving')) {
                        const componentId = element.id;
                        this.scheduleEvent(0, componentId, 'STORAGE_COMPLETE');
                    }
                }, AnimationTiming.chroma_slide_duration);
                break;
        }
    }
    
    addDataRecord(chromaElement, data) {
        const slots = chromaElement.querySelector('.storage-slots');
        const emptySlot = slots.querySelector('.empty-slot');
        
        if (emptySlot) {
            const record = document.createElement('div');
            record.className = `data-record ${data.type || 'screen-data'} sliding-in`;
            record.textContent = data.content || 'New Data Record';
            
            slots.insertBefore(record, emptySlot);
            
            // Remove animation class after animation completes
            setTimeout(() => {
                record.classList.remove('sliding-in');
            }, AnimationTiming.chroma_slide_duration);
        }
    }
    
    showHamsterInMonitor(monitorId) {
        const monitor = document.getElementById(monitorId);
        if (!monitor) return;
        
        const screen = monitor.querySelector('.screen');
        if (!screen) return;
        
        // Create tiny hamster in monitor
        const tinyHamster = document.createElement('div');
        tinyHamster.className = 'tiny-hamster';
        tinyHamster.innerHTML = '🐹📷';
        tinyHamster.style.cssText = `
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 12px;
            z-index: 10;
        `;
        
        screen.appendChild(tinyHamster);
        
        // Flash effect for screenshot
        setTimeout(() => {
            screen.style.background = 'white';
            setTimeout(() => {
                screen.style.background = '';
                tinyHamster.remove();
            }, AnimationTiming.screenshot_flash);
        }, 500);
    }
    
    triggerDependentEvents(componentId, stateChange) {
        const { newState, action, data } = stateChange;
        const componentType = componentId.split('_')[0];
        
        // Define dependent event chains
        switch (componentType) {
            case 'hamster':
                if (newState === 'delivering') {
                    // Start pipe flow when hamster delivers data
                    this.scheduleEvent(200, 'pipe-to-ocr', 'START_FLOW');
                    this.scheduleEvent(500, 'ocr-cube', 'DATA_RECEIVED');
                }
                break;
                
            case 'ocr-cube':
                if (newState === 'sending') {
                    // Send data to ChromaDB
                    this.scheduleEvent(200, 'pipe-from-ocr', 'START_FLOW');
                    this.scheduleEvent(800, 'chroma-screen', 'RECEIVE_DATA', {
                        type: 'screen-data',
                        content: `OCR Result ${Date.now()}`
                    });
                }
                break;
                
            case 'audio-cube':
                if (newState === 'sending') {
                    // Send audio data to ChromaDB
                    this.scheduleEvent(200, 'audio-pipe-2', 'START_FLOW');
                    this.scheduleEvent(800, 'chroma-audio', 'RECEIVE_DATA', {
                        type: 'audio-data',
                        content: `Transcript ${Date.now()}`
                    });
                }
                break;
        }
    }
    
    updateAnimations(currentTime) {
        // Update any time-based animations here
        this.lastFrameTime = currentTime;
    }
    
    updatePerformanceStats(currentTime) {
        this.performanceStats.frameCount++;
        
        if (currentTime - this.performanceStats.lastFpsUpdate >= 1000) {
            this.performanceStats.fps = this.performanceStats.frameCount;
            this.performanceStats.frameCount = 0;
            this.performanceStats.lastFpsUpdate = currentTime;
            
            // Update FPS display
            const fpsCounter = document.getElementById('fps-counter');
            if (fpsCounter) {
                fpsCounter.textContent = this.performanceStats.fps;
            }
        }
    }
    
    updateAnimationCount() {
        let count = 0;
        this.components.forEach(component => {
            if (component.isAnimating) count++;
        });
        
        this.performanceStats.activeAnimations = count;
        
        const animationCounter = document.getElementById('animation-counter');
        if (animationCounter) {
            animationCounter.textContent = count;
        }
    }
    
    isStateAnimated(state) {
        const animatedStates = [
            'running', 'entering_manhole', 'exiting_manhole', 'returning',
            'processing', 'flowing', 'capturing', 'receiving', 'storing'
        ];
        return animatedStates.includes(state);
    }
    
    // Start simulation
    start() {
        if (this.isRunning) return;
        
        this.isRunning = true;
        this.frameId = requestAnimationFrame(this.step);
        this.emit('simulationStarted');
    }
    
    // Stop simulation
    stop() {
        if (!this.isRunning) return;
        
        this.isRunning = false;
        if (this.frameId) {
            cancelAnimationFrame(this.frameId);
            this.frameId = null;
        }
        this.emit('simulationStopped');
    }
    
    // Reset all components to initial state
    reset() {
        this.stop();
        this.eventQueue = [];
        
        this.components.forEach(component => {
            component.stateMachine.reset();
        });
        
        this.emit('simulationReset');
    }
    
    // Load and run a scenario
    loadScenario(scenario) {
        this.reset();
        this.currentScenario = scenario;
        
        // Schedule all scenario events
        scenario.events.forEach(event => {
            this.scheduleEvent(event.delay, event.component, event.action, event.data || {});
        });
        
        this.emit('scenarioLoaded', scenario);
    }
    
    // Set simulation speed
    setSpeed(speed) {
        this.simulationSpeed = Math.max(0.1, Math.min(3.0, speed));
        this.emit('speedChanged', this.simulationSpeed);
    }
    
    // Event emitter pattern
    on(eventType, handler) {
        if (!this.eventHandlers.has(eventType)) {
            this.eventHandlers.set(eventType, []);
        }
        this.eventHandlers.get(eventType).push(handler);
        
        // Return unsubscribe function
        return () => {
            const handlers = this.eventHandlers.get(eventType);
            if (handlers) {
                const index = handlers.indexOf(handler);
                if (index > -1) {
                    handlers.splice(index, 1);
                }
            }
        };
    }
    
    emit(eventType, data) {
        const handlers = this.eventHandlers.get(eventType) || [];
        handlers.forEach(handler => {
            try {
                handler(data);
            } catch (error) {
                console.error(`Event handler error for ${eventType}:`, error);
            }
        });
    }
    
    // Get current system state for debugging
    getSystemState() {
        const state = {};
        this.components.forEach((component, id) => {
            state[id] = {
                currentState: component.stateMachine.getState(),
                possibleStates: component.stateMachine.getPossibleStates(),
                lastUpdate: component.lastUpdate,
                isAnimating: component.isAnimating
            };
        });
        return state;
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { SimulationEngine };
} else {
    window.SimulationEngine = SimulationEngine;
}


/**
 * Configuration Dashboard for Hamster Visualization
 * Handles real-time layout updates and state machine configuration
 */

class ConfigurationManager {
    constructor(simulationEngine, visualizationManager) {
        this.engine = simulationEngine;
        this.visualizationManager = visualizationManager;
        this.config = this.getDefaultConfig();
        this.isConfigOpen = false;
        
        this.setupEventListeners();
        this.loadConfigFromStorage();
        this.updateDisplayValues();
    }
    
    getDefaultConfig() {
        return {
            // Screen Configuration
            screenCount: 1,
            layoutTemplate: 'single',
            
            // State Machine Settings
            processingTime: 3000,
            pipeFlowSpeed: 1500,
            
            // Audio Configuration
            audioMode: 'balanced',
            audioSensitivity: 0.01,
            
            // Visual Settings
            blockSize: 32,
            animationQuality: 'high',
            showGrid: true,
            reducedMotion: false
        };
    }
    
    setupEventListeners() {
        // Configuration dashboard toggle
        const configDashboard = document.getElementById('config-dashboard');
        const toggleConfigBtn = document.getElementById('toggle-config');
        
        if (toggleConfigBtn) {
            toggleConfigBtn.addEventListener('click', () => {
                configDashboard.classList.toggle('collapsed');
                this.isConfigOpen = !configDashboard.classList.contains('collapsed');
            });
        }
        
        // Screen configuration
        this.setupRangeControl('screen-count', 'screenCount', (value) => {
            this.updateScreenCount(parseInt(value));
        });
        
        this.setupSelectControl('layout-template', 'layoutTemplate', (value) => {
            this.updateLayoutTemplate(value);
        });
        
        // State machine settings
        
        this.setupRangeControl('processing-time', 'processingTime', (value) => {
            this.updateProcessingTime(parseInt(value));
        });
        
        this.setupRangeControl('pipe-flow-speed', 'pipeFlowSpeed', (value) => {
            this.updatePipeFlowSpeed(parseInt(value));
        });
        
        // Audio configuration
        this.setupSelectControl('audio-mode', 'audioMode', (value) => {
            this.updateAudioMode(value);
        });
        
        this.setupRangeControl('audio-sensitivity', 'audioSensitivity', (value) => {
            this.updateAudioSensitivity(parseFloat(value));
        });
        
        // Visual settings
        this.setupRangeControl('block-size', 'blockSize', (value) => {
            this.updateBlockSize(parseInt(value));
        });
        
        this.setupSelectControl('animation-quality', 'animationQuality', (value) => {
            this.updateAnimationQuality(value);
        });
        
        this.setupCheckboxControl('show-grid', 'showGrid', (value) => {
            this.updateShowGrid(value);
        });
        
        this.setupCheckboxControl('reduced-motion', 'reducedMotion', (value) => {
            this.updateReducedMotion(value);
        });
        
        // Action buttons
        this.setupActionButtons();
    }
    
    setupRangeControl(elementId, configKey, onChange) {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        element.addEventListener('input', (e) => {
            const value = e.target.value;
            this.config[configKey] = value;
            this.updateDisplayValue(elementId, value);
            onChange(value);
        });
    }
    
    setupSelectControl(elementId, configKey, onChange) {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        element.addEventListener('change', (e) => {
            const value = e.target.value;
            this.config[configKey] = value;
            onChange(value);
        });
    }
    
    setupCheckboxControl(elementId, configKey, onChange) {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        element.addEventListener('change', (e) => {
            const value = e.target.checked;
            this.config[configKey] = value;
            onChange(value);
        });
    }
    
    setupActionButtons() {
        const applyBtn = document.getElementById('apply-config');
        const resetBtn = document.getElementById('reset-config');
        const exportBtn = document.getElementById('export-config');
        const importBtn = document.getElementById('import-config');
        
        if (applyBtn) {
            applyBtn.addEventListener('click', () => {
                this.applyConfiguration();
            });
        }
        
        if (resetBtn) {
            resetBtn.addEventListener('click', () => {
                this.resetToDefaults();
            });
        }
        
        if (exportBtn) {
            exportBtn.addEventListener('click', () => {
                this.exportConfiguration();
            });
        }
        
        if (importBtn) {
            importBtn.addEventListener('click', () => {
                this.importConfiguration();
            });
        }
    }
    
    updateDisplayValue(elementId, value) {
        const displayElement = document.getElementById(`${elementId}-display`);
        if (!displayElement) return;
        
        switch (elementId) {
            case 'screen-count':
                displayElement.textContent = value;
                break;
            case 'processing-time':
                displayElement.textContent = `${(parseInt(value) / 1000).toFixed(1)}s`;
                break;
            case 'pipe-flow-speed':
                displayElement.textContent = `${(parseInt(value) / 1000).toFixed(1)}s`;
                break;
            case 'audio-sensitivity':
                displayElement.textContent = parseFloat(value).toFixed(3);
                break;
            case 'block-size':
                displayElement.textContent = `${value}px`;
                break;
        }
    }
    
    updateDisplayValues() {
        Object.keys(this.config).forEach(key => {
            const element = document.getElementById(this.getControlId(key));
            if (element) {
                element.value = this.config[key];
                this.updateDisplayValue(this.getControlId(key), this.config[key]);
            }
        });
    }
    
    getControlId(configKey) {
        const mapping = {
            'screenCount': 'screen-count',
            'layoutTemplate': 'layout-template',
            'processingTime': 'processing-time',
            'pipeFlowSpeed': 'pipe-flow-speed',
            'audioMode': 'audio-mode',
            'audioSensitivity': 'audio-sensitivity',
            'blockSize': 'block-size',
            'animationQuality': 'animation-quality',
            'showGrid': 'show-grid',
            'reducedMotion': 'reduced-motion'
        };
        return mapping[configKey] || configKey;
    }
    
    // Configuration update methods
    updateScreenCount(count) {
        this.config.screenCount = count;
        this.updateLayoutTemplate(this.config.layoutTemplate);
        this.visualizationManager?.logEvent(`Screen count updated to ${count}`, 'info');
    }
    
    updateLayoutTemplate(template) {
        this.config.layoutTemplate = template;
        this.applyLayoutTemplate(template);
        this.visualizationManager?.logEvent(`Layout template changed to ${template}`, 'info');
    }
    
    
    updateProcessingTime(time) {
        this.config.processingTime = time;
        // Update OCR processing time
        if (window.HamsterStateMachine) {
            window.HamsterStateMachine.AnimationTiming.ocr_processing = time;
        }
        this.visualizationManager?.logEvent(`Processing time updated to ${time}ms`, 'info');
    }
    
    updatePipeFlowSpeed(speed) {
        this.config.pipeFlowSpeed = speed;
        // Update pipe flow speed
        if (window.HamsterStateMachine) {
            window.HamsterStateMachine.AnimationTiming.pipe_flow_speed = speed;
        }
        this.visualizationManager?.logEvent(`Pipe flow speed updated to ${speed}ms`, 'info');
    }
    
    updateAudioMode(mode) {
        this.config.audioMode = mode;
        // Update audio processing configuration
        const modeConfigs = {
            'realtime': { chunkDuration: 5, processingDelay: 0 },
            'balanced': { chunkDuration: 15, processingDelay: 5 },
            'accurate': { chunkDuration: 30, processingDelay: 10 },
            'batch': { chunkDuration: 60, processingDelay: 30 }
        };
        
        const config = modeConfigs[mode];
        if (config) {
            // Update audio processing settings
            this.visualizationManager?.logEvent(`Audio mode updated to ${mode}`, 'info');
        }
    }
    
    updateAudioSensitivity(sensitivity) {
        this.config.audioSensitivity = sensitivity;
        this.visualizationManager?.logEvent(`Audio sensitivity updated to ${sensitivity}`, 'info');
    }
    
    updateBlockSize(size) {
        this.config.blockSize = size;
        this.applyBlockSize(size);
        this.visualizationManager?.logEvent(`Block size updated to ${size}px`, 'info');
    }
    
    updateAnimationQuality(quality) {
        this.config.animationQuality = quality;
        this.applyAnimationQuality(quality);
        this.visualizationManager?.logEvent(`Animation quality updated to ${quality}`, 'info');
    }
    
    updateShowGrid(show) {
        this.config.showGrid = show;
        this.applyShowGrid(show);
    }
    
    updateReducedMotion(reduced) {
        this.config.reducedMotion = reduced;
        this.applyReducedMotion(reduced);
    }
    
    // Layout template application
    applyLayoutTemplate(template) {
        const visualizationArea = document.querySelector('.visualization-area');
        if (!visualizationArea) return;
        
        // Remove existing layout classes
        visualizationArea.classList.remove('layout-single', 'layout-dual', 'layout-triple', 'layout-custom');
        
        // Apply new layout class
        visualizationArea.classList.add(`layout-${template}`);
        
        // Update monitor visibility based on screen count
        this.updateMonitorVisibility();
    }
    
    updateMonitorVisibility() {
        const count = this.config.screenCount;
        
        for (let i = 1; i <= 3; i++) {
            const monitor = document.getElementById(`monitor-${i}`);
            const hamster = document.getElementById(`hamster-${i}`);
            
            if (monitor && hamster) {
                if (i <= count) {
                    monitor.style.display = 'flex';
                    hamster.style.display = 'block';
                } else {
                    monitor.style.display = 'none';
                    hamster.style.display = 'none';
                }
            }
        }
    }
    
    applyBlockSize(size) {
        document.documentElement.style.setProperty('--block-size', `${size}px`);
        
        // Update grid if visible
        if (this.config.showGrid) {
            this.applyShowGrid(true);
        }
    }
    
    applyAnimationQuality(quality) {
        const body = document.body;
        body.classList.remove('animation-high', 'animation-medium', 'animation-low', 'animation-minimal');
        body.classList.add(`animation-${quality}`);
        
        // Update animation frame rates
        const frameRates = {
            'high': 60,
            'medium': 30,
            'low': 15,
            'minimal': 0
        };
        
        const targetFPS = frameRates[quality] || 60;
        this.engine?.setTargetFPS(targetFPS);
    }
    
    applyShowGrid(show) {
        const visualizationArea = document.querySelector('.visualization-area');
        if (!visualizationArea) return;
        
        if (show) {
            const blockSize = this.config.blockSize;
            visualizationArea.style.backgroundImage = `
                linear-gradient(to right, rgba(211, 211, 211, 0.3) 1px, transparent 1px),
                linear-gradient(to bottom, rgba(211, 211, 211, 0.3) 1px, transparent 1px)
            `;
            visualizationArea.style.backgroundSize = `${blockSize}px ${blockSize}px`;
        } else {
            visualizationArea.style.backgroundImage = 'none';
        }
    }
    
    applyReducedMotion(reduced) {
        const body = document.body;
        if (reduced) {
            body.classList.add('reduced-motion');
        } else {
            body.classList.remove('reduced-motion');
        }
    }
    
    applyConfiguration() {
        // Save configuration to localStorage
        this.saveConfigToStorage();
        
        // Apply all current settings
        this.updateLayoutTemplate(this.config.layoutTemplate);
        this.updateProcessingTime(this.config.processingTime);
        this.updatePipeFlowSpeed(this.config.pipeFlowSpeed);
        this.updateAudioMode(this.config.audioMode);
        this.updateAudioSensitivity(this.config.audioSensitivity);
        this.updateBlockSize(this.config.blockSize);
        this.updateAnimationQuality(this.config.animationQuality);
        this.updateShowGrid(this.config.showGrid);
        this.updateReducedMotion(this.config.reducedMotion);
        
        this.visualizationManager?.logEvent('Configuration applied successfully', 'info');
        
        // Show success message
        this.showNotification('Configuration applied successfully!', 'success');
    }
    
    resetToDefaults() {
        if (confirm('Are you sure you want to reset all settings to defaults?')) {
            this.config = this.getDefaultConfig();
            this.updateDisplayValues();
            this.applyConfiguration();
            this.visualizationManager?.logEvent('Configuration reset to defaults', 'info');
        }
    }
    
    exportConfiguration() {
        const configJson = JSON.stringify(this.config, null, 2);
        const blob = new Blob([configJson], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = 'hamster-config.json';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        this.visualizationManager?.logEvent('Configuration exported', 'info');
    }
    
    importConfiguration() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.json';
        
        input.onchange = (e) => {
            const file = e.target.files[0];
            if (!file) return;
            
            const reader = new FileReader();
            reader.onload = (e) => {
                try {
                    const importedConfig = JSON.parse(e.target.result);
                    
                    // Validate configuration
                    if (this.validateConfig(importedConfig)) {
                        this.config = { ...this.getDefaultConfig(), ...importedConfig };
                        this.updateDisplayValues();
                        this.applyConfiguration();
                        this.visualizationManager?.logEvent('Configuration imported successfully', 'info');
                        this.showNotification('Configuration imported successfully!', 'success');
                    } else {
                        this.showNotification('Invalid configuration file', 'error');
                    }
                } catch (error) {
                    this.showNotification('Error importing configuration', 'error');
                    console.error('Import error:', error);
                }
            };
            reader.readAsText(file);
        };
        
        input.click();
    }
    
    validateConfig(config) {
        const requiredKeys = Object.keys(this.getDefaultConfig());
        return requiredKeys.every(key => config.hasOwnProperty(key));
    }
    
    saveConfigToStorage() {
        try {
            localStorage.setItem('hamster-config', JSON.stringify(this.config));
        } catch (error) {
            console.warn('Could not save configuration to localStorage:', error);
        }
    }
    
    loadConfigFromStorage() {
        try {
            const saved = localStorage.getItem('hamster-config');
            if (saved) {
                const savedConfig = JSON.parse(saved);
                this.config = { ...this.getDefaultConfig(), ...savedConfig };
                this.updateDisplayValues();
            }
        } catch (error) {
            console.warn('Could not load configuration from localStorage:', error);
        }
    }
    
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        // Style the notification
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 4px;
            color: white;
            font-weight: 500;
            z-index: 10000;
            opacity: 0;
            transform: translateX(100%);
            transition: all 0.3s ease;
        `;
        
        // Set background color based on type
        const colors = {
            'success': '#28a745',
            'error': '#dc3545',
            'warning': '#ffc107',
            'info': '#17a2b8'
        };
        notification.style.backgroundColor = colors[type] || colors.info;
        
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.style.opacity = '1';
            notification.style.transform = 'translateX(0)';
        }, 10);
        
        // Remove after 3 seconds
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 3000);
    }
    
    getCurrentConfig() {
        return { ...this.config };
    }
    
    updateConfig(newConfig) {
        this.config = { ...this.config, ...newConfig };
        this.updateDisplayValues();
        this.applyConfiguration();
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ConfigurationManager };
} else {
    window.ConfigurationManager = ConfigurationManager;
}

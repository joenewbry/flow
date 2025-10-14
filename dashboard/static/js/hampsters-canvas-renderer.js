/**
 * Canvas Renderer for Hamster Visualizations
 * Handles 8 FPS sprite-based rendering for Screen Recording and Audio Recording sections
 */

class CanvasRenderer {
    constructor(canvasElement, width = 800, height = 400) {
        this.canvas = canvasElement;
        this.ctx = canvasElement.getContext('2d');
        this.width = width;
        this.height = height;
        
        // Set canvas dimensions
        this.canvas.width = width;
        this.canvas.height = height;
        this.canvas.style.width = `${width}px`;
        this.canvas.style.height = `${height}px`;
        
        // Animation settings
        this.fps = 8;
        this.frameInterval = 1000 / this.fps;
        this.lastFrameTime = 0;
        this.animationId = null;
        this.isRunning = false;
        
        // Sprite management
        this.sprites = new Map();
        this.loadedSprites = 0;
        this.totalSprites = 0;
        
        // Scene objects
        this.objects = [];
        this.camera = { x: 0, y: 0, zoom: 1 };
        
        // Performance tracking
        this.frameCount = 0;
        this.lastFpsUpdate = 0;
        this.currentFps = 0;
        
        this.init();
    }
    
    init() {
        // Set up pixel-perfect rendering
        this.ctx.imageSmoothingEnabled = false;
        this.ctx.mozImageSmoothingEnabled = false;
        this.ctx.webkitImageSmoothingEnabled = false;
        this.ctx.msImageSmoothingEnabled = false;
        
        // Load default sprites
        this.loadSprites();
    }
    
    async loadSprites() {
        const spriteDefinitions = {
            'hamster_idle': { frames: 4, width: 24, height: 16 },
            'hamster_running': { frames: 6, width: 28, height: 18 },
            'hamster_entering': { frames: 4, width: 24, height: 16 },
            'hamster_exiting': { frames: 4, width: 24, height: 16 },
            'monitor_idle': { frames: 1, width: 48, height: 36 },
            'monitor_detected': { frames: 1, width: 48, height: 36 },
            'monitor_capturing': { frames: 3, width: 48, height: 36 },
            'manhole_closed': { frames: 1, width: 24, height: 24 },
            'manhole_opening': { frames: 4, width: 24, height: 24 },
            'pipe_empty': { frames: 1, width: 32, height: 12 },
            'pipe_flowing': { frames: 4, width: 32, height: 16 },
            'pipe_vertical': { frames: 1, width: 12, height: 32 },
            'pipe_vertical_flowing': { frames: 4, width: 12, height: 32 },
            'cube_idle': { frames: 1, width: 32, height: 32 },
            'cube_processing': { frames: 8, width: 32, height: 32 },
            'data_particle': { frames: 4, width: 8, height: 8 },
            'audio_particle': { frames: 4, width: 8, height: 8 },
            'audio_hamster_sleeping': { frames: 4, width: 24, height: 20 },
            'audio_hamster_listening': { frames: 4, width: 24, height: 20 },
            'audio_hamster_processing': { frames: 6, width: 24, height: 20 }
        };
        
        this.totalSprites = Object.keys(spriteDefinitions).length;
        
        // Create placeholder sprites (in production, these would be loaded from actual image files)
        for (const [name, def] of Object.entries(spriteDefinitions)) {
            this.createPlaceholderSprite(name, def);
        }
        
        console.log(`🎨 Canvas renderer initialized with ${this.totalSprites} sprites`);
    }
    
    createPlaceholderSprite(name, definition) {
        const { frames, width, height } = definition;
        const sprite = {
            name,
            frames,
            width,
            height,
            frameWidth: width,
            frameHeight: height,
            image: null,
            loaded: false
        };
        
        // Create a placeholder image with the sprite name
        const canvas = document.createElement('canvas');
        canvas.width = width * frames;
        canvas.height = height;
        const ctx = canvas.getContext('2d');
        
        // Draw placeholder for each frame
        for (let i = 0; i < frames; i++) {
            const x = i * width;
            
            // Different colors for different sprite types
            let color = '#8B4513'; // Default hamster brown
            if (name.includes('monitor')) color = '#1a1a2e';
            else if (name.includes('pipe')) color = '#708090';
            else if (name.includes('cube')) color = '#32CD32';
            else if (name.includes('data')) color = '#4169E1';
            else if (name.includes('audio')) color = '#8A2BE2';
            else if (name.includes('manhole')) color = '#696969';
            
            // Draw placeholder rectangle
            ctx.fillStyle = color;
            ctx.fillRect(x, 0, width, height);
            
            // Add frame number
            ctx.fillStyle = 'white';
            ctx.font = '8px monospace';
            ctx.fillText(`${name}`, x + 2, 8);
            ctx.fillText(`f${i}`, x + 2, height - 2);
            
            // Add animation indicator for multi-frame sprites
            if (frames > 1) {
                ctx.strokeStyle = 'white';
                ctx.lineWidth = 1;
                ctx.strokeRect(x, 0, width, height);
            }
        }
        
        sprite.image = canvas;
        sprite.loaded = true;
        this.sprites.set(name, sprite);
        this.loadedSprites++;
    }
    
    // Object management
    createObject(type, x, y, properties = {}) {
        const object = {
            id: Math.random().toString(36).substr(2, 9),
            type,
            x,
            y,
            width: 32,
            height: 32,
            currentFrame: 0,
            frameTime: 0,
            animationSpeed: 1,
            visible: true,
            ...properties
        };
        
        this.objects.push(object);
        return object;
    }
    
    removeObject(id) {
        this.objects = this.objects.filter(obj => obj.id !== id);
    }
    
    updateObject(id, properties) {
        const object = this.objects.find(obj => obj.id === id);
        if (object) {
            Object.assign(object, properties);
        }
    }
    
    // Animation system
    start() {
        if (this.isRunning) return;
        
        this.isRunning = true;
        this.lastFrameTime = performance.now();
        this.animate();
    }
    
    stop() {
        this.isRunning = false;
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
        }
    }
    
    animate() {
        if (!this.isRunning) return;
        
        const currentTime = performance.now();
        const deltaTime = currentTime - this.lastFrameTime;
        
        // Only update at 8 FPS
        if (deltaTime >= this.frameInterval) {
            this.update(deltaTime);
            this.render();
            
            this.lastFrameTime = currentTime;
            this.frameCount++;
            
            // Update FPS counter every second
            if (currentTime - this.lastFpsUpdate >= 1000) {
                this.currentFps = this.frameCount;
                this.frameCount = 0;
                this.lastFpsUpdate = currentTime;
            }
        }
        
        this.animationId = requestAnimationFrame(() => this.animate());
    }
    
    update(deltaTime) {
        // Update all objects
        this.objects.forEach(object => {
            if (!object.visible) return;
            
            // Update animation frames
            object.frameTime += deltaTime;
            const frameInterval = this.frameInterval * object.animationSpeed;
            
            if (object.frameTime >= frameInterval) {
                object.currentFrame = (object.currentFrame + 1) % this.getFrameCount(object.type);
                object.frameTime = 0;
            }
            
            // Update object-specific logic
            this.updateObjectLogic(object, deltaTime);
        });
    }
    
    updateObjectLogic(object, deltaTime) {
        switch (object.type) {
            case 'hamster':
                // Hamster movement logic
                if (object.state === 'running') {
                    object.x += object.speed || 2;
                }
                break;
                
            case 'data_particle':
                // Particle movement
                if (object.direction === 'horizontal') {
                    object.x += object.speed || 3;
                } else if (object.direction === 'vertical') {
                    object.y += object.speed || 3;
                }
                break;
                
            case 'cube':
                // Processing cube rotation
                if (object.state === 'processing') {
                    object.rotation = (object.rotation || 0) + 0.1;
                }
                break;
        }
    }
    
    render() {
        // Clear canvas
        this.ctx.clearRect(0, 0, this.width, this.height);
        
        // Set up camera transform
        this.ctx.save();
        this.ctx.translate(-this.camera.x, -this.camera.y);
        this.ctx.scale(this.camera.zoom, this.camera.zoom);
        
        // Render all visible objects
        this.objects.forEach(object => {
            if (object.visible) {
                this.renderObject(object);
            }
        });
        
        this.ctx.restore();
        
        // Render UI overlay (FPS counter, etc.)
        this.renderUI();
    }
    
    renderObject(object) {
        const sprite = this.sprites.get(object.type);
        if (!sprite || !sprite.loaded) return;
        
        const frameCount = this.getFrameCount(object.type);
        const frameIndex = Math.floor(object.currentFrame) % frameCount;
        
        this.ctx.save();
        
        // Apply object transformations
        this.ctx.translate(object.x + object.width / 2, object.y + object.height / 2);
        
        if (object.rotation) {
            this.ctx.rotate(object.rotation);
        }
        
        if (object.scale) {
            this.ctx.scale(object.scale, object.scale);
        }
        
        // Draw sprite frame
        const sourceX = frameIndex * sprite.frameWidth;
        const sourceY = 0;
        const destX = -object.width / 2;
        const destY = -object.height / 2;
        
        this.ctx.drawImage(
            sprite.image,
            sourceX, sourceY, sprite.frameWidth, sprite.frameHeight,
            destX, destY, object.width, object.height
        );
        
        this.ctx.restore();
    }
    
    renderUI() {
        // FPS counter
        this.ctx.save();
        this.ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
        this.ctx.fillRect(10, 10, 100, 20);
        this.ctx.fillStyle = 'white';
        this.ctx.font = '12px monospace';
        this.ctx.fillText(`FPS: ${this.currentFps}`, 15, 23);
        this.ctx.fillText(`Objects: ${this.objects.length}`, 15, 38);
        this.ctx.restore();
    }
    
    getFrameCount(type) {
        const sprite = this.sprites.get(type);
        return sprite ? sprite.frames : 1;
    }
    
    // Camera controls
    setCamera(x, y, zoom = 1) {
        this.camera.x = x;
        this.camera.y = y;
        this.camera.zoom = zoom;
    }
    
    // Utility methods
    screenToWorld(screenX, screenY) {
        return {
            x: (screenX + this.camera.x) / this.camera.zoom,
            y: (screenY + this.camera.y) / this.camera.zoom
        };
    }
    
    worldToScreen(worldX, worldY) {
        return {
            x: worldX * this.camera.zoom - this.camera.x,
            y: worldY * this.camera.zoom - this.camera.y
        };
    }
    
    // Cleanup
    destroy() {
        this.stop();
        this.sprites.clear();
        this.objects = [];
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { CanvasRenderer };
} else {
    window.CanvasRenderer = CanvasRenderer;
}


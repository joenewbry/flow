#!/usr/bin/env node

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

console.log('🚀 Starting Screen Tracker Desktop App...');

// Check if .env file exists
const envPath = path.join(__dirname, '.env');
if (!fs.existsSync(envPath)) {
    console.log('⚠️  Warning: .env file not found. Please create one with your ANTHROPIC_API_KEY');
    console.log('Example .env file:');
    console.log('ANTHROPIC_API_KEY=your_api_key_here');
    console.log('CHROMA_HOST=localhost');
    console.log('CHROMA_PORT=8000');
    console.log('');
}

// Check if node_modules exists
const nodeModulesPath = path.join(__dirname, 'node_modules');
if (!fs.existsSync(nodeModulesPath)) {
    console.log('❌ node_modules not found. Please run "npm install" first.');
    process.exit(1);
}

// Check if main files exist
const mainFiles = ['main.js', 'index.html', 'renderer.js'];
for (const file of mainFiles) {
    if (!fs.existsSync(path.join(__dirname, file))) {
        console.log(`❌ ${file} not found. Please ensure all files are present.`);
        process.exit(1);
    }
}

console.log('✅ All files present, starting Electron app...');

// Start the Electron app
const electronProcess = spawn('npx', ['electron', '.'], {
    stdio: 'inherit',
    cwd: __dirname,
    shell: true
});

electronProcess.on('error', (error) => {
    console.error('❌ Error starting Electron app:', error.message);
    process.exit(1);
});

electronProcess.on('exit', (code) => {
    console.log(`📱 Electron app exited with code ${code}`);
    process.exit(code);
});

// Handle process termination
process.on('SIGINT', () => {
    console.log('🛑 Shutting down...');
    electronProcess.kill('SIGINT');
});

process.on('SIGTERM', () => {
    console.log('🛑 Shutting down...');
    electronProcess.kill('SIGTERM');
});
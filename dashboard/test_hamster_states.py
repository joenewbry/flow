#!/usr/bin/env python3
"""
Test script for hamster states WebSocket functionality
Demonstrates how to send hamster state updates to the dashboard
"""

import asyncio
import aiohttp
import json
import random
import time

# Dashboard URL
DASHBOARD_URL = "http://localhost:8082"

# Component IDs from the dashboard
SCREEN_COMPONENTS = [
    'hamster-1', 'hamster-2', 'hamster-3',
    'monitor-1', 'monitor-2', 'monitor-3',
    'pipe-to-ocr', 'pipe-from-ocr',
    'ocr-cube', 'chroma-screen'
]

AUDIO_COMPONENTS = [
    'audio-hamster', 'audio-pipe-1', 'audio-pipe-2',
    'audio-cube', 'chroma-audio'
]

# Possible states
STATES = ['idle', 'active', 'processing', 'flowing', 'error']
ACTIONS = ['START_RUN', 'TAKE_SCREENSHOT', 'START_PROCESSING', 'START_FLOW', 'ERROR_OCCURRED', 'COMPLETED']

async def send_hamster_state_update(session, components_data):
    """Send a hamster state update to the dashboard."""
    url = f"{DASHBOARD_URL}/api/hamster-state-update"
    
    payload = {
        "components": components_data
    }
    
    try:
        async with session.post(url, json=payload) as response:
            if response.status == 200:
                result = await response.json()
                print(f"✅ State update sent: {result['message']}")
            else:
                print(f"❌ Error sending state update: {response.status}")
    except Exception as e:
        print(f"❌ Exception sending state update: {e}")

async def send_hamster_event(session, component_id, action, new_state):
    """Send a hamster event to the dashboard."""
    url = f"{DASHBOARD_URL}/api/hamster-event"
    
    payload = {
        "componentId": component_id,
        "action": action,
        "newState": new_state,
        "timestamp": time.time()
    }
    
    try:
        async with session.post(url, json=payload) as response:
            if response.status == 200:
                result = await response.json()
                print(f"🎯 Event sent: {component_id} - {action} -> {new_state}")
            else:
                print(f"❌ Error sending event: {response.status}")
    except Exception as e:
        print(f"❌ Exception sending event: {e}")

async def simulate_screen_capture_flow(session):
    """Simulate a complete screen capture flow."""
    print("\n🔄 Starting Screen Capture Flow Simulation...")
    
    # Step 1: Hamster starts running
    await send_hamster_event(session, 'hamster-1', 'START_RUN', 'running')
    await asyncio.sleep(1)
    
    # Step 2: Monitor detected
    await send_hamster_event(session, 'monitor-1', 'DETECTED', 'detected')
    await asyncio.sleep(0.5)
    
    # Step 3: Screenshot taken
    await send_hamster_event(session, 'monitor-1', 'TAKE_SCREENSHOT', 'capturing')
    await asyncio.sleep(0.2)
    
    # Step 4: Data flows through pipe
    await send_hamster_event(session, 'pipe-to-ocr', 'START_FLOW', 'flowing')
    await asyncio.sleep(0.5)
    
    # Step 5: OCR processing starts
    await send_hamster_event(session, 'ocr-cube', 'START_PROCESSING', 'processing')
    await asyncio.sleep(2)
    
    # Step 6: Data flows to ChromaDB
    await send_hamster_event(session, 'pipe-from-ocr', 'START_FLOW', 'flowing')
    await asyncio.sleep(0.5)
    
    # Step 7: Data stored in ChromaDB
    await send_hamster_event(session, 'chroma-screen', 'DATA_STORED', 'active')
    await asyncio.sleep(0.5)
    
    # Step 8: Everything returns to idle
    components = {}
    for component in SCREEN_COMPONENTS:
        components[component] = {'status': 'idle'}
    
    await send_hamster_state_update(session, components)
    print("✅ Screen Capture Flow Complete!")

async def simulate_audio_processing_flow(session):
    """Simulate a complete audio processing flow."""
    print("\n🎵 Starting Audio Processing Flow Simulation...")
    
    # Step 1: Audio hamster wakes up
    await send_hamster_event(session, 'audio-hamster', 'START_LISTENING', 'listening')
    await asyncio.sleep(1)
    
    # Step 2: Audio data flows
    await send_hamster_event(session, 'audio-pipe-1', 'START_FLOW', 'flowing')
    await asyncio.sleep(0.5)
    
    # Step 3: Audio processing
    await send_hamster_event(session, 'audio-cube', 'START_PROCESSING', 'processing')
    await send_hamster_event(session, 'audio-hamster', 'START_TRANSCRIBING', 'processing')
    await asyncio.sleep(3)
    
    # Step 4: Audio data flows to ChromaDB
    await send_hamster_event(session, 'audio-pipe-2', 'START_FLOW', 'flowing')
    await asyncio.sleep(0.5)
    
    # Step 5: Audio transcript stored
    await send_hamster_event(session, 'chroma-audio', 'TRANSCRIPT_STORED', 'active')
    await asyncio.sleep(0.5)
    
    # Step 6: Audio hamster goes back to sleep
    components = {}
    for component in AUDIO_COMPONENTS:
        if component == 'audio-hamster':
            components[component] = {'status': 'sleeping'}
        else:
            components[component] = {'status': 'idle'}
    
    await send_hamster_state_update(session, components)
    print("✅ Audio Processing Flow Complete!")

async def simulate_random_activity(session):
    """Simulate random hamster activity."""
    print("\n🎲 Starting Random Activity Simulation...")
    
    for _ in range(10):
        component = random.choice(SCREEN_COMPONENTS + AUDIO_COMPONENTS)
        action = random.choice(ACTIONS)
        new_state = random.choice(STATES)
        
        await send_hamster_event(session, component, action, new_state)
        await asyncio.sleep(random.uniform(0.5, 2.0))

async def main():
    """Main test function."""
    print("🐹 Hamster States Test Script")
    print("=" * 40)
    print(f"Dashboard URL: {DASHBOARD_URL}")
    print("Make sure the dashboard is running on port 8082")
    print("=" * 40)
    
    async with aiohttp.ClientSession() as session:
        try:
            # Test 1: Send initial states
            print("\n📡 Sending initial states...")
            initial_states = {}
            for component in SCREEN_COMPONENTS + AUDIO_COMPONENTS:
                initial_states[component] = {'status': 'idle'}
            
            await send_hamster_state_update(session, initial_states)
            await asyncio.sleep(2)
            
            # Test 2: Simulate screen capture flow
            await simulate_screen_capture_flow(session)
            await asyncio.sleep(2)
            
            # Test 3: Simulate audio processing flow
            await simulate_audio_processing_flow(session)
            await asyncio.sleep(2)
            
            # Test 4: Random activity
            await simulate_random_activity(session)
            
            print("\n🎉 All tests completed!")
            print("Check the dashboard to see the hamster states in action!")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())


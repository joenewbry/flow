/**
 * State Machine Implementation for Hamster Visualization
 * Provides functional state management with closures
 */

// Create a state machine with immutable state transitions
function createStateMachine(initialState, transitions) {
    let currentState = initialState;
    let stateHistory = [initialState];
    let listeners = [];
    
    return {
        // Get current state (read-only copy)
        getState: () => currentState,
        
        // Get possible next states
        getPossibleStates: () => Object.keys(transitions[currentState] || {}),
        
        // Check if transition is valid
        canTransition: (action) => {
            const possibleTransitions = transitions[currentState];
            return possibleTransitions && possibleTransitions.hasOwnProperty(action);
        },
        
        // Transition to new state
        transition: (action, data = {}) => {
            const possibleTransitions = transitions[currentState];
            if (!possibleTransitions || !possibleTransitions[action]) {
                throw new Error(`Invalid transition: ${currentState} -> ${action}`);
            }
            
            const oldState = currentState;
            const newState = possibleTransitions[action];
            
            stateHistory.push(newState);
            currentState = newState;
            
            // Notify listeners
            listeners.forEach(listener => {
                try {
                    listener({ oldState, newState, action, data });
                } catch (error) {
                    console.error('State machine listener error:', error);
                }
            });
            
            return currentState;
        },
        
        // Get state history for debugging
        getHistory: () => [...stateHistory],
        
        // Reset to initial state
        reset: () => {
            const oldState = currentState;
            currentState = initialState;
            stateHistory = [initialState];
            
            // Notify listeners of reset
            listeners.forEach(listener => {
                try {
                    listener({ oldState, newState: initialState, action: 'RESET', data: {} });
                } catch (error) {
                    console.error('State machine listener error:', error);
                }
            });
        },
        
        // Add state change listener
        onStateChange: (listener) => {
            listeners.push(listener);
            return () => {
                const index = listeners.indexOf(listener);
                if (index > -1) {
                    listeners.splice(index, 1);
                }
            };
        }
    };
}

// Hamster State Machine Definition
const HamsterStates = {
    WAITING: 'waiting',
    RUNNING: 'running',
    ENTERING_MANHOLE: 'entering_manhole',
    IN_MONITOR: 'in_monitor',
    EXITING_MANHOLE: 'exiting_manhole',
    RETURNING: 'returning',
    DELIVERING: 'delivering',
    ERROR: 'error'
};

const HamsterTransitions = {
    [HamsterStates.WAITING]: {
        START_RUN: HamsterStates.RUNNING,
        ERROR: HamsterStates.ERROR
    },
    [HamsterStates.RUNNING]: {
        REACH_MONITOR: HamsterStates.ENTERING_MANHOLE,
        RETURN_HOME: HamsterStates.WAITING,
        ERROR: HamsterStates.ERROR
    },
    [HamsterStates.ENTERING_MANHOLE]: {
        ENTER_COMPLETE: HamsterStates.IN_MONITOR,
        ERROR: HamsterStates.ERROR
    },
    [HamsterStates.IN_MONITOR]: {
        SCREENSHOT_TAKEN: HamsterStates.EXITING_MANHOLE,
        ERROR: HamsterStates.ERROR
    },
    [HamsterStates.EXITING_MANHOLE]: {
        EXIT_COMPLETE: HamsterStates.RETURNING,
        ERROR: HamsterStates.ERROR
    },
    [HamsterStates.RETURNING]: {
        DELIVER_DATA: HamsterStates.DELIVERING,
        ERROR: HamsterStates.ERROR
    },
    [HamsterStates.DELIVERING]: {
        DELIVERY_COMPLETE: HamsterStates.WAITING,
        ERROR: HamsterStates.ERROR
    },
    [HamsterStates.ERROR]: {
        RESET: HamsterStates.WAITING
    }
};

// Audio Hamster State Machine
const AudioHamsterStates = {
    SLEEPING: 'sleeping',
    LISTENING: 'listening',
    PROCESSING: 'processing',
    TRANSCRIBING: 'transcribing',
    ERROR: 'error'
};

const AudioHamsterTransitions = {
    [AudioHamsterStates.SLEEPING]: {
        AUDIO_DETECTED: AudioHamsterStates.LISTENING,
        ERROR: AudioHamsterStates.ERROR
    },
    [AudioHamsterStates.LISTENING]: {
        START_PROCESSING: AudioHamsterStates.PROCESSING,
        NO_AUDIO: AudioHamsterStates.SLEEPING,
        ERROR: AudioHamsterStates.ERROR
    },
    [AudioHamsterStates.PROCESSING]: {
        TRANSCRIPTION_START: AudioHamsterStates.TRANSCRIBING,
        PROCESSING_COMPLETE: AudioHamsterStates.LISTENING,
        ERROR: AudioHamsterStates.ERROR
    },
    [AudioHamsterStates.TRANSCRIBING]: {
        TRANSCRIPTION_COMPLETE: AudioHamsterStates.LISTENING,
        ERROR: AudioHamsterStates.ERROR
    },
    [AudioHamsterStates.ERROR]: {
        RESET: AudioHamsterStates.SLEEPING
    }
};

// Monitor State Machine
const MonitorStates = {
    IDLE: 'idle',
    DETECTED: 'detected',
    CAPTURING: 'capturing',
    CAPTURED: 'captured',
    ERROR: 'error'
};

const MonitorTransitions = {
    [MonitorStates.IDLE]: {
        DETECT_SCREEN: MonitorStates.DETECTED,
        ERROR: MonitorStates.ERROR
    },
    [MonitorStates.DETECTED]: {
        TAKE_SCREENSHOT: MonitorStates.CAPTURING,
        DETECTION_LOST: MonitorStates.IDLE,
        ERROR: MonitorStates.ERROR
    },
    [MonitorStates.CAPTURING]: {
        SCREENSHOT_COMPLETE: MonitorStates.CAPTURED,
        ERROR: MonitorStates.ERROR
    },
    [MonitorStates.CAPTURED]: {
        RESET_MONITOR: MonitorStates.IDLE,
        ERROR: MonitorStates.ERROR
    },
    [MonitorStates.ERROR]: {
        RESET: MonitorStates.IDLE
    }
};

// Processing Cube State Machine
const ProcessingCubeStates = {
    IDLE: 'idle',
    RECEIVING: 'receiving',
    PROCESSING: 'processing',
    COMPLETE: 'complete',
    SENDING: 'sending',
    ERROR: 'error'
};

const ProcessingCubeTransitions = {
    [ProcessingCubeStates.IDLE]: {
        DATA_RECEIVED: ProcessingCubeStates.RECEIVING,
        ERROR: ProcessingCubeStates.ERROR
    },
    [ProcessingCubeStates.RECEIVING]: {
        START_PROCESSING: ProcessingCubeStates.PROCESSING,
        ERROR: ProcessingCubeStates.ERROR
    },
    [ProcessingCubeStates.PROCESSING]: {
        PROCESSING_COMPLETE: ProcessingCubeStates.COMPLETE,
        ERROR: ProcessingCubeStates.ERROR
    },
    [ProcessingCubeStates.COMPLETE]: {
        SEND_DATA: ProcessingCubeStates.SENDING,
        ERROR: ProcessingCubeStates.ERROR
    },
    [ProcessingCubeStates.SENDING]: {
        SEND_COMPLETE: ProcessingCubeStates.IDLE,
        ERROR: ProcessingCubeStates.ERROR
    },
    [ProcessingCubeStates.ERROR]: {
        RESET: ProcessingCubeStates.IDLE
    }
};

// Pipe State Machine
const PipeStates = {
    EMPTY: 'empty',
    FLOWING: 'flowing',
    BLOCKED: 'blocked'
};

const PipeTransitions = {
    [PipeStates.EMPTY]: {
        START_FLOW: PipeStates.FLOWING,
        BLOCK_PIPE: PipeStates.BLOCKED
    },
    [PipeStates.FLOWING]: {
        STOP_FLOW: PipeStates.EMPTY,
        BLOCK_PIPE: PipeStates.BLOCKED
    },
    [PipeStates.BLOCKED]: {
        CLEAR_BLOCK: PipeStates.EMPTY
    }
};

// ChromaDB State Machine
const ChromaDBStates = {
    IDLE: 'idle',
    RECEIVING: 'receiving',
    STORING: 'storing',
    ERROR: 'error'
};

const ChromaDBTransitions = {
    [ChromaDBStates.IDLE]: {
        RECEIVE_DATA: ChromaDBStates.RECEIVING,
        ERROR: ChromaDBStates.ERROR
    },
    [ChromaDBStates.RECEIVING]: {
        START_STORING: ChromaDBStates.STORING,
        ERROR: ChromaDBStates.ERROR
    },
    [ChromaDBStates.STORING]: {
        STORAGE_COMPLETE: ChromaDBStates.IDLE,
        ERROR: ChromaDBStates.ERROR
    },
    [ChromaDBStates.ERROR]: {
        RESET: ChromaDBStates.IDLE
    }
};

// Factory functions for creating state machines
const StateMachineFactory = {
    createHamster: () => createStateMachine(HamsterStates.WAITING, HamsterTransitions),
    createAudioHamster: () => createStateMachine(AudioHamsterStates.SLEEPING, AudioHamsterTransitions),
    createMonitor: () => createStateMachine(MonitorStates.IDLE, MonitorTransitions),
    createProcessingCube: () => createStateMachine(ProcessingCubeStates.IDLE, ProcessingCubeTransitions),
    createPipe: () => createStateMachine(PipeStates.EMPTY, PipeTransitions),
    createChromaDB: () => createStateMachine(ChromaDBStates.IDLE, ChromaDBTransitions)
};

// Animation timing configuration
const AnimationTiming = {
    hamster_run_duration: 2000,      // 2 seconds to reach monitor
    screenshot_flash: 200,           // Brief flash for screenshot
    ocr_processing: 3000,           // 3 seconds OCR spinning
    pipe_flow_speed: 1500,          // Data flow animation speed
    chroma_slide_duration: 800,     // Rectangle sliding animation
    error_flash_interval: 500,      // Error state blinking
    manhole_animation: 500,         // Manhole open/close
    audio_chunk_processing: 5000    // Audio processing time
};

// State timeout configuration
const StateTimeouts = {
    max_processing_time: 10000,     // 10 seconds before error
    idle_return_delay: 2000,        // Delay before returning to idle
    error_display_duration: 5000,   // How long to show errors
    audio_silence_timeout: 30000    // Return to sleep after silence
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        createStateMachine,
        StateMachineFactory,
        HamsterStates,
        AudioHamsterStates,
        MonitorStates,
        ProcessingCubeStates,
        PipeStates,
        ChromaDBStates,
        AnimationTiming,
        StateTimeouts
    };
} else {
    // Browser environment
    window.HamsterStateMachine = {
        createStateMachine,
        StateMachineFactory,
        HamsterStates,
        AudioHamsterStates,
        MonitorStates,
        ProcessingCubeStates,
        PipeStates,
        ChromaDBStates,
        AnimationTiming,
        StateTimeouts
    };
}


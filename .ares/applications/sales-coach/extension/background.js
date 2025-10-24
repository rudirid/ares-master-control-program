// background.js - Service Worker for Sales Coach Extension
// Manages WebSocket connection to Python backend and coordinates messaging

class SalesCoachBackground {
    constructor() {
        this.ws = null;
        this.isActive = false;
        this.isConnected = false;
        this.contextFile = 'sample';
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;

        console.log('[Sales Coach] Background service worker initialized');

        this.setupMessageHandlers();
        this.connectBackend();
    }

    setupMessageHandlers() {
        // Listen for messages from content script and popup
        chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
            console.log('[Background] Received message:', message.type);

            switch (message.type) {
                case 'TRANSCRIPT':
                    this.handleTranscript(message.data);
                    sendResponse({success: true});
                    break;

                case 'START_COACHING':
                    this.startCoaching(message.contextFile || 'sample');
                    sendResponse({success: true});
                    break;

                case 'STOP_COACHING':
                    this.stopCoaching();
                    sendResponse({success: true});
                    break;

                case 'GET_STATUS':
                    sendResponse({
                        active: this.isActive,
                        connected: this.isConnected
                    });
                    break;

                case 'PING':
                    sendResponse({pong: true});
                    break;
            }

            return true;  // Keep channel open for async response
        });

        // Listen for extension install/update
        chrome.runtime.onInstalled.addListener((details) => {
            console.log('[Sales Coach] Extension installed/updated:', details.reason);

            if (details.reason === 'install') {
                // Open welcome page
                chrome.tabs.create({
                    url: 'https://github.com/your-repo/sales-coach/wiki/Getting-Started'
                });
            }
        });
    }

    connectBackend() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            console.log('[Background] Already connected');
            return;
        }

        console.log('[Background] Connecting to backend...');

        try {
            this.ws = new WebSocket('ws://localhost:5001/extension');

            this.ws.onopen = () => {
                console.log('[Background] Connected to backend');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this.updateIcon('connected');
                this.notifyContentScripts({type: 'BACKEND_CONNECTED'});
            };

            this.ws.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    console.log('[Background] Received from backend:', message.type);

                    if (message.type === 'suggestion') {
                        this.broadcastSuggestion(message.data);
                    }
                    else if (message.type === 'meddic_update') {
                        this.broadcastMeddicUpdate(message.data);
                    }
                    else if (message.type === 'transcript_echo') {
                        // Echo back to content script for display
                        this.notifyContentScripts({
                            type: 'TRANSCRIPT_ECHO',
                            data: message.data
                        });
                    }
                } catch (error) {
                    console.error('[Background] Error parsing message:', error);
                }
            };

            this.ws.onerror = (error) => {
                console.error('[Background] WebSocket error:', error);
                this.isConnected = false;
                this.updateIcon('error');
            };

            this.ws.onclose = () => {
                console.log('[Background] Disconnected from backend');
                this.isConnected = false;
                this.updateIcon('disconnected');

                // Auto-reconnect with exponential backoff
                if (this.reconnectAttempts < this.maxReconnectAttempts) {
                    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
                    console.log(`[Background] Reconnecting in ${delay}ms...`);

                    setTimeout(() => {
                        this.reconnectAttempts++;
                        this.connectBackend();
                    }, delay);
                } else {
                    console.error('[Background] Max reconnection attempts reached');
                    this.notifyContentScripts({
                        type: 'BACKEND_ERROR',
                        message: 'Cannot connect to backend. Is the server running?'
                    });
                }
            };
        } catch (error) {
            console.error('[Background] Error creating WebSocket:', error);
            this.isConnected = false;
            this.updateIcon('error');
        }
    }

    handleTranscript(transcript) {
        if (!this.isActive) {
            console.log('[Background] Coaching not active, ignoring transcript');
            return;
        }

        if (!this.isConnected || this.ws?.readyState !== WebSocket.OPEN) {
            console.warn('[Background] Not connected to backend, cannot send transcript');
            return;
        }

        // Send to backend
        try {
            this.ws.send(JSON.stringify({
                type: 'transcript',
                data: transcript
            }));
            console.log('[Background] Sent transcript to backend');
        } catch (error) {
            console.error('[Background] Error sending transcript:', error);
        }
    }

    broadcastSuggestion(suggestion) {
        console.log('[Background] Broadcasting suggestion to content scripts');

        // Send to all Google Meet tabs
        this.notifyContentScripts({
            type: 'SUGGESTION',
            data: suggestion
        });
    }

    broadcastMeddicUpdate(data) {
        console.log('[Background] Broadcasting MEDDIC update');

        this.notifyContentScripts({
            type: 'MEDDIC_UPDATE',
            data: data
        });
    }

    notifyContentScripts(message) {
        // Send message to all Meet tabs
        chrome.tabs.query({url: "https://meet.google.com/*"}, (tabs) => {
            tabs.forEach(tab => {
                chrome.tabs.sendMessage(tab.id, message, (response) => {
                    if (chrome.runtime.lastError) {
                        // Tab might not have content script loaded yet
                        console.log('[Background] Could not send to tab:', chrome.runtime.lastError.message);
                    }
                });
            });
        });
    }

    startCoaching(contextFile) {
        console.log('[Background] Starting coaching with context:', contextFile);
        this.isActive = true;
        this.contextFile = contextFile;

        // Notify backend
        if (this.isConnected && this.ws?.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'start_call',
                context_file: contextFile
            }));
        }

        // Notify content scripts
        this.notifyContentScripts({type: 'START_COACHING'});

        // Update icon
        this.updateIcon('active');
    }

    stopCoaching() {
        console.log('[Background] Stopping coaching');
        this.isActive = false;

        // Notify backend
        if (this.isConnected && this.ws?.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'stop_call'
            }));
        }

        // Notify content scripts
        this.notifyContentScripts({type: 'STOP_COACHING'});

        // Update icon
        this.updateIcon('connected');
    }

    updateIcon(status) {
        const iconPaths = {
            'active': {
                '16': 'icons/icon16.png',
                '48': 'icons/icon48.png',
                '128': 'icons/icon128.png'
            },
            'connected': {
                '16': 'icons/icon16.png',
                '48': 'icons/icon48.png',
                '128': 'icons/icon128.png'
            },
            'disconnected': {
                '16': 'icons/icon16.png',
                '48': 'icons/icon48.png',
                '128': 'icons/icon128.png'
            },
            'error': {
                '16': 'icons/icon16.png',
                '48': 'icons/icon48.png',
                '128': 'icons/icon128.png'
            }
        };

        chrome.action.setIcon({
            path: iconPaths[status] || iconPaths['disconnected']
        });

        // Set badge
        const badges = {
            'active': {text: '●', color: '#4CAF50'},
            'connected': {text: '', color: '#4CAF50'},
            'disconnected': {text: '!', color: '#f44336'},
            'error': {text: '!', color: '#f44336'}
        };

        const badge = badges[status] || badges['disconnected'];
        chrome.action.setBadgeText({text: badge.text});
        chrome.action.setBadgeBackgroundColor({color: badge.color});
    }
}

// Initialize on service worker startup
console.log('[Sales Coach] Initializing background service worker...');
const salesCoach = new SalesCoachBackground();

// Keep service worker alive
chrome.runtime.onConnect.addListener((port) => {
    console.log('[Background] Port connected:', port.name);
});

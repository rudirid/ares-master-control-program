// content.js - Injected into Google Meet pages
// Handles speech recognition, UI overlay, and communication with background script

class SalesCoachContent {
    constructor() {
        this.speechHandler = null;
        this.overlay = null;
        this.isCoachingActive = false;
        this.isInMeeting = false;
        this.suggestionCount = 0;

        console.log('[Sales Coach] Content script loaded');
        this.init();
    }

    async init() {
        // Wait for Google Meet to fully load
        await this.waitForMeet();

        console.log('[Sales Coach] Google Meet detected');

        // Create UI overlay
        this.createOverlay();

        // Setup Web Speech API
        this.setupSpeechRecognition();

        // Listen for messages from background script
        this.setupMessageHandlers();

        // Detect when meeting starts/ends
        this.detectMeetingState();

        console.log('[Sales Coach] Initialization complete');
    }

    waitForMeet() {
        return new Promise((resolve) => {
            // Wait for Meet's UI to be present
            const checkInterval = setInterval(() => {
                // Look for Meet's main container
                if (document.querySelector('[data-meeting-co-host-join-token]') ||
                    document.querySelector('[jsname="HlFzfd"]') ||
                    document.querySelector('.KBy0wd')) {
                    clearInterval(checkInterval);
                    console.log('[Sales Coach] Meet UI detected');
                    resolve();
                }
            }, 500);

            // Timeout after 10 seconds
            setTimeout(() => {
                clearInterval(checkInterval);
                console.log('[Sales Coach] Timeout waiting for Meet, proceeding anyway');
                resolve();
            }, 10000);
        });
    }

    setupSpeechRecognition() {
        if (!window.WebSpeechHandler) {
            console.error('[Sales Coach] WebSpeechHandler not available');
            return;
        }

        this.speechHandler = new WebSpeechHandler(
            // onTranscript callback
            (transcript) => this.handleTranscript(transcript),
            // onError callback
            (error) => this.handleSpeechError(error)
        );

        if (!this.speechHandler.isSupported()) {
            this.showError('Web Speech API not supported in this browser');
        }

        console.log('[Sales Coach] Speech recognition initialized');
    }

    setupMessageHandlers() {
        chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
            console.log('[Content] Received message:', message.type);

            switch (message.type) {
                case 'SUGGESTION':
                    this.displaySuggestion(message.data);
                    break;

                case 'MEDDIC_UPDATE':
                    this.updateMeddic(message.data);
                    break;

                case 'START_COACHING':
                    this.startCoaching();
                    break;

                case 'STOP_COACHING':
                    this.stopCoaching();
                    break;

                case 'BACKEND_CONNECTED':
                    this.updateStatus('connected', 'Connected to backend');
                    break;

                case 'BACKEND_ERROR':
                    this.showError(message.message);
                    break;

                case 'TRANSCRIPT_ECHO':
                    // Display transcript from backend (for debugging)
                    break;
            }

            sendResponse({received: true});
            return true;
        });
    }

    handleTranscript(transcript) {
        if (!this.isCoachingActive) return;

        // Send to background script
        chrome.runtime.sendMessage({
            type: 'TRANSCRIPT',
            data: transcript
        });

        // Update overlay transcript display
        this.updateTranscript(transcript.text, transcript.is_final);
    }

    handleSpeechError(error) {
        console.error('[Sales Coach] Speech error:', error);
        this.showError(`Speech recognition error: ${error}`);
    }

    detectMeetingState() {
        // Watch for participants to detect meeting start
        const observer = new MutationObserver(() => {
            const participantElements = document.querySelectorAll('[data-participant-id], [data-self-name]');
            const participantCount = participantElements.length;

            const wasInMeeting = this.isInMeeting;
            this.isInMeeting = participantCount > 0;

            if (this.isInMeeting && !wasInMeeting) {
                console.log('[Sales Coach] Meeting started');
                this.onMeetingStart();
            }
            else if (!this.isInMeeting && wasInMeeting) {
                console.log('[Sales Coach] Meeting ended');
                this.onMeetingEnd();
            }
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    onMeetingStart() {
        this.updateStatus('ready', 'Meeting active - Ready to coach');
        this.overlay.style.display = 'flex';

        // Show notification
        this.showNotification('Meeting detected. Click extension icon to start coaching.');
    }

    onMeetingEnd() {
        this.updateStatus('ended', 'Meeting ended');

        if (this.isCoachingActive) {
            this.stopCoaching();
        }
    }

    startCoaching() {
        console.log('[Sales Coach] Starting coaching');
        this.isCoachingActive = true;

        // Start speech recognition
        if (this.speechHandler) {
            this.speechHandler.start();
        }

        this.updateStatus('active', 'Coaching active - Listening...');
        this.clearSuggestions();
    }

    stopCoaching() {
        console.log('[Sales Coach] Stopping coaching');
        this.isCoachingActive = false;

        // Stop speech recognition
        if (this.speechHandler) {
            this.speechHandler.stop();
        }

        this.updateStatus('ready', 'Coaching stopped');
    }

    createOverlay() {
        // Create main overlay container
        this.overlay = document.createElement('div');
        this.overlay.id = 'sales-coach-overlay';
        this.overlay.innerHTML = `
            <div class="sc-header">
                <span class="sc-title">SALES COACH</span>
                <div class="sc-header-controls">
                    <button class="sc-btn sc-minimize" title="Minimize">_</button>
                    <button class="sc-btn sc-close" title="Close">×</button>
                </div>
            </div>
            <div class="sc-content">
                <div class="sc-status">
                    <div class="sc-status-indicator"></div>
                    <div class="sc-status-info">
                        <div class="sc-status-text">Initializing...</div>
                        <div class="sc-status-detail"></div>
                    </div>
                </div>

                <div class="sc-section">
                    <div class="sc-section-header">
                        <span class="sc-section-title">TACTICAL SUGGESTIONS</span>
                        <span class="sc-suggestion-count">0</span>
                    </div>
                    <div class="sc-suggestions" id="sc-suggestions">
                        <div class="sc-empty">Waiting for call to start...</div>
                    </div>
                </div>

                <div class="sc-section sc-collapsible">
                    <div class="sc-section-header sc-clickable" id="sc-transcript-toggle">
                        <span class="sc-section-title">LIVE TRANSCRIPT</span>
                        <span class="sc-toggle-icon">▼</span>
                    </div>
                    <div class="sc-transcript" id="sc-transcript">
                        <div class="sc-transcript-content"></div>
                    </div>
                </div>

                <div class="sc-section sc-collapsible">
                    <div class="sc-section-header sc-clickable" id="sc-meddic-toggle">
                        <span class="sc-section-title">MEDDIC PROGRESS</span>
                        <span class="sc-meddic-percentage">0%</span>
                    </div>
                    <div class="sc-meddic" id="sc-meddic">
                        <div class="sc-meddic-items">
                            <div class="sc-meddic-item" data-component="Metrics">
                                <span class="sc-check">[ ]</span> Metrics
                            </div>
                            <div class="sc-meddic-item" data-component="Economic Buyer">
                                <span class="sc-check">[ ]</span> Economic Buyer
                            </div>
                            <div class="sc-meddic-item" data-component="Decision Criteria">
                                <span class="sc-check">[ ]</span> Decision Criteria
                            </div>
                            <div class="sc-meddic-item" data-component="Decision Process">
                                <span class="sc-check">[ ]</span> Decision Process
                            </div>
                            <div class="sc-meddic-item" data-component="Pain">
                                <span class="sc-check">[ ]</span> Pain
                            </div>
                            <div class="sc-meddic-item" data-component="Champion">
                                <span class="sc-check">[ ]</span> Champion
                            </div>
                        </div>
                        <div class="sc-progress-bar">
                            <div class="sc-progress-fill" id="sc-meddic-progress"></div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(this.overlay);

        // Setup event listeners
        this.overlay.querySelector('.sc-close').addEventListener('click', () => {
            this.overlay.style.display = 'none';
        });

        this.overlay.querySelector('.sc-minimize').addEventListener('click', () => {
            this.overlay.classList.toggle('sc-minimized');
        });

        // Collapsible sections
        document.getElementById('sc-transcript-toggle').addEventListener('click', (e) => {
            e.currentTarget.parentElement.classList.toggle('sc-collapsed');
        });

        document.getElementById('sc-meddic-toggle').addEventListener('click', (e) => {
            e.currentTarget.parentElement.classList.toggle('sc-collapsed');
        });

        // Make draggable
        this.makeDraggable(this.overlay);

        console.log('[Sales Coach] Overlay created');
    }

    displaySuggestion(suggestion) {
        const container = document.getElementById('sc-suggestions');

        // Remove empty state
        const empty = container.querySelector('.sc-empty');
        if (empty) {
            empty.remove();
        }

        // Create suggestion element
        const suggestionEl = document.createElement('div');
        suggestionEl.className = `sc-suggestion sc-urgency-${suggestion.urgency}`;
        suggestionEl.innerHTML = `
            <div class="sc-suggestion-header">
                <div class="sc-suggestion-badges">
                    <span class="sc-badge sc-badge-${suggestion.urgency}">${suggestion.urgency.toUpperCase()}</span>
                    <span class="sc-badge">${suggestion.category}</span>
                </div>
                <span class="sc-confidence">${Math.round(suggestion.confidence * 100)}%</span>
            </div>
            <div class="sc-suggestion-text">${this.escapeHtml(suggestion.text)}</div>
            <div class="sc-suggestion-footer">
                <span class="sc-framework">${this.escapeHtml(suggestion.framework)}</span>
                ${suggestion.source ? `<span class="sc-source">${suggestion.source}</span>` : ''}
            </div>
        `;

        // Add to top (most recent first)
        container.insertBefore(suggestionEl, container.firstChild);

        // Update count
        this.suggestionCount++;
        this.overlay.querySelector('.sc-suggestion-count').textContent = this.suggestionCount;

        // Limit to 5 visible suggestions
        const suggestions = container.querySelectorAll('.sc-suggestion');
        if (suggestions.length > 5) {
            suggestions[suggestions.length - 1].remove();
        }

        // Flash animation
        suggestionEl.classList.add('sc-flash');
        setTimeout(() => suggestionEl.classList.remove('sc-flash'), 500);

        console.log('[Sales Coach] Displayed suggestion:', suggestion.urgency);
    }

    updateTranscript(text, isFinal) {
        const transcriptContent = this.overlay.querySelector('.sc-transcript-content');

        if (isFinal) {
            // Add new final transcript line
            const line = document.createElement('div');
            line.className = 'sc-transcript-line';
            line.textContent = text;
            transcriptContent.appendChild(line);

            // Auto-scroll
            transcriptContent.scrollTop = transcriptContent.scrollHeight;

            // Limit to 10 lines
            const lines = transcriptContent.querySelectorAll('.sc-transcript-line');
            if (lines.length > 10) {
                lines[0].remove();
            }

            // Remove interim if present
            const interim = transcriptContent.querySelector('.sc-transcript-interim');
            if (interim) {
                interim.remove();
            }
        } else {
            // Update interim result
            let interim = transcriptContent.querySelector('.sc-transcript-interim');
            if (!interim) {
                interim = document.createElement('div');
                interim.className = 'sc-transcript-interim';
                transcriptContent.appendChild(interim);
            }
            interim.textContent = text;
        }
    }

    updateMeddic(data) {
        if (!data.components) return;

        const items = this.overlay.querySelectorAll('.sc-meddic-item');
        items.forEach(item => {
            const component = item.getAttribute('data-component');
            const isComplete = data.components[component];
            const checkbox = item.querySelector('.sc-check');

            if (isComplete) {
                checkbox.textContent = '[X]';
                checkbox.classList.add('sc-checked');
            } else {
                checkbox.textContent = '[ ]';
                checkbox.classList.remove('sc-checked');
            }
        });

        // Update progress bar
        const percentage = data.percentage || 0;
        document.getElementById('sc-meddic-progress').style.width = `${percentage}%`;
        this.overlay.querySelector('.sc-meddic-percentage').textContent = `${percentage}%`;
    }

    updateStatus(state, text, detail = '') {
        const indicator = this.overlay.querySelector('.sc-status-indicator');
        const statusText = this.overlay.querySelector('.sc-status-text');
        const statusDetail = this.overlay.querySelector('.sc-status-detail');

        indicator.className = 'sc-status-indicator sc-status-' + state;
        statusText.textContent = text;
        statusDetail.textContent = detail;
    }

    clearSuggestions() {
        const container = document.getElementById('sc-suggestions');
        container.innerHTML = '<div class="sc-empty">Listening for conversation...</div>';
        this.suggestionCount = 0;
        this.overlay.querySelector('.sc-suggestion-count').textContent = '0';
    }

    showNotification(message) {
        // Simple in-overlay notification
        const notification = document.createElement('div');
        notification.className = 'sc-notification';
        notification.textContent = message;

        this.overlay.appendChild(notification);

        setTimeout(() => {
            notification.classList.add('sc-notification-show');
        }, 10);

        setTimeout(() => {
            notification.classList.remove('sc-notification-show');
            setTimeout(() => notification.remove(), 300);
        }, 4000);
    }

    showError(message) {
        console.error('[Sales Coach] Error:', message);
        this.updateStatus('error', 'Error', message);
    }

    makeDraggable(element) {
        const header = element.querySelector('.sc-header');
        let isDragging = false;
        let currentX, currentY, initialX, initialY;

        header.addEventListener('mousedown', (e) => {
            if (e.target.classList.contains('sc-btn')) return;

            isDragging = true;
            initialX = e.clientX - element.offsetLeft;
            initialY = e.clientY - element.offsetTop;
            header.style.cursor = 'grabbing';
        });

        document.addEventListener('mousemove', (e) => {
            if (!isDragging) return;

            e.preventDefault();
            currentX = e.clientX - initialX;
            currentY = e.clientY - initialY;

            // Keep within viewport
            const maxX = window.innerWidth - element.offsetWidth;
            const maxY = window.innerHeight - element.offsetHeight;

            currentX = Math.max(0, Math.min(currentX, maxX));
            currentY = Math.max(0, Math.min(currentY, maxY));

            element.style.left = currentX + 'px';
            element.style.top = currentY + 'px';
        });

        document.addEventListener('mouseup', () => {
            if (isDragging) {
                isDragging = false;
                header.style.cursor = 'move';
            }
        });
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new SalesCoachContent();
    });
} else {
    new SalesCoachContent();
}

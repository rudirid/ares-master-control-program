// popup.js - Popup UI logic for Sales Coach extension

document.addEventListener('DOMContentLoaded', () => {
    const statusCard = document.getElementById('status-card');
    const statusIndicator = document.getElementById('status-indicator');
    const statusText = document.getElementById('status-text');
    const statusDetail = document.getElementById('status-detail');
    const toggleBtn = document.getElementById('toggle-btn');
    const contextSelect = document.getElementById('context-file');
    const errorContainer = document.getElementById('error-container');
    const successContainer = document.getElementById('success-container');

    let isActive = false;
    let isConnected = false;

    // Check status on load
    checkStatus();

    // Refresh status every 2 seconds
    setInterval(checkStatus, 2000);

    // Toggle button click
    toggleBtn.addEventListener('click', () => {
        if (isActive) {
            stopCoaching();
        } else {
            startCoaching();
        }
    });

    // Help link
    document.getElementById('help-link').addEventListener('click', (e) => {
        e.preventDefault();
        chrome.tabs.create({
            url: 'https://github.com/your-repo/sales-coach/wiki'
        });
    });

    // Settings link
    document.getElementById('settings-link').addEventListener('click', (e) => {
        e.preventDefault();
        showMessage('success', 'Settings coming soon!');
    });

    function checkStatus() {
        chrome.runtime.sendMessage({type: 'GET_STATUS'}, (response) => {
            if (chrome.runtime.lastError) {
                console.error('Error getting status:', chrome.runtime.lastError);
                setDisconnected();
                return;
            }

            if (response) {
                isActive = response.active;
                isConnected = response.connected;

                if (isActive) {
                    setActive();
                } else if (isConnected) {
                    setReady();
                } else {
                    setDisconnected();
                }
            } else {
                setDisconnected();
            }
        });
    }

    function startCoaching() {
        const contextFile = contextSelect.value;

        chrome.runtime.sendMessage({
            type: 'START_COACHING',
            contextFile: contextFile
        }, (response) => {
            if (chrome.runtime.lastError) {
                showMessage('error', 'Failed to start coaching: ' + chrome.runtime.lastError.message);
                return;
            }

            showMessage('success', 'Coaching started! Suggestions will appear in the overlay.');
            checkStatus();
        });
    }

    function stopCoaching() {
        chrome.runtime.sendMessage({type: 'STOP_COACHING'}, (response) => {
            if (chrome.runtime.lastError) {
                showMessage('error', 'Failed to stop coaching: ' + chrome.runtime.lastError.message);
                return;
            }

            showMessage('success', 'Coaching stopped.');
            checkStatus();
        });
    }

    function setActive() {
        statusCard.className = 'status-card active';
        statusIndicator.className = 'status-indicator active';
        statusText.textContent = 'Coaching Active';
        statusDetail.textContent = 'Listening to call...';
        toggleBtn.textContent = 'Stop Coaching';
        toggleBtn.className = 'stop';
        toggleBtn.disabled = false;
        contextSelect.disabled = true;
    }

    function setReady() {
        statusCard.className = 'status-card connected';
        statusIndicator.className = 'status-indicator connected';
        statusText.textContent = 'Ready';
        statusDetail.textContent = 'Backend connected';
        toggleBtn.textContent = 'Start Coaching';
        toggleBtn.className = '';
        toggleBtn.disabled = false;
        contextSelect.disabled = false;
    }

    function setDisconnected() {
        statusCard.className = 'status-card error';
        statusIndicator.className = 'status-indicator error';
        statusText.textContent = 'Not Connected';
        statusDetail.textContent = 'Backend server not running';
        toggleBtn.textContent = 'Start Coaching';
        toggleBtn.className = '';
        toggleBtn.disabled = true;
        contextSelect.disabled = false;
    }

    function showMessage(type, message) {
        const container = type === 'error' ? errorContainer : successContainer;
        const className = type === 'error' ? 'error-message' : 'success-message';

        container.innerHTML = `<div class="${className}">${message}</div>`;

        // Auto-clear after 4 seconds
        setTimeout(() => {
            container.innerHTML = '';
        }, 4000);
    }
});

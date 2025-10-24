// lib/webspeech-handler.js
// Web Speech API wrapper for reliable speech recognition

class WebSpeechHandler {
    constructor(onTranscript, onError) {
        this.onTranscript = onTranscript;
        this.onError = onError;
        this.recognition = null;
        this.isListening = false;
        this.restartTimeout = null;

        this.setupRecognition();
    }

    setupRecognition() {
        if (!('webkitSpeechRecognition' in window)) {
            console.error('[WebSpeech] Web Speech API not supported');
            if (this.onError) {
                this.onError('Web Speech API not supported in this browser');
            }
            return;
        }

        this.recognition = new webkitSpeechRecognition();

        // Configuration for optimal real-time performance
        this.recognition.continuous = true;  // Keep listening
        this.recognition.interimResults = true;  // Get partial results
        this.recognition.lang = 'en-US';
        this.recognition.maxAlternatives = 1;

        // Handle results
        this.recognition.onresult = (event) => {
            try {
                const result = event.results[event.results.length - 1];
                const transcript = result[0].transcript.trim();
                const isFinal = result.isFinal;
                const confidence = result[0].confidence || 0;

                if (transcript && this.onTranscript) {
                    this.onTranscript({
                        text: transcript,
                        is_final: isFinal,
                        confidence: confidence,
                        timestamp: new Date().toISOString()
                    });
                }
            } catch (error) {
                console.error('[WebSpeech] Error processing result:', error);
            }
        };

        // Handle errors
        this.recognition.onerror = (event) => {
            console.error('[WebSpeech] Recognition error:', event.error);

            // Don't treat "no-speech" as a fatal error
            if (event.error === 'no-speech') {
                console.log('[WebSpeech] No speech detected, continuing...');
                return;
            }

            if (this.onError) {
                this.onError(event.error);
            }

            // Auto-restart on certain errors
            if (['network', 'aborted'].includes(event.error)) {
                console.log('[WebSpeech] Restarting due to error:', event.error);
                this.restart();
            }
        };

        // Handle end (auto-restart)
        this.recognition.onend = () => {
            console.log('[WebSpeech] Recognition ended');

            if (this.isListening) {
                // Auto-restart with small delay to prevent rapid cycling
                console.log('[WebSpeech] Auto-restarting...');
                clearTimeout(this.restartTimeout);
                this.restartTimeout = setTimeout(() => {
                    this.start();
                }, 100);
            }
        };

        this.recognition.onstart = () => {
            console.log('[WebSpeech] Recognition started');
        };

        console.log('[WebSpeech] Recognition configured');
    }

    start() {
        if (!this.recognition) {
            console.error('[WebSpeech] Recognition not initialized');
            return false;
        }

        if (this.isListening) {
            console.log('[WebSpeech] Already listening');
            return true;
        }

        try {
            this.isListening = true;
            this.recognition.start();
            console.log('[WebSpeech] Started listening');
            return true;
        } catch (error) {
            console.error('[WebSpeech] Error starting:', error);
            this.isListening = false;
            return false;
        }
    }

    stop() {
        if (!this.recognition || !this.isListening) {
            return;
        }

        try {
            this.isListening = false;
            clearTimeout(this.restartTimeout);
            this.recognition.stop();
            console.log('[WebSpeech] Stopped listening');
        } catch (error) {
            console.error('[WebSpeech] Error stopping:', error);
        }
    }

    restart() {
        this.stop();
        setTimeout(() => this.start(), 500);
    }

    isSupported() {
        return 'webkitSpeechRecognition' in window;
    }
}

// Make available globally
window.WebSpeechHandler = WebSpeechHandler;

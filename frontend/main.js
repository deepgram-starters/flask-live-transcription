const streamUrlInput = document.getElementById('stream-url-input');
const modelInput = document.getElementById('model-input');
const languageInput = document.getElementById('language-input');
const startButton = document.getElementById('start-button');
const cancelButton = document.getElementById('cancel-button');
const stopButton = document.getElementById('stop-button');
const clearButton = document.getElementById('clear-transcript');
const statusIndicator = document.getElementById('status-indicator');
const statusText = document.getElementById('status-text');
const transcriptContainer = document.getElementById('transcript-container');


let websocket = null;
let isConnected = false;
let isConnecting = false;


function showStatus(message, type = 'info') {
  statusText.textContent = message;
  statusIndicator.className = `dg-status dg-status--${type}`;
  statusIndicator.style.display = 'flex';
}

function hideStatus() {
  statusIndicator.style.display = 'none';
}

function clearTranscript() {
  transcriptContainer.innerHTML = `
    <div class="transcript-placeholder">
      <i class="fa-solid fa-tower-broadcast" style="font-size: 3rem; opacity: 0.3; margin-bottom: 1rem;"></i>
      <p>Enter an audio stream URL and click "Start Transcription" to begin...</p>
    </div>
  `;
}

function addTranscriptItem(transcript, isFinal, metadata = {}) {
  // Remove placeholder if it exists
  const placeholder = transcriptContainer.querySelector('.transcript-placeholder');
  if (placeholder) {
    placeholder.remove();
  }

  // Create transcript item
  const item = document.createElement('div');
  item.className = isFinal ? 'transcript-item' : 'transcript-item transcript-item--interim';

  // Add metadata
  let metaHtml = '';
  if (metadata.confidence !== undefined) {
    metaHtml += `<div class="transcript-meta">Confidence: ${(metadata.confidence * 100).toFixed(1)}%</div>`;
  }

  // Add transcript text
  item.innerHTML = `
    ${metaHtml}
    <div class="transcript-text">${escapeHtml(transcript)}</div>
  `;

  // If this is an interim result, check if we should replace the last interim
  const lastItem = transcriptContainer.lastElementChild;
  if (!isFinal && lastItem && lastItem.classList.contains('transcript-item--interim')) {
    lastItem.replaceWith(item);
  } else {
    transcriptContainer.appendChild(item);
  }

  // Auto-scroll to bottom
  transcriptContainer.scrollTop = transcriptContainer.scrollHeight;
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function startTranscription() {
  const streamUrl = streamUrlInput.value.trim();

  if (!streamUrl) {
    showStatus('Please enter a stream URL', 'error');
    return;
  }

  // Validate URL format
  try {
    const url = new URL(streamUrl);
    if (url.protocol !== 'http:' && url.protocol !== 'https:') {
      showStatus('Stream URL must use http:// or https://', 'error');
      return;
    }
  } catch (error) {
    showStatus('Invalid stream URL format', 'error');
    return;
  }

  // Build WebSocket URL with query parameters
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsHost = window.location.host;

  const params = new URLSearchParams({
    model: modelInput.value.trim() || 'nova-3',
    language: languageInput.value.trim() || 'en',
  });

  const wsUrl = `${wsProtocol}//${wsHost}/live-stt/stream?${params.toString()}`;

  showStatus('Connecting to server...', 'info');

  // Update UI for connecting state
  isConnecting = true;
  startButton.hidden = true;
  cancelButton.hidden = false;
  streamUrlInput.disabled = true;
  modelInput.disabled = true;
  languageInput.disabled = true;

  try {
    websocket = new WebSocket(wsUrl);
    websocket.binaryType = 'arraybuffer';

    websocket.onopen = async () => {
      isConnecting = false;
      isConnected = true;
      showStatus('Connected - fetching stream...', 'success');

      // Update UI - switch from cancel to stop button
      cancelButton.hidden = true;
      stopButton.hidden = false;
      stopButton.disabled = false;

      clearTranscript();

      // Frontend fetches the stream and sends binary to server
      try {
        showStatus('Streaming audio...', 'success');
        const response = await fetch(streamUrl);

        if (!response.ok) {
          throw new Error(`Failed to fetch stream: ${response.statusText}`);
        }

        const reader = response.body.getReader();

        while (true) {
          const { done, value } = await reader.read();

          if (done) {
            console.log('Stream ended');
            showStatus('Stream ended', 'info');
            stopTranscription();
            break;
          }

          // Send binary audio chunk to server
          if (websocket && websocket.readyState === WebSocket.OPEN && value) {
            websocket.send(value.buffer);
          }

          // Stop if connection closed
          if (!isConnected) {
            reader.cancel();
            break;
          }
        }
      } catch (streamError) {
        console.error('Stream fetch error:', streamError);
        showStatus(`Stream error: ${streamError.message}`, 'error');
        stopTranscription();
      }
    };

    websocket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);

        switch (message.type) {
          case 'Metadata':
            showStatus(`Transcribing with model: ${message.model_info?.name || 'unknown'}`, 'success');
            break;

          case 'Results':
            // Display transcript result
            if (message.transcript) {
              addTranscriptItem(
                message.transcript,
                message.is_final || false,
                {
                  confidence: message.confidence,
                  speechFinal: message.speech_final
                }
              );
            }
            break;

          case 'Error':
            console.error('Error from server:', message.error);
            showStatus(`Error: ${message.error.message}`, 'error');

            // Reset state immediately
            isConnecting = false;
            isConnected = false;

            // Close websocket if still open
            if (websocket) {
              websocket.close(1000, 'Client closing due to error');
              websocket = null;
            }

            // Reset UI immediately so user can try again
            resetUI();
            break;

          default:
            console.log('Unknown message type:', message.type);
        }
      } catch (error) {
        console.error('Error parsing message:', error);
      }
    };

    websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
      showStatus('Connection error occurred', 'error');
    };

    websocket.onclose = (event) => {
      isConnecting = false;
      isConnected = false;

      // Code 1011: Server error - don't overwrite the error message already shown
      if (event.code === 1011) {
        // Error message was already displayed via the 'Error' message type
        // Just reset UI silently
      } else if (event.code === 1008) {
        // Policy violation (e.g., invalid parameters)
        showStatus(`Connection closed: ${event.reason || 'Invalid request'}`, 'error');
      } else if (event.code === 1000) {
        // Normal closure
        showStatus('Connection closed', 'info');
      } else if (event.code === 1006) {
        // Abnormal closure (connection dropped)
        showStatus('Connection lost', 'warning');
      } else {
        // Unknown close code
        showStatus(`Connection closed unexpectedly (code: ${event.code})`, 'warning');
      }

      resetUI();
    };

  } catch (error) {
    console.error('Error creating WebSocket:', error);
    showStatus('Failed to create connection', 'error');
    isConnecting = false;
    resetUI();
  }
}

function cancelConnection() {
  showStatus('Connection canceled', 'info');

  if (websocket) {
    // Close the WebSocket if it exists
    try {
      websocket.close(1000, 'User canceled');
    } catch (error) {
      console.error('Error closing WebSocket:', error);
    }
    websocket = null;
  }

  isConnecting = false;
  isConnected = false;
  resetUI();
}

function stopTranscription() {
  if (websocket && isConnected) {
    showStatus('Stopping transcription...', 'info');
    websocket.close();
    websocket = null;
  }
  isConnected = false;
  resetUI();
}

function resetUI() {
  // Reset all UI elements to initial state
  startButton.hidden = false;
  startButton.disabled = false;
  cancelButton.hidden = true;
  stopButton.hidden = true;
  stopButton.disabled = true;
  streamUrlInput.disabled = false;
  modelInput.disabled = false;
  languageInput.disabled = false;
}

startButton.addEventListener('click', startTranscription);
cancelButton.addEventListener('click', cancelConnection);
stopButton.addEventListener('click', stopTranscription);
clearButton.addEventListener('click', clearTranscript);

// Allow Enter key in stream URL input to start
streamUrlInput.addEventListener('keypress', (e) => {
  if (e.key === 'Enter' && !startButton.disabled) {
    startTranscription();
  }
});

// Clean up on page unload
window.addEventListener('beforeunload', () => {
  if (websocket && isConnected) {
    websocket.close();
  }
});

hideStatus();


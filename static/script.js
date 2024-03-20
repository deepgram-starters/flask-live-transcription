var socket_port = 5001;
var socket = io.connect(
  "http://" + window.location.hostname + ":" + socket_port.toString()
);

document.getElementById("record").addEventListener("change", function () {
  if (this.checked) {
    // Start transcription
    socket.emit("toggle_transcription", {action: "start"});
    startStreaming();
  } else {
    // Stop transcription
    stopStreaming();
    socket.emit("toggle_transcription", {action: "stop"});
  }
});

// Write transcription updates to the page
socket.on("transcription_update", function (data) {
  document.getElementById("captions").innerHTML = data.transcription;
});


let mediaStream = null;
let audioProcessor = null;

function startStreaming() {
  const constraints = {
    audio: true,
  };

  navigator.mediaDevices.getUserMedia(constraints)
    .then(function (stream) {
      mediaStream = stream;
      const audioContext = new (window.AudioContext || window.webkitAudioContext)({
        sampleRate: 16000,
      });

      // Create a MediaStreamAudioSourceNode from the stream
      const source = audioContext.createMediaStreamSource(stream);

      // Use the ScriptProcessorNode for direct audio processing
      audioProcessor = audioContext.createScriptProcessor(4096, 1, 1);
      source.connect(audioProcessor);
      audioProcessor.connect(audioContext.destination);

      audioProcessor.onaudioprocess = function (audioProcessingEvent) {
        const inputBuffer = audioProcessingEvent.inputBuffer;
        const outputBuffer = audioProcessingEvent.outputBuffer;

        for (let channel = 0; channel < outputBuffer.numberOfChannels; channel++) {
          const inputData = inputBuffer.getChannelData(channel);
          const outputData = new Int16Array(inputData.length);

          // Convert to 16-bit PCM
          for (let sample = 0; sample < inputData.length; sample++) {
            // Multiply by 0x7FFF; convert to 16-bit PCM
            outputData[sample] = Math.max(-1, Math.min(1, inputData[sample])) * 0x7FFF;
          }

          // At this point, outputData contains the 16-bit PCM audio
          // Here, you would typically send the data over a WebSocket or another method
          const blob = new Blob([outputData.buffer], {type: 'audio/wav'});
          socket.emit('audio_stream', blob);
        }
      };
    })
    .catch(function (err) {
      console.error('Error accessing microphone:', err);
    });
}

function stopStreaming() {
  if (audioProcessor) {
    audioProcessor.disconnect();
    mediaStream.getTracks().forEach(track => track.stop());
    mediaStream = null;
    audioProcessor = null;
  }
}
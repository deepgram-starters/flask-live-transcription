var socket = io.connect(
  "http://" + window.location.hostname + ":" + location.port
);

var isTranscribing = false;

document.getElementById("record").addEventListener("change", function () {
  if (this.checked) {
    // Start transcription
    isTranscribing = true;
    socket.emit("toggle_transcription", { action: "start" });
  } else {
    // Stop transcription
    isTranscribing = false;
    socket.emit("toggle_transcription", { action: "stop" });
  }
});

socket.on("transcription_update", function (data) {
  document.getElementById("captions").innerHTML = data.transcription;
});

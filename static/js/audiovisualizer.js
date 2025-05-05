// Select the canvas element
const canvas = document.getElementById("audioVisualizer");
const canvasCtx = canvas.getContext("2d");

// Set up audio context
const audioContext = new (window.AudioContext || window.webkitAudioContext)();
const analyser = audioContext.createAnalyser();
analyser.fftSize = 2048; // Determines the resolution of the visualization
const bufferLength = analyser.frequencyBinCount;
const dataArray = new Uint8Array(bufferLength);

// Function to draw the audio visualization
function draw() {
    console.log("Drawing...");
    requestAnimationFrame(draw);

    // Get the audio data
    analyser.getByteTimeDomainData(dataArray);

    // Clear the canvas
    canvasCtx.fillStyle = "black";
    canvasCtx.fillRect(0, 0, canvas.width, canvas.height);

    // Draw the waveform
    canvasCtx.lineWidth = 2;
    canvasCtx.strokeStyle = "lime";
    canvasCtx.beginPath();

    const sliceWidth = canvas.width / bufferLength;
    let x = 0;

    for (let i = 0; i < bufferLength; i++) {
        const v = dataArray[i] / 128.0; // Normalize data to range [0, 1]
        const y = (v * canvas.height) / 2;

        if (i === 0) {
            canvasCtx.moveTo(x, y);
        } else {
            canvasCtx.lineTo(x, y);
        }

        x += sliceWidth;
    }

    canvasCtx.lineTo(canvas.width, canvas.height / 2);
    canvasCtx.stroke();
}
// Function to start capturing audio
function startVisualizer() {
    console.log("starting visualizer");
    navigator.mediaDevices
        .getUserMedia({ audio: true })
        .then((stream) => {
            console.log("Microphone access granted.");     
            const source = audioContext.createMediaStreamSource(stream);
            source.connect(analyser);
            draw();
        })
        .catch((err) => {
            console.error("Error accessing microphone:", err);
        });
}

// Automatically start the visualizer when the page loads
startVisualizer();
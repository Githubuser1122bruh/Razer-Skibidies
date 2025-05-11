// Element references
const recordButton = document.getElementById("recordButton");
const recordStop = document.getElementById("recordStop");
const muteButton = document.getElementById("muteButton");
const downloadAudio = document.getElementById("downloadAudio");
const errorMessage = document.getElementById("errorMessage");
const canvas = document.getElementById("canvas");
const startVisualizerButton = document.getElementById("startVisualizer");
const stopVisualizerButton = document.getElementById("stopVisualizer");

// State variables
let controlsMuted = false;
let visualizerActive = false;
let audioCtx = null;
const BASE_URL = "http://127.0.0.1:5001";

// --- Recording Start ---
recordButton?.addEventListener("click", async () => {
    try {
        alert("Recording Started");

        const response = await fetch(`${BASE_URL}/run-script`, {
            method: "POST",
        });

        if (!response.ok) {
            throw new Error("Failed to execute script");
        }

        const data = await response.json();
        console.log(data.message);
    } catch (error) {
        console.error("Error:", error);
    }
});

// --- Recording Stop ---
recordStop?.addEventListener("click", async () => {
    try {
        alert("Recording Stopped");

        const response = await fetch(`${BASE_URL}/stop-script`, {
            method: "POST",
        });

        if (!response.ok) {
            throw new Error("Failed to execute script");
        }

        const data = await response.json();
        console.log(data.message);
    } catch (error) {
        console.error("Error:", error);
    }
});

// --- Mute / Unmute ---
muteButton?.addEventListener("click", () => {
    if (!controlsMuted) {
        recordButton?.setAttribute("disabled", true);
        recordStop?.setAttribute("disabled", true);
        muteButton.innerText = "Unmute";
        controlsMuted = true;
        console.log("Mute enabled");

        [recordButton, recordStop].forEach(btn => {
            if (btn) {
                btn.style.backgroundColor = "#778275";
                btn.style.cursor = "default";
            }
        });
    } else {
        recordButton?.removeAttribute("disabled");
        recordStop?.removeAttribute("disabled");
        muteButton.innerText = "Mute";
        controlsMuted = false;
        console.log("Mute disabled");

        [recordButton, recordStop].forEach(btn => {
            if (btn) {
                btn.style.backgroundColor = "#3d7340";
                btn.style.cursor = "pointer";
            }
        });
    }
});

// --- Download Audio ---
downloadAudio?.addEventListener("click", async () => {
    try {
        const response = await fetch("/get-latest-audio");

        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.error);
        }

        const data = await response.json();
        const filename = data.filename;

        const audioResponse = await fetch(`/download-audio/${filename}`);
        if (!audioResponse.ok) {
            const errorData = await audioResponse.json();
            throw new Error(errorData.error || "File not found.");
        }

        const blob = await audioResponse.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "recorded_audio.mp3";
        document.body.appendChild(a);
        a.click();
        a.remove();

        errorMessage.innerText = "";
    } catch (error) {
        console.error("Error downloading file:", error);
        errorMessage.innerText = "Error: " + error.message;
    }
});

// --- Canvas Utility ---
function getCanvasContext() {
    if (!canvas) {
        console.error("Canvas element not found");
        return null;
    }
    const ctx = canvas.getContext("2d");
    if (!ctx) {
        console.error("Failed to get canvas context");
        return null;
    }
    return ctx;
}

function updatePrediction() {
    fetch('/predict')
      .then(response => response.json())
      .then(data => {
        const pred = data.result;
        const label = document.getElementById('resultLabel');
        if (pred > 0.9) {
          label.textContent = `🧠 You have brainrot (${pred.toFixed(2)})`;
          label.style.color = "red";
        } else {
          label.textContent = `✅ No brainrot detected (${pred.toFixed(2)})`;
          label.style.color = "green";
        }
      })
      .catch(err => {
        document.getElementById('resultLabel').textContent = "⚠️ Error fetching data";
      });
}

// --- Start Visualizer ---
function startVisualizer() {
    console.log("startVisualizer called");

    const ctx = getCanvasContext();
    if (!ctx) return;

    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
        console.log("Microphone access granted");

        if (!audioCtx) {
            audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        }

        const source = audioCtx.createMediaStreamSource(stream);
        const analyser = audioCtx.createAnalyser();
        source.connect(analyser);
        analyser.fftSize = 256;

        const bufferLength = analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);

        visualizerActive = true;

        function draw() {
            if (!visualizerActive) return;
            requestAnimationFrame(draw);

            analyser.getByteFrequencyData(dataArray);

            ctx.fillStyle = "black";
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            const barWidth = (canvas.width / bufferLength) * 2.5;
            let x = 0;

            for (let i = 0; i < bufferLength; i++) {
                const barHeight = dataArray[i] * 3.0;
                const r = barHeight + 25;
                const g = 250 * (i / bufferLength);
                const b = 50;

                ctx.fillStyle = `rgb(${r},${g},${b})`;
                ctx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);
                x += barWidth + 1;
            }
        }

        draw();
    }).catch(err => {
        console.error("Mic access denied or error:", err);
    });
}

// --- Stop Visualizer ---
function stopVisualizer() {
    console.log("stopVisualizer called");

    const ctx = getCanvasContext();
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    visualizerActive = false;
    console.log("Canvas cleared and visualizer stopped");
}

// --- Setup Event Listeners on DOM Load ---
document.addEventListener("DOMContentLoaded", () => {
    startVisualizerButton?.addEventListener("click", startVisualizer);
    stopVisualizerButton?.addEventListener("click", stopVisualizer);
});

setInterval(updatePrediction, 3000);  // Update every 3 seconds
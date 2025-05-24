const recordButton = document.getElementById("recordButton");
const recordStop = document.getElementById("recordStop");
const muteButton = document.getElementById("muteButton");
const downloadAudio = document.getElementById("downloadAudio");
const errorMessage = document.getElementById("errorMessage");
const canvas = document.getElementById("canvas");
const startVisualizerButton = document.getElementById("startVisualizer");
const stopVisualizerButton = document.getElementById("stopVisualizer");
const resultLabel = document.getElementById("resultLabel");

let controlsMuted = false;
let visualizerActive = false;
let audioCtx = null;
let animationId = null;
let isRecording = false;

const BASE_URL = "http://127.0.0.1:5001";

// --- Recording Start ---
recordButton?.addEventListener("click", async () => {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        stream.getTracks().forEach(track => track.stop());

        const response = await fetch(`${BASE_URL}/run-script`, { method: "POST" });
        if (!response.ok) throw new Error("Failed to start recording script");

        const data = await response.json();
        console.log(data.message);

        isRecording = true;
        resultLabel.innerText = "🎙️ Recording...";
        resultLabel.style.color = "orange";

        alert("Recording Started");
    } catch (error) {
        console.error("Error starting recording:", error);
        errorMessage.innerText = "⚠️ Could not start recording: " + error.message;
    }
});

// --- Recording Stop ---
recordStop?.addEventListener("click", async () => {
    isRecording = false;
    resultLabel.innerText = "🔴 Not recording";
    resultLabel.style.color = "gray";

    try {
        const response = await fetch(`${BASE_URL}/stop`, { method: "POST" });
        if (!response.ok) throw new Error("Failed to stop recording");
        const data = await response.json();
        console.log(data.message);
    } catch (error) {
        console.error("Error stopping recording:", error);
        errorMessage.innerText = "⚠️ " + error.message;
    }
});

// --- Mute / Unmute Controls ---
muteButton?.addEventListener("click", () => {
    controlsMuted = !controlsMuted;
    recordButton.disabled = controlsMuted;
    recordStop.disabled = controlsMuted;
    muteButton.textContent = controlsMuted ? "Unmute" : "Mute";

    [recordButton, recordStop].forEach(btn => {
        btn.style.backgroundColor = controlsMuted ? "#778275" : "#3d7340";
        btn.style.cursor = controlsMuted ? "default" : "pointer";
    });
});

// --- Download Latest Audio ---
downloadAudio?.addEventListener("click", async () => {
    try {
        const response = await fetch(`${BASE_URL}/get-latest-audio`);
        if (!response.ok) throw new Error("No recent audio to download.");

        const { filename } = await response.json();
        const audioResponse = await fetch(`${BASE_URL}/download-audio/${filename}`);
        if (!audioResponse.ok) throw new Error("Audio file not found on server.");

        const blob = await audioResponse.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
    } catch (error) {
        console.error("Download failed:", error);
        errorMessage.innerText = "⚠️ " + error.message;
    }
});

// --- Prediction Polling ---
function updatePrediction() {
    if (!isRecording) return;

    fetch(`${BASE_URL}/predict`)
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                resultLabel.textContent = "⚠️ Error: " + data.error;
                resultLabel.style.color = "gray";
            } else if (data.status === "waiting") {
                resultLabel.textContent = "⏳ Waiting for audio...";
                resultLabel.style.color = "gray";
            } else {
                const score = data.score;
                if (score > 0.9) {
                    resultLabel.textContent = `🧠 You have brainrot (${score.toFixed(2)})`;
                    resultLabel.style.color = "red";
                } else {
                    resultLabel.textContent = `✅ No brainrot detected (${score.toFixed(2)})`;
                    resultLabel.style.color = "green";
                }
            }
        })
        .catch(() => {
            resultLabel.textContent = "⚠️ Error fetching prediction";
            resultLabel.style.color = "gray";
        });
}
setInterval(updatePrediction, 3000);

// --- Visualizer Logic ---
function getCanvasContext() {
    if (!canvas) return null;
    return canvas.getContext("2d");
}

function startVisualizer() {
    const ctx = getCanvasContext();
    if (!ctx) return;

    canvas.width = window.innerWidth;
    canvas.height = 200;

    navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
        audioCtx = audioCtx || new (window.AudioContext || window.webkitAudioContext)();
        const source = audioCtx.createMediaStreamSource(stream);
        const analyser = audioCtx.createAnalyser();
        source.connect(analyser);
        analyser.fftSize = 256;

        const bufferLength = analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        visualizerActive = true;

        function draw() {
            if (!visualizerActive) return cancelAnimationFrame(animationId);
            animationId = requestAnimationFrame(draw);

            analyser.getByteFrequencyData(dataArray);

            ctx.fillStyle = "black";
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            const barWidth = (canvas.width / bufferLength) * 2.5;
            let x = 0;

            for (let i = 0; i < bufferLength; i++) {
                const barHeight = dataArray[i] * 2.0;
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
        console.error("Microphone access error:", err);
        errorMessage.innerText = "Mic access blocked or unavailable.";
    });
}

function stopVisualizer() {
    const ctx = getCanvasContext();
    if (!ctx) return;

    visualizerActive = false;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    cancelAnimationFrame(animationId);
}

// --- DOM Setup ---
document.addEventListener("DOMContentLoaded", () => {
    startVisualizerButton?.addEventListener("click", startVisualizer);
    stopVisualizerButton?.addEventListener("click", stopVisualizer);
});
const recordButton = document.getElementById("recordButton");
const recordStop = document.getElementById("recordStop");
const muteButton = document.getElementById("muteButton");
const downloadAudio = document.getElementById("downloadAudio");
const errorMessage = document.getElementById("errorMessage");
const canvas = document.getElementById("canvas");
const startVisualizerButton = document.getElementById("startVisualizer");
const stopVisualizerButton = document.getElementById("stopVisualizer");
const resultLabel = document.getElementById("resultLabel");
const realtimeStatusLabel = document.getElementById("realtimeStatusLabel");

let controlsMuted = false;
let visualizerActive = false;
let audioCtx = null;
let animationId = null;

const BASE_URL = "";
const WS_URL = "ws://localhost:5001/ws/realtime-predictions";

let mediaRecorder, recordedChunks = [];
let realTimeWebSocket = null;

function updateResultLabel(text, color) {
    resultLabel.textContent = text;
    resultLabel.style.color = color;
}

function updateErrorMessage(text) {
    errorMessage.innerText = text;
}

function updateRealtimeStatus(statusText, statusColor) {
    if (realtimeStatusLabel) {
        realtimeStatusLabel.textContent = `Real-time Analysis: ${statusText}`;
        realtimeStatusLabel.style.color = statusColor;
    }
}

recordButton?.addEventListener("click", async () => {
    try {
        stopRealtimeDetection();
        updateRealtimeStatus("Stopped", "gray");

        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        recordedChunks = [];

        mediaRecorder.ondataavailable = event => {
            if (event.data.size > 0) recordedChunks.push(event.data);
        };

        mediaRecorder.onstop = async () => {
            const blob = new Blob(recordedChunks, { type: "audio/webm" });
            const formData = new FormData();
            formData.append("audio", blob, "recording.webm");

            updateResultLabel("Analyzing...", "orange");

            try {
                const response = await fetch(`${BASE_URL}/upload`, {
                    method: "POST",
                    body: formData
                });

                if (!response.ok) {
                    const text = await response.text();
                    throw new Error(`Server error: ${text}`);
                }

                const data = await response.json();

                if (data.error) {
                    updateResultLabel("⚠️ Error: " + data.error, "gray");
                } else {
                    const { score, label } = data;
                    updateResultLabel(
                        label === "brainrot" ?
                        `🧠 Your brain is ROTTING (${score})` :
                        `✅ No brainrot your good for now... (${score})`,
                        label === "brainrot" ? "red" : "green"
                    );
                }
            } catch (error) {
                updateResultLabel("⚠️ " + error.message, "gray");
                console.error("Upload error:", error);
            }
        };

        mediaRecorder.start();
        updateResultLabel("Recording...", "green");
    } catch (err) {
        console.error("Mic access error:", err);
        updateErrorMessage("Mic access blocked or unavailable.");
    }
});

recordStop?.addEventListener("click", () => {
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
        mediaRecorder.stop();
        updateResultLabel("Analyzing...", "orange");
    }
});

muteButton?.addEventListener("click", () => {
    controlsMuted = !controlsMuted;
    recordButton.disabled = controlsMuted;
    recordStop.disabled = controlsMuted;
    muteButton.textContent = controlsMuted ? "Unmute" : "Mute";

    [recordButton, recordStop].forEach(btn => {
        btn.style.backgroundColor = controlsMuted ? "#778275" : "#3d7340";
        btn.style.cursor = controlsMuted ? "default" : "pointer";
    });

    if (controlsMuted) {
        stopRealtimeDetection();
        stopVisualizer();
        updateRealtimeStatus("Stopped (Muted)", "gray");
    }
});

downloadAudio?.addEventListener("click", async () => {
    try {
        const response = await fetch(`${BASE_URL}/get-latest-audio`);
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Server error getting latest audio: ${errorText}`);
        }

        const { filename } = await response.json();
        if (!filename) {
            throw new Error("No recent audio to download.");
        }

        const audioResponse = await fetch(`${BASE_URL}/download-audio/${filename}`);
        if (!audioResponse.ok) {
            const errorText = await audioResponse.text();
            throw new Error(`Audio file not found on server or download failed: ${errorText}`);
        }

        const blob = await audioResponse.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
        updateErrorMessage("");
    } catch (error) {
        console.error("Download failed:", error);
        updateErrorMessage("⚠️ " + error.message);
    }
});

function getCanvasContext() {
    if (!canvas) return null;
    return canvas.getContext("2d");
}

function startVisualizer() {
    const ctx = getCanvasContext();
    if (!ctx) return;

    canvas.width = window.innerWidth;
    canvas.height = 200;

    if (visualizerActive) return;

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
        updateErrorMessage("");
    }).catch(err => {
        console.error("Microphone access error for visualizer:", err);
        updateErrorMessage("Mic access blocked or unavailable for visualizer.");
        visualizerActive = false;
    });
}

function stopVisualizer() {
    const ctx = getCanvasContext();
    if (!ctx) return;

    if (!visualizerActive) return;

    visualizerActive = false;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    cancelAnimationFrame(animationId);
    if (audioCtx) {
        audioCtx.close().then(() => {
            audioCtx = null;
        });
    }
}

function startRealtimeDetection() {
    if (realTimeWebSocket && realTimeWebSocket.readyState === WebSocket.OPEN) {
        console.log("Real-time detection already active.");
        return;
    }

    updateRealtimeStatus("Connecting...", "orange");
    updateResultLabel("Listening for brainrot...", "purple");

    realTimeWebSocket = new WebSocket(WS_URL);

    realTimeWebSocket.onopen = (event) => {
        console.log("WebSocket opened:", event);
        updateRealtimeStatus("Active", "green");
        updateErrorMessage("");
    };

    realTimeWebSocket.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            if (data.error) {
                updateResultLabel("⚠️ Real-time Error: " + data.error, "gray");
                console.error("Real-time detection error:", data.error);
            } else {
                const { score, label } = data;
                updateResultLabel(
                    label === "brainrot" ?
                    `🧠 LIVE: Brainrot Detected (${score})` :
                    `✅ LIVE: No brainrot (${score})`,
                    label === "brainrot" ? "red" : "green"
                );
            }
        } catch (e) {
            console.error("Failed to parse WebSocket message:", e, event.data);
            updateResultLabel("⚠️ Live Data Error", "gray");
        }
    };

    realTimeWebSocket.onclose = (event) => {
        console.log("WebSocket closed:", event);
        updateRealtimeStatus("Stopped", "gray");
        updateResultLabel("Real-time analysis stopped.", "gray");
        realTimeWebSocket = null;
    };

    realTimeWebSocket.onerror = (error) => {
        console.error("WebSocket error:", error);
        updateRealtimeStatus("Error", "red");
        updateErrorMessage("WebSocket connection error. Check server logs.");
        if (realTimeWebSocket) realTimeWebSocket.close();
    };
}

function stopRealtimeDetection() {
    if (realTimeWebSocket && realTimeWebSocket.readyState === WebSocket.OPEN) {
        console.log("Closing WebSocket for real-time detection.");
        realTimeWebSocket.close();
    } else {
        console.log("Real-time detection not active or already stopped.");
    }
    updateRealtimeStatus("Stopped", "gray");
}

document.addEventListener("DOMContentLoaded", () => {
    startVisualizerButton?.addEventListener("click", () => {
        startVisualizer();
        startRealtimeDetection();
    });
    stopVisualizerButton?.addEventListener("click", () => {
        stopVisualizer();
        stopRealtimeDetection();
    });

    updateRealtimeStatus("Not Started", "gray");
});
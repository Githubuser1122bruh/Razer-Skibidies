const recordButton = document.getElementById("recordButton");
const recordStop = document.getElementById("recordStop");
const muteButton = document.getElementById("muteButton")
const downloadAudio = document.getElementById("downloadAudio")
let isdisabled = false;
const errorMessage = document.getElementById("errorMessage")

recordButton.addEventListener("click", () => {
    alert("Recording Started");

    fetch("http://127.0.0.1:5001/run-script", {
        method: "POST",
    })
    .then(response => {
        if (respond.ok) {
            return response.json();
        } else {
            throw new Error("failed to execute script");
        }
    })
    .then(data => {
        console.log(data.message);
    })
    .catch(error => {
        console.error("error", error);
    });
});

recordStop.addEventListener("click", () => {
    alert("Recording Stopped");

    fetch("http://127.0.0.1:5001/stop-script", {
        method: "POST",
    })
    .then(response => {
        if (response.ok) {
            return response.json();
        } else {
            throw new Error("failed to execute script");
        }
    })
    .then(data => {
        console.log(data.message);
    })
    .catch(error => {
        console.error("error", error);
    });
});

muteButton.addEventListener("click", () => {
    if (!isdisabled) {
        recordButton.setAttribute("disabled", true);
        recordStop.setAttribute("disabled", true);
        muteButton.innerText = "Unmute";
        isdisabled = true;
        console.log("worked2")
        recordStop.style.backgroundColor = "#778275";
        recordButton.style.backgroundColor = "#778275";
        recordStop.style.cursor = "default";
        recordButton.style.cursor = "default";
    } else {
        recordButton.removeAttribute("disabled");
        recordStop.removeAttribute("disabled");
        muteButton.innerText = "Mute";
        isdisabled = false;
        console.log("worked")
        recordButton.style.backgroundColor = "#3d7340";
        recordStop.style.backgroundColor = "#3d7340";
        recordStop.style.cursor = "pointer";
        recordButton.style.cursor = "pointer";
    }
});

downloadAudio.addEventListener("click", () => {
    fetch("/get-latest-audio")
        .then(response => {
            if (response.ok) {
                return response.json();
            } else {
                return response.json().then(data => {
                    throw new Error(data.error);
                });
            }
        })
        .then(data => {
            const filename = data.filename;

            return fetch(`/download-audio/${filename}`);
        })
        .then(response => {
            if (response.ok) {
                return response.blob();
            } else {
                return response.json().then(data => {
                    throw new Error(data.error || "File not found.");
                });
            }
        })
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = "recorded_audio.mp3";
            document.body.appendChild(a);
            a.click();
            a.remove();

            errorMessage.innerText = "";
        })
        .catch(error => {
            console.error("Error downloading file:", error);

            errorMessage.innerText = "Error: " + error.message;
        });
});
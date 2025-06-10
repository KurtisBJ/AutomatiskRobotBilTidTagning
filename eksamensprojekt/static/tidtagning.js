const display = document.getElementById("Display");
let timer = null;
let startTime = 0;
let elapsedtime = 0;
let isRunning = false;

function start() {
    if (!isRunning) {
        startTime = Date.now() - elapsedtime;
        timer = setInterval(update, 10);
        isRunning = true;


        // Send MQTT til HiveMQ
        fetch("/send_mqtt?command=start")
            .then(res => res.json())
            .then(data => console.log("MQTT respons:", data))
            .catch(err => console.error("MQTT fejl:", err));
    }
}

function stop(){
    if(isRunning) {
        clearInterval(timer);
        elapsedtime = Date.now() - startTime
        isRunning = false;

    }
}

function reset(){
    clearInterval(timer);
    startTime = 0;
    elapsedtime = 0;
    isRunning = false;
    display.textContent = "00:00:00";
}

function update() {
    const currentTime = Date.now();
    elapsedtime = currentTime - startTime;


    let minutes = Math.floor((elapsedtime / (1000 * 60)) % 60);
    let seconds = Math.floor((elapsedtime / 1000) % 60);
    let milliseconds = Math.floor((elapsedtime % 1000) / 10);

    minutes = String(minutes).padStart(2, "0");
    seconds = String(seconds).padStart(2, "0");
    milliseconds = String(milliseconds).padStart(2, "0");

    display.textContent = `${minutes}:${seconds}:${milliseconds}`;
}

function Upload() {
    const holdid = document.getElementById("holdid-select").value;

    let minutes = String(Math.floor((elapsedtime / (1000 * 60)) % 60)).padStart(2, "0");
    let seconds = String(Math.floor((elapsedtime / 1000) % 60)).padStart(2, "0");
    let milliseconds = String(Math.floor((elapsedtime % 1000))).padStart(2, "0");

    const tid = `${minutes}:${seconds}:${milliseconds}`;

    // Find nuværende side for at vælge rigtig URL
    let currentPath = window.location.pathname;
    let redirectUrl = "";

    if (currentPath.includes("walltid")) {
        redirectUrl = `/walltid?But=upload&holdid=${encodeURIComponent(holdid)}&tid=${encodeURIComponent(tid)}`;

        // Først upload lab tider
        fetch(`/upload_labtimes?holdid=${encodeURIComponent(holdid)}`, {
        method: "POST"
        })
        .then(res => res.json())
        .then(data => {
            console.log("Upload respons:", data);
            window.location.href = redirectUrl;
        })
        .catch(err => {
            console.error("Fejl ved upload:", err);
            alert("Kunne ikke uploade lab tider!");
        });

    } else if (currentPath.includes("sumotid")) {
        // Ingen lab times her – upload og redirect direkte
        redirectUrl = `/sumotid?But=upload&holdid=${encodeURIComponent(holdid)}&tid=${encodeURIComponent(tid)}`;
        window.location.href = redirectUrl;

    } else {
        console.warn("Ukendt side. ingen upload sker.");
    }

}
// Tjek serverens kommando hvert sekund
setInterval(() => {
    fetch("/get_command")
        .then(res => res.json())
        .then(data => {
            if (data.command === "stop") {
                console.log("Modtog stop-kommando fra server");
                stop();  // Kalder din egen stop-funktion
            }
        })
        .catch(err => console.error("Fejl ved hentning af kommando:", err));
}, 1000); // Tjek hvert sekund






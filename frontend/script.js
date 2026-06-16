const API = "http://127.0.0.1:5000";

let avatarHideTimeout = null;
let currentWord = "";
let voiceBusy = false;

/* COLOR CYCLE INDEX */

let colorIndex = 0;
const avatarColors = ["avatar-high", "avatar-medium", "avatar-low"];

/* RESET UI */

function resetAvatarOverlay() {
  const overlay = document.getElementById("avatarOverlay");
  const avatar = document.getElementById("avatarModel");
  const output = document.getElementById("output");

  if (output) output.innerHTML = "";

  if (overlay) {
    overlay.classList.remove(
      "show",
      "avatar-high",
      "avatar-medium",
      "avatar-low",
    );
    overlay.style.display = "none";
  }

  if (avatar) {
    const src = avatar.getAttribute("src");
    avatar.setAttribute("src", "");
    avatar.setAttribute("src", src);
  }

  if (avatarHideTimeout) {
    clearTimeout(avatarHideTimeout);
    avatarHideTimeout = null;
  }
}

/* TTS */

function speakInBrowser(text) {
  if (!window.speechSynthesis) {
    alert("Speech synthesis not supported");
    return;
  }

  window.speechSynthesis.cancel();

  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = "en-US";
  utterance.rate = 1;
  utterance.pitch = 1;

  window.speechSynthesis.speak(utterance);
}

/* AVATAR */

function showAvatarOverlay(word) {
  const overlay = document.getElementById("avatarOverlay");
  const avatar = document.getElementById("avatarModel");
  const label = document.getElementById("avatarLabel");

  if (!overlay || !avatar || !label) return;

  const cleanWord = word.trim().replace(/\b\w/g, (c) => c.toUpperCase());

  label.textContent = `Showing sign: ${cleanWord}`;

  /* REMOVE OLD COLORS */

  overlay.classList.remove("avatar-high", "avatar-medium", "avatar-low");

  /* APPLY NEXT COLOR IN CYCLE */

  overlay.classList.add(avatarColors[colorIndex]);

  colorIndex = (colorIndex + 1) % avatarColors.length;

  avatar.setAttribute("auto-rotate", true);

  overlay.style.display = "flex";
  setTimeout(() => overlay.classList.add("show"), 10);
}

/* TEXT → SIGN */

function sendText() {
  resetAvatarOverlay();

  const text = document.getElementById("textInput").value;
  if (!text) return;

  currentWord = text;

  fetch(`${API}/text-to-sign`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  })
    .then((res) => res.json())
    .then((data) => {
      const output = document.getElementById("output");

      data.signs.forEach((sign, index) => {
        setTimeout(() => {
          output.innerHTML = "";

          const img = new Image();

          img.src = `${API}/signs/${sign}`;

          img.onload = () => {
            window.scrollTo({
              top: document.body.scrollHeight,
              behavior: "smooth",
            });
          };

          output.appendChild(img);

          showAvatarOverlay(currentWord);
        }, index * 1500);
      });

      const totalDuration = data.signs.length * 1500;

      setTimeout(() => {
        output.innerHTML = "";
      }, totalDuration);

      avatarHideTimeout = setTimeout(() => {
        const overlay = document.getElementById("avatarOverlay");
        if (!overlay) return;

        overlay.classList.remove("show");

        setTimeout(() => {
          overlay.style.display = "none";
          overlay.classList.remove(
            "avatar-high",
            "avatar-medium",
            "avatar-low",
          );
        }, 500);
      }, totalDuration + 300);
    });
}

/* VOICE → TEXT */

async function startVoice() {
  if (voiceBusy) return;

  voiceBusy = true;

  document.getElementById("voiceBtn").disabled = true;
  document.getElementById("listeningIndicator").style.display = "flex";

  document
    .getElementById("listeningIndicator")
    .scrollIntoView({ behavior: "smooth", block: "center" });

  resetAvatarOverlay();

  try {
    let text = "";

    for (let i = 0; i < 2; i++) {
      let res = await fetch(`${API}/speech-to-text`);
      let data = await res.json();

      if (data.text) {
        text = data.text;
        break;
      }

      await new Promise((r) => setTimeout(r, 600));
    }

    if (!text) {
      alert("Voice not detected");
    } else {
      document.getElementById("textInput").value = text;
      sendText();
    }
  } catch (err) {
    console.error(err);
    alert("Microphone error");
  }

  document.getElementById("listeningIndicator").style.display = "none";
  document.getElementById("voiceBtn").disabled = false;

  voiceBusy = false;
}

/* TEXT → VOICE → SIGN */

function textToVoiceAndSign() {
  resetAvatarOverlay();

  const text = document.getElementById("textInput").value;
  if (!text) return;

  speakInBrowser(text);

  sendText();
}

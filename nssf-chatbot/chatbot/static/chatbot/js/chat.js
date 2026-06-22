document.addEventListener("DOMContentLoaded", () => {
    const chatForm = document.getElementById("chatForm");
    const chatBody = document.getElementById("chatBody");
    const chatHistory = document.getElementById("chatHistory");
    const messageInput = document.getElementById("messageInput");
    const sendButton = document.getElementById("sendButton");
    const voiceButton = document.getElementById("voiceButton");
    const voiceFeedbackButton = document.getElementById("voiceFeedbackButton");
    const voiceStatus = document.getElementById("voiceStatus");
    const typingIndicator = document.getElementById("typingIndicator");
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const canSpeak = "speechSynthesis" in window && "SpeechSynthesisUtterance" in window;
    let recognition = null;
    let isListening = false;
    let voiceBaseText = "";
    let voiceFeedbackEnabled = canSpeak;

    function getCurrentTime() {
        return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    }

    function scrollToLatest() {
        requestAnimationFrame(() => {
            chatBody.scrollTop = chatBody.scrollHeight;
        });
    }

    function resizeMessageInput() {
        messageInput.style.height = "auto";
        messageInput.style.height = `${messageInput.scrollHeight}px`;
    }

    function setVoiceStatus(message = "", type = "") {
        voiceStatus.textContent = message;
        voiceStatus.classList.toggle("is-error", type === "error");
        voiceStatus.classList.toggle("is-listening", type === "listening");
    }

    function setVoiceFeedbackEnabled(nextIsEnabled) {
        voiceFeedbackEnabled = canSpeak && nextIsEnabled;
        voiceFeedbackButton.classList.toggle("is-muted", !voiceFeedbackEnabled);
        voiceFeedbackButton.setAttribute("aria-pressed", String(voiceFeedbackEnabled));
        voiceFeedbackButton.setAttribute(
            "aria-label",
            voiceFeedbackEnabled ? "Turn voice feedback off" : "Turn voice feedback on",
        );
        voiceFeedbackButton.querySelector(".btn-icon").textContent = voiceFeedbackEnabled ? "\uD83D\uDD0A" : "\uD83D\uDD07";

        if (!voiceFeedbackEnabled && canSpeak) {
            window.speechSynthesis.cancel();
        }
    }

    function setVoiceListening(nextIsListening) {
        isListening = nextIsListening;
        voiceButton.classList.toggle("is-listening", isListening);
        voiceButton.setAttribute("aria-pressed", String(isListening));
        voiceButton.setAttribute(
            "aria-label",
            isListening ? "Stop voice input" : "Start voice input",
        );
    }

    function updateInputFromVoice(transcript) {
        const separator = voiceBaseText && transcript ? " " : "";
        messageInput.value = `${voiceBaseText}${separator}${transcript}`.trimStart();
        resizeMessageInput();
        messageInput.focus();
    }

    function stopListening() {
        if (recognition && isListening) {
            recognition.stop();
        }
    }

    function speakAssistantResponse(text) {
        if (!voiceFeedbackEnabled || !canSpeak || !text) {
            return;
        }

        window.speechSynthesis.cancel();

        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = "en-US";
        utterance.rate = 0.95;
        utterance.pitch = 1;
        window.speechSynthesis.speak(utterance);
    }

    // Browser Speech Recognition turns microphone audio into text locally in the UI flow.
    // The transcript is inserted into the existing textarea, so backend submission is unchanged.
    function setupSpeechRecognition() {
        if (!SpeechRecognition) {
            voiceButton.disabled = true;
            setVoiceStatus("Voice input is not supported in this browser.", "error");
            return;
        }

        recognition = new SpeechRecognition();
        recognition.lang = "en-US";
        recognition.interimResults = true;
        recognition.continuous = false;

        recognition.addEventListener("start", () => {
            setVoiceListening(true);
            setVoiceStatus("Listening...", "listening");
        });

        recognition.addEventListener("result", (event) => {
            let transcript = "";
            for (let index = event.resultIndex; index < event.results.length; index += 1) {
                transcript += event.results[index][0].transcript;
            }
            updateInputFromVoice(transcript.trim());
        });

        recognition.addEventListener("error", (event) => {
            const permissionErrors = ["not-allowed", "service-not-allowed"];
            const message = permissionErrors.includes(event.error)
                ? "Microphone permission was denied. Allow microphone access and try again."
                : "Voice input could not start. Please try again or type your message.";
            setVoiceStatus(message, "error");
            setVoiceListening(false);
        });

        recognition.addEventListener("end", () => {
            setVoiceListening(false);
            if (!voiceStatus.classList.contains("is-error")) {
                setVoiceStatus(messageInput.value.trim() ? "Voice text added. You can edit or send it." : "");
            }
        });
    }

    function toggleVoiceInput() {
        if (!recognition) {
            setVoiceStatus("Voice input is not supported in this browser.", "error");
            return;
        }

        if (isListening) {
            stopListening();
            return;
        }

        voiceBaseText = messageInput.value.trim();
        setVoiceStatus("");

        try {
            recognition.start();
        } catch (error) {
            setVoiceStatus("Voice input is already starting. Please try again in a moment.", "error");
        }
    }

    function appendMessage(role, content, includeTime = true, shouldSpeak = false) {
        const row = document.createElement("div");
        row.className = `message-row ${role}`;

        const bubble = document.createElement("div");
        bubble.className = "message-bubble";

        const text = document.createElement("div");
        text.className = "message-text";
        text.textContent = content;

        bubble.appendChild(text);

        if (includeTime) {
            const meta = document.createElement("div");
            meta.className = "message-meta";

            const roleLabel = document.createElement("span");
            roleLabel.className = "message-role";
            roleLabel.textContent = role === "user" ? "You" : "NSSF Assistant";

            const timeLabel = document.createElement("span");
            timeLabel.className = "message-time";
            timeLabel.textContent = getCurrentTime();

            meta.appendChild(roleLabel);
            meta.appendChild(timeLabel);
            bubble.appendChild(meta);
        }

        row.appendChild(bubble);
        chatHistory.appendChild(row);
        scrollToLatest();

        if (shouldSpeak && role === "assistant") {
            speakAssistantResponse(content);
        }
    }

    function setLoading(isLoading) {
        sendButton.disabled = isLoading;
        messageInput.disabled = isLoading;
        voiceButton.disabled = isLoading || !recognition;
        typingIndicator.classList.toggle("show", isLoading);
        if (isLoading) {
            scrollToLatest();
        }
    }

    async function sendMessage(message) {
        const formData = new FormData(chatForm);
        formData.set("message", message);

        const response = await fetch(chatForm.action, {
            method: "POST",
            body: formData,
            headers: { "X-Requested-With": "XMLHttpRequest" },
        });

        return response.json().then((data) => ({ status: response.ok, data }));
    }

    chatForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const message = messageInput.value.trim();
        if (!message) {
            messageInput.focus();
            return;
        }

        stopListening();
        appendMessage("user", message);
        messageInput.value = "";
        resizeMessageInput();
        setLoading(true);

        try {
            const { status, data } = await sendMessage(message);

            if (!status) {
                appendMessage("assistant", data.error || "Sorry, I could not process that request.", true, true);
            } else {
                appendMessage("assistant", data.response, true, true);
            }
        } catch (error) {
            appendMessage("assistant", "Network error. Please check your connection and try again.", true, true);
        } finally {
            setLoading(false);
            messageInput.focus();
        }
    });

    messageInput.addEventListener("keydown", (event) => {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            chatForm.requestSubmit();
        }
    });

    messageInput.addEventListener("input", resizeMessageInput);
    voiceButton.addEventListener("click", toggleVoiceInput);
    voiceFeedbackButton.addEventListener("click", () => {
        setVoiceFeedbackEnabled(!voiceFeedbackEnabled);
    });

    if (!canSpeak) {
        voiceFeedbackButton.disabled = true;
        voiceFeedbackButton.setAttribute("aria-label", "Voice feedback is not supported in this browser");
    }

    setVoiceFeedbackEnabled(canSpeak);
    setupSpeechRecognition();
    resizeMessageInput();
    messageInput.focus();
});

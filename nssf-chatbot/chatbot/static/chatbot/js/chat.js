document.addEventListener("DOMContentLoaded", () => {
    const chatForm = document.getElementById("chatForm");
    const chatHistory = document.getElementById("chatHistory");
    const messageInput = document.getElementById("messageInput");
    const sendButton = document.getElementById("sendButton");
    const typingIndicator = document.getElementById("typingIndicator");

    function getCurrentTime() {
        return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    }

    function appendMessage(role, content, includeTime = true) {
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
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    function setLoading(isLoading) {
        sendButton.disabled = isLoading;
        messageInput.disabled = isLoading;
        typingIndicator.classList.toggle("show", isLoading);
        if (isLoading) {
            chatHistory.scrollTop = chatHistory.scrollHeight;
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

        appendMessage("user", message);
        messageInput.value = "";
        setLoading(true);

        try {
            const { status, data } = await sendMessage(message);

            if (!status) {
                appendMessage("assistant", data.error || "Sorry, I could not process that request.");
            } else {
                appendMessage("assistant", data.response);
            }
        } catch (error) {
            appendMessage("assistant", "Network error. Please check your connection and try again.");
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

    messageInput.focus();
});

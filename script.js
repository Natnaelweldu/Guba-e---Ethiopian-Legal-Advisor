const form = document.getElementById("chat-form");
const input = document.getElementById("user-input");
const chatHistory = document.getElementById("chat-history");

// Auto-resize textarea
input.addEventListener("input", function () {
  this.style.height = "auto";
  this.style.height = this.scrollHeight + "px";
});

// Handle Enter key (Shift+Enter for new line)
input.addEventListener("keydown", function (e) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    form.dispatchEvent(new Event("submit"));
  }
});

function appendMessage(role, text, citation = null) {
  const isUser = role === "user";
  const msgDiv = document.createElement("div");
  msgDiv.className = `msg ${isUser ? "outgoing" : "incoming"}`;

  // Avatar
  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = isUser ? "U" : "G";

  // Content Box
  const content = document.createElement("div");
  content.className = "msg-content";
  content.innerHTML = `<p>${text}</p>`;

  // Add Citation if provided (The Legal UI touch)
  if (citation) {
    const citeTag = document.createElement("div");
    citeTag.className = "citation";
    citeTag.innerHTML = `
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path></svg>
            ${citation}
        `;
    content.appendChild(citeTag);
  }

  msgDiv.appendChild(avatar);
  msgDiv.appendChild(content);
  chatHistory.appendChild(msgDiv);

  // Smooth scroll to the bottom of the new message
  msgDiv.scrollIntoView({ behavior: "smooth", block: "end" });
  return content; // Return content block in case we need to update it
}

function showTypingIndicator() {
  const msgDiv = document.createElement("div");
  msgDiv.className = "msg incoming typing-indicator";
  msgDiv.innerHTML = `
        <div class="avatar">G</div>
        <div class="msg-content">
            <div class="typing-pulse"><span></span><span></span><span></span></div>
        </div>
    `;
  chatHistory.appendChild(msgDiv);
  msgDiv.scrollIntoView({ behavior: "smooth", block: "end" });
  return msgDiv;
}

// Form Submission
form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = input.value.trim();
  if (!text) return;

  // Reset input
  input.value = "";
  input.style.height = "auto";
  input.focus();

  // Show User Message
  appendMessage("user", text);

  // Show AI Thinking
  const typingUI = showTypingIndicator();

  // TODO: Connect to your FastAPI Backend here
  // Mocking a network delay for the animation
  setTimeout(() => {
    typingUI.remove(); // Remove thinking dots

    // Mocking Guba'e's response with a citation
    const mockResponse =
      "Under Ethiopian law, a contract of employment is formed when a person agrees to render services to an employer under the latter's direction in return for remuneration.";
    const mockCitation = "Labour Proclamation No. 1156/2019, Art. 4(1)";

    appendMessage("assistant", mockResponse, mockCitation);
  }, 1500);
});

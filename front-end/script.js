const form = document.getElementById("chat-form");
const input = document.getElementById("user-input");
const chatHistory = document.getElementById("chat-history");

// --- UI UTILITIES ---

const updateTextareaHeight = (el) => {
    el.style.height = "auto";
    el.style.height = el.scrollHeight + "px";
};

input.addEventListener("input", function () { updateTextareaHeight(this); });

input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        form.requestSubmit(); 
    }
});

/**
 * Appends a message to the UI.
 * citation is expected to be a formatted string.
 */
function appendMessage(role, text, citation = null, isError = false) {
    const isUser = role === "user";
    const msgDiv = document.createElement("div");
    msgDiv.className = `msg ${isUser ? "outgoing" : "incoming"} ${isError ? "error-msg" : ""}`;

    const avatar = document.createElement("div");
    avatar.className = "avatar";
    avatar.textContent = isUser ? "U" : "G";

    const content = document.createElement("div");
    content.className = "msg-content";
    content.innerHTML = `<p>${text}</p>`;

    if (citation && citation.trim() !== "") {
        const citeTag = document.createElement("div");
        citeTag.className = "citation";
        citeTag.innerHTML = `
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path>
                <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>
            </svg>
            <span>Source: ${citation}</span>
        `;
        content.appendChild(citeTag);
    }

    msgDiv.appendChild(avatar);
    msgDiv.appendChild(content);
    chatHistory.appendChild(msgDiv);

    msgDiv.scrollIntoView({ behavior: "smooth", block: "end" });
    return content;
}

function toggleTypingIndicator(show = true) {
    const existing = document.querySelector(".typing-indicator");
    if (!show && existing) return existing.remove();
    if (show && !existing) {
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
    }
}

// --- BACKEND INTEGRATION ---

async function fetchGubaeResponse(userPrompt) {
    const API_URL = "http://localhost:8000/chat"; 
    
    try {
        const response = await fetch(API_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query: userPrompt }),
        });

        if (!response.ok) throw new Error("Failed to connect to Guba'e engine.");
        
        const data = await response.json();
        
        // CRITICAL: Return the whole object { answer, citation } 
        // so the caller can access both.
        return data; 

    } catch (err) {
        console.error("RAG Error:", err);
        return { error: true, message: err.message };
    }
}

// --- MAIN EVENT HANDLER ---

form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const query = input.value.trim();
    if (!query) return;

    // UI Reset
    input.value = "";
    updateTextareaHeight(input);
    appendMessage("user", query);
    
    toggleTypingIndicator(true);

    // Call Backend
    const result = await fetchGubaeResponse(query);
    
    toggleTypingIndicator(false);

    if (result.error) {
        appendMessage("assistant", `⚠️ Error: ${result.message}`, null, true);
    } else {
        // 1. Extract the answer
        const textAnswer = result.answer || "I'm sorry, I couldn't find a specific answer.";

        // 2. Format citations from list to string
        let formattedCitations = "";
        if (result.citation && Array.isArray(result.citation) && result.citation.length > 0) {
            formattedCitations = result.citation
                .map(c => `${c.source} (Page ${c.page_num})`)
                .join(", ");
        }

        // 3. Render to UI
        appendMessage("assistant", textAnswer, formattedCitations);
    }
});
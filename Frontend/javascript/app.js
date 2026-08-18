// ============================
// HTML elements
// ============================

const conversation = document.getElementById("conversation");
const messageInput = document.getElementById("messageInput");
const sendButton = document.getElementById("sendButton");
const newChatButton = document.getElementById("newChatButton");
const clearChatButton = document.getElementById("clearChatButton");
const chatList = document.getElementById("chatList");
const chatTitle = document.getElementById("chatTitle");
const status = document.getElementById("status");

let isGenerating = false;


// ============================
// Browser conversation storage
// ============================

// Load previous chats from localStorage.
// If none exist, begin with an empty list.
let chats = JSON.parse(localStorage.getItem("aiChats")) || [];

// ID of the chat currently open.
let sessionId = null;


// Save all chats into the browser.
function saveChats() {
    localStorage.setItem("aiChats", JSON.stringify(chats));
}


// Find the currently selected chat.
function getCurrentChat() {
    return chats.find(chat => chat.id === sessionId);
}


// ============================
// Create and load chats
// ============================

function createNewChat() {
    const newChat = {
        id: crypto.randomUUID(),
        title: "New Chat",
        messages: []
    };

    // Put newest chats first.
    chats.unshift(newChat);

    sessionId = newChat.id;

    saveChats();
    renderChatList();
    loadChat(sessionId);

    messageInput.focus();
}


function loadChat(chatId) {
    const selectedChat = chats.find(chat => chat.id === chatId);

    if (!selectedChat) {
        return;
    }

    sessionId = selectedChat.id;
    chatTitle.textContent = selectedChat.title;

    // Remove currently displayed messages.
    conversation.innerHTML = "";

    // Display this saved chat's messages.
    selectedChat.messages.forEach(message => {
        addMessage(message.role, message.content, false);
    });

    status.textContent = "";
    renderChatList();

    conversation.scrollTop = conversation.scrollHeight;
}


// Display every saved chat in the sidebar.
function renderChatList() {
    chatList.innerHTML = "";

    chats.forEach(chat => {
        const chatButton = document.createElement("button");

        chatButton.className = "chat-item";
        chatButton.textContent = chat.title;

        if (chat.id === sessionId) {
            chatButton.classList.add("active");
        }

        chatButton.addEventListener("click", () => {
            loadChat(chat.id);
        });

        chatList.appendChild(chatButton);
    });
}


// ============================
// Message display and storage
// ============================

function addMessage(role, content, shouldSave = true) {
    const messageElement = document.createElement("div");

    messageElement.className = `message ${role}`;
    messageElement.textContent = content;

    conversation.appendChild(messageElement);
    conversation.scrollTop = conversation.scrollHeight;

    if (shouldSave) {
        const currentChat = getCurrentChat();

        currentChat.messages.push({
            role: role,
            content: content
        });

        // Use the first user message as the chat name.
        if (
            role === "user" &&
            currentChat.title === "New Chat"
        ) {
            currentChat.title =
                content.length > 28
                    ? content.slice(0, 28) + "..."
                    : content;

            chatTitle.textContent = currentChat.title;
        }

        saveChats();
        renderChatList();
    }

    return messageElement;
}


// Typing animation.
// This is visual typing, not true API token streaming.
async function typeAssistantMessage(content) {
    const messageElement = document.createElement("div");

    messageElement.className = "message assistant";
    messageElement.textContent = "";

    conversation.appendChild(messageElement);

    for (const character of content) {
        messageElement.textContent += character;
        conversation.scrollTop = conversation.scrollHeight;

        await new Promise(resolve =>
            setTimeout(resolve, 8)
        );
    }

    // Save the complete assistant message after typing finishes.
    const currentChat = getCurrentChat();

    currentChat.messages.push({
        role: "assistant",
        content: content
    });

    saveChats();
}


// ============================
// Send message to Flask
// ============================

async function sendMessage() {
    const message = messageInput.value.trim();

    if (!message) {
        status.textContent = "Please enter a message.";
        status.className = "error";
        return;
    }

    if (isGenerating) {
        return;
    }

    isGenerating = true;

    sendButton.disabled = true;
    messageInput.disabled = true;

    status.textContent = "Generating response...";
    status.className = "";

    addMessage("user", message);

    messageInput.value = "";

    try {
        const response = await fetch("/api/chat", {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                message: message,
                session_id: sessionId
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.error || "Request failed."
            );
        }

        status.textContent = "";

        await typeAssistantMessage(data.reply);

    } catch (error) {
        status.textContent = error.message;
        status.className = "error";

    } finally {
        isGenerating = false;

        sendButton.disabled = false;
        messageInput.disabled = false;

        messageInput.focus();
    }
}


// ============================
// Clear current chat
// ============================

async function clearCurrentChat() {
    if (!sessionId) {
        return;
    }

    try {
        await fetch(`/api/chat/${sessionId}`, {
            method: "DELETE"
        });
    } catch (error) {
        console.error("Backend clear error:", error);
    }

    const currentChat = getCurrentChat();

    currentChat.messages = [];
    currentChat.title = "New Chat";

    saveChats();
    loadChat(sessionId);
}


// ============================
// Buttons and keyboard
// ============================

sendButton.addEventListener("click", sendMessage);

messageInput.addEventListener("keydown", event => {
    if (event.key === "Enter") {
        sendMessage();
    }
});

newChatButton.addEventListener("click", createNewChat);
clearChatButton.addEventListener("click", clearCurrentChat);


// ============================
// Initial page setup
// ============================

// If saved chats exist, open the newest one.
// Otherwise create the first chat.
if (chats.length > 0) {
    loadChat(chats[0].id);
} else {
    createNewChat();
}
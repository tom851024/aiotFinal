const chatContainer = document.getElementById('chat-container');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');

let isProcessing = false;

// Initialize Markdown
marked.setOptions({
    breaks: true,
    gfm: true
});

function addMessage(role, text) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${role}`;

    const avatarDiv = document.createElement('div');
    avatarDiv.className = `avatar ${role}`;

    if (role === 'ai') {
        avatarDiv.innerHTML = `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 2a10 10 0 0 1 10 10c0 5.523-4.477 10-10 10S2 17.523 2 12 6.477 2 12 2z"/>
                <path d="M12 16v-4"/>
                <path d="M12 8h.01"/>
            </svg>
        `;
    } else {
        avatarDiv.textContent = 'You';
    }

    const contentDiv = document.createElement('div');
    contentDiv.className = 'content';

    // Render Markdown for AI, plain text for User (to preserve input format)
    if (role === 'ai') {
        contentDiv.innerHTML = marked.parse(text);
    } else {
        contentDiv.textContent = text;
    }

    msgDiv.appendChild(avatarDiv);
    msgDiv.appendChild(contentDiv);
    chatContainer.appendChild(msgDiv);

    // Scroll to bottom
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function addLoading() {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message ai loading';
    msgDiv.id = 'loading-msg';

    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'avatar ai';
    avatarDiv.innerHTML = `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2a10 10 0 0 1 10 10c0 5.523-4.477 10-10 10S2 17.523 2 12 6.477 2 12 2z"/>
            <path d="M12 16v-4"/>
            <path d="M12 8h.01"/>
        </svg>
    `;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'content';
    contentDiv.innerHTML = `
        <div class="dot"></div>
        <div class="dot"></div>
        <div class="dot"></div>
    `;

    msgDiv.appendChild(avatarDiv);
    msgDiv.appendChild(contentDiv);
    chatContainer.appendChild(msgDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function removeLoading() {
    const loadingMsg = document.getElementById('loading-msg');
    if (loadingMsg) {
        loadingMsg.remove();
    }
}

async function fetchNews() {
    addLoading();
    try {
        const response = await fetch('http://127.0.0.1:5000/api/briefing');
        const data = await response.json();

        let welcomeMsg = "## 📰 每日新聞快訊\n\n";

        if (data.categories && data.categories.length > 0) {
            data.categories.forEach(category => {
                welcomeMsg += `### 📂 ${category.name}\n`;
                category.articles.forEach(article => {
                    welcomeMsg += `*   **${article.zh_title}**\n    ${article.takeaway}\n`;
                });
                welcomeMsg += "\n";
            });
        } else {
            welcomeMsg += "目前沒有新聞摘要，請確認後端是否已執行資料匯入。\n";
        }

        welcomeMsg += "---\n\n**想了解更多細節嗎？** 請直接輸入問題，我會根據新聞內文回答您。";

        removeLoading();
        addMessage('ai', welcomeMsg);
    } catch (error) {
        console.error('Error:', error);
        removeLoading();
        addMessage('ai', '抱歉，無法取得新聞快訊。請確認後端伺服器已啟動。');
    }
}

async function sendMessage() {
    const text = userInput.value.trim();
    if (!text || isProcessing) return;

    isProcessing = true;
    userInput.value = '';
    sendBtn.disabled = true;

    addMessage('user', text);
    addLoading();

    try {
        const response = await fetch('http://127.0.0.1:5000/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: text })
        });
        const data = await response.json();

        removeLoading();
        addMessage('ai', data.response);
    } catch (error) {
        console.error('Error:', error);
        removeLoading();
        addMessage('ai', '抱歉，發生錯誤，請稍後再試。');
    } finally {
        isProcessing = false;
        sendBtn.disabled = false;
        userInput.focus();
    }
}

// Event Listeners
sendBtn.addEventListener('click', sendMessage);

userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

// Init
fetchNews();

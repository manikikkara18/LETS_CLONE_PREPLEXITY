// Initialize Lucide icons
lucide.createIcons();

// Sidebar Toggling
const sidebarToggle = document.querySelector('.sidebar-toggle');
const sidebar = document.querySelector('.sidebar');
const appContainer = document.querySelector('.app-container');

if (sidebarToggle) {
    sidebarToggle.addEventListener('click', () => {
        sidebar.classList.toggle('open');
        
        // On desktop, we might want to collapse instead of hide
        if (window.innerWidth > 768) {
            if (sidebar.style.display === 'none') {
                sidebar.style.display = 'flex';
                appContainer.style.setProperty('--sidebar-width', '240px');
            } else {
                sidebar.style.display = 'none';
                appContainer.style.setProperty('--sidebar-width', '0px');
            }
        }
    });
}

// Chat Integration Logic
const chatInput = document.getElementById('chatInput');
const sendBtn = document.getElementById('sendBtn');
const chatResponse = document.getElementById('chatResponse');
const responseText = document.getElementById('responseText');
const heroDashboard = document.getElementById('heroDashboard');
const searchWrapper = document.getElementById('searchWrapper');

// File Upload Elements
const attachBtn = document.getElementById('attachBtn');
const fileInput = document.getElementById('fileInput');
const filePreview = document.getElementById('filePreview');
const fileName = document.getElementById('fileName');
const removeFile = document.getElementById('removeFile');

let selectedFile = null;

// Auto-resize textarea
if (chatInput) {
    chatInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
        
        if (this.value.trim().length > 0) {
            sendBtn.classList.add('active');
        } else {
            sendBtn.classList.remove('active');
        }
    });
}

async function sendChat() {
    const message = chatInput.value.trim();
    if (!message && !selectedFile) return;

    // Show loading state
    console.log("Sending to Perplexity backend:", message);
    chatInput.disabled = true;
    sendBtn.classList.remove('active');
    
    // UI Transitions on first search
    if (heroDashboard) {
        heroDashboard.style.display = 'none';
    }
    if (searchWrapper) {
        searchWrapper.classList.remove('landing-mode');
        searchWrapper.classList.add('chat-mode');
    }
    
    // Ensure response area is visible and reset
    chatResponse.style.display = 'block';
    responseText.innerHTML = '<span style="opacity: 0.5;">Analyzing your request...</span>';

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 120000); // Increased to 120s timeout

    try {
        let file_uri = null;
        let file_mime = null;
        
        // 1. Upload file if selected
        if (selectedFile) {
            console.log("Uploading file first...");
            const formData = new FormData();
            formData.append('file', selectedFile);
            
            const uploadResponse = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            
            const uploadData = await uploadResponse.json();
            if (uploadData.status === 'success') {
                file_uri = uploadData.file_uri;
                file_mime = uploadData.mime_type;
            } else {
                throw new Error(uploadData.error || "File upload failed.");
            }
        }

        // 2. Send Chat with optional file_uri
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                message: message,
                file_uri: file_uri,
                file_mime: file_mime
            }),
            signal: controller.signal
        });

        clearTimeout(timeoutId);
        const data = await response.json();
        
        if (data.status === 'success') {
            // Simple markdown-to-html like formatting for newlines
            responseText.innerText = data.response;
        } else {
            responseText.innerHTML = '<span style="color: #ed4245;">Error: ' + (data.error || "Could not generate response.") + '</span>';
        }
    } catch (error) {
        if (error.name === 'AbortError') {
            responseText.innerText = "Error: Request timed out. Gemini is taking too long to respond.";
        } else {
            console.error("Error:", error);
            responseText.innerText = "Error: " + (error.message || "Could not reach the backend.");
        }
    } finally {
        chatInput.disabled = false;
        chatInput.value = '';
        chatInput.style.height = 'auto';
        
        // Reset file state
        selectedFile = null;
        filePreview.style.display = 'none';
        fileInput.value = '';
        
        // Scroll to response
        chatResponse.scrollIntoView({ behavior: 'smooth' });
    }
}

// File Selection Handlers
if (attachBtn) {
    attachBtn.addEventListener('click', () => fileInput.click());
}

if (fileInput) {
    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            selectedFile = file;
            fileName.innerText = file.name;
            filePreview.style.display = 'flex';
            sendBtn.classList.add('active');
            lucide.createIcons();
        }
    });
}

if (removeFile) {
    removeFile.addEventListener('click', () => {
        selectedFile = null;
        filePreview.style.display = 'none';
        fileInput.value = '';
        if (chatInput.value.trim().length === 0) {
            sendBtn.classList.remove('active');
        }
    });
}

// Event Listeners
if (chatInput) {
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendChat();
        }
    });
}

if (sendBtn) {
    sendBtn.addEventListener('click', () => {
        sendChat();
    });
}

// Suggestions click handler
document.querySelectorAll('.suggestion-card').forEach(card => {
    card.addEventListener('click', () => {
        const text = card.querySelector('span').innerText;
        chatInput.value = text;
        chatInput.dispatchEvent(new Event('input'));
        sendChat();
    });
});

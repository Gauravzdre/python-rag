/**
 * RAG Chatbot Widget - Embeddable JavaScript
 * Add this script to any website to embed the RAG chatbot
 * 
 * Usage:
 * <script src="https://your-domain.com/rag-widget.js" 
 *         data-api-url="http://localhost:8000" 
 *         data-tenant-id="your-tenant-id">
 * </script>
 */

(function() {
    'use strict';

    // Configuration from script tag attributes
    const script = document.currentScript;
    const config = {
        apiUrl: script.getAttribute('data-api-url') || 'http://localhost:8000',
        tenantId: script.getAttribute('data-tenant-id') || 'default',
        apiKey: script.getAttribute('data-api-key') || null,
        position: script.getAttribute('data-position') || 'bottom-right',
        theme: script.getAttribute('data-theme') || 'default',
        title: script.getAttribute('data-title') || 'AI Assistant'
    };

    // Create widget HTML
    function createWidgetHTML() {
        return `
            <div id="rag-chatbot-widget" style="
                position: fixed;
                bottom: 20px;
                right: 20px;
                width: 350px;
                height: 500px;
                background: white;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                z-index: 10000;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                display: none;
                flex-direction: column;
                overflow: hidden;
            ">
                <div style="
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 15px 20px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    cursor: pointer;
                " onclick="ragToggleWidget()">
                    <h3 style="margin: 0; font-size: 16px; font-weight: 600;">${config.title}</h3>
                    <button onclick="ragToggleWidget()" style="
                        background: none;
                        border: none;
                        color: white;
                        font-size: 20px;
                        cursor: pointer;
                        padding: 0;
                        width: 24px;
                        height: 24px;
                    ">×</button>
                </div>
                
                <div style="
                    flex: 1;
                    display: flex;
                    flex-direction: column;
                    background: #f8f9fa;
                ">
                    <div id="rag-messages" style="
                        flex: 1;
                        padding: 20px;
                        overflow-y: auto;
                        max-height: 350px;
                    ">
                        <div style="
                            margin-bottom: 15px;
                            padding: 12px 16px;
                            border-radius: 18px;
                            background: #fff3cd;
                            color: #856404;
                            margin: 0 auto;
                            text-align: center;
                            font-size: 12px;
                            border: 1px solid #ffeaa7;
                        ">👋 Hi! I'm your AI assistant. How can I help you today?</div>
                    </div>
                    
                    <div id="rag-loading" style="
                        display: none;
                        text-align: center;
                        padding: 20px;
                        color: #6c757d;
                    ">🤔 Thinking...</div>
                    
                    <div style="
                        padding: 15px 20px;
                        background: white;
                        border-top: 1px solid #e9ecef;
                        display: flex;
                        gap: 10px;
                    ">
                        <input id="rag-input" type="text" placeholder="Type your message..." style="
                            flex: 1;
                            padding: 12px 16px;
                            border: 1px solid #ddd;
                            border-radius: 25px;
                            font-size: 14px;
                            outline: none;
                        " onkeypress="ragHandleKeyPress(event)">
                        <button onclick="ragSendMessage()" style="
                            background: #007bff;
                            color: white;
                            border: none;
                            border-radius: 50%;
                            width: 40px;
                            height: 40px;
                            cursor: pointer;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            font-size: 16px;
                        ">➤</button>
                    </div>
                </div>
            </div>
            
            <button id="rag-toggle-btn" onclick="ragToggleWidget()" style="
                position: fixed;
                bottom: 20px;
                right: 20px;
                width: 60px;
                height: 60px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border: none;
                border-radius: 50%;
                color: white;
                font-size: 24px;
                cursor: pointer;
                z-index: 10001;
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            ">💬</button>
        `;
    }

    // Widget state
    let isOpen = false;
    let messages = [];
    let authToken = null;

    // Initialize widget
    async function initWidget() {
        try {
            if (config.apiKey) {
                // Use the provided API key directly
                authToken = config.apiKey;
                console.log('RAG Widget: Using provided API key');
            } else {
                // Try to get embed token (public endpoint)
                const response = await fetch(`${config.apiUrl}/embed-token`);
                if (response.ok) {
                    const data = await response.json();
                    authToken = data.token;
                    console.log('RAG Widget: Connected with embed token');
                } else {
                    console.error('RAG Widget: Failed to get embed token');
                }
            }
        } catch (error) {
            console.error('RAG Widget: Connection error:', error);
        }
    }

    // Toggle widget
    window.ragToggleWidget = function() {
        const widget = document.getElementById('rag-chatbot-widget');
        const toggle = document.getElementById('rag-toggle-btn');
        
        isOpen = !isOpen;
        
        if (isOpen) {
            widget.style.display = 'flex';
            toggle.style.display = 'none';
            document.getElementById('rag-input').focus();
        } else {
            widget.style.display = 'none';
            toggle.style.display = 'block';
        }
    };

    // Add message
    function addMessage(type, content) {
        const messagesContainer = document.getElementById('rag-messages');
        const messageDiv = document.createElement('div');
        
        let style = `
            margin-bottom: 15px;
            padding: 12px 16px;
            border-radius: 18px;
            max-width: 80%;
            word-wrap: break-word;
            font-size: 14px;
            line-height: 1.4;
        `;
        
        if (type === 'user') {
            style += `
                background: #007bff;
                color: white;
                margin-left: auto;
                text-align: right;
            `;
        } else if (type === 'assistant') {
            style += `
                background: white;
                color: #333;
                margin-right: auto;
                border: 1px solid #e9ecef;
            `;
        } else {
            style += `
                background: #fff3cd;
                color: #856404;
                margin: 0 auto;
                text-align: center;
                font-size: 12px;
                border: 1px solid #ffeaa7;
            `;
        }
        
        messageDiv.style.cssText = style;
        messageDiv.textContent = content;
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        // Store message
        messages.push({ type, content, timestamp: new Date() });
    }

    // Send message
    window.ragSendMessage = async function() {
        const input = document.getElementById('rag-input');
        const message = input.value.trim();
        
        if (!message || !authToken) return;
        
        // Add user message
        addMessage('user', message);
        input.value = '';
        
        // Show loading
        const loading = document.getElementById('rag-loading');
        const sendButton = document.querySelector('button[onclick="ragSendMessage()"]');
        
        loading.style.display = 'block';
        sendButton.disabled = true;
        
        try {
            // Try authenticated endpoint first if we have an API key
            let response;
            if (authToken && authToken.startsWith('mt_')) {
                response = await fetch(`${config.apiUrl}/query/tenant`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${authToken}`
                    },
                    body: JSON.stringify({
                        query: message,
                        tenant_id: config.tenantId
                    })
                });
            } else {
                // Fallback to embed endpoint
                response = await fetch(`${config.apiUrl}/embed/query`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        query: message,
                        tenant_id: config.tenantId
                    })
                });
            }
            
            if (response.ok) {
                const result = await response.json();
                addMessage('assistant', result.answer);
                
                if (result.sources && result.sources.length > 0) {
                    const sources = result.sources.map(s => s.source).join(', ');
                    addMessage('system', `📚 Sources: ${sources}`);
                }
            } else {
                addMessage('assistant', 'Sorry, I encountered an error. Please try again.');
            }
        } catch (error) {
            console.error('RAG Widget: Send error:', error);
            addMessage('assistant', 'Sorry, I\'m having trouble connecting. Please try again later.');
        } finally {
            loading.style.display = 'none';
            sendButton.disabled = false;
            input.focus();
        }
    };

    // Handle Enter key
    window.ragHandleKeyPress = function(event) {
        if (event.key === 'Enter') {
            ragSendMessage();
        }
    };

    // Initialize when DOM is ready
    function initialize() {
        // Add widget HTML to page
        document.body.insertAdjacentHTML('beforeend', createWidgetHTML());
        
        // Initialize connection
        initWidget();
    }

    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initialize);
    } else {
        initialize();
    }

})();

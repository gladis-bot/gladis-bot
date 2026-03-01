(function() {
    if (window.__GLADIS_CHAT_LOADED) return;
    window.__GLADIS_CHAT_LOADED = true;
    
    // Ждем полной загрузки страницы, включая все скрипты
    function initWhenReady() {
        // Даем время сайту загрузить свои скрипты (даже если они с ошибками)
        setTimeout(initWidget, 1500); // Задержка 1.5 секунды
    }
    
    if (document.readyState === 'complete') {
        initWhenReady();
    } else {
        window.addEventListener('load', initWhenReady);
        // Запасной вариант
        document.addEventListener('DOMContentLoaded', initWhenReady);
    }
    
    function initWidget() {
        // Проверяем, не сломана ли страница
        try {
            // Проверяем, работает ли document.body
            if (!document.body) {
                setTimeout(initWidget, 500);
                return;
            }
            
            // Создаем элементы с защитой от ошибок
            createChatElements();
            
        } catch (e) {
            console.error('GLADIS Chat init error:', e);
            // Пробуем еще раз через секунду
            setTimeout(initWidget, 1000);
        }
    }
    
    function createChatElements() {
        // Проверяем, не создан ли уже чат
        if (document.getElementById('gladis-chat-icon')) return;
        
        // Создаем иконку
        const chatIcon = document.createElement('div');
        chatIcon.id = 'gladis-chat-icon';
        chatIcon.innerHTML = `<svg width="30" height="30" viewBox="0 0 24 24" fill="white"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/></svg>`;
        
        // Стили с защитой от переопределения
        chatIcon.style.cssText = `
            position: fixed !important;
            bottom: 25px !important;
            right: 25px !important;
            width: 60px !important;
            height: 60px !important;
            border-radius: 50% !important;
            background: linear-gradient(135deg, #2ecc71, #27ae60) !important;
            color: white !important;
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
            cursor: pointer !important;
            z-index: 999999 !important;
            box-shadow: 0 4px 12px rgba(46, 204, 113, 0.3) !important;
            transition: all 0.3s ease !important;
            pointer-events: auto !important;
        `;
        
        // Создаем окно чата (скрытое)
        const chatWindow = document.createElement('div');
        chatWindow.id = 'gladis-chat-window';
        chatWindow.style.cssText = `
            position: fixed !important;
            bottom: 100px !important;
            right: 20px !important;
            width: 350px !important;
            height: 500px !important;
            background: white !important;
            border: 1px solid #e0e0e0 !important;
            border-radius: 15px !important;
            display: none !important;
            flex-direction: column !important;
            z-index: 999998 !important;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15) !important;
            overflow: hidden !important;
            font-family: Arial, sans-serif !important;
            pointer-events: auto !important;
        `;
        
        // Добавляем на страницу
        document.body.appendChild(chatIcon);
        document.body.appendChild(chatWindow);
        
        // Добавляем остальной контент чата
        setupChatContent(chatWindow, chatIcon);
    }
    
    function setupChatContent(chatWindow, chatIcon) {
        // Заголовок
        const header = document.createElement('div');
        header.style.cssText = `
            background: linear-gradient(135deg, #2ecc71, #27ae60) !important;
            color: white !important;
            padding: 15px !important;
            font-weight: bold !important;
            font-size: 16px !important;
            display: flex !important;
            align-items: center !important;
            font-family: Arial, sans-serif !important;
            position: relative !important;
        `;
        header.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="white" style="margin-right: 10px;">
                <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/>
            </svg>
            Консультация GLADIS
        `;
        
        // Кнопка закрытия
        const closeBtn = document.createElement('span');
        closeBtn.innerHTML = '×';
        closeBtn.style.cssText = `
            position: absolute !important;
            top: 10px !important;
            right: 15px !important;
            color: white !important;
            cursor: pointer !important;
            font-size: 24px !important;
            font-weight: normal !important;
            opacity: 0.8 !important;
            transition: opacity 0.3s !important;
            font-family: Arial, sans-serif !important;
        `;
        closeBtn.onmouseover = () => closeBtn.style.opacity = '1';
        closeBtn.onmouseout = () => closeBtn.style.opacity = '0.8';
        header.appendChild(closeBtn);
        
        // Область сообщений
        const chatArea = document.createElement('div');
        chatArea.style.cssText = `
            flex: 1 !important;
            padding: 15px !important;
            overflow-y: auto !important;
            background-color: #f9f9f9 !important;
            font-size: 14px !important;
            line-height: 1.5 !important;
            font-family: Arial, sans-serif !important;
        `;
        chatArea.innerHTML = `
            <div style="background: #e8f5e9; padding: 10px 15px; border-radius: 15px 15px 15px 5px; margin-bottom: 10px; max-width: 80%;">
                <div style="font-weight: bold; color: #27ae60; margin-bottom: 5px;">GLADIS Бот</div>
                Здравствуйте! Я помогу подобрать процедуру и запишу на консультацию. Чем могу помочь?
            </div>
        `;
        
        // Поле ввода
        const inputContainer = document.createElement('div');
        inputContainer.style.cssText = `
            display: flex !important;
            border-top: 1px solid #e0e0e0 !important;
            padding: 10px !important;
            background: white !important;
            font-family: Arial, sans-serif !important;
        `;
        
        const input = document.createElement('input');
        input.placeholder = 'Напишите ваш вопрос...';
        input.style.cssText = `
            border: none !important;
            flex: 1 !important;
            padding: 12px 15px !important;
            outline: none !important;
            font-size: 14px !important;
            border-radius: 25px !important;
            background-color: #f5f5f5 !important;
            font-family: Arial, sans-serif !important;
        `;
        
        const sendBtn = document.createElement('button');
        sendBtn.innerHTML = '➤';
        sendBtn.style.cssText = `
            background: #2ecc71 !important;
            color: white !important;
            border: none !important;
            border-radius: 50% !important;
            width: 40px !important;
            height: 40px !important;
            margin-left: 10px !important;
            cursor: pointer !important;
            font-size: 16px !important;
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
            transition: background 0.3s !important;
            font-family: Arial, sans-serif !important;
        `;
        sendBtn.onmouseover = () => sendBtn.style.background = '#27ae60';
        sendBtn.onmouseout = () => sendBtn.style.background = '#2ecc71';
        
        inputContainer.appendChild(input);
        inputContainer.appendChild(sendBtn);
        
        // Собираем окно чата
        chatWindow.appendChild(header);
        chatWindow.appendChild(chatArea);
        chatWindow.appendChild(inputContainer);
        
        // Логика открытия/закрытия
        let isChatOpen = false;
        
        function toggleChat(e) {
            e.stopPropagation();
            isChatOpen = !isChatOpen;
            chatWindow.style.display = isChatOpen ? 'flex' : 'none';
            if (isChatOpen) setTimeout(() => input.focus(), 100);
        }
        
        chatIcon.onclick = toggleChat;
        closeBtn.onclick = toggleChat;
        
        // Функция отправки сообщения
        async function sendMessage() {
            const message = input.value.trim();
            if (!message) return;
            
            // Добавляем сообщение пользователя
            chatArea.innerHTML += `
                <div style="text-align: right; margin-bottom: 10px;">
                    <div style="background: #2ecc71; color: white; padding: 10px 15px; border-radius: 15px 15px 5px 15px; display: inline-block; max-width: 80%;">
                        ${escapeHtml(message)}
                    </div>
                </div>
            `;
            
            input.value = '';
            chatArea.scrollTop = chatArea.scrollHeight;
            
            // Индикатор загрузки
            const loadingId = 'loading-' + Date.now();
            chatArea.innerHTML += `
                <div id="${loadingId}" style="background: #e8f5e9; padding: 10px 15px; border-radius: 15px 15px 15px 5px; margin-bottom: 10px; max-width: 80%;">
                    <div style="font-weight: bold; color: #27ae60; margin-bottom: 5px;">GLADIS Бот</div>
                    <div style="display: flex; align-items: center;">
                        <div class="typing-indicator">
                            <span></span>
                            <span></span>
                            <span></span>
                        </div>
                    </div>
                </div>
            `;
            
            // Добавляем стили для индикатора печати
            if (!document.getElementById('typing-styles')) {
                const style = document.createElement('style');
                style.id = 'typing-styles';
                style.textContent = `
                    .typing-indicator { display: flex; align-items: center; height: 20px; }
                    .typing-indicator span { 
                        height: 8px; width: 8px; background: #27ae60; 
                        border-radius: 50%; margin: 0 2px; opacity: 0.4;
                        animation: typing 1s infinite;
                    }
                    .typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
                    .typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
                    @keyframes typing { 0%,100%{opacity:0.4} 50%{opacity:1} }
                `;
                document.head.appendChild(style);
            }
            
            try {
                const API_URL = window.GLADIS_BOT_URL || "https://gladis-bot.onrender.com/chat";
                
                const res = await fetch(API_URL, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ message })
                });
                
                const data = await res.json();
                
                // Убираем индикатор
                const loadingEl = document.getElementById(loadingId);
                if (loadingEl) loadingEl.remove();
                
                // Показываем ответ
                chatArea.innerHTML += `
                    <div style="margin-bottom: 10px;">
                        <div style="font-weight: bold; color: #27ae60; margin-bottom: 5px;">GLADIS Бот</div>
                        <div style="background: #e8f5e9; padding: 10px 15px; border-radius: 15px 15px 15px 5px; max-width: 80%;">
                            ${escapeHtml(data.reply).replace(/\n/g, '<br>')}
                        </div>
                    </div>
                `;
                
            } catch (error) {
                console.error('Chat error:', error);
                const loadingEl = document.getElementById(loadingId);
                if (loadingEl) loadingEl.remove();
                
                chatArea.innerHTML += `
                    <div style="margin-bottom: 10px;">
                        <div style="font-weight: bold; color: #27ae60; margin-bottom: 5px;">GLADIS Бот</div>
                        <div style="background: #ffebee; padding: 10px 15px; border-radius: 15px 15px 15px 5px; max-width: 80%; color: #d32f2f;">
                            Извините, произошла ошибка. Пожалуйста, позвоните нам: 8-928-458-32-88
                        </div>
                    </div>
                `;
            }
            
            chatArea.scrollTop = chatArea.scrollHeight;
        }
        
        // Функция для экранирования HTML
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
        
        sendBtn.onclick = sendMessage;
    }
})();

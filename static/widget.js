(function () {
    // Создаем значок диалога (иконка чата)
    const chatIcon = document.createElement("div");
    chatIcon.innerHTML = `
        <svg width="30" height="30" viewBox="0 0 24 24" fill="white">
            <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/>
        </svg>
    `;
    chatIcon.style.position = "fixed";
    chatIcon.style.bottom = "25px";
    chatIcon.style.right = "25px";
    chatIcon.style.width = "60px";
    chatIcon.style.height = "60px";
    chatIcon.style.borderRadius = "50%";
    chatIcon.style.background = "linear-gradient(135deg, #2ecc71, #27ae60)";
    chatIcon.style.color = "white";
    chatIcon.style.display = "flex";
    chatIcon.style.justifyContent = "center";
    chatIcon.style.alignItems = "center";
    chatIcon.style.cursor = "pointer";
    chatIcon.style.zIndex = "99999";
    chatIcon.style.boxShadow = "0 4px 12px rgba(46, 204, 113, 0.3)";
    chatIcon.style.transition = "all 0.3s ease";
    
    // Эффект при наведении
    chatIcon.onmouseover = () => {
        chatIcon.style.transform = "scale(1.1)";
        chatIcon.style.boxShadow = "0 6px 16px rgba(46, 204, 113, 0.4)";
    };
    chatIcon.onmouseout = () => {
        chatIcon.style.transform = "scale(1)";
        chatIcon.style.boxShadow = "0 4px 12px rgba(46, 204, 113, 0.3)";
    };
    
    document.body.appendChild(chatIcon);

    // Создаем окно чата (изначально скрыто)
    const chatWindow = document.createElement("div");
    chatWindow.style.position = "fixed";
    chatWindow.style.bottom = "100px";
    chatWindow.style.right = "20px";
    chatWindow.style.width = "350px";
    chatWindow.style.height = "500px";
    chatWindow.style.background = "white";
    chatWindow.style.border = "1px solid #e0e0e0";
    chatWindow.style.borderRadius = "15px";
    chatWindow.style.display = "none"; // Изначально скрыто
    chatWindow.style.flexDirection = "column";
    chatWindow.style.zIndex = "99998";
    chatWindow.style.boxShadow = "0 10px 30px rgba(0, 0, 0, 0.15)";
    chatWindow.style.overflow = "hidden";
    chatWindow.style.fontFamily = "Arial, sans-serif";
    document.body.appendChild(chatWindow);

    // Заголовок чата
    const header = document.createElement("div");
    header.style.background = "linear-gradient(135deg, #2ecc71, #27ae60)";
    header.style.color = "white";
    header.style.padding = "15px";
    header.style.fontWeight = "bold";
    header.style.fontSize = "16px";
    header.style.display = "flex";
    header.style.alignItems = "center";
    header.style.fontFamily = "Arial, sans-serif";
    header.innerHTML = `
        <svg width="20" height="20" viewBox="0 0 24 24" fill="white" style="margin-right: 10px;">
            <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/>
        </svg>
        Консультация GLADIS
    `;
    chatWindow.appendChild(header);

    // Область сообщений
    const chatArea = document.createElement("div");
    chatArea.style.flex = "1";
    chatArea.style.padding = "15px";
    chatArea.style.overflowY = "auto";
    chatArea.style.backgroundColor = "#f9f9f9";
    chatArea.style.fontSize = "14px";
    chatArea.style.lineHeight = "1.5";
    chatArea.style.fontFamily = "Arial, sans-serif";
    
    // Начальное сообщение
    chatArea.innerHTML = `
        <div style="background: #e8f5e9; padding: 10px 15px; border-radius: 15px 15px 15px 5px; margin-bottom: 10px; max-width: 80%;">
            <div style="font-weight: bold; color: #27ae60; margin-bottom: 5px; font-family: Arial, sans-serif;">GLADIS Бот</div>
            Здравствуйте! Я помогу подобрать процедуру и запишу на консультацию. Чем могу помочь?
        </div>
    `;
    
    chatWindow.appendChild(chatArea);

    // Поле ввода
    const inputContainer = document.createElement("div");
    inputContainer.style.display = "flex";
    inputContainer.style.borderTop = "1px solid #e0e0e0";
    inputContainer.style.padding = "10px";
    inputContainer.style.background = "white";
    inputContainer.style.fontFamily = "Arial, sans-serif";
    chatWindow.appendChild(inputContainer);

    const input = document.createElement("input");
    input.placeholder = "Напишите ваш вопрос...";
    input.style.border = "none";
    input.style.flex = "1";
    input.style.padding = "12px 15px";
    input.style.outline = "none";
    input.style.fontSize = "14px";
    input.style.borderRadius = "25px";
    input.style.backgroundColor = "#f5f5f5";
    input.style.fontFamily = "Arial, sans-serif";
    inputContainer.appendChild(input);

    const sendBtn = document.createElement("button");
    sendBtn.innerHTML = "➤";
    sendBtn.style.background = "#2ecc71";
    sendBtn.style.color = "white";
    sendBtn.style.border = "none";
    sendBtn.style.borderRadius = "50%";
    sendBtn.style.width = "40px";
    sendBtn.style.height = "40px";
    sendBtn.style.marginLeft = "10px";
    sendBtn.style.cursor = "pointer";
    sendBtn.style.fontSize = "16px";
    sendBtn.style.display = "flex";
    sendBtn.style.justifyContent = "center";
    sendBtn.style.alignItems = "center";
    sendBtn.style.transition = "background 0.3s";
    sendBtn.style.fontFamily = "Arial, sans-serif";
    
    sendBtn.onmouseover = () => {
        sendBtn.style.background = "#27ae60";
    };
    sendBtn.onmouseout = () => {
        sendBtn.style.background = "#2ecc71";
    };
    
    inputContainer.appendChild(sendBtn);

    // Кнопка закрытия
    const closeBtn = document.createElement("div");
    closeBtn.innerHTML = "×";
    closeBtn.style.position = "absolute";
    closeBtn.style.top = "10px";
    closeBtn.style.right = "15px";
    closeBtn.style.color = "white";
    closeBtn.style.cursor = "pointer";
    closeBtn.style.fontSize = "24px";
    closeBtn.style.fontWeight = "normal";
    closeBtn.style.opacity = "0.8";
    closeBtn.style.transition = "opacity 0.3s";
    closeBtn.style.fontFamily = "Arial, sans-serif";
    
    closeBtn.onmouseover = () => {
        closeBtn.style.opacity = "1";
    };
    closeBtn.onmouseout = () => {
        closeBtn.style.opacity = "0.8";
    };
    
    header.appendChild(closeBtn);

    // Логика открытия/закрытия
    let isChatOpen = false;
    
    function toggleChat() {
        if (isChatOpen) {
            // Закрываем чат
            chatWindow.style.display = "none";
            isChatOpen = false;
        } else {
            // Открываем чат
            chatWindow.style.display = "flex";
            isChatOpen = true;
            // Фокус на поле ввода
            setTimeout(() => input.focus(), 100);
        }
    }

    // Обработчики событий
    chatIcon.onclick = toggleChat;
    closeBtn.onclick = toggleChat;

    // Функция отправки сообщения
    async function sendMessage() {
        const message = input.value.trim();
        if (!message) return;

        // Показываем сообщение пользователя
        chatArea.innerHTML += `
            <div style="text-align: right; margin-bottom: 10px; font-family: Arial, sans-serif;">
                <div style="background: #2ecc71; color: white; padding: 10px 15px; border-radius: 15px 15px 5px 15px; display: inline-block; max-width: 80%;">
                    ${message}
                </div>
            </div>
        `;
        
        input.value = "";
        chatArea.scrollTop = chatArea.scrollHeight;

        // Показываем индикатор загрузки
        const loadingId = Date.now();
        chatArea.innerHTML += `
            <div id="loading-${loadingId}" style="background: #e8f5e9; padding: 10px 15px; border-radius: 15px 15px 15px 5px; margin-bottom: 10px; max-width: 80%; font-family: Arial, sans-serif;">
                <div style="font-weight: bold; color: #27ae60; margin-bottom: 5px; font-family: Arial, sans-serif;">GLADIS Бот</div>
                <div style="display: flex; align-items: center;">
                    <div class="typing-indicator">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                    <style>
                        .typing-indicator {
                            display: flex;
                            align-items: center;
                            height: 20px;
                        }
                        .typing-indicator span {
                            height: 8px;
                            width: 8px;
                            background: #27ae60;
                            border-radius: "50%";
                            margin: 0 2px;
                            opacity: 0.4;
                            animation: typing 1s infinite;
                        }
                        .typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
                        .typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
                        @keyframes typing {
                            0%, 100% { opacity: 0.4; }
                            50% { opacity: 1; }
                        }
                    </style>
                </div>
            </div>
        `;
        chatArea.scrollTop = chatArea.scrollHeight;

        try {
            // URL вашего бота на Render
            const API_URL = window.GLADIS_BOT_URL || "https://gladis-bot.onrender.com/chat";
            
            const res = await fetch(API_URL, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message })
            });

            const data = await res.json();
            
            // Убираем индикатор загрузки
            const loadingElement = document.getElementById(`loading-${loadingId}`);
            if (loadingElement) {
                loadingElement.remove();
            }
            
            // Показываем ответ бота
            chatArea.innerHTML += `
                <div style="margin-bottom: 10px; font-family: Arial, sans-serif;">
                    <div style="font-weight: bold; color: #27ae60; margin-bottom: 5px; font-family: Arial, sans-serif;">GLADIS Бот</div>
                    <div style="background: #e8f5e9; padding: 10px 15px; border-radius: 15px 15px 15px 5px; max-width: 80%;">
                        ${data.reply.replace(/\n/g, '<br>')}
                    </div>
                </div>
            `;
            
        } catch (error) {
            // Убираем индикатор загрузки
            const loadingElement = document.getElementById(`loading-${loadingId}`);
            if (loadingElement) {
                loadingElement.remove();
            }
            
            // Показываем ошибку
            chatArea.innerHTML += `
                <div style="margin-bottom: 10px; font-family: Arial, sans-serif;">
                    <div style="font-weight: bold; color: #27ae60; margin-bottom: 5px; font-family: Arial, sans-serif;">GLADIS Бот</div>
                    <div style="background: #ffebee; padding: 10px 15px; border-radius: 15px 15px 15px 5px; max-width: 80%; color: #d32f2f;">
                        Извините, произошла ошибка. Пожалуйста, попробуйте позже или позвоните нам.
                    </div>
                </div>
            `;
            
            console.error("Ошибка чат-бота:", error);
        }
        
        chatArea.scrollTop = chatArea.scrollHeight;
    }

    // Обработчики событий
    input.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
            sendMessage();
        }
    });

    sendBtn.onclick = sendMessage;
})();

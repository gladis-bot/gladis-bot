(function () {
    // Создаем кнопку чата
    const btn = document.createElement("div");
    btn.innerHTML = "💬";
    btn.style.position = "fixed";
    btn.style.bottom = "20px";
    btn.style.right = "20px";
    btn.style.width = "60px";
    btn.style.height = "60px";
    btn.style.borderRadius = "50%";
    btn.style.background = "linear-gradient(135deg, #8a2be2, #9370db)"; // Фиолетовый градиент как на сайте
    btn.style.color = "white";
    btn.style.display = "flex";
    btn.style.justifyContent = "center";
    btn.style.alignItems = "center";
    btn.style.cursor = "pointer";
    btn.style.zIndex = "99999";
    btn.style.boxShadow = "0 4px 12px rgba(138, 43, 226, 0.3)";
    btn.style.fontSize = "24px";
    btn.style.transition = "all 0.3s ease";
    
    // Эффект при наведении
    btn.onmouseover = () => {
        btn.style.transform = "scale(1.1)";
        btn.style.boxShadow = "0 6px 16px rgba(138, 43, 226, 0.4)";
    };
    btn.onmouseout = () => {
        btn.style.transform = "scale(1)";
        btn.style.boxShadow = "0 4px 12px rgba(138, 43, 226, 0.3)";
    };
    
    document.body.appendChild(btn);

    // Создаем окно чата
    const box = document.createElement("div");
    box.style.position = "fixed";
    box.style.bottom = "100px";
    box.style.right = "20px";
    box.style.width = "350px";
    box.style.height = "500px";
    box.style.background = "white";
    box.style.border = "1px solid #e0e0e0";
    box.style.borderRadius = "15px";
    box.style.display = "none";
    box.style.flexDirection = "column";
    box.style.zIndex = "99999";
    box.style.boxShadow = "0 10px 30px rgba(0, 0, 0, 0.15)";
    box.style.overflow = "hidden";
    document.body.appendChild(box);

    // Заголовок чата
    const header = document.createElement("div");
    header.style.background = "linear-gradient(135deg, #8a2be2, #9370db)";
    header.style.color = "white";
    header.style.padding = "15px";
    header.style.fontWeight = "bold";
    header.style.fontSize = "16px";
    header.style.display = "flex";
    header.style.alignItems = "center";
    header.innerHTML = "💬 Консультация GLADIS";
    box.appendChild(header);

    // Область сообщений
    const chat = document.createElement("div");
    chat.style.flex = "1";
    chat.style.padding = "15px";
    chat.style.overflowY = "auto";
    chat.style.backgroundColor = "#f9f9f9";
    chat.style.fontSize = "14px";
    chat.style.lineHeight = "1.5";
    
    // Начальное сообщение
    chat.innerHTML = `
        <div style="background: #e6e6fa; padding: 10px 15px; border-radius: 15px 15px 15px 5px; margin-bottom: 10px; max-width: 80%;">
            <div style="font-weight: bold; color: #8a2be2; margin-bottom: 5px;">GLADIS Бот</div>
            Здравствуйте! Я помогу подобрать процедуру и запишу на консультацию. Чем могу помочь?
        </div>
    `;
    
    box.appendChild(chat);

    // Поле ввода
    const inputContainer = document.createElement("div");
    inputContainer.style.display = "flex";
    inputContainer.style.borderTop = "1px solid #e0e0e0";
    inputContainer.style.padding = "10px";
    inputContainer.style.background = "white";
    box.appendChild(inputContainer);

    const input = document.createElement("input");
    input.placeholder = "Напишите ваш вопрос...";
    input.style.border = "none";
    input.style.flex = "1";
    input.style.padding = "12px 15px";
    input.style.outline = "none";
    input.style.fontSize = "14px";
    input.style.borderRadius = "25px";
    input.style.backgroundColor = "#f5f5f5";
    inputContainer.appendChild(input);

    const sendBtn = document.createElement("button");
    sendBtn.innerHTML = "➤";
    sendBtn.style.background = "#8a2be2";
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
    
    sendBtn.onmouseover = () => {
        sendBtn.style.background = "#7a1bd2";
    };
    sendBtn.onmouseout = () => {
        sendBtn.style.background = "#8a2be2";
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
    
    closeBtn.onmouseover = () => {
        closeBtn.style.opacity = "1";
    };
    closeBtn.onmouseout = () => {
        closeBtn.style.opacity = "0.8";
    };
    
    header.appendChild(closeBtn);

    // Функции
    btn.onclick = () => {
        box.style.display = box.style.display === "none" ? "flex" : "none";
    };

    closeBtn.onclick = () => {
        box.style.display = "none";
    };

    // Функция отправки сообщения
    async function sendMessage() {
        const message = input.value.trim();
        if (!message) return;

        // Показываем сообщение пользователя
        chat.innerHTML += `
            <div style="text-align: right; margin-bottom: 10px;">
                <div style="background: #8a2be2; color: white; padding: 10px 15px; border-radius: 15px 15px 5px 15px; display: inline-block; max-width: 80%;">
                    ${message}
                </div>
            </div>
        `;
        
        input.value = "";
        chat.scrollTop = chat.scrollHeight;

        // Показываем индикатор загрузки
        const loadingId = Date.now();
        chat.innerHTML += `
            <div id="loading-${loadingId}" style="background: #e6e6fa; padding: 10px 15px; border-radius: 15px 15px 15px 5px; margin-bottom: 10px; max-width: 80%;">
                <div style="font-weight: bold; color: #8a2be2; margin-bottom: 5px;">GLADIS Бот</div>
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
                            background: #8a2be2;
                            border-radius: 50%;
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
        chat.scrollTop = chat.scrollHeight;

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
            chat.innerHTML += `
                <div style="margin-bottom: 10px;">
                    <div style="font-weight: bold; color: #8a2be2; margin-bottom: 5px;">GLADIS Бот</div>
                    <div style="background: #e6e6fa; padding: 10px 15px; border-radius: 15px 15px 15px 5px; max-width: 80%;">
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
            chat.innerHTML += `
                <div style="margin-bottom: 10px;">
                    <div style="font-weight: bold; color: #8a2be2; margin-bottom: 5px;">GLADIS Бот</div>
                    <div style="background: #ffe6e6; padding: 10px 15px; border-radius: 15px 15px 15px 5px; max-width: 80%; color: #d32f2f;">
                        Извините, произошла ошибка. Пожалуйста, попробуйте позже или позвоните нам.
                    </div>
                </div>
            `;
            
            console.error("Ошибка чат-бота:", error);
        }
        
        chat.scrollTop = chat.scrollHeight;
    }

    // Обработчики событий
    input.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
            sendMessage();
        }
    });

    sendBtn.onclick = sendMessage;

    // Автофокус на поле ввода при открытии
    const observer = new MutationObserver(() => {
        if (box.style.display === "flex") {
            input.focus();
        }
    });
    observer.observe(box, { attributes: true, attributeFilter: ['style'] });
})();

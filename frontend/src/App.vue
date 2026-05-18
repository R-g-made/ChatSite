<template>
  <div class="container">
    <!-- Header -->
    <header class="header">
      <div class="logo">
        <img src="./assets/flash.gif" alt="flash" class="flash-icon" />
        <span>ЧатТоэ</span>
      </div>
      <div class="nav">
        <div class="nav-active-bg" :style="{ transform: currentTab === 'chat' ? 'translateX(3px)' : 'translateX(101.5px)' }"></div>
        <button :class="{ active: currentTab === 'chat' }" @click="currentTab = 'chat'">Чат</button>
        <button :class="{ active: currentTab === 'about' }" @click="currentTab = 'about'">О проекте</button>
      </div>
    </header>

    <!-- Chat Body -->
    <main v-if="currentTab === 'chat'" class="chat-body" ref="chatBox">
      <!-- State 1: Empty Chat -->
      <div v-if="messages.length === 0" class="empty-state">
        <h2 class="welcome-text">Привет !</h2>
        <p class="sub-text">Спроси меня о чем-нибудь</p>
      </div>

      <!-- Messages List -->
      <div v-else class="messages-list">
        <transition-group name="message-anim">
          <div v-for="(msg, index) in messages" :key="index" :class="['message-wrapper', msg.role]">
            
            <!-- User Message -->
            <div v-if="msg.role === 'user'" class="user-bubble">
              {{ msg.content }}
            </div>

            <!-- Bot Response -->
            <div v-else class="bot-container">
              <!-- Loading State -->
              <div v-if="msg.status === 'loading'" class="status-badge search">Поиск</div>
              <div v-if="msg.status === 'loading'" class="bot-text">Ищем ответ...</div>

              <!-- Suggestion State (Top 3) -->
              <div v-else-if="msg.status === 'suggesting'" class="suggestion-box">
                <div class="status-badge choice">Ждем выбора</div>
                <p class="bot-text">Уточните вопрос из варианта ниже:</p>
                <div class="options">
                  <button 
                    v-for="opt in msg.suggestions" 
                    :key="opt.id" 
                    class="option-btn"
                    @click="selectSuggestion(opt)"
                  >
                    {{ opt.question }}
                  </button>
                </div>
              </div>

              <!-- Final Answer State -->
              <div v-else-if="msg.status === 'done'" class="answer-box">
                <div class="status-badge answer">Ответ</div>
                <div class="bot-text">{{ msg.content }}</div>
              </div>
            </div>
          </div>
        </transition-group>
      </div>
    </main>

    <!-- About Page -->
    <main v-else class="chat-body about-page">
      <div class="about-card">
        <img src="./assets/flash.gif" alt="flash" class="flash-icon" />
        <span class="about-text">Чаттоэ - твой онлайн помощник по ТОЭ</span>
      </div>

      <div class="about-actions">
        <button class="action-btn">
          <span>Презентация</span>
          <img src="./assets/arrow.svg" alt="arrow" class="arrow-icon" />
        </button>
        <button class="action-btn">
          <span>Список вопросов</span>
          <img src="./assets/arrow.svg" alt="arrow" class="arrow-icon" />
        </button>
      </div>
    </main>

    <!-- Input Footer -->
    <footer v-if="currentTab === 'chat'" class="footer">
      <div class="input-wrapper">
        <input 
          v-model="userInput" 
          @keyup.enter="handleSend" 
          placeholder="Спросите о ТОЭ"
          :disabled="isProcessing"
        />
        <button class="send-btn" @click="handleSend" :disabled="isProcessing || !userInput.trim()">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M9 18L15 12L9 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'

const currentTab = ref('chat')
const userInput = ref('')
const messages = ref([])
const isProcessing = ref(false)
const chatBox = ref(null)

const scrollToBottom = async () => {
  await nextTick()
  if (chatBox.value) {
    chatBox.value.scrollTop = chatBox.value.scrollHeight
  }
}

const handleSend = async () => {
  if (!userInput.value.trim() || isProcessing.value) return

  const text = userInput.value.trim()
  messages.value.push({ role: 'user', content: text })
  userInput.value = ''
  isProcessing.value = true
  
  await scrollToBottom()

  // Delay of 0.4s before bot starts "loading"
  await new Promise(resolve => setTimeout(resolve, 400))

  // Add loading message from bot
  const botMsgIndex = messages.value.push({ 
    role: 'bot', 
    status: 'loading',
    content: '' 
  }) - 1

  await scrollToBottom()

  try {
    const response = await fetch('https://chattoe.ru/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text })
    })

    const data = await response.json()
    
    if (data.results && data.results.length > 0) {
      // Check if we have a very high score match (exact match)
      const topResult = data.results[0]
      // Скор теперь выше из-за BM25, порог 300
      if (topResult.score > 300) {
        messages.value[botMsgIndex] = {
          role: 'bot',
          status: 'done',
          content: topResult.answer
        }
      } else {
        // State 3: Suggesting options
        messages.value[botMsgIndex] = {
          role: 'bot',
          status: 'suggesting',
          suggestions: data.results.slice(0, 3)
        }
      }
    } else {
      messages.value[botMsgIndex] = {
        role: 'bot',
        status: 'done',
        content: 'К сожалению, я не нашел ответа на ваш вопрос.'
      }
    }
  } catch (error) {
    messages.value[botMsgIndex] = {
      role: 'bot',
      status: 'done',
      content: 'Произошла ошибка при поиске. Проверьте подключение к серверу.'
    }
  } finally {
    isProcessing.value = false
    await scrollToBottom()
  }
}

const selectSuggestion = async (opt) => {
  // Имитируем отправку сообщ.
  messages.value.push({
    role: 'user',
    content: opt.question
  })
  
  await scrollToBottom()
  
  // 2. Задержка 0.4 секунды перед ответом
  await new Promise(resolve => setTimeout(resolve, 400))
  
  // 3. Фмнальный ответ
  messages.value.push({
    role: 'bot',
    status: 'done',
    content: opt.answer
  })
  
  await scrollToBottom()
}
</script>

<style scoped>
.container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100%;
  max-width: 500px;
  margin: 0 auto;
  background-color: #0D0D0D;
  color: white;
}

.header {
  padding: 20px 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
  background-color: #0D0D0D;
}

.logo {
  font-size: 23.88px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
}

.flash-icon {
  width: 24px;
  height: 24px;
  object-fit: contain;
}

.nav {
  background: var(--nav-bg);
  border-radius: 20px;
  display: flex;
  align-items: center;
  width: 190.96px;
  height: 42px;
  position: relative;
  padding: 0;
}

.nav-active-bg {
  position: absolute;
  width: 87px;
  height: 36px;
  background: var(--nav-active);
  border-radius: 16px;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 0;
  top: 3px;
  left: 0;
}

.nav button {
  background: transparent;
  border: none;
  color: #888;
  width: 50%;
  height: 100%;
  cursor: pointer;
  font-size: 14.88px;
  font-family: 'Inter', sans-serif;
  font-weight: 500;
  transition: color 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  z-index: 1;
}

.nav button.active {
  color: white;
}

.chat-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px 0;
  display: flex;
  flex-direction: column;
  background-color: #0D0D0D;
}

.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
  padding: 0 20px;
}

.welcome-text {
  font-size: 22.83px;
  margin-bottom: 10px;
  font-weight: 500;
}

.sub-text {
  color: #888;
  font-weight: 500;
  font-size: 22.83px;
}

.messages-list {
  display: flex;
  flex-direction: column;
  gap: 50px;
}

.message-wrapper {
  display: flex;
  flex-direction: column;
}

.message-wrapper.user {
  align-self: flex-end;
  padding-right: 20px;
}

.user-bubble {
  background: var(--user-msg-gradient);
  padding: 20px 30px;
  border-radius: 36px 9px 36px 36px;
  max-width: 300px;
  font-size: 17.1px;
  border: 1px solid rgba(255, 255, 255, 0.05);
  text-align: left;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.bot-container {
  align-self: flex-start;
  width: 100%;
  max-width: 450px;
  padding-left: 0;
}

.status-badge {
  font-size: 13.32px;
  padding: 6px 12px;
  border-radius: 12px;
  background: #222;
  color: #888;
  display: inline-block;
  margin-bottom: 16px;
  margin-left: 20px;
}

.bot-text {
  font-size: 17.1px;
  line-height: 1.4;
  font-weight: 500;
  padding-left: 20px;
}

.suggestion-box {
  background: transparent;
  padding: 0;
  border-radius: 0;
  border: none;
  margin-left: 20px;
}

.suggestion-box .status-badge {
  margin-left: 0;
  margin-bottom: 16px;
}

.suggestion-box .bot-text {
  padding-left: 0;
  font-size: 16.19px;
}

.options {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 16px;
  margin-top: 25px;
}

.option-btn {
  background: #262626;
  border: none;
  color: white;
  padding: 16px 15px;
  border-radius: 24px;
  text-align: left;
  cursor: pointer;
  font-size: 14px;
  font-family: 'Inter', sans-serif;
  font-weight: 500;
  transition: background 0.2s;
  width: auto;
  max-width: 100%;
  height: auto;
  line-height: 1.4;
  display: inline-block;
}

.option-btn:hover {
  background: #313131;
}

/* Анимация сообщений */
.message-anim-enter-active {
  transition: all 0.3s ease-out;
}

.message-anim-enter-from {
  opacity: 0;
  transform: scale(0.9);
  transform-origin: bottom right;
}

.bot-container.message-anim-enter-from {
  transform-origin: bottom left;
}

.about-page {
  padding: 40px 20px;
  display: flex;
  flex-direction: column;
  gap: 30px;
}

.about-card {
  background: var(--user-msg-gradient);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 40px;
  padding: 30px;
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.about-text {
  font-size: 20px;
  line-height: 1.4;
  color: white;
  font-weight: 500;
}

.about-actions {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.action-btn {
  background: transparent;
  border: none;
  color: white;
  padding: 14px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  font-size: 18px;
  font-family: 'Inter', sans-serif;
  font-weight: 500;
  width: 100%;
  border-radius: 100px;
  transition: background 0.2s ease;
  outline: none;
}

.action-btn:hover {
  background: #1a1a1a;
}

.action-btn:active {
  background: #262626;
}

.arrow-icon {
  width: 14px;
  height: 14px;
}

.footer {
  padding: 20px;
  background-color: #0D0D0D;
}

.input-wrapper {
  background: var(--input-bg);
  border-radius: 34px;
  display: flex;
  align-items: center;
  padding: 0 10px 0 25px;
  height: 67.83px;
  border: none;
}

input {
  flex: 1;
  background: transparent;
  border: none;
  color: white;
  padding: 10px 0;
  outline: none;
  font-size: 18.1px; /* Спросить о ТОЭ */
  font-family: 'Inter', sans-serif;
  font-weight: 500;
}

input::placeholder {
  color: #888;
}

.send-btn {
  background: white;
  color: black;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: transform 0.2s;
}

.send-btn:disabled {
  background: #333;
  color: #666;
  cursor: not-allowed;
}

.send-btn:active {
  transform: scale(0.9);
}

.send-btn svg {
  width: 24px;
  height: 24px;
}
</style>

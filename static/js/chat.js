const chatMessages = document.getElementById('chatMessages');
const questionInput = document.getElementById('questionInput');
const sendBtn = document.getElementById('sendBtn');

// Cargar información del sistema al inicio
async function loadSystemInfo() {
    try {
        const response = await fetch('/system-info');
        const data = await response.json();
        
        // Crear mensaje de bienvenida personalizado
        const welcomeMessage = createWelcomeMessage(data);
        chatMessages.innerHTML = welcomeMessage;
        
    } catch (error) {
        console.error('Error cargando información del sistema:', error);
        // Mensaje por defecto si falla
        addMessage('bot', '¡Hola! Soy tu asistente de estudio. Pregúntame sobre el contenido de la asignatura.');
    }
}

function createWelcomeMessage(systemInfo) {
    const { total_chunks, total_documents, documents } = systemInfo;
    
    // Crear lista de documentos
    const docsList = documents.map(doc => 
        `<li><strong>${doc.name}</strong> (${doc.chunks} fragmentos)</li>`
    ).join('');
    
    // Generar ejemplos de preguntas basados en los documentos
    const docNames = documents.map(d => d.name.replace('.pdf', '')).join(', ');
    
    const welcomeHTML = `
        <div class="message bot-message">
            <div class="message-content">
                <h3>🤖 ¡Hola! Soy tu Asistente de Estudio IA</h3>
                
                <p>He cargado y procesado la siguiente información:</p>
                
                <div class="system-info">
                    <p><strong>📚 Documentos disponibles:</strong> ${total_documents}</p>
                    <ul class="documents-list">
                        ${docsList}
                    </ul>
                    <p><strong>📊 Total de fragmentos indexados:</strong> ${total_chunks}</p>
                </div>
                
                <div class="examples-section">
                    <p><strong>💡 Ejemplos de preguntas que puedes hacer:</strong></p>
                    <ul class="examples-list">
                        <li>"¿Qué temas se tratan en ${documents[0]?.name || 'los documentos'}?"</li>
                        <li>"Explícame el concepto principal del material"</li>
                        <li>"¿Qué información hay sobre [tema específico]?"</li>
                        <li>"Resume el contenido de ${documents[0]?.name || 'un documento'}"</li>
                    </ul>
                </div>
                
                <p class="prompt-text">✨ <em>Hazme cualquier pregunta sobre este material y te ayudaré con información detallada.</em></p>
            </div>
        </div>
    `;
    
    return welcomeHTML;
}

function addMessage(type, content, sources = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;
    
    let messageContent = `<div class="message-content">${content}</div>`;
    
    // Agregar fuentes si existen
    if (sources && sources.length > 0) {
        messageContent += `
            <div class="sources">
                <strong>📄 Fuentes consultadas:</strong>
                <ul>
                    ${sources.map(source => `<li>${source}</li>`).join('')}
                </ul>
            </div>
        `;
    }
    
    messageDiv.innerHTML = messageContent;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function showTypingIndicator() {
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message bot-message typing-indicator';
    typingDiv.id = 'typingIndicator';
    typingDiv.innerHTML = `
        <div class="message-content">
            <div class="typing-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function removeTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) {
        indicator.remove();
    }
}

async function sendQuestion() {
    const question = questionInput.value.trim();
    
    if (!question) return;
    
    // Deshabilitar input y botón
    questionInput.disabled = true;
    sendBtn.disabled = true;
    
    // Mostrar pregunta del usuario
    addMessage('user', question);
    
    // Limpiar input
    questionInput.value = '';
    
    // Mostrar indicador de escritura
    showTypingIndicator();
    
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ question: question })
        });
        
        const data = await response.json();
        
        // Quitar indicador de escritura
        removeTypingIndicator();
        
        if (response.ok) {
            // Mostrar respuesta
            addMessage('bot', data.answer, data.sources);
            
            // Debug en consola
            if (data.debug) {
                console.log('Debug info:', data.debug);
            }
        } else {
            addMessage('bot', `❌ Error: ${data.error || 'Error desconocido'}`);
        }
        
    } catch (error) {
        removeTypingIndicator();
        console.error('Error:', error);
        addMessage('bot', '❌ Error al conectar con el servidor. Por favor, intenta de nuevo.');
    } finally {
        // Rehabilitar input y botón
        questionInput.disabled = false;
        sendBtn.disabled = false;
        questionInput.focus();
    }
}

// Event listeners
sendBtn.addEventListener('click', sendQuestion);

questionInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendQuestion();
    }
});

// Cargar información del sistema al cargar la página
window.addEventListener('load', loadSystemInfo);
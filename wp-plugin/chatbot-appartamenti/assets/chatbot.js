/**
 * Chatbot Appartamenti - Frontend JavaScript
 * Compatibile con WordPress e jQuery
 */

(function($) {
    'use strict';

    // Configurazione
    const ChatBot = {
        config: {
            apiBaseUrl: chatbot_ajax?.api_base_url || 'https://api.viamerano24.it/api',
            ajaxUrl: chatbot_ajax?.ajax_url || '/wp-admin/admin-ajax.php',
            nonce: chatbot_ajax?.nonce || '',
            sessionId: null,
            isTyping: false,
            maxRetries: 3,
            typingDelay: 800,
            bookingPageUrl: window.location.origin + '/prenotazione/'
        },

        // Elementi DOM
        elements: {},

        // Inizializzazione
        init: function() {
            this.bindElements();
            this.initSession();
            ChatBot.elements.input.prop('disabled', false);
            ChatBot.elements.sendButton.prop('disabled', false);
            ChatBot.elements.input.focus();
            this.bindEvents();
            this.setupScrollbar();
            console.log('🤖 Chatbot Appartamenti inizializzato');

            // Test connessione API
            this.testApiConnection();
        },

        // Bind elementi DOM
        bindElements: function() {
            this.elements = {
                container: $('#appartamenti-chatbot'),
                messages: $('#chat-messages'),
                input: $('#chat-input'),
                sendButton: $('#send-button'),
                typingIndicator: $('#typing-indicator'),
                bookingToast: $('#booking-toast')
            };

            // Verifica che gli elementi esistano
            if (this.elements.container.length === 0) {
                console.warn('⚠️ Container chatbot non trovato');
            }
        },

        // Inizializzazione sessione
        initSession: function() {
            // Tenta di recuperare la sessione da localStorage
            const storedSessionId = localStorage.getItem('chatbotSessionId');
            if (storedSessionId) {
                ChatBot.config.sessionId = storedSessionId;
                console.log('Sessione recuperata:', storedSessionId);
            } else {
                // Se non presente, la prima richiesta al backend la creerà
                console.log('Nessuna sessione trovata, verrà creata una nuova.');
            }
            // Aggiungi un messaggio di benvenuto all'avvio del chatbot
            ChatBot.displayMessage("Ciao! Sono il tuo assistente virtuale per le prenotazioni a Villa Celi. Come posso aiutarti oggi?", 'bot');
        },

        // Binding eventi
        bindEvents: function() {
            ChatBot.elements.sendButton.on('click', ChatBot.sendMessage);
            ChatBot.elements.input.on('keypress', function(e) {
                if (e.which === 13) { // Invio
                    e.preventDefault(); // Impedisce nuova riga nel textarea
                    ChatBot.sendMessage();
                }
            });
            // Autoresize del textarea
            ChatBot.elements.input.on('input', ChatBot.autoResizeInput);
        },

        // Test connessione API
        testApiConnection: function() {
            fetch(ChatBot.config.apiBaseUrl + '/test')
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    console.log('API Connessione OK:', data.message);
                })
                .catch(error => {
                    console.error('API Connessione fallita:', error);
                    ChatBot.displayMessage("Siamo spiacenti, il servizio di chat non è al momento disponibile. Riprova più tardi.", 'bot');
                    ChatBot.elements.input.prop('disabled', true);
                    ChatBot.elements.sendButton.prop('disabled', true);
                });
        },

        // Invia messaggio
        sendMessage: function() {
            const messageText = ChatBot.elements.input.val().trim();
            if (messageText === '') {
                return;
            }

            ChatBot.displayMessage(messageText, 'user');
            ChatBot.elements.input.val('');
            ChatBot.autoResizeInput(); // Resetta altezza input

            ChatBot.elements.input.prop('disabled', true);
            ChatBot.elements.sendButton.prop('disabled', true);
            ChatBot.elements.typingIndicator.show();

            const payload = {
                message: messageText
            };
            if (ChatBot.config.sessionId) {
                payload.session_id = ChatBot.config.sessionId;
            }

            fetch(ChatBot.config.apiBaseUrl + '/chatbot', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-WP-Nonce': ChatBot.config.nonce // Invia il nonce per sicurezza
                    },
                    body: JSON.stringify(payload)
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    console.log("🔥 DEBUG: Risposta API ricevuta:", data);
                    ChatBot.elements.typingIndicator.hide();
                    ChatBot.elements.input.prop('disabled', false).focus();
                    ChatBot.elements.sendButton.prop('disabled', false);

                    if (data.message) {
                        ChatBot.displayMessage(data.message, 'bot');
                    } else if (data.error) {
                        ChatBot.displayMessage("Errore: " + data.error, 'bot');
                    }

                    // DEBUG: Verifica gestione prenotazioni
                    console.log("🔍 Tipo risposta:", data.type);
                    console.log("📋 Booking data:", data.booking_data);
                    
                    // Gestione prenotazioni - CORRETTA (senza duplicazione inappropriata)
                    if (data.type === 'booking_redirect' && data.booking_data) {
                        console.log("✅ Attivando handleBookingAction...");
                        ChatBot.handleBookingAction(data.booking_data);
                    } else if (data.type === 'availability_list') {
                        // Tipo availability_list - I pulsanti sono già gestiti da displayMessage
                        console.log("📋 Lista disponibilità mostrata con pulsanti");
                    } else if (data.booking_data) {
                        // Fallback per compatibilità
                        console.log("🔄 Fallback handleBookingAction...");
                        ChatBot.handleBookingAction(data.booking_data);
                    }
                    // RIMOSSO: Il log "❌ Condizioni per booking non soddisfatte" inappropriato

                    if (data.session_id && data.session_id !== ChatBot.config.sessionId) {
                        ChatBot.config.sessionId = data.session_id;
                        localStorage.setItem('chatbotSessionId', data.session_id);
                        console.log('Session ID aggiornato:', ChatBot.config.sessionId);
                    }
                    ChatBot.setupScrollbar();
                })
                .catch(error => {
                    console.error('Errore durante la comunicazione con l\'API:', error);
                    ChatBot.elements.typingIndicator.hide();
                    ChatBot.displayMessage("C'è stato un problema nel connettersi. Riprova più tardi.", 'bot');
                    ChatBot.elements.input.prop('disabled', false);
                    ChatBot.elements.sendButton.prop('disabled', false);
                    ChatBot.setupScrollbar();
                });
        },

        // Visualizza messaggio
        displayMessage: function(message, sender) {
            // PRIMA: Controlla se aggiungere pulsanti (sul messaggio originale)
            let needsButtons = false;
            let buttonNumbers = [];
            
            if (sender === 'bot' && message.includes('Per prenotare')) {
                // Trova i numeri PRIMA della conversione markdown
                const matches = message.match(/\*\*(\d+)\.\*\*/g);
                if (matches) {
                    needsButtons = true;
                    buttonNumbers = matches.map(match => 
                        match.replace(/\*\*/g, '').replace('.', '')
                    );
                    console.log('🔢 Pulsanti da creare:', buttonNumbers);
                }
            }
            
            // DOPO: Converti markdown in HTML
            let formattedMessage = message
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.*?)\*/g, '<em>$1</em>')
                .replace(/\n/g, '<br>')
                .replace(/💡/g, '💡')
                .replace(/✅/g, '✅')
                .replace(/🏠/g, '🏠')
                .replace(/📅/g, '📅');

            const messageBubble = $('<div>').addClass('message-bubble').html(formattedMessage);
            const messageDiv = $('<div>').addClass('message ' + sender).append(messageBubble);
            
            // Aggiungi pulsanti se necessario
            if (needsButtons && buttonNumbers.length > 0) {
                console.log('✅ Aggiungendo pulsanti...');
                this.addQuickActionButtons(messageBubble, buttonNumbers);
            }
            
            ChatBot.elements.messages.append(messageDiv);
            ChatBot.setupScrollbar();
        },

        // Modifica funzione pulsanti
        addQuickActionButtons: function(messageBubble, buttonNumbers) {
            const quickActions = $('<div>').addClass('quick-actions');
            
            buttonNumbers.forEach(number => {
                const button = $('<button>')
                    .addClass('quick-action-btn')
                    .text(`Prenota ${number}`)
                    .data('choice', number)
                    .on('click', function() {
                        const choice = $(this).data('choice');
                        ChatBot.elements.input.val(choice);
                        ChatBot.sendMessage();
                    });
                quickActions.append(button);
            });
            
            messageBubble.append(quickActions);
            console.log('🎯 Pulsanti aggiunti:', buttonNumbers);
        },

        // Gestione azioni specifiche del bot (es. booking)
        handleBookingAction: function(bookingData) {
            console.log("🎯 handleBookingAction chiamata con:", bookingData);
            
            if (bookingData && bookingData.appartamento && bookingData.check_in && bookingData.check_out) {
                ChatBot.elements.typingIndicator.hide();

                const baseUrl = ChatBot.config.bookingPageUrl;
                const params = new URLSearchParams({
                    appartamento: bookingData.appartamento,
                    check_in: bookingData.check_in,
                    check_out: bookingData.check_out,
                    check_in_formatted: bookingData.check_in_formatted,
                    check_out_formatted: bookingData.check_out_formatted
                }).toString();

                const bookingUrl = `${baseUrl}?${params}`;
                console.log("🔗 URL generato:", bookingUrl);

                const messageHtml = `
                    Abbiamo trovato disponibilità per l'appartamento <strong>${bookingData.appartamento}</strong>
                    dal <strong>${bookingData.check_in_formatted}</strong> al <strong>${bookingData.check_out_formatted}</strong>.
                    <br><br>
                    Puoi procedere con la prenotazione cliccando qui:
                    <a href="${bookingUrl}" target="_blank" class="quick-action-btn primary-btn">Vai alla prenotazione</a>
                    <br>
                    Oppure continua a chattare.
                `;
                ChatBot.displayMessage(messageHtml, 'bot');

                // ATTIVA il redirect automatico
                setTimeout(() => {
                    console.log("🚀 Reindirizzamento automatico...");
                    window.location.href = bookingUrl; // ← Stesso tab invece di nuovo
                }, 3000); // Ritardo di 3 secondi
                
                ChatBot.setupScrollbar();
                ChatBot.elements.input.prop('disabled', false).focus();
                ChatBot.elements.sendButton.prop('disabled', false);
            } else {
                console.log("❌ Dati booking incompleti:", bookingData);
                ChatBot.displayMessage("Mi dispiace, non ho abbastanza informazioni per creare un link di prenotazione. Potresti ripetere l'appartamento e le date?", 'bot');
                ChatBot.elements.typingIndicator.hide();
                ChatBot.elements.input.prop('disabled', false).focus();
                ChatBot.elements.sendButton.prop('disabled', false);
            }
        },

        // Scrollbar sempre in fondo
        setupScrollbar: function() {
            ChatBot.elements.messages.scrollTop(ChatBot.elements.messages[0].scrollHeight);
        },

        // Autoresize del campo input
        autoResizeInput: function() {
            ChatBot.elements.input.css('height', 'auto');
            ChatBot.elements.input.css('height', ChatBot.elements.input[0].scrollHeight + 'px');
        }
    };

    // Funzioni globali per widget floating
    window.toggleFloatingChatbot = function() {
        const container = $('#floating-chatbot-container');
        const trigger = $('#floating-chatbot-trigger');

        if (container.is(':visible')) {
            container.hide();
            trigger.html(trigger.data('original-text') || '💬 Prenota ora');
        } else {
            container.show();
            if (!trigger.data('original-text')) {
                trigger.data('original-text', trigger.html());
            }
            trigger.html('❌ Chiudi');

            // Inizializza chatbot se non già fatto
            if (!window.chatbotInitialized) {
                ChatBot.init();
                window.chatbotInitialized = true;
            }
        }
    };

    // Inizializzazione al DOM ready
    $(document).ready(function() {
        // Inizializza solo se il container esiste
        if ($('#appartamenti-chatbot').length > 0) {
            ChatBot.init();
            window.chatbotInitialized = true;
        }

        // Debug info
        if (typeof chatbot_ajax !== 'undefined') {
            console.log('🔧 Configurazione chatbot:', {
                api_url: chatbot_ajax.api_base_url,
                ajax_url: chatbot_ajax.ajax_url,
                has_nonce: !!chatbot_ajax.nonce
            });
        }
    });

    // Esporta per debug
    window.ChatBot = ChatBot;

})(jQuery);
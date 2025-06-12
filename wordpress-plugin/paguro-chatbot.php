<?php
/**
 * Plugin Name: Chatbot Appartamenti
 * Description: Sistema di prenotazione appartamenti con Paguro AI e integrazione Ninja Forms
 * Version: 1.0.0
 * Author: Il Tuo Nome
 */

// Sicurezza: impedisce accesso diretto
if (!defined('ABSPATH')) {
    exit;
}

class AppartamentiChatbot {
    
    public function __construct() {
        add_action('init', array($this, 'init'));
        add_action('wp_enqueue_scripts', array($this, 'enqueue_scripts'));
        add_shortcode('appartamenti_chatbot', array($this, 'chatbot_shortcode'));
        add_action('wp_ajax_get_booking_data', array($this, 'handle_booking_data'));
        add_action('wp_ajax_nopriv_get_booking_data', array($this, 'handle_booking_data'));
    }
    
    public function init() {
        // Crea pagina di prenotazione se non esiste
        $this->create_booking_page();
        
        // Registra custom fields per Ninja Forms (se necessario)
        add_action('ninja_forms_loaded', array($this, 'setup_ninja_forms'));
    }
    
    public function enqueue_scripts() {
        // CSS del chatbot
        wp_enqueue_style(
            'appartamenti-chatbot-css',
            plugin_dir_url(__FILE__) . 'assets/css/chatbot.css',
            array(),
            '2.2.0' // Incrementata per Paguro
        );
        
        // JavaScript del chatbot
        wp_enqueue_script(
            'appartamenti-chatbot-js',
            plugin_dir_url(__FILE__) . 'assets/js/chatbot.js',
            array('jquery'),
            '1.2.0', // Incrementata
            true
        );
        
        // JavaScript per popolamento booking (SOLO sulla pagina prenotazione)
        if (is_page('prenotazione')) {
            wp_enqueue_script(
                'booking-populate-js',
                plugin_dir_url(__FILE__) . 'assets/js/booking-populate.js',
                array('jquery'),
                '1.0.0',
                true
            );
        }
        
        // Passa dati PHP a JavaScript
        wp_localize_script('appartamenti-chatbot-js', 'chatbot_ajax', array(
            'ajax_url' => admin_url('admin-ajax.php'),
            'nonce' => wp_create_nonce('chatbot_nonce'),
            'api_base_url' => get_option('chatbot_api_url', 'https://api.viamerano24.it/api')
        ));
    }
    
    public function chatbot_shortcode($atts) {
        $atts = shortcode_atts(array(
            'height' => '400px',
            'width' => '100%',
            'title' => '🐚 Paguro - Receptionist Virtuale'
        ), $atts);
        
        ob_start();
        ?>
        <!-- Rimuove altezza inline per permettere altezza dinamica -->
        <div class="chatbot-container" id="appartamenti-chatbot" style="max-width: <?php echo esc_attr($atts['width']); ?>;" data-height="<?php echo esc_attr($atts['height']); ?>">
            <div class="chatbot-header">
                <?php echo esc_html($atts['title']); ?>
            </div>
            
            <div class="chat-messages" id="chat-messages">
                <div class="message bot">
                    <div class="message-bubble">
                        🐚 <strong>Ciao sono Paguro</strong>, il receptionist virtuale e ti aiuterò a trovare le date disponibili e procedere con la prenotazione.<br><br>
                        💡 <em>Scrivi ad esempio: "che disponibilità c'è per luglio"</em>
                    </div>
                </div>
            </div>
            
            <div class="typing-indicator" id="typing-indicator">
                <div class="message-bubble">
                    <span>Paguro sta scrivendo</span>
                    <div class="typing-dots">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                </div>
            </div>
            
            <div class="chat-input-container">
                <input 
                    type="text" 
                    class="chat-input" 
                    id="chat-input" 
                    placeholder="Scrivi la tua richiesta..."
                    maxlength="200"
                >
                <button class="send-button" id="send-button" type="button">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                    </svg>
                </button>
            </div>
        </div>
        
        <div class="booking-toast" id="booking-toast">
            <strong>✅ Reindirizzamento al form di prenotazione...</strong>
        </div>
        <?php
        return ob_get_clean();
    }
    
    public function create_booking_page() {
        // Controlla se la pagina di prenotazione esiste
        $page = get_page_by_path('prenotazione');
        
        if (!$page) {
            // Crea la pagina di prenotazione
            $page_data = array(
                'post_title' => 'Prenotazione Appartamento',
                'post_content' => $this->get_booking_page_content(),
                'post_status' => 'publish',
                'post_type' => 'page',
                'post_name' => 'prenotazione'
            );
            
            wp_insert_post($page_data);
        }
    }
    
    private function get_booking_page_content() {
        // Aggiornato con colori coordinati e Paguro
        return '
        <div id="booking-form-container">
            <h2>🐚 Conferma la tua prenotazione con Paguro</h2>
            
            <div id="booking-summary" style="background: #f8fffd; padding: 20px; margin-bottom: 20px; border-radius: 8px; border: 2px solid #1e6763;">
                <h3>📋 Riepilogo Prenotazione</h3>
                <div id="summary-content">
                    <p><strong>Appartamento:</strong> <span id="summary-appartamento" style="color: #1e6763; font-weight: bold;">In caricamento...</span></p>
                    <p><strong>Check-in:</strong> <span id="summary-checkin" style="color: #28a745;">In caricamento...</span></p>
                    <p><strong>Check-out:</strong> <span id="summary-checkout" style="color: #dc3545;">In caricamento...</span></p>
                </div>
                <div id="loading-indicator" style="text-align: center; margin-top: 10px;">
                    <em>🐚 Paguro sta caricando i dati prenotazione...</em>
                </div>
            </div>
            
            [ninja_form id="1"]
        </div>
        ';
    }
    
    public function setup_ninja_forms() {
        // Personalizzazioni Ninja Forms se necessario
        add_filter('ninja_forms_field_template_file_paths', array($this, 'custom_field_templates'));
    }
    
    public function custom_field_templates($paths) {
        $paths[] = plugin_dir_path(__FILE__) . 'ninja-forms-templates/';
        return $paths;
    }
    
    public function handle_booking_data() {
        // Verifica nonce per sicurezza
        if (!wp_verify_nonce($_POST['nonce'], 'chatbot_nonce')) {
            wp_die('Unauthorized');
        }
        
        // Gestisci dati di prenotazione dal chatbot
        $appartamento = sanitize_text_field($_POST['appartamento']);
        $check_in = sanitize_text_field($_POST['check_in']);
        $check_out = sanitize_text_field($_POST['check_out']);
        
        // Salva dati in sessione o database temporaneo
        if (!session_id()) {
            session_start();
        }
        
        $_SESSION['pending_booking'] = array(
            'appartamento' => $appartamento,
            'check_in' => $check_in,
            'check_out' => $check_out,
            'timestamp' => current_time('timestamp')
        );
        
        wp_send_json_success(array(
            'redirect_url' => home_url('/prenotazione/'),
            'message' => 'Dati di prenotazione salvati da Paguro'
        ));
    }
}

// Inizializza il plugin
new AppartamentiChatbot();

// Hook per form submission (opzionale)
add_action('ninja_forms_after_submission', 'handle_appartamenti_form_submission');

function handle_appartamenti_form_submission($form_data) {
    // Processa la submission del form di prenotazione
    $form_id = $form_data['form_id'];
    $fields = $form_data['fields'];
    
    // Se è il form di prenotazione appartamenti (ID = 1)
    if ($form_id == 1) {
        // Estrai i dati del form
        $appartamento = '';
        $check_in = '';
        $check_out = '';
        $nome = '';
        $email = '';
        
        foreach ($fields as $field) {
            switch ($field['key']) {
                case 'appartamento':
                    $appartamento = $field['value'];
                    break;
                case 'check_in':
                    $check_in = $field['value'];
                    break;
                case 'check_out':
                    $check_out = $field['value'];
                    break;
                case 'nome':
                    $nome = $field['value'];
                    break;
                case 'email':
                    $email = $field['value'];
                    break;
            }
        }
        
        // Invia email di conferma con Paguro
        $to = $email;
        $subject = '🐚 Conferma prenotazione da Paguro - Villa Celi';
        $message = "
        Gentile {$nome},
        
        🐚 Paguro ti conferma che la tua prenotazione è stata ricevuta:
        
        🏠 Appartamento: {$appartamento}
        📅 Check-in: {$check_in}
        📅 Check-out: {$check_out}
        
        Ti contatteremo presto per la conferma.
        
        🏖️ Grazie per aver scelto Villa Celi a Palinuro!
        
        🐚 Paguro - Receptionist Virtuale
        ";
        
        wp_mail($to, $subject, $message);
        
        // Invia notifica all'admin
        $admin_email = get_option('admin_email');
        $admin_subject = '🐚 Nuova prenotazione tramite Paguro';
        $admin_message = "
        🐚 Paguro ha ricevuto una nuova prenotazione:
        
        Nome: {$nome}
        Email: {$email}
        Appartamento: {$appartamento}
        Check-in: {$check_in}
        Check-out: {$check_out}
        
        🏖️ Villa Celi - Palinuro
        ";
        
        wp_mail($admin_email, $admin_subject, $admin_message);
        
        // Salva nel database (opzionale)
        global $wpdb;
        $table_name = $wpdb->prefix . 'appartamenti_prenotazioni';
        
        $wpdb->insert(
            $table_name,
            array(
                'appartamento' => $appartamento,
                'check_in' => $check_in,
                'check_out' => $check_out,
                'nome' => $nome,
                'email' => $email,
                'status' => 'pending',
                'created_at' => current_time('mysql')
            )
        );
    }
}

// Crea tabella per prenotazioni (attivazione plugin)
register_activation_hook(__FILE__, 'create_appartamenti_tables');

function create_appartamenti_tables() {
    global $wpdb;
    
    $table_name = $wpdb->prefix . 'appartamenti_prenotazioni';
    
    $charset_collate = $wpdb->get_charset_collate();
    
    $sql = "CREATE TABLE $table_name (
        id mediumint(9) NOT NULL AUTO_INCREMENT,
        appartamento varchar(255) NOT NULL,
        check_in date NOT NULL,
        check_out date NOT NULL,
        nome varchar(255) NOT NULL,
        email varchar(255) NOT NULL,
        telefono varchar(50),
        note text,
        status varchar(20) DEFAULT 'pending',
        created_at datetime DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (id)
    ) $charset_collate;";
    
    require_once(ABSPATH . 'wp-admin/includes/upgrade.php');
    dbDelta($sql);
}

// ==========================================
// FLOATING CHATBOT PAGURO COMPLETO 🐚
// ==========================================

add_shortcode('chatbot_floating', 'chatbot_floating_widget');

function chatbot_floating_widget($atts) {
    $atts = shortcode_atts(array(
        'position' => 'bottom-right',
        'trigger_text' => '🐚 Paguro',
        'trigger_size' => 'medium'
    ), $atts);
    
    ob_start();
    ?>
    
    <!-- TRIGGER BUTTON -->
    <div id="floating-chatbot-trigger" onclick="toggleFloatingChatbot()" style="
        position: fixed;
        <?php if ($atts['position'] === 'bottom-left'): ?>
            bottom: 20px; left: 20px;
        <?php else: ?>
            bottom: 20px; right: 20px;
        <?php endif; ?>
        background: #1e6763;
        color: white;
        padding: 12px 16px;
        border-radius: 25px;
        cursor: pointer;
        box-shadow: 0 4px 16px rgba(30, 103, 99, 0.3);
        z-index: 9999;
        font-weight: 600;
        font-size: 14px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        transition: all 0.3s ease;
        border: none;
        outline: none;
        min-width: 140px;
        text-align: center;
    " 
    onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 20px rgba(30, 103, 99, 0.4)'"
    onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 16px rgba(30, 103, 99, 0.3)'">
        <?php echo esc_html($atts['trigger_text']); ?>
    </div>
    
    <!-- CHATBOT CONTAINER -->
    <div id="floating-chatbot-container" style="
        position: fixed;
        <?php if ($atts['position'] === 'bottom-left'): ?>
            bottom: 80px; left: 20px;
        <?php else: ?>
            bottom: 80px; right: 20px;
        <?php endif; ?>
        width: 350px;
        height: 450px;
        display: none;
        z-index: 9998;
        box-shadow: 0 8px 30px rgba(30, 103, 99, 0.25);
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid #e0e0e0;
        background: white;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    ">
        
        <!-- HEADER -->
        <div style="
            background: #1e6763;
            color: white;
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-weight: 600;
            font-size: 15px;
            height: 50px;
            box-sizing: border-box;
        ">
            <span style="flex: 1;">🐚 Paguro - Receptionist</span>
            <button onclick="toggleFloatingChatbot()" style="
                background: rgba(255,255,255,0.2);
                border: none;
                color: white;
                font-size: 16px;
                cursor: pointer;
                padding: 5px;
                width: 28px;
                height: 28px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 50%;
                transition: background 0.2s;
                font-weight: bold;
                margin-left: 10px;
            " onmouseover="this.style.background='rgba(255,255,255,0.3)'"
               onmouseout="this.style.background='rgba(255,255,255,0.2)'">×</button>
        </div>
        
        <!-- AREA MESSAGGI -->
        <div style="
            height: 320px;
            overflow-y: auto;
            padding: 15px;
            background: #fafafa;
            border-bottom: 1px solid #e0e0e0;
        " id="floating-chat-messages">
            <div style="margin-bottom: 15px;">
                <div style="
                    background: white;
                    color: #2c3e50;
                    padding: 12px 16px;
                    border-radius: 18px;
                    border-bottom-left-radius: 4px;
                    display: inline-block;
                    max-width: 85%;
                    font-size: 14px;
                    line-height: 1.4;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                ">
                    🐚 <strong>Ciao sono Paguro!</strong> Come posso aiutarti?<br>
                    💡 <em>Prova: "che disponibilità c'è per luglio"</em>
                </div>
            </div>
        </div>
        
        <!-- TYPING INDICATOR -->
        <div id="floating-typing-indicator" style="
            padding: 10px 15px;
            background: #fafafa;
            display: none;
            border-bottom: 1px solid #e0e0e0;
        ">
            <div style="
                background: #f0f0f0;
                padding: 8px 12px;
                border-radius: 15px;
                display: inline-flex;
                align-items: center;
                gap: 8px;
                font-size: 12px;
                color: #6c757d;
            ">
                <span>Paguro sta scrivendo</span>
                <div style="display: flex; gap: 3px;">
                    <span style="width: 4px; height: 4px; background: #999; border-radius: 50%; animation: typing 1.4s infinite;"></span>
                    <span style="width: 4px; height: 4px; background: #999; border-radius: 50%; animation: typing 1.4s infinite 0.2s;"></span>
                    <span style="width: 4px; height: 4px; background: #999; border-radius: 50%; animation: typing 1.4s infinite 0.4s;"></span>
                </div>
            </div>
        </div>
        
        <!-- AREA INPUT -->
        <div style="
            background: white;
            padding: 15px;
            display: flex;
            gap: 10px;
            align-items: center;
            height: 80px;
            box-sizing: border-box;
            border-top: 1px solid #e0e0e0;
        ">
            <input 
                type="text" 
                id="floating-chat-input" 
                placeholder="Scrivi qui..."
                style="
                    flex: 1;
                    padding: 12px 16px;
                    border: 2px solid #d0d0d0;
                    border-radius: 25px;
                    outline: none;
                    font-size: 14px;
                    font-family: inherit;
                    color: #2c3e50;
                    background: #f8f9fa;
                    transition: all 0.2s ease;
                "
                maxlength="200"
                onfocus="this.style.borderColor='#1e6763'; this.style.background='white';"
                onblur="this.style.borderColor='#d0d0d0'; this.style.background='#f8f9fa';"
                onkeypress="if(event.key==='Enter'){event.preventDefault();sendFloatingMessage();}"
            >
            <button onclick="sendFloatingMessage()" style="
                background: #1e6763;
                color: white;
                border: none;
                border-radius: 50%;
                width: 42px;
                height: 42px;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.2s ease;
                box-shadow: 0 2px 8px rgba(30, 103, 99, 0.3);
            " onmouseover="this.style.background='#155a56'; this.style.transform='translateY(-1px)'"
               onmouseout="this.style.background='#1e6763'; this.style.transform='translateY(0)'">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                </svg>
            </button>
        </div>
    </div>
    
    <!-- CSS -->
    <style>
    @keyframes typing {
        0%, 60%, 100% { transform: translateY(0); }
        30% { transform: translateY(-6px); }
    }
    
    #floating-chatbot-container {
        animation: slideUpIn 0.3s ease-out;
    }
    
    @keyframes slideUpIn {
        from {
            opacity: 0;
            transform: translateY(20px) scale(0.95);
        }
        to {
            opacity: 1;
            transform: translateY(0) scale(1);
        }
    }
    
    #floating-chat-messages::-webkit-scrollbar {
        width: 6px;
    }
    
    #floating-chat-messages::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 3px;
    }
    
    #floating-chat-messages::-webkit-scrollbar-thumb {
        background: #1e6763;
        border-radius: 3px;
        opacity: 0.7;
    }
    
    #floating-chat-messages::-webkit-scrollbar-thumb:hover {
        opacity: 1;
    }
    
    @media (max-width: 768px) {
        #floating-chatbot-container {
            width: calc(100vw - 40px) !important;
            height: 400px !important;
            bottom: 70px !important;
            left: 20px !important;
            right: 20px !important;
        }
        
        #floating-chatbot-trigger {
            bottom: 15px !important;
            right: 15px !important;
            left: auto !important;
            padding: 10px 14px !important;
            font-size: 13px !important;
            min-width: 120px !important;
        }
        
        #floating-chat-messages {
            height: 250px !important;
        }
    }
    
    body:has([href*="whatsapp"]) #floating-chatbot-trigger,
    body:has([href*="wa.me"]) #floating-chatbot-trigger {
        bottom: 80px !important;
    }
    </style>
    
    <script>
    // Variabili globali per floating chatbot
    let floatingChatbotOpen = false;
    let floatingSessionId = localStorage.getItem('chatbotSessionId') || null;
    
    function toggleFloatingChatbot() {
        const container = document.getElementById('floating-chatbot-container');
        const trigger = document.getElementById('floating-chatbot-trigger');
        
        if (!floatingChatbotOpen) {
            container.style.display = 'block';
            trigger.innerHTML = '✕ Chiudi';
            trigger.style.background = '#dc3545';
            floatingChatbotOpen = true;
            
            setTimeout(() => {
                const input = document.getElementById('floating-chat-input');
                if (input) input.focus();
            }, 100);
            
        } else {
            container.style.display = 'none';
            trigger.innerHTML = '<?php echo esc_js($atts['trigger_text']); ?>';
            trigger.style.background = '#1e6763';
            floatingChatbotOpen = false;
        }
    }
    
    function sendFloatingMessage() {
        const input = document.getElementById('floating-chat-input');
        const message = input.value.trim();
        
        if (!message) return;
        
        addFloatingMessage(message, 'user');
        input.value = '';
        showFloatingTyping();
        
        // Chiamata API
        const payload = { message: message };
        if (floatingSessionId) {
            payload.session_id = floatingSessionId;
        }
        
        fetch('<?php echo esc_js(get_option('chatbot_api_url', 'https://api.viamerano24.it/api')); ?>/chatbot', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
        })
        .then(response => response.json())
        .then(data => {
            hideFloatingTyping();
            
            if (data.message) {
                addFloatingMessage(data.message, 'bot');
            }
            
            if (data.session_id && data.session_id !== floatingSessionId) {
                floatingSessionId = data.session_id;
                localStorage.setItem('chatbotSessionId', data.session_id);
            }
            
            // Gestione booking
            if (data.type === 'booking_redirect' && data.booking_data) {
                handleFloatingBooking(data.booking_data);
            }
        })
        .catch(error => {
            console.error('Errore API:', error);
            hideFloatingTyping();
            addFloatingMessage("Errore di connessione. Riprova più tardi.", 'bot');
        });
    }
    
    function addFloatingMessage(message, sender) {
        const messagesContainer = document.getElementById('floating-chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.style.marginBottom = '15px';
        messageDiv.style.textAlign = sender === 'user' ? 'right' : 'left';
        
        // Formatta il messaggio
        let formattedMessage = message
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br>');
        
        const bubble = document.createElement('div');
        bubble.style.cssText = `
            display: inline-block;
            max-width: 85%;
            padding: 12px 16px;
            border-radius: 18px;
            font-size: 14px;
            line-height: 1.4;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            ${sender === 'user' ? 
                'background: #1e6763; color: white; border-bottom-right-radius: 4px;' : 
                'background: white; color: #2c3e50; border-bottom-left-radius: 4px;'
            }
        `;
        bubble.innerHTML = formattedMessage;
        
        // Aggiungi pulsanti se necessario
        if (sender === 'bot' && message.includes('Per prenotare')) {
            const matches = message.match(/\*\*(\d+)\.\*\*/g);
            if (matches) {
                const buttonContainer = document.createElement('div');
                buttonContainer.style.marginTop = '10px';
                
                matches.forEach(match => {
                    const number = match.replace(/\*\*/g, '').replace('.', '');
                    const button = document.createElement('button');
                    button.textContent = `Prenota ${number}`;
                    button.style.cssText = `
                        background: #f1f5f4;
                        border: 2px solid #1e6763;
                        color: #1e6763;
                        padding: 8px 16px;
                        border-radius: 20px;
                        cursor: pointer;
                        margin: 3px;
                        font-size: 12px;
                        transition: all 0.2s;
                    `;
                    button.onmouseover = () => {
                        button.style.background = '#1e6763';
                        button.style.color = 'white';
                    };
                    button.onmouseout = () => {
                        button.style.background = '#f1f5f4';
                        button.style.color = '#1e6763';
                    };
                    button.onclick = () => {
                        document.getElementById('floating-chat-input').value = number;
                        sendFloatingMessage();
                    };
                    buttonContainer.appendChild(button);
                });
                
                bubble.appendChild(buttonContainer);
            }
        }
        
        messageDiv.appendChild(bubble);
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    function showFloatingTyping() {
        document.getElementById('floating-typing-indicator').style.display = 'block';
    }
    
    function hideFloatingTyping() {
        document.getElementById('floating-typing-indicator').style.display = 'none';
    }
    
    function handleFloatingBooking(bookingData) {
        if (bookingData && bookingData.appartamento && bookingData.check_in && bookingData.check_out) {
            const baseUrl = '<?php echo home_url('/prenotazione/'); ?>';
            const params = new URLSearchParams({
                appartamento: bookingData.appartamento,
                check_in: bookingData.check_in,
                check_out: bookingData.check_out,
                check_in_formatted: bookingData.check_in_formatted,
                check_out_formatted: bookingData.check_out_formatted
            }).toString();
            
            const bookingUrl = `${baseUrl}?${params}`;
            
            const messageHtml = `
                🐚 Perfetto! Paguro ti sta reindirizzando alla prenotazione per <strong>${bookingData.appartamento}</strong><br>
                <a href="${bookingUrl}" style="
                    display: inline-block;
                    background: #1e6763;
                    color: white;
                    padding: 8px 16px;
                    border-radius: 20px;
                    text-decoration: none;
                    margin-top: 8px;
                    font-size: 13px;
                ">Vai alla prenotazione</a>
            `;
            
            addFloatingMessage(messageHtml, 'bot');
            
            setTimeout(() => {
                window.location.href = bookingUrl;
            }, 2000);
        }
    }
    
    // Auto-posizionamento WhatsApp
    document.addEventListener('DOMContentLoaded', function() {
        const whatsappButtons = document.querySelectorAll('[href*="whatsapp"], [href*="wa.me"], [class*="whatsapp"]');
        const trigger = document.getElementById('floating-chatbot-trigger');
        
        if (whatsappButtons.length > 0 && trigger) {
            trigger.style.bottom = '80px';
        }
    });
    </script>
    
    <?php
    return ob_get_clean();
}

// Menu admin per configurazione (aggiornato con Paguro)
add_action('admin_menu', 'appartamenti_chatbot_admin_menu');

function appartamenti_chatbot_admin_menu() {
    add_options_page(
        'Paguro - Chatbot Appartamenti',
        'Paguro Chatbot',
        'manage_options',
        'appartamenti-chatbot',
        'appartamenti_chatbot_admin_page'
    );
}

function appartamenti_chatbot_admin_page() {
    if (isset($_POST['submit'])) {
        update_option('chatbot_api_url', sanitize_url($_POST['api_url']));
        update_option('chatbot_ninja_form_id', intval($_POST['ninja_form_id']));
        echo '<div class="notice notice-success"><p>🐚 Impostazioni di Paguro salvate!</p></div>';
    }
    
    $api_url = get_option('chatbot_api_url', 'http://127.0.0.1:5000/api');
    $ninja_form_id = get_option('chatbot_ninja_form_id', 1);
    ?>
    <div class="wrap">
        <h1>🐚 Configurazione Paguro - Chatbot Appartamenti</h1>
        
        <form method="post" action="">
            <table class="form-table">
                <tr>
                    <th scope="row">URL API Paguro</th>
                    <td>
                        <input type="url" name="api_url" value="<?php echo esc_attr($api_url); ?>" class="regular-text" />
                        <p class="description">URL del server Python (es: http://127.0.0.1:5000/api)</p>
                    </td>
                </tr>
                <tr>
                    <th scope="row">ID Form Ninja Forms</th>
                    <td>
                        <input type="number" name="ninja_form_id" value="<?php echo esc_attr($ninja_form_id); ?>" />
                        <p class="description">ID del form Ninja Forms per le prenotazioni</p>
                    </td>
                </tr>
            </table>
            
            <?php submit_button(); ?>
        </form>
        
        <h2>Come usare Paguro</h2>
        <p><strong>Shortcode per embedare Paguro:</strong></p>
        <code>[appartamenti_chatbot]</code>
        
        <p><strong>Shortcode per Paguro floating:</strong></p>
        <code>[chatbot_floating]</code>
        
        <p><strong>Shortcode Paguro personalizzato:</strong></p>
        <code>[chatbot_floating trigger_text="🐚 Prenota con Paguro" position="bottom-right"]</code>
        
        <h2>🐚 Stato Paguro</h2>
        <div id="system-status">
            <p>🔄 Controllo connessione API...</p>
        </div>
        
        <script>
        // Test connessione API
        fetch('<?php echo esc_js($api_url); ?>/health')
            .then(response => response.json())
            .then(data => {
                document.getElementById('system-status').innerHTML = '✅ <strong>🐚 Paguro online</strong> - Status: ' + data.status;
            })
            .catch(error => {
                document.getElementById('system-status').innerHTML = '❌ <strong>🐚 Paguro offline</strong> - Controlla configurazione server Python';
            });
        </script>
    </div>
    <?php
}
?>
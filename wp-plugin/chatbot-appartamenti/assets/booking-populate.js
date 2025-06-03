/**
 * Booking Form Auto-Population Script - Versione Migliorata
 * Popola automaticamente i campi Ninja Forms e il riepilogo con dati dal chatbot
 */

(function($) {
    'use strict';

    // Configurazione
    var config = {
        maxAttempts: 8, // Ridotto da 15 a 8
        retryDelay: 800, // Ridotto da 1000 a 800ms
        debug: true,
        summaryUpdateDelay: 500
    };

    // Flag globale per tracciare il successo
    var populationCompleted = false;

    // Utility functions
    function log(message, data) {
        if (config.debug) {
            if (data) {
                console.log('📋 [BookingPopulate]', message, data);
            } else {
                console.log('📋 [BookingPopulate]', message);
            }
        }
    }

    function convertDateFormat(dateStr) {
        if (!dateStr || dateStr.indexOf('-') === -1) return dateStr;

        var parts = dateStr.split('-');
        if (parts.length !== 3) return dateStr;

        var year = parts[0];
        var month = parts[1];
        var day = parts[2];

        return day + '/' + month + '/' + year;
    }

    function getUrlParams() {
        var urlParams = new URLSearchParams(window.location.search);
        
        // Decodifica i parametri correttamente
        var checkinFormatted = urlParams.get('check_in_formatted');
        var checkoutFormatted = urlParams.get('check_out_formatted');
        
        if (checkinFormatted) {
            checkinFormatted = decodeURIComponent(checkinFormatted.replace(/\+/g, ' '));
        }
        
        if (checkoutFormatted) {
            checkoutFormatted = decodeURIComponent(checkoutFormatted.replace(/\+/g, ' '));
        }
        
        return {
            appartamento: urlParams.get('appartamento'),
            checkin: checkinFormatted,
            checkout: checkoutFormatted,
            checkinRaw: urlParams.get('check_in'),
            checkoutRaw: urlParams.get('check_out')
        };
    }

    function updateSummary(data) {
        log('🔄 Aggiornamento riepilogo...', data);
        
        var hasData = false;
        
        // Nascondi indicatore di caricamento
        var loadingIndicator = document.getElementById('loading-indicator');
        if (loadingIndicator) {
            loadingIndicator.style.display = 'none';
        }
        
        // Appartamento
        var elemApt = document.getElementById('summary-appartamento');
        if (elemApt && data.appartamento) {
            elemApt.textContent = data.appartamento;
            elemApt.style.color = '#007cba';
            elemApt.style.fontWeight = 'bold';
            hasData = true;
            log('✅ Appartamento aggiornato:', data.appartamento);
        }

        // Check-in
        var elemIn = document.getElementById('summary-checkin');
        if (elemIn && data.checkin) {
            elemIn.innerHTML = '📅 Sabato ' + data.checkin;
            elemIn.style.color = '#28a745';
            hasData = true;
            log('✅ Check-in aggiornato:', data.checkin);
        }

        // Check-out
        var elemOut = document.getElementById('summary-checkout');
        if (elemOut && data.checkout) {
            elemOut.innerHTML = '📅 Sabato ' + data.checkout;
            elemOut.style.color = '#dc3545';
            hasData = true;
            log('✅ Check-out aggiornato:', data.checkout);
        }
        
        if (hasData) {
            // Evidenzia il riepilogo
            var summaryDiv = document.getElementById('booking-summary');
            if (summaryDiv) {
                summaryDiv.style.border = '2px solid #28a745';
                summaryDiv.style.backgroundColor = '#f8fff9';
                
                // Aggiungi un indicatore di successo
                var successIndicator = document.createElement('div');
                successIndicator.innerHTML = '✅ <strong>Dati caricati dal chatbot</strong>';
                successIndicator.style.cssText = 'text-align: center; color: #28a745; margin-top: 10px; font-size: 14px;';
                successIndicator.id = 'success-indicator';
                
                // Rimuovi indicatore precedente se esiste
                var existingIndicator = document.getElementById('success-indicator');
                if (existingIndicator) {
                    existingIndicator.remove();
                }
                
                summaryDiv.appendChild(successIndicator);
            }
            
            log('🎉 Riepilogo aggiornato con successo!');
        } else {
            log('⚠️ Nessun dato disponibile per il riepilogo');
            
            // Mostra messaggio di errore
            var elemApt = document.getElementById('summary-appartamento');
            var elemIn = document.getElementById('summary-checkin');
            var elemOut = document.getElementById('summary-checkout');
            
            if (elemApt) elemApt.textContent = 'Non disponibile';
            if (elemIn) elemIn.textContent = 'Non disponibile';
            if (elemOut) elemOut.textContent = 'Non disponibile';
            
            if (loadingIndicator) {
                loadingIndicator.innerHTML = '❌ <em>Errore nel caricamento dei dati</em>';
                loadingIndicator.style.display = 'block';
                loadingIndicator.style.color = '#dc3545';
            }
        }
    }

    function simulateChangeEvent(element) {
        // Triggera eventi multipli per compatibilità con Ninja Forms
        var events = ['change', 'input', 'blur', 'keyup'];
        
        events.forEach(function(eventType) {
            try {
                if (typeof Event === 'function') {
                    var evt = new Event(eventType, { bubbles: true, cancelable: true });
                    element.dispatchEvent(evt);
                } else {
                    // Fallback per browser più vecchi
                    var evt = document.createEvent('HTMLEvents');
                    evt.initEvent(eventType, true, true);
                    element.dispatchEvent(evt);
                }
            } catch (e) {
                log('⚠️ Errore nell\'evento ' + eventType + ':', e);
            }
        });
        
        // Trigger specifico per Ninja Forms se disponibile
        if (typeof jQuery !== 'undefined' && jQuery.fn.trigger) {
            try {
                jQuery(element).trigger('change').trigger('nf:change');
            } catch (e) {
                log('⚠️ Errore nel trigger jQuery:', e);
            }
        }
    }

    function populateField(field, value, rawValue, fieldNameForLogging) {
        if (!field || (!value && !rawValue)) {
            log('⚠️ Campo o valore nullo per ' + fieldNameForLogging);
            return false;
        }

        var finalValue = value;
        
        // Determina il valore da usare in base al tipo di campo
        if (field.type === 'date' && rawValue) {
            finalValue = rawValue; // YYYY-MM-DD per campi date HTML
        } else if (rawValue && (field.type === 'text' || !field.type)) {
            // Per campi text, usa il formato DD/MM/YYYY se disponibile
            if (rawValue.indexOf('-') > -1) {
                finalValue = convertDateFormat(rawValue);
            } else {
                finalValue = value || rawValue;
            }
        } else {
            finalValue = value || rawValue;
        }

        if (!finalValue) {
            log('⚠️ Nessun valore finale per ' + fieldNameForLogging);
            return false;
        }

        try {
            // Imposta il valore
            field.value = finalValue;
            
            // Simula eventi
            simulateChangeEvent(field);
            
            log('✅ Campo "' + fieldNameForLogging + '" popolato con: ' + finalValue);
            return true;
        } catch (e) {
            log('❌ Errore nel popolare il campo "' + fieldNameForLogging + '":', e);
            return false;
        }
    }

    // Nuova funzione per debug completo dei campi disponibili
    function debugAvailableFields() {
        var formElements = document.querySelectorAll('input, select, textarea');
        log('🔍 DEBUG: Elementi form disponibili (' + formElements.length + '):');
        
        for (var i = 0; i < formElements.length; i++) {
            var field = formElements[i];
            var info = {
                tag: field.tagName,
                type: field.type || 'N/A',
                id: field.id || 'N/A',
                name: field.name || 'N/A',
                placeholder: field.placeholder || 'N/A',
                class: field.className || 'N/A'
            };
            log('   ' + (i+1) + '. ' + info.tag + '[type=' + info.type + '] id="' + info.id + '" name="' + info.name + '" placeholder="' + info.placeholder + '"');
        }
    }

    function findFormFields() {
        var campiTrovati = {
            appartamento: null,
            checkin: null,
            checkout: null
        };

        // Debug completo dei campi disponibili
        debugAvailableFields();

        // Cerca prima per ID specifici (più preciso)
        var specificIds = {
            appartamento: 'appartamento_1748608121609',
            checkin: 'check-in_1748608017696',
            checkout: 'check-out_1748608049117'
        };

        for (var fieldType in specificIds) {
            var element = document.getElementById(specificIds[fieldType]);
            if (element) {
                campiTrovati[fieldType] = element;
                log('✅ Campo ' + fieldType + ' trovato per ID specifico: ' + specificIds[fieldType]);
            }
        }

        // Se non trovati, cerca con selettori generici più ampliati
        if (!campiTrovati.appartamento || !campiTrovati.checkin || !campiTrovati.checkout) {
            var formElements = document.querySelectorAll('input, select, textarea');
            log('🔍 Ricerca generica tra ' + formElements.length + ' elementi');

            for (var i = 0; i < formElements.length; i++) {
                var field = formElements[i];
                var fieldName = (field.name || '').toLowerCase();
                var fieldId = (field.id || '').toLowerCase();
                var fieldPlaceholder = (field.placeholder || '').toLowerCase();
                var fieldClass = (field.className || '').toLowerCase();
                var fieldValue = (field.value || '').toLowerCase();

                // Debug per ogni campo
                log('🔍 Analizzando campo: ID="' + field.id + '", name="' + field.name + '", placeholder="' + field.placeholder + '"');

                // Appartamento - ricerca più ampia
                if (!campiTrovati.appartamento && (
                    fieldName.includes('appartamento') || fieldName.includes('apartment') ||
                    fieldId.includes('appartamento') || fieldId.includes('apartment') ||
                    fieldPlaceholder.includes('appartamento') || fieldPlaceholder.includes('apartment') ||
                    fieldClass.includes('appartamento') || fieldClass.includes('apartment') ||
                    fieldName.includes('casa') || fieldName.includes('house') ||
                    fieldName.includes('room') || fieldName.includes('villa')
                )) {
                    campiTrovati.appartamento = field;
                    log('✅ Campo appartamento trovato (generico): ID="' + field.id + '", name="' + field.name + '"');
                }

                // Check-in - ricerca più ampia
                if (!campiTrovati.checkin && (
                    fieldName.includes('check-in') || fieldName.includes('checkin') ||
                    fieldName.includes('check_in') || fieldName.includes('arrivo') ||
                    fieldId.includes('check-in') || fieldId.includes('checkin') ||
                    fieldId.includes('check_in') || fieldId.includes('arrivo') ||
                    fieldPlaceholder.includes('check-in') || fieldPlaceholder.includes('arrivo') ||
                    fieldPlaceholder.includes('entrada') || fieldPlaceholder.includes('entry') ||
                    fieldName.includes('start') || fieldName.includes('from')
                )) {
                    campiTrovati.checkin = field;
                    log('✅ Campo check-in trovato (generico): ID="' + field.id + '", name="' + field.name + '"');
                }

                // Check-out - ricerca più ampia
                if (!campiTrovati.checkout && (
                    fieldName.includes('check-out') || fieldName.includes('checkout') ||
                    fieldName.includes('check_out') || fieldName.includes('partenza') ||
                    fieldId.includes('check-out') || fieldId.includes('checkout') ||
                    fieldId.includes('check_out') || fieldId.includes('partenza') ||
                    fieldPlaceholder.includes('check-out') || fieldPlaceholder.includes('partenza') ||
                    fieldPlaceholder.includes('salida') || fieldPlaceholder.includes('exit') ||
                    fieldName.includes('end') || fieldName.includes('to')
                )) {
                    campiTrovati.checkout = field;
                    log('✅ Campo check-out trovato (generico): ID="' + field.id + '", name="' + field.name + '"');
                }
            }
        }

        // Log risultati finali
        var foundCount = Object.keys(campiTrovati).filter(function(key) {
            return campiTrovati[key] !== null;
        }).length;
        
        log('📊 Campi trovati: ' + foundCount + '/3');
        
        // Se ancora non trovato nulla, prova ricerca per posizione/ordine
        if (foundCount === 0) {
            log('🔄 Tentativo ricerca per posizione...');
            var allInputs = document.querySelectorAll('input[type="text"], input[type="date"], input:not([type]), select');
            
            if (allInputs.length >= 3) {
                log('📋 Trovati ' + allInputs.length + ' input generici, assegnazione per posizione:');
                
                // Strategia: cerca i campi in base all'ordine tipico di un form booking
                for (var j = 0; j < allInputs.length && foundCount < 3; j++) {
                    var input = allInputs[j];
                    
                    if (!campiTrovati.appartamento && 
                        (j === 0 || input.type === 'text' || input.tagName === 'SELECT')) {
                        campiTrovati.appartamento = input;
                        foundCount++;
                        log('✅ Appartamento assegnato per posizione: ' + (input.id || input.name || 'elemento ' + j));
                    } else if (!campiTrovati.checkin && 
                               (input.type === 'date' || input.type === 'text')) {
                        campiTrovati.checkin = input;
                        foundCount++;
                        log('✅ Check-in assegnato per posizione: ' + (input.id || input.name || 'elemento ' + j));
                    } else if (!campiTrovati.checkout && 
                               (input.type === 'date' || input.type === 'text')) {
                        campiTrovati.checkout = input;
                        foundCount++;
                        log('✅ Check-out assegnato per posizione: ' + (input.id || input.name || 'elemento ' + j));
                    }
                }
                
                log('📊 Campi assegnati per posizione: ' + foundCount + '/3');
            }
        }
        
        return campiTrovati;
    }

    function attemptPopulation(data, attempt) {
        attempt = attempt || 1;
        
        // Se il popolamento è già completato, non fare altri tentativi
        if (populationCompleted) {
            log('✅ Popolamento già completato, saltando tentativo');
            return;
        }
        
        log('🔄 Tentativo popolamento ' + attempt + '/' + config.maxAttempts);

        if (!data || (!data.appartamento && !data.checkinRaw && !data.checkoutRaw)) {
            log('❌ Nessun dato valido per il popolamento');
            updateSummary({}); // Aggiorna comunque il riepilogo con dati vuoti
            return;
        }

        // Aggiorna sempre il riepilogo
        updateSummary(data);

        // Trova e popola i campi del form
        var campi = findFormFields();
        var populatedCount = 0;
        var totalExpectedFields = 0;

        // Conta i campi che dovremmo popolare in base ai dati disponibili
        if (data.appartamento) totalExpectedFields++;
        if (data.checkinRaw || data.checkin) totalExpectedFields++;
        if (data.checkoutRaw || data.checkout) totalExpectedFields++;

        if (campi.appartamento && data.appartamento) {
            if (populateField(campi.appartamento, data.appartamento, null, 'appartamento')) {
                populatedCount++;
            }
        }

        if (campi.checkin && (data.checkinRaw || data.checkin)) {
            if (populateField(campi.checkin, data.checkin, data.checkinRaw, 'check-in')) {
                populatedCount++;
            }
        }

        if (campi.checkout && (data.checkoutRaw || data.checkout)) {
            if (populateField(campi.checkout, data.checkout, data.checkoutRaw, 'check-out')) {
                populatedCount++;
            }
        }

        // Controlla se abbiamo popolato tutti i campi disponibili
        if (populatedCount > 0 && populatedCount === totalExpectedFields) {
            populationCompleted = true;
            log('🎉 Popolamento completato con successo! (' + populatedCount + '/' + totalExpectedFields + ')');
            log('🛑 Interrompendo ulteriori tentativi');
        } else if (attempt < config.maxAttempts && !populationCompleted) {
            log('⏳ Popolamento parziale (' + populatedCount + '/' + totalExpectedFields + '). Riprovo in ' + config.retryDelay + 'ms...');
            setTimeout(function() {
                attemptPopulation(data, attempt + 1);
            }, config.retryDelay);
        } else {
            log('⚠️ Raggiunti i tentativi massimi. Popolamento finale: ' + populatedCount + '/' + totalExpectedFields);
        }
    }

    function setupMutationObserver(data) {
        if (typeof MutationObserver === 'undefined') {
            log('⚠️ MutationObserver non supportato');
            return;
        }

        var observer = new MutationObserver(function(mutations) {
            // Se il popolamento è già completato, non fare nulla
            if (populationCompleted) {
                return;
            }
            
            var shouldRetry = false;
            
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                    for (var i = 0; i < mutation.addedNodes.length; i++) {
                        var node = mutation.addedNodes[i];
                        if (node.nodeType === 1) {
                            var isFormField = node.tagName === 'INPUT' || 
                                            node.tagName === 'SELECT' || 
                                            node.tagName === 'TEXTAREA';
                            var containsFormFields = node.querySelector && 
                                                   node.querySelector('input, select, textarea');
                            
                            if (isFormField || containsFormFields) {
                                shouldRetry = true;
                                break;
                            }
                        }
                    }
                }
            });

            if (shouldRetry) {
                log('🔄 Nuovi campi rilevati dal MutationObserver, riprovando...');
                setTimeout(function() {
                    attemptPopulation(data);
                }, 300); // Ridotto il delay
            }
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });

        // Disconnetti dopo 20 secondi (ridotto da 30)
        setTimeout(function() {
            observer.disconnect();
            log('🔌 MutationObserver disconnesso');
        }, 20000);
        
        // Disconnetti anche quando il popolamento è completato
        var checkCompletion = setInterval(function() {
            if (populationCompleted) {
                observer.disconnect();
                clearInterval(checkCompletion);
                log('🔌 MutationObserver disconnesso (popolamento completato)');
            }
        }, 1000);
    }

    function init() {
        // Evita inizializzazioni multiple
        if (window.bookingPopulateInitialized) {
            log('⚠️ Script già inizializzato, saltando');
            return;
        }
        window.bookingPopulateInitialized = true;
        
        log('🚀 Inizializzazione script booking-populate');
        
        var params = getUrlParams();
        log('📋 Parametri URL:', params);

        if (params.appartamento || params.checkinRaw || params.checkoutRaw) {
            // Aggiorna immediatamente il riepilogo
            setTimeout(function() {
                updateSummary(params);
            }, config.summaryUpdateDelay);
            
            // Aspetta che Ninja Forms sia pronto
            if (typeof jQuery !== 'undefined') {
                jQuery(document).on('nfFormReady', function(e, layoutView) {
                    if (!populationCompleted) {
                        log('🎉 Evento nfFormReady rilevato');
                        setTimeout(function() {
                            attemptPopulation(params);
                        }, 500);
                    }
                });
            }

            // Setup MutationObserver come fallback
            setupMutationObserver(params);

            // Tentativo iniziale ritardato
            setTimeout(function() {
                if (!populationCompleted) {
                    attemptPopulation(params);
                }
            }, 1200); // Aumentato leggermente per dare tempo al form di caricarsi
        } else {
            log('ℹ️ Nessun parametro di booking nell\'URL');
            
            // Aggiorna comunque il riepilogo per mostrare "Non disponibile"
            setTimeout(function() {
                updateSummary({});
            }, config.summaryUpdateDelay);
        }
    }

    // Inizializzazione - con protezione contro multiple chiamate
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        setTimeout(init, 100);
    }

    // Fallback con window.load (solo se non già inizializzato)
    window.addEventListener('load', function() {
        setTimeout(function() {
            if (!window.bookingPopulateInitialized) {
                init();
            }
        }, 1000);
    });

    // Se jQuery è disponibile, usa anche jQuery ready (solo se non già inizializzato)
    if (typeof jQuery !== 'undefined') {
        jQuery(document).ready(function() {
            setTimeout(function() {
                if (!window.bookingPopulateInitialized) {
                    init();
                }
            }, 300);
        });
    }

})(typeof jQuery !== 'undefined' ? jQuery : null);
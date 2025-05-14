/* filepath: c:\Users\fizyo\OneDrive\Masaüstü\discord-bot\webdashboard\static\js\server.js */
document.addEventListener('DOMContentLoaded', function() {
    const guildId = getGuildId();
    if (!guildId) return;
    
    // İlk yükleme - aktif sekmeyi yükle
    loadActivePanelData();
    
    // Tab değişikliklerini dinle
    document.querySelectorAll('button[data-bs-toggle="pill"]').forEach(tab => {
        tab.addEventListener('shown.bs.tab', function(e) {
            const targetId = e.target.getAttribute('data-bs-target');
            loadTabContent(targetId);
        });
    });
    
    // Form olaylarını dinle
    setupFormListeners();
    
    // Toast mesajı gösterimi için eventListener
    setupToastListeners();
});

// Genel hata yakalama
window.addEventListener('error', function(event) {
    reportError({
        message: event.message,
        location: event.filename + ':' + event.lineno,
        stack: event.error ? event.error.stack : 'Stack trace not available'
    });
});

// API istekleri için hata raporlama
function reportError(error) {
    fetch('/api/error-report', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(error)
    }).catch(() => {
        // Sessizce başarısız ol (zaten hata raporlayıcısında hata var)
        console.error('Failed to report error:', error);
    });
}

// Aktif sekmenin içeriğini yükle
function loadActivePanelData() {
    const activeTab = document.querySelector('.nav-link.active');
    if (!activeTab) return;
    
    const targetId = activeTab.getAttribute('data-bs-target');
    loadTabContent(targetId);
}

// Tab ID'sine göre içerik yükleme
function loadTabContent(tabId) {
    switch(tabId) {
        case '#v-pills-general':
            loadGeneralSettings();
            break;
        case '#v-pills-invite':
            loadInviteSettings();
            break;
        case '#v-pills-moderation':
            loadModerationSettings();
            break;
        case '#v-pills-automod':
            loadAutomodSettings();
            // Event listener'ları kur
            document.getElementById('add-blacklisted-word').addEventListener('click', addBlacklistedWord);
            document.getElementById('add-blacklisted-domain').addEventListener('click', addBlacklistedDomain);
            break;
        case '#v-pills-giveaway':
            loadGiveaways();
            setupGiveawayModal();
            break;
        case '#v-pills-logs':
            loadLogSettings();
            break;
        case '#v-pills-game-news':
            loadGameNewsSettings();
            break;
        case '#v-pills-notes':
            setupNotesListeners();
            break;
        default:
            console.log('Bilinmeyen tab ID:', tabId);
    }
}

// Genel ayarları yükle
function loadGeneralSettings() {
    const guildId = getGuildId();
    showTabLoading('#v-pills-general');
    
    fetch(`/api/guild/${guildId}/settings?type=general`)
        .then(response => response.json())
        .then(data => {
            hideTabLoading('#v-pills-general');
            
            if (data.error) {
                showApiError('#v-pills-general', data.error);
                return;
            }
            
            // Form değerlerini doldur
            if (data.prefix) {
                document.getElementById('prefix').value = data.prefix;
            }
            
            if (data.log_channel_id) {
                document.getElementById('log-channel').value = data.log_channel_id;
            }
        })
        .catch(error => {
            hideTabLoading('#v-pills-general');
            showApiError('#v-pills-general', 'Ayarlar yüklenirken bir hata oluştu.');
            console.error('Error loading general settings:', error);
        });
}

// Davet ayarlarını yükle
function loadInviteSettings() {
    const guildId = getGuildId();
    showTabLoading('#v-pills-invite');
    
    fetch(`/api/guild/${guildId}/invites`)
        .then(response => response.json())
        .then(data => {
            hideTabLoading('#v-pills-invite');
            
            if (data.error) {
                showApiError('#v-pills-invite', data.error);
                return;
            }
            
            // İstatistikleri güncelle
            updateInviteStats(data.stats);
            
            // Form değerlerini doldur
            if (data.settings) {
                document.getElementById('invite-system-toggle').checked = data.settings.enabled !== false;
                
                if (data.settings.welcome_channel_id) {
                    document.getElementById('welcome-channel').value = data.settings.welcome_channel_id;
                }
                
                if (data.settings.log_channel_id) {
                    document.getElementById('invite-log-channel').value = data.settings.log_channel_id;
                }
                
                if (data.settings.welcome_message) {
                    document.getElementById('welcome-message').value = data.settings.welcome_message;
                }
            }
            
            // Liderlik tablosunu güncelle
            updateInviteLeaderboard(data.leaderboard || []);
        })
        .catch(error => {
            hideTabLoading('#v-pills-invite');
            showApiError('#v-pills-invite', 'Davet verileri yüklenirken bir hata oluştu.');
            console.error('Error loading invite settings:', error);
        });
}

// AutoMod ayarlarını yükle
function loadAutomodSettings() {
    const guildId = getGuildId();
    showTabLoading('#v-pills-automod');
    
    fetch(`/api/guild/${guildId}/automod/settings`)
        .then(response => response.json())
        .then(data => {
            hideTabLoading('#v-pills-automod');
            
            if (data.error) {
                showApiError('#v-pills-automod', data.error);
                return;
            }
            
            // Genel ayarlar
            document.getElementById('automod-toggle').checked = data.enabled !== false;
            
            // Wordlist
            updateBlacklistedWordsList(data.blacklisted_words || []);
            updateBlacklistedDomainsList(data.blacklisted_domains || []);
            
            // Diğer ayarlar
            if (data.max_mentions) {
                document.getElementById('max-mentions').value = data.max_mentions;
            }
            
            if (data.max_messages) {
                document.getElementById('spam-message-count').value = data.max_messages;
            }
            
            if (data.time_window) {
                document.getElementById('spam-time-window').value = data.time_window;
            }
            
            // Muaf roller ve kanallar listesi güncellenebilir
        })
        .catch(error => {
            hideTabLoading('#v-pills-automod');
            showApiError('#v-pills-automod', 'AutoMod ayarları yüklenirken bir hata oluştu.');
            console.error('Error loading AutoMod settings:', error);
        });
}

// Yasaklı kelime listesini güncelle
function updateBlacklistedWordsList(words) {
    const container = document.querySelector('.blacklisted-items-container.words-container');
    
    if (!words || words.length === 0) {
        container.innerHTML = '<div class="text-center text-muted py-3">Yasaklı kelime bulunmuyor</div>';
        return;
    }
    
    container.innerHTML = '';
    
    words.forEach(word => {
        const item = document.createElement('div');
        item.className = 'blacklist-item d-flex justify-content-between align-items-center p-2 border-bottom';
        
        const wordSpan = document.createElement('span');
        wordSpan.textContent = word;
        
        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'btn btn-sm btn-outline-danger';
        deleteBtn.innerHTML = '<i class="fas fa-times"></i>';
        deleteBtn.onclick = function() {
            removeBlacklistedWord(word);
        };
        
        item.appendChild(wordSpan);
        item.appendChild(deleteBtn);
        container.appendChild(item);
    });
}

// Yasaklı domain listesini güncelle
function updateBlacklistedDomainsList(domains) {
    const container = document.querySelector('.blacklisted-items-container.domains-container');
    
    if (!domains || domains.length === 0) {
        container.innerHTML = '<div class="text-center text-muted py-3">Yasaklı domain bulunmuyor</div>';
        return;
    }
    
    container.innerHTML = '';
    
    domains.forEach(domain => {
        const item = document.createElement('div');
        item.className = 'blacklist-item d-flex justify-content-between align-items-center p-2 border-bottom';
        
        const domainSpan = document.createElement('span');
        domainSpan.textContent = domain;
        
        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'btn btn-sm btn-outline-danger';
        deleteBtn.innerHTML = '<i class="fas fa-times"></i>';
        deleteBtn.onclick = function() {
            removeBlacklistedDomain(domain);
        };
        
        item.appendChild(domainSpan);
        item.appendChild(deleteBtn);
        container.appendChild(item);
    });
}

// Yasaklı kelime ekle
function addBlacklistedWord() {
    const input = document.getElementById('blacklisted-word');
    const word = input.value.trim();
    
    if (!word) {
        showToast('Lütfen bir kelime girin', 'warning');
        return;
    }
    
    const guildId = getGuildId();
    
    fetch(`/api/guild/${guildId}/automod/blacklist/add`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ word: word })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast(`"${word}" yasaklı kelimelere eklendi`, 'success');
            input.value = '';
            // Listeyi yeniden yükle
            loadAutomodSettings();
        } else {
            showToast('Kelime eklenirken bir hata oluştu: ' + data.error, 'error');
        }
    })
    .catch(error => {
        showToast('Bir hata oluştu: ' + error, 'error');
    });
}

// Yasaklı kelime kaldır
function removeBlacklistedWord(word) {
    const guildId = getGuildId();
    
    fetch(`/api/guild/${guildId}/automod/blacklist/remove`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ word: word })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast(`"${word}" yasaklı kelimelerden kaldırıldı`, 'success');
            // Listeyi yeniden yükle
            loadAutomodSettings();
        } else {
            showToast('Kelime kaldırılırken bir hata oluştu: ' + data.error, 'error');
        }
    })
    .catch(error => {
        showToast('Bir hata oluştu: ' + error, 'error');
    });
}

// Yasaklı domain ekle
function addBlacklistedDomain() {
    const input = document.getElementById('blacklisted-domain');
    const domain = input.value.trim();
    
    if (!domain) {
        showToast('Lütfen bir domain girin', 'warning');
        return;
    }
    
    const guildId = getGuildId();
    
    fetch(`/api/guild/${guildId}/automod/domain/add`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ domain: domain })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast(`"${domain}" yasaklı domainlere eklendi`, 'success');
            input.value = '';
            // Listeyi yeniden yükle
            loadAutomodSettings();
        } else {
            showToast('Domain eklenirken bir hata oluştu: ' + data.error, 'error');
        }
    })
    .catch(error => {
        showToast('Bir hata oluştu: ' + error, 'error');
    });
}

// Yasaklı domain kaldır
function removeBlacklistedDomain(domain) {
    const guildId = getGuildId();
    
    fetch(`/api/guild/${guildId}/automod/domain/remove`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ domain: domain })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast(`"${domain}" yasaklı domainlerden kaldırıldı`, 'success');
            // Listeyi yeniden yükle
            loadAutomodSettings();
        } else {
            showToast('Domain kaldırılırken bir hata oluştu: ' + data.error, 'error');
        }
    })
    .catch(error => {
        showToast('Bir hata oluştu: ' + error, 'error');
    });
}

// AutoMod ayarlarını kaydet
function saveAutomodSettings(form) {
    const guildId = getGuildId();
    showLoading(form);
    
    const settings = {
        enabled: document.getElementById('automod-toggle').checked,
        max_mentions: parseInt(document.getElementById('max-mentions').value),
        max_messages: parseInt(document.getElementById('spam-message-count').value),
        time_window: parseInt(document.getElementById('spam-time-window').value)
    };
    
    fetch(`/api/guild/${guildId}/automod/settings`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(settings)
    })
    .then(response => response.json())
    .then(data => {
        hideLoading(form);
        
        if (data.success) {
            showToast('AutoMod ayarları başarıyla güncellendi!', 'success');
        } else {
            showToast('Ayarlar güncellenirken bir hata oluştu: ' + data.error, 'error');
        }
    })
    .catch(error => {
        hideLoading(form);
        showToast('Bir hata oluştu: ' + error, 'error');
        console.error('Error saving AutoMod settings:', error);
    });
}

// Oyun haberleri ayarlarını yükle
function loadGameNewsSettings() {
    const guildId = getGuildId();
    showTabLoading('#v-pills-game-news');
    
    fetch(`/api/guild/${guildId}/game-news/settings`)
        .then(response => response.json())
        .then(data => {
            hideTabLoading('#v-pills-game-news');
            
            if (data.error) {
                showApiError('#v-pills-game-news', data.error);
                return;
            }
            
            // Form değerlerini doldur
            document.getElementById('enable-game-news').checked = data.enabled;
            
            if (data.news_channel_id) {
                document.getElementById('news-channel').value = data.news_channel_id;
            }
            
            if (data.ping_role_id) {
                document.getElementById('ping-role').value = data.ping_role_id;
            }
            
            document.getElementById('epic-games-source').checked = data.news_sources?.epic_games !== false;
            document.getElementById('steam-deals-source').checked = data.news_sources?.steam_deals !== false;
            
            if (data.check_interval_minutes) {
                document.getElementById('check-interval').value = data.check_interval_minutes;
            }
            
            if (data.min_discount_percent) {
                document.getElementById('min-discount').value = data.min_discount_percent;
            }
            
            // Son haberleri göster
            if (data.last_news) {
                updateLastNewsDisplay(data.last_news);
            }
        })
        .catch(error => {
            hideTabLoading('#v-pills-game-news');
            showApiError('#v-pills-game-news', 'Ayarlar yüklenirken bir hata oluştu.');
            console.error('Error loading game news settings:', error);
        });
        
    // Test webhook butonu için event listener
    document.getElementById('test-webhook').addEventListener('click', function() {
        testGameNewsWebhook(guildId);
    });
}

// Son haberleri görüntüle
function updateLastNewsDisplay(lastNews) {
    const container = document.getElementById('last-news-container');
    if (!lastNews || (!lastNews.epic_free.length && !lastNews.steam_deals.length)) {
        container.textContent = 'Henüz haber gönderilmedi.';
        return;
    }
    
    let html = '';
    
    if (lastNews.epic_free.length > 0) {
        html += '<p><strong>Epic Games Son Ücretsiz Oyunlar:</strong></p>';
        html += '<ul class="mb-3">';
        lastNews.epic_free.slice(-3).forEach(game => {
            html += `<li>${game.title}</li>`;
        });
        html += '</ul>';
    }
    
    if (lastNews.steam_deals.length > 0) {
        html += '<p><strong>Steam Son İndirimler:</strong></p>';
        html += '<ul>';
        lastNews.steam_deals.slice(-3).forEach(deal => {
            html += `<li>${deal.title} (-${deal.discount_percent}%)</li>`;
        });
        html += '</ul>';
    }
    
    container.innerHTML = html;
}

// Test webhook fonksiyonu
function testGameNewsWebhook(guildId) {
    const button = document.getElementById('test-webhook');
    const originalText = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Gönderiliyor...';
    button.disabled = true;
    
    fetch(`/api/guild/${guildId}/game-news/test`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        button.innerHTML = originalText;
        button.disabled = false;
        
        if (data.success) {
            showToast('Test mesajları başarıyla gönderildi!', 'success');
        } else {
            showToast('Test mesajı gönderilemedi: ' + data.error, 'error');
        }
    })
    .catch(error => {
        button.innerHTML = originalText;
        button.disabled = false;
        showToast('Bir hata oluştu: ' + error, 'error');
    });
}

// Oyun haberleri ayarlarını kaydet
function saveGameNewsSettings(form) {
    const guildId = getGuildId();
    showLoading(form);
    
    const settings = {
        enabled: document.getElementById('enable-game-news').checked,
        news_channel_id: document.getElementById('news-channel').value,
        ping_role_id: document.getElementById('ping-role').value,
        check_interval_minutes: parseInt(document.getElementById('check-interval').value),
        min_discount_percent: parseInt(document.getElementById('min-discount').value),
        news_sources: {
            epic_games: document.getElementById('epic-games-source').checked,
            steam_deals: document.getElementById('steam-deals-source').checked
        }
    };
    
    fetch(`/api/guild/${guildId}/game-news/settings`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(settings)
    })
    .then(response => response.json())
    .then(data => {
        hideLoading(form);
        
        if (data.success) {
            showToast('Oyun haberleri ayarları başarıyla güncellendi!', 'success');
        } else {
            showToast('Ayarlar güncellenirken bir hata oluştu: ' + data.error, 'error');
        }
    })
    .catch(error => {
        hideLoading(form);
        showToast('Bir hata oluştu: ' + error, 'error');
    });
}

// Çekiliş yönetimi için gerekli fonksiyonlar

// Çekilişleri yükle
function loadGiveaways() {
    const guildId = getGuildId();
    showTabLoading('#v-pills-giveaway');
    
    fetch(`/api/guild/${guildId}/giveaways`)
        .then(response => response.json())
        .then(data => {
            hideTabLoading('#v-pills-giveaway');
            
            if (data.error) {
                showApiError('#v-pills-giveaway', data.error);
                return;
            }
            
            // Aktif çekilişleri göster
            updateActiveGiveaways(data.active || []);
            
            // Geçmiş çekilişleri göster
            updatePastGiveaways(data.past || []);
        })
        .catch(error => {
            hideTabLoading('#v-pills-giveaway');
            showApiError('#v-pills-giveaway', 'Çekilişler yüklenirken bir hata oluştu.');
            console.error('Error loading giveaways:', error);
        });
}

// Aktif çekilişleri listele
function updateActiveGiveaways(giveaways) {
    const tableBody = document.querySelector('#active-giveaways-table tbody');
    const noGiveawaysMsg = document.getElementById('no-active-giveaways');
    
    tableBody.innerHTML = '';
    
    if (!giveaways || giveaways.length === 0) {
        noGiveawaysMsg.classList.remove('d-none');
        return;
    }
    
    noGiveawaysMsg.classList.add('d-none');
    
    giveaways.forEach(giveaway => {
        const row = document.createElement('tr');
        
        // Ödül hücresi
        const prizeCell = document.createElement('td');
        prizeCell.textContent = giveaway.prize;
        row.appendChild(prizeCell);
        
        // Kanal hücresi
        const channelCell = document.createElement('td');
        channelCell.textContent = `#${giveaway.channel_name}`;
        row.appendChild(channelCell);
        
        // Bitiş tarihi hücresi
        const endTimeCell = document.createElement('td');
        const endTime = new Date(giveaway.end_time);
        const timeRemaining = getTimeRemaining(endTime);
        endTimeCell.innerHTML = `<span class="countdown" data-end="${giveaway.end_time}">${timeRemaining}</span>`;
        row.appendChild(endTimeCell);
        
        // Katılımcılar hücresi
        const entriesCell = document.createElement('td');
        entriesCell.textContent = giveaway.entries;
        row.appendChild(entriesCell);
        
        // Kazanan sayısı hücresi
        const winnersCell = document.createElement('td');
        winnersCell.textContent = giveaway.winner_count;
        row.appendChild(winnersCell);
        
        // İşlemler hücresi
        const actionsCell = document.createElement('td');
        
        // Düzenle butonu
        const editBtn = document.createElement('button');
        editBtn.className = 'btn btn-sm btn-outline-primary me-1';
        editBtn.innerHTML = '<i class="fas fa-edit"></i>';
        editBtn.onclick = function() {
            editGiveaway(giveaway.id);
        };
        actionsCell.appendChild(editBtn);
        
        // Bitir butonu
        const endBtn = document.createElement('button');
        endBtn.className = 'btn btn-sm btn-outline-warning me-1';
        endBtn.innerHTML = '<i class="fas fa-stop"></i>';
        endBtn.onclick = function() {
            endGiveaway(giveaway.id);
        };
        actionsCell.appendChild(endBtn);
        
        // Sil butonu
        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'btn btn-sm btn-outline-danger';
        deleteBtn.innerHTML = '<i class="fas fa-trash"></i>';
        deleteBtn.onclick = function() {
            deleteGiveaway(giveaway.id);
        };
        actionsCell.appendChild(deleteBtn);
        
        row.appendChild(actionsCell);
        
        tableBody.appendChild(row);
    });
    
    // Countdownları güncelle
    startCountdownUpdates();
}

// Geçmiş çekilişleri listele
function updatePastGiveaways(giveaways) {
    const tableBody = document.querySelector('#past-giveaways-table tbody');
    const noGiveawaysMsg = document.getElementById('no-past-giveaways');
    
    tableBody.innerHTML = '';
    
    if (!giveaways || giveaways.length === 0) {
        noGiveawaysMsg.classList.remove('d-none');
        return;
    }
    
    noGiveawaysMsg.classList.add('d-none');
    
    giveaways.forEach(giveaway => {
        const row = document.createElement('tr');
        
        // Ödül hücresi
        const prizeCell = document.createElement('td');
        prizeCell.textContent = giveaway.prize;
        row.appendChild(prizeCell);
        
        // Kanal hücresi
        const channelCell = document.createElement('td');
        channelCell.textContent = `#${giveaway.channel_name}`;
        row.appendChild(channelCell);
        
        // Bitiş tarihi hücresi
        const endTimeCell = document.createElement('td');
        const endDate = new Date(giveaway.end_time);
        endTimeCell.textContent = endDate.toLocaleDateString() + ' ' + endDate.toLocaleTimeString();
        row.appendChild(endTimeCell);
        
        // Katılımcılar hücresi
        const entriesCell = document.createElement('td');
        entriesCell.textContent = giveaway.entries;
        row.appendChild(entriesCell);
        
        // Kazananlar hücresi
        const winnersCell = document.createElement('td');
        if (giveaway.winners && giveaway.winners.length > 0) {
            winnersCell.textContent = giveaway.winners.join(', ');
        } else {
            winnersCell.innerHTML = '<em>Kazanan yok</em>';
        }
        row.appendChild(winnersCell);
        
        tableBody.appendChild(row);
    });
}

// Kalan süreyi hesapla
function getTimeRemaining(endTime) {
    const total = Date.parse(endTime) - Date.parse(new Date());
    
    if (total <= 0) {
        return 'Bitti';
    }
    
    const seconds = Math.floor((total / 1000) % 60);
    const minutes = Math.floor((total / 1000 / 60) % 60);
    const hours = Math.floor((total / (1000 * 60 * 60)) % 24);
    const days = Math.floor(total / (1000 * 60 * 60 * 24));
    
    if (days > 0) {
        return `${days} gün ${hours} saat`;
    }
    
    return `${hours} saat ${minutes} dakika`;
}

// Geri sayımları güncelle
function startCountdownUpdates() {
    // Her dakika güncelleme yap
    setInterval(() => {
        const countdowns = document.querySelectorAll('.countdown');
        countdowns.forEach(el => {
            const endTime = el.dataset.end;
            el.textContent = getTimeRemaining(endTime);
        });
    }, 60000); // 1 dakika
}

// Çekiliş modalını ayarla
function setupGiveawayModal() {
    document.getElementById('create-giveaway-btn').addEventListener('click', function() {
        const modal = new bootstrap.Modal(document.getElementById('create-giveaway-modal'));
        modal.show();
    });
    
    document.getElementById('giveaway-required-role-toggle').addEventListener('change', function() {
        document.getElementById('required-role-container').style.display = this.checked ? 'block' : 'none';
    });
    
    document.getElementById('start-giveaway-btn').addEventListener('click', function() {
        createGiveaway();
    });
}

// Yeni çekiliş oluştur
function createGiveaway() {
    const form = document.getElementById('giveaway-form');
    
    // Form doğrulama
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }
    
    const prize = document.getElementById('giveaway-prize').value;
    const channelId = document.getElementById('giveaway-channel').value;
    const winnerCount = document.getElementById('giveaway-winners').value;
    const duration = document.getElementById('giveaway-duration').value;
    const description = document.getElementById('giveaway-description').value;
    
    let requiredRoleId = null;
    if (document.getElementById('giveaway-required-role-toggle').checked) {
        requiredRoleId = document.getElementById('giveaway-required-role').value;
    }
    
    const guildId = getGuildId();
    const saveBtn = document.getElementById('start-giveaway-btn');
    
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Oluşturuluyor...';
    
    fetch(`/api/guild/${guildId}/giveaways/create`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            prize: prize,
            channel_id: channelId,
            winner_count: parseInt(winnerCount),
            duration_hours: parseInt(duration),
            description: description,
            required_role_id: requiredRoleId
        })
    })
    .then(response => response.json())
    .then(data => {
        saveBtn.disabled = false;
        saveBtn.innerHTML = '<i class="fas fa-play"></i> Çekilişi Başlat';
        
        if (data.success) {
            showToast('Çekiliş başarıyla oluşturuldu!', 'success');
            bootstrap.Modal.getInstance(document.getElementById('create-giveaway-modal')).hide();
            
            // Form alanlarını temizle
            document.getElementById('giveaway-prize').value = '';
            document.getElementById('giveaway-description').value = '';
            document.getElementById('giveaway-winners').value = '1';
            document.getElementById('giveaway-duration').value = '24';
            document.getElementById('giveaway-required-role-toggle').checked = false;
            document.getElementById('required-role-container').style.display = 'none';
            
            // Çekiliş listesini yenile
            loadGiveaways();
        } else {
            showToast('Çekiliş oluşturulurken bir hata oluştu: ' + data.error, 'error');
        }
    })
    .catch(error => {
        saveBtn.disabled = false;
        saveBtn.innerHTML = '<i class="fas fa-play"></i> Çekilişi Başlat';
        showToast('Bir hata oluştu: ' + error, 'error');
    });
}

// Çekiliş düzenle
function editGiveaway(giveawayId) {
    // İlgili implementasyon eklenebilir
    showToast('Çekiliş düzenleme özelliği yakında eklenecek', 'info');
}

// Çekilişi erken bitir
function endGiveaway(giveawayId) {
    if (!confirm('Çekilişi şimdi bitirmek istediğinize emin misiniz?')) {
        return;
    }
    
    const guildId = getGuildId();
    
    fetch(`/api/guild/${guildId}/giveaways/${giveawayId}/end`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Çekiliş başarıyla sonlandırıldı!', 'success');
            loadGiveaways();
        } else {
            showToast('Çekiliş sonlandırılırken bir hata oluştu: ' + data.error, 'error');
        }
    })
    .catch(error => {
        showToast('Bir hata oluştu: ' + error, 'error');
    });
}

// Çekiliş sil
function deleteGiveaway(giveawayId) {
    if (!confirm('Çekilişi silmek istediğinize emin misiniz? Bu işlem geri alınamaz!')) {
        return;
    }
    
    const guildId = getGuildId();
    
    fetch(`/api/guild/${guildId}/giveaways/${giveawayId}/delete`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Çekiliş başarıyla silindi!', 'success');
            loadGiveaways();
        } else {
            showToast('Çekiliş silinirken bir hata oluştu: ' + data.error, 'error');
        }
    })
    .catch(error => {
        showToast('Bir hata oluştu: ' + error, 'error');
    });
}

// Diğer içerik yükleme fonksiyonları benzer şekilde oluşturulabilir

// İstatistikleri güncelle
function updateInviteStats(stats) {
    if (!stats) return;
    
    // Sayıları animasyonlu olarak göster
    animateCounter('total-invites', stats.total_invites || 0);
    animateCounter('active-inviters', stats.active_inviters || 0);
    animateCounter('tracked-users', stats.tracked_users || 0);
}

// Sayıyı animasyonla güncelle
function animateCounter(elementId, endValue) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const startValue = parseInt(element.textContent) || 0;
    const duration = 1000; // ms
    const frameRate = 20; // her 20ms'de bir güncelle
    const steps = duration / frameRate;
    const increment = (endValue - startValue) / steps;
    
    let currentValue = startValue;
    let currentStep = 0;
    
    const timer = setInterval(() => {
        currentStep++;
        currentValue += increment;
        
        if (currentStep >= steps) {
            clearInterval(timer);
            currentValue = endValue;
        }
        
        element.textContent = Math.round(currentValue);
    }, frameRate);
}

// Davet liderlik tablosunu güncelle
function updateInviteLeaderboard(leaderboard) {
    const leaderboardTable = document.getElementById('invite-leaderboard');
    if (!leaderboardTable) return;
    
    const tbody = leaderboardTable.querySelector('tbody');
    tbody.innerHTML = '';
    
    if (!leaderboard.length) {
        tbody.innerHTML = `<tr><td colspan="5" class="text-center py-4">Henüz davet verisi bulunmuyor</td></tr>`;
        return;
    }
    
    leaderboard.forEach((entry, index) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${index + 1}</td>
            <td>
                <div class="d-flex align-items-center">
                    ${entry.avatar ? `<img src="${entry.avatar}" class="avatar-img me-2" alt="">` : 
                      `<div class="avatar-placeholder me-2">${entry.username ? entry.username[0] : '?'}</div>`}
                    <span>${entry.username || `Kullanıcı#${entry.user_id}`}</span>
                </div>
            </td>
            <td>${entry.total}</td>
            <td>${entry.bonus || 0}</td>
            <td>
                <button class="btn btn-sm btn-primary add-bonus" data-user-id="${entry.user_id}">
                    <i class="fas fa-plus"></i> Bonus
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
    
    // Bonus ekleme düğmelerine tıklama olayı ekle
    document.querySelectorAll('.add-bonus').forEach(btn => {
        btn.addEventListener('click', function() {
            const userId = this.getAttribute('data-user-id');
            showBonusModal(userId);
        });
    });
}

// Form event listener'ları
function setupFormListeners() {
    // Genel ayarlar formu
    const generalForm = document.getElementById('general-settings-form');
    if (generalForm) {
        generalForm.addEventListener('submit', function(e) {
            e.preventDefault();
            saveGeneralSettings(this);
        });
    }
    
    // Davet ayarları formu
    const inviteForm = document.getElementById('invite-settings-form');
    if (inviteForm) {
        inviteForm.addEventListener('submit', function(e) {
            e.preventDefault();
            saveInviteSettings(this);
        });
    }
    
    // Oyun haberleri ayarları formu
    const gameNewsForm = document.getElementById('game-news-settings-form');
    if (gameNewsForm) {
        gameNewsForm.addEventListener('submit', function(e) {
            e.preventDefault();
            saveGameNewsSettings(this);
        });
    }
    
    // AutoMod ayarları formu
    const automodForm = document.getElementById('automod-settings-form');
    if (automodForm) {
        automodForm.addEventListener('submit', function(e) {
            e.preventDefault();
            saveAutomodSettings(this);
        });
    }
    
    // Diğer formlar için benzer listener'lar eklenebilir
}

// Genel ayarları kaydet
function saveGeneralSettings(form) {
    const prefix = document.getElementById('prefix').value;
    const logChannel = document.getElementById('log-channel').value;
    
    const guildId = getGuildId();
    if (!guildId) return;
    
    showLoading(form);
    
    fetch(`/api/guild/${guildId}/settings`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            type: 'general',
            prefix: prefix,
            log_channel_id: logChannel
        })
    })
    .then(response => response.json())
    .then(data => {
        hideLoading(form);
        
        if (data.success) {
            showToast('Ayarlar başarıyla kaydedildi!', 'success');
        } else {
            showToast('Ayarlar kaydedilirken bir hata oluştu: ' + data.error, 'error');
        }
    })
    .catch(error => {
        hideLoading(form);
        showToast('Bir hata oluştu: ' + error, 'error');
        console.error('Error saving general settings:', error);
    });
}

// Davet ayarlarını kaydet
function saveInviteSettings(form) {
    const enabled = document.getElementById('invite-system-toggle').checked;
    const welcomeChannel = document.getElementById('welcome-channel').value;
    const inviteLogChannel = document.getElementById('invite-log-channel').value;
    const welcomeMessage = document.getElementById('welcome-message').value;
    
    const guildId = getGuildId();
    if (!guildId) return;
    
    showLoading(form);
    
    fetch(`/api/guild/${guildId}/settings`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            type: 'invite',
            settings: {
                enabled: enabled,
                welcome_channel_id: welcomeChannel,
                log_channel_id: inviteLogChannel,
                welcome_message: welcomeMessage
            }
        })
    })
    .then(response => response.json())
    .then(data => {
        hideLoading(form);
        
        if (data.success) {
            showToast('Davet sistemi ayarları başarıyla kaydedildi!', 'success');
        } else {
            showToast('Ayarlar kaydedilirken bir hata oluştu: ' + data.error, 'error');
        }
    })
    .catch(error => {
        hideLoading(form);
        showToast('Bir hata oluştu: ' + error, 'error');
        console.error('Error saving invite settings:', error);
    });
}

// Bonus davet ekleme modalını göster
function showBonusModal(userId) {
    let modal = document.getElementById('bonus-modal');
    
    if (!modal) {
        // Modal yoksa oluştur
        const modalHTML = `
            <div class="modal fade" id="bonus-modal" tabindex="-1" aria-hidden="true">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Bonus Davet Ekle</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <form id="bonus-form">
                                <input type="hidden" id="bonus-user-id" value="">
                                <div class="mb-3">
                                    <label for="bonus-amount" class="form-label">Bonus Davet Miktarı</label>
                                    <input type="number" class="form-control" id="bonus-amount" min="0" value="1">
                                    <div class="form-text">Kullanıcıya eklenecek bonus davet sayısı</div>
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">İptal</button>
                            <button type="button" class="btn btn-primary" id="save-bonus">
                                <i class="fas fa-check"></i> Ekle
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        modal = document.getElementById('bonus-modal');
        
        // Bonus ekleme butonu için event listener
        document.getElementById('save-bonus').addEventListener('click', function() {
            saveBonusInvites();
        });
    }
    
    // Form değerlerini ayarla
    document.getElementById('bonus-user-id').value = userId;
    document.getElementById('bonus-amount').value = "1";
    
    // Modalı göster
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
}

// Bonus davetleri kaydet
function saveBonusInvites() {
    const userId = document.getElementById('bonus-user-id').value;
    const amount = parseInt(document.getElementById('bonus-amount').value) || 0;
    
    if (amount <= 0) {
        showToast('Lütfen geçerli bir miktar girin', 'warning');
        return;
    }
    
    const guildId = getGuildId();
    if (!guildId) return;
    
    const saveBtn = document.getElementById('save-bonus');
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> İşleniyor...';
    
    fetch(`/api/guild/${guildId}/invite/bonus`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            user_id: userId,
            amount: amount
        })
    })
    .then(response => response.json())
    .then(data => {
        saveBtn.disabled = false;
        saveBtn.innerHTML = '<i class="fas fa-check"></i> Ekle';
        
        if (data.success) {
            showToast(`${amount} bonus davet başarıyla eklendi`, 'success');
            bootstrap.Modal.getInstance(document.getElementById('bonus-modal')).hide();
            
            // Davet verilerini yeniden yükle
            loadInviteSettings();
        } else {
            showToast('Bonus davetler eklenirken bir hata oluştu: ' + data.error, 'error');
        }
    })
    .catch(error => {
        saveBtn.disabled = false;
        saveBtn.innerHTML = '<i class="fas fa-check"></i> Ekle';
        
        showToast('Bir hata oluştu: ' + error, 'error');
        console.error('Error saving bonus invites:', error);
    });
}

// Notlar/moderasyon kayıtları için event listener'lar
function setupNotesListeners() {
    // Kullanıcı arama butonu
    document.getElementById('notes-search-button').addEventListener('click', function() {
        const userId = document.getElementById('notes-search-input').value.trim();
        if (userId) {
            loadUserNotes(userId);
        } else {
            showToast('Lütfen geçerli bir kullanıcı ID\'si girin', 'warning');
        }
    });
    
    // Enter tuşu ile arama
    document.getElementById('notes-search-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            const userId = this.value.trim();
            if (userId) {
                loadUserNotes(userId);
            } else {
                showToast('Lütfen geçerli bir kullanıcı ID\'si girin', 'warning');
            }
        }
    });
    
    // Not silme modalı
    let noteToDelete = null;
    
    // Delete butonlarını dinle (butonlar dinamik olarak eklendiği için event delegation kullanıyoruz)
    document.addEventListener('click', function(e) {
        if (e.target && e.target.classList.contains('delete-note-btn')) {
            const btn = e.target;
            const userId = btn.dataset.userId;
            const noteType = btn.dataset.noteType;
            const noteId = btn.dataset.noteId;
            
            noteToDelete = { userId, noteType, noteId };
            
            // Modalı göster
            const modal = new bootstrap.Modal(document.getElementById('delete-note-modal'));
            modal.show();
        }
    });
    
    // Silme onayı
    document.getElementById('confirm-delete-note').addEventListener('click', function() {
        if (noteToDelete) {
            deleteNote(noteToDelete.userId, noteToDelete.noteType, noteToDelete.noteId);
        }
    });
}

// Kullanıcı notlarını yükle
function loadUserNotes(userId) {
    const guildId = getGuildId();
    showLoading(document.querySelector('.notes-result-container'));
    
    fetch(`/api/guild/${guildId}/notes/${userId}`)
        .then(response => response.json())
        .then(data => {
            hideLoading(document.querySelector('.notes-result-container'));
            
            if (data.error) {
                showToast(data.error, 'error');
                return;
            }
            
            document.querySelector('.notes-placeholder').style.display = 'none';
            document.querySelector('.notes-data').style.display = 'block';
            
            // Kullanıcı bilgilerini güncelle
            document.getElementById('notes-user-name').textContent = data.user.username;
            document.getElementById('notes-user-id').textContent = `ID: ${userId}`;
            document.getElementById('notes-user-avatar').src = data.user.avatar_url;
            
            // Notları tablolara ekle
            updateNotesTable('warnings', data.notes.UYARILAR || []);
            updateNotesTable('timeouts', data.notes.TIMEOUTLAR || []);
            updateNotesTable('bans', data.notes.BANLAR || []);
        })
        .catch(error => {
            hideLoading(document.querySelector('.notes-result-container'));
            showToast('Kayıtlar yüklenirken bir hata oluştu', 'error');
            console.error('Error loading user notes:', error);
        });
}

// Not tablosunu güncelle
function updateNotesTable(type, notes) {
    const tableBody = document.getElementById(`${type}-table-body`);
    const noMessage = document.getElementById(`no-${type}-message`);
    tableBody.innerHTML = '';
    
    if (notes.length === 0) {
        noMessage.classList.remove('d-none');
        return;
    }
    
    noMessage.classList.add('d-none');
    
    notes.forEach((note, index) => {
        const row = document.createElement('tr');
        
        // Index hücresi
        const indexCell = document.createElement('td');
        indexCell.textContent = index + 1;
        row.appendChild(indexCell);
        
        // Tarih hücresi
        const dateCell = document.createElement('td');
        dateCell.textContent = note.tarih || 'Belirtilmedi';
        row.appendChild(dateCell);
        
        // Sebep hücresi
        const reasonCell = document.createElement('td');
        reasonCell.textContent = note.sebep || 'Belirtilmedi';
        row.appendChild(reasonCell);
        
        // Süre hücresi (sadece timeout'lar için)
        if (type === 'timeouts') {
            const durationCell = document.createElement('td');
            durationCell.textContent = note.süre || 'Belirtilmedi';
            row.appendChild(durationCell);
        }
        
        // Moderatör hücresi
        const modCell = document.createElement('td');
        modCell.textContent = note.moderator || 'Bilinmiyor';
        if (note.moderator === 'AutoMod') {
            modCell.innerHTML = '<i class="fas fa-robot"></i> AutoMod';
        }
        row.appendChild(modCell);
        
        // İşlemler hücresi
        const actionsCell = document.createElement('td');
        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'btn btn-sm btn-outline-danger delete-note-btn';
        deleteBtn.innerHTML = '<i class="fas fa-trash"></i>';
        deleteBtn.dataset.userId = document.getElementById('notes-user-id').textContent.split(':')[1].trim();
        deleteBtn.dataset.noteType = type === 'warnings' ? 'UYARILAR' : (type === 'timeouts' ? 'TIMEOUTLAR' : 'BANLAR');
        deleteBtn.dataset.noteId = index + 1;
        actionsCell.appendChild(deleteBtn);
        row.appendChild(actionsCell);
        
        tableBody.appendChild(row);
    });
}

// Not sil
function deleteNote(userId, noteType, noteId) {
    const guildId = getGuildId();
    
    fetch(`/api/guild/${guildId}/notes/delete`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            user_id: userId,
            note_type: noteType,
            note_id: noteId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Kayıt başarıyla silindi', 'success');
            // Kapatma
            const modal = bootstrap.Modal.getInstance(document.getElementById('delete-note-modal'));
            modal.hide();
            // Notları yeniden yükle
            loadUserNotes(userId);
        } else {
            showToast('Kayıt silinemedi: ' + data.error, 'error');
        }
    })
    .catch(error => {
        showToast('Bir hata oluştu: ' + error, 'error');
    });
}

// Yardımcı fonksiyonlar
function getGuildId() {
    const path = window.location.pathname;
    const parts = path.split('/');
    if (parts.length >= 3 && parts[1] === 'server') {
        return parts[2];
    }
    return null;
}

function showTabLoading(tabId) {
    const tabPane = document.querySelector(tabId);
    if (!tabPane) return;
    
    // Tüm içeriği geçici olarak gizle
    Array.from(tabPane.children).forEach(child => {
        child.style.opacity = '0.5';
        child.style.pointerEvents = 'none';
    });
    
    // Loading spinner ekle
    const spinner = document.createElement('div');
    spinner.className = 'tab-loading-spinner';
    spinner.innerHTML = `
        <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Yükleniyor...</span>
        </div>
    `;
    tabPane.appendChild(spinner);
}

function hideTabLoading(tabId) {
    const tabPane = document.querySelector(tabId);
    if (!tabPane) return;
    
    // Loading spinner'ı kaldır
    const spinner = tabPane.querySelector('.tab-loading-spinner');
    if (spinner) {
        spinner.remove();
    }
    
    // İçeriği tekrar göster
    Array.from(tabPane.children).forEach(child => {
        child.style.opacity = '1';
        child.style.pointerEvents = '';
    });
}

function showApiError(tabId, message) {
    const tabPane = document.querySelector(tabId);
    if (!tabPane) return;
    
    // Hata mesajı oluştur
    const errorMsg = document.createElement('div');
    errorMsg.className = 'alert alert-danger mt-3';
    errorMsg.innerHTML = `<i class="fas fa-exclamation-triangle"></i> ${message}`;
    
    // Tabpane'in başına ekle
    tabPane.prepend(errorMsg);
    
    // 5 saniye sonra kaldır
    setTimeout(() => {
        errorMsg.remove();
    }, 5000);
}

function showLoading(form) {
    const submitBtn = form.querySelector('[type="submit"]');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.dataset.originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> İşleniyor...';
    }
}

function hideLoading(form) {
    const submitBtn = form.querySelector('[type="submit"]');
    if (submitBtn && submitBtn.dataset.originalText) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = submitBtn.dataset.originalText;
    }
}

function setupToastListeners() {
    // Toast mesajlarını kapatma butonu
    document.addEventListener('click', function(e) {
        if (e.target && e.target.classList.contains('toast-close')) {
            const toast = e.target.closest('.toast');
            if (toast) {
                toast.remove();
            }
        }
    });
}

// main.js dosyasındaki showToast fonksiyonu ile çakışmayı önleyin
// Bu satırın üstündeki tüm kodları koruyun
function showToast(message, type = 'info') {
    // Toast container oluştur (yoksa)
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    // Toast ID'si
    const id = 'toast-' + Date.now();
    
    // Toast türüne göre sınıf ve ikon belirle
    let toastClass, toastIcon;
    switch(type) {
        case 'success':
            toastClass = 'bg-success text-white';
            toastIcon = 'fas fa-check-circle';
            break;
        case 'error':
            toastClass = 'bg-danger text-white';
            toastIcon = 'fas fa-exclamation-circle';
            break;
        case 'warning':
            toastClass = 'bg-warning';
            toastIcon = 'fas fa-exclamation-triangle';
            break;
        default:
            toastClass = 'bg-info text-white';
            toastIcon = 'fas fa-info-circle';
    }
    
    // Toast HTML
    const toastHtml = `
        <div id="${id}" class="toast ${toastClass} border-0 show" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header ${toastClass} border-0">
                <i class="${toastIcon} me-2"></i>
                <strong class="me-auto">LunarisBot</strong>
                <small>Şimdi</small>
                <button type="button" class="btn-close btn-close-white toast-close" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;
    
    // Toast'ı ekle
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    
    // Belirli bir süre sonra otomatik kapat
    setTimeout(() => {
        const toastElement = document.getElementById(id);
        if (toastElement) {
            // Toast'ı kaldır
            toastElement.classList.remove('show');
            setTimeout(() => {
                if (toastElement.parentNode) {
                    toastElement.parentNode.removeChild(toastElement);
                }
            }, 300);
        }
    }, 5000);
}
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
            break;
        case '#v-pills-giveaway':
            loadGiveawaySettings();
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

// Toast mesajı göster
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
                <button type="button" class="btn-close toast-close" data-bs-dismiss="toast" aria-label="Close"></button>
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
        const toast = document.getElementById(id);
        if (toast) {
            toast.classList.remove('show');
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 500);
        }
    }, 5000);
}
/* filepath: c:\Users\fizyo\OneDrive\Masaüstü\discord-bot\webdashboard\static\js\server.js */
document.addEventListener('DOMContentLoaded', function() {
    const guildId = getGuildId();
    if (!guildId) return;
    
    // Tab değiştiğinde veri yükle
    document.querySelectorAll('button[data-bs-toggle="tab"]').forEach(tab => {
        tab.addEventListener('shown.bs.tab', function(e) {
            const targetId = e.target.getAttribute('data-bs-target');
            
            switch(targetId) {
                case '#nav-invite':
                    loadInviteData();
                    break;
                case '#nav-moderation':
                    loadModerationData();
                    break;
                case '#nav-giveaway':
                    loadGiveawayData();
                    break;
                case '#nav-automod':
                    loadAutomodData();
                    break;
                case '#nav-logs':
                    loadLogData();
                    break;
            }
        });
    });
    
    // İlk sekmede veri yükle
    loadGeneralData();
    
    // Aktif sekmenin verisini yükle
    const activeTab = document.querySelector('.nav-link.active');
    if (activeTab) {
        const targetId = activeTab.getAttribute('data-bs-target');
        if (targetId === '#nav-invite') loadInviteData();
    }
});

// Veri yükleme fonksiyonları
function loadGeneralData() {
    const guildId = getGuildId();
    
    fetch(`/api/guild/${guildId}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showToast(data.error, 'error');
                return;
            }
            
            // Form alanlarını doldur
            if (data.settings && data.settings.prefix) {
                document.getElementById('prefix').value = data.settings.prefix;
            }
            
            if (data.settings && data.settings.log_channel_id) {
                document.getElementById('log-channel').value = data.settings.log_channel_id;
            }
        })
        .catch(error => {
            console.error('Error loading general data:', error);
            showToast('Sunucu bilgileri yüklenirken bir hata oluştu', 'error');
        });
}

function loadInviteData() {
    const guildId = getGuildId();
    
    // İstatistikler
    fetch(`/api/guild/${guildId}/invites`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showToast(data.error, 'error');
                return;
            }
            
            // İstatistikleri güncelle
            document.getElementById('total-invites').textContent = data.stats.total_invites || 0;
            document.getElementById('active-inviters').textContent = data.stats.active_inviters || 0;
            document.getElementById('tracked-users').textContent = data.stats.tracked_users || 0;
            
            // Ayarları form alanlarına doldur
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
            const leaderboardTable = document.getElementById('invite-leaderboard');
            if (leaderboardTable && data.leaderboard) {
                const tbody = leaderboardTable.querySelector('tbody');
                tbody.innerHTML = '';
                
                if (data.leaderboard.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="5" class="text-center">Henüz davet verisi bulunmuyor</td></tr>`;
                } else {
                    data.leaderboard.forEach((entry, index) => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>${index + 1}</td>
                            <td>
                                <div class="d-flex align-items-center">
                                    ${entry.avatar ? `<img src="${entry.avatar}" class="avatar-img me-2" alt="">` : ''}
                                    ${entry.username || `Kullanıcı#${entry.user_id}`}
                                </div>
                            </td>
                            <td>${entry.total}</td>
                            <td>${entry.bonus || 0}</td>
                            <td>
                                <button class="btn btn-sm btn-primary add-bonus" data-user-id="${entry.user_id}">
                                    <i class="fas fa-plus"></i> Bonus Ekle
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
            }
        })
        .catch(error => {
            console.error('Error loading invite data:', error);
            showToast('Davet verileri yüklenirken bir hata oluştu', 'error');
        });
}

// Bonus ekleme modalını göster
function showBonusModal(userId) {
    // Modal zaten var mı kontrol et
    let modal = document.getElementById('bonus-modal');
    
    // Yoksa oluştur
    if (!modal) {
        const modalHtml = `
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
                                    <label for="bonus-amount" class="form-label">Miktar</label>
                                    <input type="number" class="form-control" id="bonus-amount" min="0" value="0">
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">İptal</button>
                            <button type="button" class="btn btn-primary" id="save-bonus">Kaydet</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        modal = document.getElementById('bonus-modal');
        
        // Kaydet düğmesi için olay ekle
        document.getElementById('save-bonus').addEventListener('click', function() {
            saveBonusInvites();
        });
    }
    
    // Modal içeriğini ayarla
    document.getElementById('bonus-user-id').value = userId;
    
    // Modalı göster
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
}

// Bonus davetleri kaydet
function saveBonusInvites() {
    const guildId = getGuildId();
    const userId = document.getElementById('bonus-user-id').value;
    const amount = parseInt(document.getElementById('bonus-amount').value) || 0;
    
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
        if (data.success) {
            showToast('Bonus davetler başarıyla eklendi', 'success');
            bootstrap.Modal.getInstance(document.getElementById('bonus-modal')).hide();
            loadInviteData(); // Yeniden yükle
        } else {
            showToast('Bonus davetler eklenirken bir hata oluştu: ' + data.error, 'error');
        }
    })
    .catch(error => {
        showToast('Bir hata oluştu: ' + error, 'error');
    });
}

// URL'den guild ID'sini al
function getGuildId() {
    const path = window.location.pathname;
    const parts = path.split('/');
    if (parts.length >= 3 && parts[1] === 'server') {
        return parts[2];
    }
    return null;
}
/* filepath: c:\Users\fizyo\OneDrive\Masaüstü\discord-bot\webdashboard\static\js\main.js */
document.addEventListener('DOMContentLoaded', function() {
    // Tooltips
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    if (tooltipTriggerList.length > 0) {
        tooltipTriggerList.forEach(el => new bootstrap.Tooltip(el));
    }
    
    // Sayfa yükleme animasyonu
    document.body.classList.add('loaded');
    
    // Form submit olaylarını engelle
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formId = this.id;
            
            // Form ID'sine göre uygun işlemi yap
            switch(formId) {
                case 'general-settings-form':
                    saveGeneralSettings(this);
                    break;
                case 'invite-settings-form':
                    saveInviteSettings(this);
                    break;
                case 'moderation-settings-form':
                    saveModerationSettings(this);
                    break;
                case 'automod-settings-form':
                    saveAutomodSettings(this);
                    break;
                default:
                    console.log('Form ID tanınmadı:', formId);
            }
        });
    });
});

// Ayarları kaydetme fonksiyonları
function saveGeneralSettings(form) {
    const prefix = document.getElementById('prefix').value;
    const logChannel = document.getElementById('log-channel').value;
    
    // API'ye gönder
    const guildId = getGuildId();
    if (!guildId) return;
    
    fetch(`/api/guild/${guildId}/settings`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            prefix: prefix,
            log_channel_id: logChannel
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Ayarlar başarıyla kaydedildi!', 'success');
        } else {
            showToast('Ayarlar kaydedilirken bir hata oluştu: ' + data.error, 'error');
        }
    })
    .catch(error => {
        showToast('Bir hata oluştu: ' + error, 'error');
    });
}

function saveInviteSettings(form) {
    const enabled = document.getElementById('invite-system-toggle').checked;
    const welcomeChannel = document.getElementById('welcome-channel').value;
    const inviteLogChannel = document.getElementById('invite-log-channel').value;
    const welcomeMessage = document.getElementById('welcome-message').value;
    
    // API'ye gönder
    const guildId = getGuildId();
    if (!guildId) return;
    
    fetch(`/api/guild/${guildId}/settings`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            module: 'invite',
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
        if (data.success) {
            showToast('Davet sistemi ayarları kaydedildi!', 'success');
        } else {
            showToast('Ayarlar kaydedilirken bir hata oluştu: ' + data.error, 'error');
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

// Bildirim gösterme fonksiyonu
function showToast(message, type = 'info') {
    // Toast zaten eklenmiş mi kontrol et
    let toastContainer = document.querySelector('.toast-container');
    
    // Yoksa oluştur
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    // Toast ID'si
    const id = 'toast-' + Date.now();
    
    // Toast sınıfı
    let toastClass = 'bg-info text-white';
    if (type === 'success') toastClass = 'bg-success text-white';
    if (type === 'error') toastClass = 'bg-danger text-white';
    if (type === 'warning') toastClass = 'bg-warning text-dark';
    
    // Toast HTML
    const toastHtml = `
        <div id="${id}" class="toast ${toastClass}" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header">
                <strong class="me-auto">LunarisBot</strong>
                <small>Şimdi</small>
                <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;
    
    // Toast'ı ekle
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    
    // Toast'ı göster
    const toastElement = document.getElementById(id);
    const toast = new bootstrap.Toast(toastElement, { delay: 5000 });
    toast.show();
    
    // Belirli bir süre sonra sil
    setTimeout(() => {
        if (toastElement && toastElement.parentNode) {
            toastElement.parentNode.removeChild(toastElement);
        }
    }, 5500);
}
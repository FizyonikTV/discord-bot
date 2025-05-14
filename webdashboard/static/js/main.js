/* filepath: c:\Users\fizyo\OneDrive\Masaüstü\discord-bot\webdashboard\static\js\main.js */
document.addEventListener('DOMContentLoaded', function() {
    // Dropdown ve popovers gibi Bootstrap bileşenlerini etkinleştir
    var dropdownElementList = [].slice.call(document.querySelectorAll('.dropdown-toggle'));
    dropdownElementList.map(function (dropdownToggleEl) {
        return new bootstrap.Dropdown(dropdownToggleEl);
    });
    
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

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

// Toast bildirimi gösterme fonksiyonu
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

// Generic error handler
window.addEventListener('error', function(event) {
    console.error('Sayfa hatası:', event.message);
    showToast('Bir hata oluştu: ' + event.message, 'error');
});
/* filepath: c:\Users\fizyo\OneDrive\Masaüstü\Lunaris Discord COG Bot\webdashboard\static\js\main.js */
document.addEventListener('DOMContentLoaded', function() {
    // Fontawesome için
    const script = document.createElement('script');
    script.src = 'https://kit.fontawesome.com/a076d05399.js';
    script.crossOrigin = 'anonymous';
    document.head.appendChild(script);
    
    // Bootstrap tooltipleri etkinleştir
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
    
    // Sayfa yükleme animasyonu
    document.body.classList.add('loaded');
    
    // Mobil menü toggle
    const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
    if (mobileMenuToggle) {
        mobileMenuToggle.addEventListener('click', function() {
            document.querySelector('.menu').classList.toggle('active');
        });
    }
    
    // Dashboard cards animation
    const cards = document.querySelectorAll('.stat-card, .feature-item');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.classList.add('hover');
        });
        card.addEventListener('mouseleave', function() {
            this.classList.remove('hover');
        });
    });
});
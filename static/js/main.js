// ── Theme Manager ───────────────────
const themeToggle = document.getElementById('themeToggle');
const currentTheme = localStorage.getItem('growthhive-theme') || 'light';

document.documentElement.setAttribute('data-theme', currentTheme);

if (themeToggle) {
    themeToggle.innerHTML = currentTheme === 'dark' ? '<i class="bi bi-sun-fill"></i>' : '<i class="bi bi-moon-fill"></i>';
    
    themeToggle.addEventListener('click', () => {
        let theme = document.documentElement.getAttribute('data-theme');
        let newTheme = theme === 'light' ? 'dark' : 'light';
        
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('growthhive-theme', newTheme);
        
        themeToggle.innerHTML = newTheme === 'dark' ? '<i class="bi bi-sun-fill"></i>' : '<i class="bi bi-moon-fill"></i>';
        
        // Refresh ripple color context if needed
    });
}

// ── Mobile sidebar toggle ───────────────────
const sidebar = document.getElementById('sidebar');
const overlay = document.getElementById('sidebarOverlay');
const toggle = document.getElementById('sidebarToggle');

if (toggle && sidebar) {
    toggle.addEventListener('click', () => {
        sidebar.classList.toggle('open');
        overlay.classList.toggle('show');
    });
    overlay.addEventListener('click', () => {
        sidebar.classList.remove('open');
        overlay.classList.remove('show');
    });
}

// ── Ripple Effect ───────────────────
document.addEventListener('click', function (e) {
    const target = e.target.closest('.gh-btn-primary, .gh-btn-outline, .gh-nav-link');
    if (!target) return;

    const ripple = document.createElement('span');
    ripple.classList.add('ripple');
    
    const rect = target.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = e.clientX - rect.left - size / 2;
    const y = e.clientY - rect.top - size / 2;
    
    ripple.style.width = ripple.style.height = `${size}px`;
    ripple.style.left = `${x}px`;
    ripple.style.top = `${y}px`;
    
    target.appendChild(ripple);
    
    ripple.addEventListener('animationend', () => {
        ripple.remove();
    });
});

// ── Toast Manager ───────────────────
class ToastManager {
    constructor() {
        this.container = document.querySelector('.gh-toast-container');
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.classList.add('gh-toast-container');
            document.body.appendChild(this.container);
        }
    }

    show(message, type = 'info', duration = 5000) {
        const toast = document.createElement('div');
        toast.className = `gh-toast gh-toast--${type}`;
        
        toast.innerHTML = `
            <div class="gh-toast-content">${message}</div>
            <button class="gh-toast-close"><i class="bi bi-x"></i></button>
        `;
        
        this.container.appendChild(toast);
        
        // Trigger animation
        setTimeout(() => toast.classList.add('show'), 10);
        
        const closeBtn = toast.querySelector('.gh-toast-close');
        closeBtn.addEventListener('click', () => this.hide(toast));
        
        if (duration > 0) {
            setTimeout(() => this.hide(toast), duration);
        }
    }

    hide(toast) {
        toast.classList.remove('show');
        toast.addEventListener('transitionend', () => {
            toast.remove();
        });
    }
}

window.GrowthHiveToasts = new ToastManager();

// Auto-display Django messages as toasts if they exist in the DOM
document.addEventListener('DOMContentLoaded', () => {
    const messages = document.querySelectorAll('.gh-message-data');
    messages.forEach(msg => {
        const text = msg.dataset.text;
        const tags = msg.dataset.tags || 'info';
        window.GrowthHiveToasts.show(text, tags);
    });
});


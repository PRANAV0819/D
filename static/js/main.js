// Mobile sidebar toggle
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

// Auto-dismiss alert messages after 4 s
document.querySelectorAll('.alert.fade.show').forEach(el => {
    setTimeout(() => {
        const bs = bootstrap.Alert.getOrCreateInstance(el);
        bs && bs.close();
    }, 4000);
});
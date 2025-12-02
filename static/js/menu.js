document.addEventListener('DOMContentLoaded', function () {
    const menuBtn = document.getElementById('menuToggle');
    const menu = document.getElementById('nav');

    if (!menuBtn || !menu) {
        console.warn('Missing #menuToggle or #nav element');
        return;
    }

    function showMenu() {
        menu.classList.remove('hide');
        menu.classList.add('show');
        menuBtn.setAttribute('aria-expanded', 'true');
        console.log('Menu shown');
    }

    function hideMenu() {
        menu.classList.remove('show');
        menu.classList.add('hide');
        menuBtn.setAttribute('aria-expanded', 'false');
        console.log('Menu hidden');
    }

    menuBtn.addEventListener('click', () => {
        if (menu.classList.contains('show')) {
            hideMenu();
        } else {
            showMenu();
        }
    });

    document.addEventListener('click', (event) => {
        if (!menu.contains(event.target) && !menuBtn.contains(event.target)) {
            if (menu.classList.contains('show')) {
                hideMenu();
            }
        }
    });
});

class ComponentManager {
    static init() {
        this.injectNavbar();
        this.injectFooter();
        this.setupMobileNav();
        this.setActiveNavLink();
    }

    static injectNavbar() {
        const navbarHtml = `
            <div class="nav-container">
                <a href="index.html" class="nav-logo">SC <span>TW Guide</span></a>
                <ul class="nav-links">
                    <li><a href="index.html">首頁</a></li>
                    <li><a href="ship-purchase-guide.html">飛機購買指南</a></li>
                    <li><a href="cargo.html">貨運</a></li>
                    <li><a href="mining.html">挖礦</a></li>
                    <li><a href="first-flight.html">基礎飛行</a></li>
                    <li><a href="ground-combat.html">地面 FPS</a></li>
                    <li><a href="ctinput1.html">中文化與輸入</a></li>
                </ul>
                <div class="hamburger">
                    <span></span><span></span><span></span>
                </div>
            </div>
        `;
        
        let nav = document.getElementById('main-nav');
        if (!nav) {
            nav = document.createElement('nav');
            nav.id = 'main-nav';
            nav.className = 'navbar';
            document.body.insertBefore(nav, document.body.firstChild);
        }
        nav.innerHTML = navbarHtml;
    }

    static injectFooter() {
        const footerHtml = `
            <div class="footer-content">
                <h3 class="text-gradient" style="margin-bottom: 10px;">Star Citizen Traditional Chinese Guide</h3>
                <p>這是一個由玩家建立的非官方新手教學網站。Star Citizen 及其相關資產版權歸 Cloud Imperium Games 所有。</p>
                <p style="margin-top: 10px; font-size: 0.8rem;">See You In The 'Verse! o7</p>
            </div>
        `;

        let footer = document.getElementById('main-footer');
        if (!footer) {
            footer = document.createElement('footer');
            footer.id = 'main-footer';
            document.body.appendChild(footer);
        }
        footer.innerHTML = footerHtml;
    }

    static setupMobileNav() {
        const hamburger = document.querySelector('.hamburger');
        const navLinks = document.querySelector('.nav-links');

        if (hamburger && navLinks) {
            hamburger.addEventListener('click', () => {
                navLinks.classList.toggle('active');
            });
        }
    }

    static setActiveNavLink() {
        const currentPath = window.location.pathname.split('/').pop() || 'index.html';
        const links = document.querySelectorAll('.nav-links a');
        
        links.forEach(link => {
            const href = link.getAttribute('href');
            if (href === currentPath) {
                link.classList.add('active');
            }
        });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    ComponentManager.init();
});

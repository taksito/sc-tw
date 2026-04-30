class ComponentManager {
    static init() {
        this.injectNavigation();
        this.injectFooter();
        this.setupMobileNav();
        this.setActiveNavLink();
    }

    static getPathPrefix() {
        const path = window.location.pathname;
        const folders = ['/ships/', '/rockbreaker/', '/cargohauling/'];
        return folders.some(f => path.includes(f)) ? '../' : '';
    }

    static injectNavigation() {
        const prefix = this.getPathPrefix();
        const navHtml = `
            <header class="mobile-header">
                <a href="${prefix}index.html" class="nav-logo" style="font-family: 'Orbitron', sans-serif; text-decoration: none; color: var(--text-main); font-weight: bold;">SC <span style="color: var(--primary);">TW Guide</span></a>
                <div class="hamburger">
                    <span></span><span></span><span></span>
                </div>
            </header>

            <nav class="sidebar" id="main-sidebar">
                <a href="${prefix}index.html" class="sidebar-logo">
                    <h2 style="font-family: 'Orbitron', sans-serif; font-size: 1.4rem; color: var(--text-main); margin: 0;">SC <span style="color: var(--primary);">TW Guide</span></h2>
                </a>
                
                <div class="nav-category">主要指南</div>
                <ul class="sidebar-nav">
                    <li><a href="${prefix}index.html">🏠 首頁</a></li>
                    <li><a href="${prefix}ctinput1.html">⌨️ 中文化與輸入</a></li>
                    <li class="has-submenu">
                        <div class="submenu-header" onclick="ComponentManager.toggleSubmenu(this)">
                            <a href="${prefix}first-flight.html" onclick="event.stopPropagation()">🚀 基礎飛行</a>
                            <span class="toggle-icon">▼</span>
                        </div>
                        <ul class="submenu">
                            <li><a href="${prefix}first-flight.html">• 呼叫與登機</a></li>
                            <li><a href="${prefix}flight-movements.html">• 基礎操作</a></li>
                            <li><a href="${prefix}flight-quantum.html">• 量子航行</a></li>
                            <li><a href="${prefix}stanton-intro.html">• Stanton 星系介紹</a></li>
                            <li><a href="${prefix}flight-landing.html">• 降落指南</a></li>
                        </ul>
                    </li>
                </ul>

                <div class="nav-category">專業領域</div>
                <ul class="sidebar-nav">
                    <li class="has-submenu">
                        <div class="submenu-header" onclick="ComponentManager.toggleSubmenu(this)">
                            <a href="${prefix}cargohauling/cargo.html" onclick="event.stopPropagation()">📦 貨運教學</a>
                            <span class="toggle-icon">▼</span>
                        </div>
                        <ul class="submenu">
                            <li><a href="${prefix}cargohauling/cargo.html">• 貨運基礎</a></li>
                            <li><a href="${prefix}cargohauling/mission-tips.html">• 接任務技巧</a></li>
                        </ul>
                    </li>
                    <li><a href="${prefix}mining.html">⛏️ 挖礦教學</a></li>
                    <li><a href="${prefix}ground-combat.html">🔫 地面 FPS</a></li>
                </ul>

                <div class="nav-category">參考手冊</div>
                <ul class="sidebar-nav">
                    <li><a href="${prefix}ship-purchase-guide.html">🚢 飛機購買指南</a></li>
                    <li><a href="${prefix}ship-travel.html">✈️ 移動與交通推薦</a></li>
                </ul>

                <div class="nav-category">PTU 改版資訊 <span style="font-size: 0.7rem; color: var(--accent); vertical-align: middle;">(持續更新中)</span></div>
                <ul class="sidebar-nav">
                    <li><a href="${prefix}ptu-48-tactical.html">⚔️ 4.8 戰術打擊群</a></li>
                    <li><a href="${prefix}rockbreaker/rock-breaker.html">⛏️ 4.7 碎石機啟動</a></li>
                </ul>
            </nav>
        `;
        
        let container = document.getElementById('nav-wrapper');
        if (!container) {
            container = document.createElement('div');
            container.id = 'nav-wrapper';
            document.body.insertBefore(container, document.body.firstChild);
        }
        container.innerHTML = navHtml;
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
        const sidebar = document.querySelector('.sidebar');

        if (hamburger && sidebar) {
            hamburger.addEventListener('click', () => {
                sidebar.classList.toggle('active');
            });

            const links = sidebar.querySelectorAll('a');
            links.forEach(link => {
                link.addEventListener('click', () => {
                    if (window.innerWidth <= 992) {
                        sidebar.classList.remove('active');
                    }
                });
            });
        }
    }

    static toggleSubmenu(header) {
        const parent = header.parentElement;
        parent.classList.toggle('expanded');
    }

    static setActiveNavLink() {
        const pathParts = window.location.pathname.split('/');
        const currentPath = pathParts.pop() || 'index.html';
        const isInSubfolder = window.location.pathname.includes('/ships/');
        
        const links = document.querySelectorAll('.sidebar-nav a');
        
        links.forEach(link => {
            const href = link.getAttribute('href');
            const hrefParts = href.split('/');
            const hrefFile = hrefParts.pop();
            
            if (hrefFile === currentPath) {
                link.classList.add('active');
                // Auto-expand parent if active link is in a submenu
                const submenu = link.closest('.submenu');
                if (submenu) {
                    submenu.parentElement.classList.add('expanded');
                }
            }
        });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    ComponentManager.init();
});

class ComponentManager {
    static init() {
        this.injectNavigation();
        this.injectFooter();
        this.setupMobileNav();
        this.setActiveNavLink();
        this.setupLightbox();
    }

    // 點圖放大：任何有 data-full 屬性的圖片，點擊後顯示大圖
    static setupLightbox() {
        const images = document.querySelectorAll('img[data-full]');
        if (!images.length) return;

        const box = document.createElement('div');
        box.className = 'lightbox';
        box.innerHTML = `
            <button class="lightbox-close" aria-label="關閉">×</button>
            <img alt="">
            <div class="lightbox-caption"></div>
        `;
        document.body.appendChild(box);

        const bigImg = box.querySelector('img');
        const caption = box.querySelector('.lightbox-caption');
        const close = () => box.classList.remove('open');

        images.forEach(img => {
            img.addEventListener('click', () => {
                bigImg.src = img.dataset.full;
                bigImg.alt = img.alt;
                const fig = img.closest('figure');
                const figcap = fig ? fig.querySelector('figcaption') : null;
                caption.textContent = figcap ? figcap.textContent : img.alt;
                box.classList.add('open');
            });
        });

        box.addEventListener('click', close);
        document.addEventListener('keydown', e => {
            if (e.key === 'Escape') close();
        });
    }

    static getPathPrefix() {
        const decodedPath = decodeURIComponent(window.location.pathname);
        const folders = ['/ships/', '/rockbreaker/', '/cargohauling/', '/update48/', '/update49/', '/update410/'];
        return folders.some(f => decodedPath.includes(f)) ? '../' : '';
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
                    <li><a href="${prefix}about-sc.html">🌌 星際公民是什麼？</a></li>
                    <li><a href="${prefix}blog.html">📝 塔克 Blog</a></li>
                    <li><a href="${prefix}ctinput1.html">⌨️ 中文化與輸入</a></li>
                    <li class="has-submenu">
                        <div class="submenu-header" onclick="ComponentManager.toggleSubmenu(this)">
                            <a href="${prefix}journey.html" onclick="event.stopPropagation()">🧭 開始旅程</a>
                            <span class="toggle-icon">▼</span>
                        </div>
                        <ul class="submenu">
                            <li><a href="${prefix}journey.html">• 旅程總覽</a></li>
                            <li><a href="${prefix}journey-pc.html">• ① 電腦檢核</a></li>
                            <li><a href="${prefix}journey-install.html">• ② 註冊與安裝</a></li>
                            <li><a href="${prefix}character-creation.html">• ③ 角色創建</a></li>
                            <li><a href="${prefix}first-flight.html">• ④ 第一次飛行</a></li>
                        </ul>
                    </li>
                    <li class="has-submenu">
                        <div class="submenu-header" onclick="ComponentManager.toggleSubmenu(this)">
                            <a href="${prefix}first-flight.html" onclick="event.stopPropagation()">🚀 基礎飛行</a>
                            <span class="toggle-icon">▼</span>
                        </div>
                        <ul class="submenu">
                            <li><a href="${prefix}first-flight.html">• 呼叫與登機</a></li>
                            <li><a href="${prefix}flight-movements.html">• 基礎操作</a></li>
                            <li><a href="${prefix}flight-quantum.html">• 量子航行</a></li>
                            <li><a href="${prefix}flight-landing.html">• 降落指南</a></li>
                        </ul>
                    </li>
                    <li class="has-submenu">
                        <div class="submenu-header" onclick="ComponentManager.toggleSubmenu(this)">
                            <a href="${prefix}professions.html" onclick="event.stopPropagation()">💼 專業領域</a>
                            <span class="toggle-icon">▼</span>
                        </div>
                        <ul class="submenu">
                            <li><a href="${prefix}cargohauling/cargo.html">• 📦 貨運教學</a></li>
                            <li><a href="${prefix}cargohauling/mission-tips.html" class="sub-sub">↳ 賺錢 vs 解聲望</a></li>
                            <li><a href="${prefix}cargohauling/covalex.html" class="sub-sub">↳ Covalex 任務攻略</a></li>
                            <li><a href="${prefix}cargohauling/red-wind.html" class="sub-sub">↳ Red Wind 高收益</a></li>
                            <li><a href="${prefix}cargohauling/ling-family.html" class="sub-sub">↳ Ling Family 小船</a></li>
                            <li><a href="${prefix}cargohauling/equipment.html" class="sub-sub">↳ ATLS 與 MaxLift</a></li>
                            <li><a href="${prefix}ship-combat.html">• ⚔️ 飛船戰鬥</a></li>
                            <li><a href="${prefix}ground-combat.html">• 🔫 地面 FPS</a></li>
                            <li><a href="${prefix}refueling.html">• ⛽ 加油任務</a></li>
                            <li><a href="${prefix}mining.html">• ⛏️ 挖礦教學</a></li>
                        </ul>
                    </li>
                    <li class="has-submenu">
                        <div class="submenu-header" onclick="ComponentManager.toggleSubmenu(this)">
                            <a href="${prefix}advanced.html" onclick="event.stopPropagation()">⚙️ 進階技巧</a>
                            <span class="toggle-icon">▼</span>
                        </div>
                        <ul class="submenu">
                            <li><a href="${prefix}insurance.html">• 🛡️ 保險配置</a></li>
                            <li><a href="${prefix}ship-components.html">• ⚙️ 飛機組件</a></li>
                            <li><a href="${prefix}components-weapons.html" class="sub-sub">↳ 武器與飛彈</a></li>
                            <li><a href="${prefix}components-systems.html" class="sub-sub">↳ 電源、護盾、冷卻</a></li>
                            <li><a href="${prefix}components-quantum.html" class="sub-sub">↳ QT 引擎與燃料</a></li>
                            <li><a href="${prefix}wikelo.html">• 🦎 Wikelo 交易</a></li>
                        </ul>
                    </li>
                    <li class="has-submenu">
                        <div class="submenu-header" onclick="ComponentManager.toggleSubmenu(this)">
                            <a href="${prefix}world-intro.html" onclick="event.stopPropagation()">🌎 世界介紹</a>
                            <span class="toggle-icon">▼</span>
                        </div>
                        <ul class="submenu">
                            <li><a href="${prefix}stanton-intro.html">• Stanton 星系</a></li>
                            <li><a href="${prefix}pyro-intro.html">• Pyro 星系</a></li>
                            <li><a href="${prefix}nyx-intro.html">• Nyx 星系</a></li>
                        </ul>
                    </li>
                </ul>

                <div class="nav-category">參考手冊</div>
                <ul class="sidebar-nav">
                    <li class="has-submenu">
                        <div class="submenu-header" onclick="ComponentManager.toggleSubmenu(this)">
                            <a href="${prefix}ship-purchase-guide.html" onclick="event.stopPropagation()">🚢 飛機購買指南</a>
                            <span class="toggle-icon">▼</span>
                        </div>
                        <ul class="submenu">
                            <li><a href="${prefix}ship-purchase-guide.html">• 購買指南首頁</a></li>
                            <li><a href="${prefix}ship-travel.html">• ✈️ 移動與交通推薦</a></li>
                            <li><a href="${prefix}ships/hauling-list.html">• 📦 貨運飛船推薦清單</a></li>
                            <li><a href="${prefix}ship-ccu.html">• 💵 CCU 現金購船</a></li>
                        </ul>
                    </li>
                    <li><a href="${prefix}resource.html">🔗 常用網路資源</a></li>
                </ul>


                <div class="nav-category">目前版本 <span style="font-size: 0.7rem; color: var(--success); vertical-align: middle;">● LIVE</span></div>
                <ul class="sidebar-nav">
                    <li><a href="${prefix}update410/4102.html">🟢 4.10.2 RSI 探索月</a></li>
                </ul>

                <div class="nav-category">PTU 測試中 <span style="font-size: 0.7rem; color: var(--warning); vertical-align: middle;">(持續更新中)</span></div>
                <ul class="sidebar-nav">
                    <li><a href="${prefix}update410/4103-ptu.html">🧪 4.10.3 Vanduul 入侵</a></li>
                </ul>

                <div class="nav-category">舊版資訊</div>
                <ul class="sidebar-nav">
                    <li class="has-submenu">
                        <div class="submenu-header" onclick="ComponentManager.toggleSubmenu(this)">
                            <a href="${prefix}update410/index.html" onclick="event.stopPropagation()">📰 4.10 改版</a>
                            <span class="toggle-icon">▼</span>
                        </div>
                        <ul class="submenu">
                            <li><a href="${prefix}update410/index.html">• 4.10.0 圍攻 Orison</a></li>
                            <li><a href="${prefix}update410/4101.html">• 4.10.1 Orison 重建救援</a></li>
                        </ul>
                    </li>
                    <li><a href="${prefix}update49/index.html">📰 4.9 邊境緊張局勢</a></li>
                    <li class="has-submenu">
                        <div class="submenu-header" onclick="ComponentManager.toggleSubmenu(this)">
                            <a href="${prefix}update48/index.html" onclick="event.stopPropagation()">📰 4.8 改版</a>
                            <span class="toggle-icon">▼</span>
                        </div>
                        <ul class="submenu">
                            <li><a href="${prefix}update48/index.html">• 4.8 改版首頁</a></li>
                            <li><a href="${prefix}update48/ptu-48-tactical.html">• ⚔️ 4.8 戰術打擊群</a></li>
                        </ul>
                    </li>
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
        // 用完整路徑比對，避免不同資料夾的 index.html 同時被標成目前頁面
        const normalize = path => decodeURIComponent(path).replace(/\/$/, '/index.html');
        const currentPath = normalize(window.location.pathname);
        const links = document.querySelectorAll('.sidebar-nav a');

        links.forEach(link => {
            const linkPath = normalize(new URL(link.getAttribute('href'), window.location.href).pathname);
            if (linkPath === currentPath) {
                link.classList.add('active');
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

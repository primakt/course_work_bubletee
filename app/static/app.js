let cart = JSON.parse(localStorage.getItem('teezy_cart') || '[]');
let menuItems = [];

const API_BASE = "/api";

function initApp() {
    Telegram.WebApp.ready();
    Telegram.WebApp.expand();
    updateCartBadge();
    loadMenu();
    loadPromotions();
    loadLoyalty();
    setMinPickupTime();
}

async function apiCall(endpoint, options = {}) {
    const initData = Telegram.WebApp.initData;
    const headers = { "Content-Type": "application/json" };
    if (initData) headers["X-Telegram-Init-Data"] = initData;

    const res = await fetch(API_BASE + endpoint, { ...options, headers });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        alert(err.detail || "Ошибка");
        throw new Error(err.detail);
    }
    return res.json();
}

async function loadMenu() {
    menuItems = await apiCall("/menu/");
    const list = document.getElementById("menu-list");
    list.innerHTML = menuItems.map(item => `
        <div class="menu-item">
            ${item.image_url ? `<img src="${item.image_url}" alt="${item.name}">` : '<div style="height:120px;background:#f3e5f5;border-radius:12px;"></div>'}
            <h3>${item.name}</h3>
            <p>${item.price} ₽</p>
            <button class="add-btn" onclick="addToCart(${item.id})">+</button>
        </div>
    `).join('');
}

async function loadPromotions() {
    const promotions = await apiCall("/promotions/");
    const discounts = await apiCall("/promotions/discounts");
    const list = document.getElementById("promo-list");
    let html = "<h3>🔥 Акции</h3>";
    promotions.forEach(p => html += `<div class="card"><strong>${p.title}</strong><p>${p.description}</p></div>`);
    if (discounts.length) {
        html += "<h3>🎟 Промокоды</h3>";
        discounts.forEach(d => html += `<div class="card"><strong>${d.code}</strong> — ${d.percentage ? d.percentage + '%' : d.value + ' ₽'} скидка</div>`);
    }
    list.innerHTML = html || "Нет активных акций";
}

async function loadLoyalty() {
    const { points } = await apiCall("/loyalty/balance");
    document.getElementById("points").innerText = points;
}

function addToCart(id) {
    const item = menuItems.find(i => i.id === id);
    const existing = cart.find(c => c.menu_item_id === id);
    if (existing) existing.quantity++;
    else cart.push({ menu_item_id: id, quantity: 1, name: item.name, price: item.price });
    localStorage.setItem('teezy_cart', JSON.stringify(cart));
    updateCartBadge();
    updateCartDisplay();
    // Анимация
    Telegram.WebApp.HapticFeedback.impactOccurred('light');
}

function updateCartBadge() {
    const count = cart.reduce((s, i) => s + i.quantity, 0);
    document.getElementById("cart-count").innerText = count;
}

function updateCartDisplay() {
    const container = document.getElementById("cart-items");
    if (cart.length === 0) {
        container.innerHTML = "<p style='text-align:center;color:#999;'>Корзина пуста</p>";
        return;
    }
    container.innerHTML = cart.map(c => `
        <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid #eee;">
            <div><strong>${c.name}</strong> × ${c.quantity}</div>
            <div>${c.price * c.quantity} ₽</div>
        </div>
    `).join('');
}

async function loadFavorite() {
    const fav = await apiCall("/loyalty/favorite");
    if (fav && fav.order_details?.length) {
        cart = fav.order_details.map(d => ({
            menu_item_id: d.menu_item_id,
            quantity: d.quantity,
            name: menuItems.find(i => i.id === d.menu_item_id)?.name || "???",
            price: menuItems.find(i => i.id === d.menu_item_id)?.price || 0
        }));
        localStorage.setItem('teezy_cart', JSON.stringify(cart));
        updateCartDisplay();
        updateCartBadge();
        showSection('order');
        alert("Любимый заказ загружен! 🍵");
    } else alert("Любимый заказ не сохранён");
}

function setMinPickupTime() {
    const input = document.getElementById("pickup-time");
    const min = new Date(Date.now() + 15*60*1000);
    input.min = min.toISOString().slice(0,16);
}

document.getElementById("place-order").addEventListener("click", async () => {
    if (cart.length === 0) return alert("Корзина пуста");
    const pickup = document.getElementById("pickup-time").value;
    if (!pickup) return alert("Выберите время самовывоза");

    const data = {
        items: cart.map(c => ({ menu_item_id: c.menu_item_id, quantity: c.quantity })),
        discount_code: document.getElementById("discount-code").value.trim() || null,
        pickup_time: new Date(pickup).toISOString(),
        store_id: 1
    };

    try {
        const order = await apiCall("/orders/", { method: "POST", body: JSON.stringify(data) });
        alert(`Заказ №${order.id} оформлен!\nНачислено баллов: ${Math.floor(order.total_price / 100)}`);
        cart = [];
        localStorage.removeItem('teezy_cart');
        updateCartBadge();
        updateCartDisplay();
        loadLoyalty();
    } catch (e) {}
});

function showSection(id) {
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    document.getElementById(id).classList.add('active');
    document.querySelectorAll('nav button').forEach(b => b.classList.remove('active'));
    document.querySelector(`nav button[onclick="showSection('${id}')"]`).classList.add('active');
    if (id === 'order') updateCartDisplay();
}

initApp();
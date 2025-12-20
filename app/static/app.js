// === КОНФИГУРАЦИЯ ===
const API_BASE = "/api";
const STORAGE_KEY = 'teezy_cart';

// === СОСТОЯНИЕ ПРИЛОЖЕНИЯ ===
let cart = [];
let menuItems = [];
let userData = null;

// === ИНИЦИАЛИЗАЦИЯ ===
function initApp() {
    try {
        // Инициализация Telegram WebApp
        if (window.Telegram?.WebApp) {
            Telegram.WebApp.ready();
            Telegram.WebApp.expand();
            Telegram.WebApp.enableClosingConfirmation();
            
            // Настройка темы
            Telegram.WebApp.setHeaderColor('#D946EF');
            Telegram.WebApp.setBackgroundColor('#FDF4FF');
        }
        
        // Загрузка корзины из localStorage
        loadCartFromStorage();
        
        // Установка минимального времени самовывоза
        setMinPickupTime();
        
        // Загрузка данных
        loadMenu();
        loadPromotions();
        loadLoyalty();
        
        // Обновление UI
        updateCartBadge();
        updateCartDisplay();
        
        console.log('✅ App initialized successfully');
        
    } catch (error) {
        console.error('❌ Initialization error:', error);
        showError('Ошибка инициализации приложения');
    }
}

// === API ФУНКЦИИ ===
async function apiCall(endpoint, options = {}) {
    try {
        // Получаем initData из Telegram WebApp
        const initData = window.Telegram?.WebApp?.initData || '';
        
        if (!initData) {
            console.warn('⚠️ No Telegram initData available');
        }
        
        const headers = {
            "Content-Type": "application/json",
            "X-Telegram-Init-Data": initData
        };
        
        const config = {
            ...options,
            headers: {
                ...headers,
                ...(options.headers || {})
            }
        };
        
        console.log(`🌐 API Call: ${endpoint}`, config);
        
        const response = await fetch(API_BASE + endpoint, config);
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP ${response.status}`);
        }
        
        return await response.json();
        
    } catch (error) {
        console.error(`❌ API Error [${endpoint}]:`, error);
        throw error;
    }
}

// === МЕНЮ ===
async function loadMenu() {
    try {
        menuItems = await apiCall("/menu/");
        renderMenu();
        console.log('✅ Menu loaded:', menuItems.length, 'items');
    } catch (error) {
        showError('Не удалось загрузить меню');
        document.getElementById("menu-list").innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">😔</div>
                <p>Не удалось загрузить меню</p>
            </div>
        `;
    }
}

function renderMenu() {
    const container = document.getElementById("menu-list");
    
    if (menuItems.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">🍵</div>
                <p>Меню временно недоступно</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = menuItems.map(item => `
        <div class="menu-item">
            <div class="menu-item-image">
                ${item.image_url 
                    ? `<img src="${item.image_url}" alt="${item.name}" onerror="this.style.display='none'">`
                    : '🧋'
                }
            </div>
            <div class="menu-item-info">
                <h3>${item.name}</h3>
                <div class="menu-item-price">${item.price} ₽</div>
                <button class="add-btn" onclick="addToCart(${item.id})">
                    Добавить
                </button>
            </div>
        </div>
    `).join('');
}

// === АКЦИИ ===
async function loadPromotions() {
    try {
        const [promotions, discounts] = await Promise.all([
            apiCall("/promotions/"),
            apiCall("/promotions/discounts")
        ]);
        
        renderPromotions(promotions, discounts);
        console.log('✅ Promotions loaded');
        
    } catch (error) {
        showError('Не удалось загрузить акции');
        document.getElementById("promo-list").innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">😔</div>
                <p>Не удалось загрузить акции</p>
            </div>
        `;
    }
}

function renderPromotions(promotions, discounts) {
    const container = document.getElementById("promo-list");
    let html = '';
    
    if (promotions.length > 0) {
        html += promotions.map(promo => `
            <div class="promo-card">
                <h3>${promo.title}</h3>
                <p>${promo.description}</p>
            </div>
        `).join('');
    }
    
    if (discounts.length > 0) {
        html += '<div class="card"><h3>🎟️ Промокоды</h3>';
        html += discounts.map(discount => `
            <div class="promo-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div class="promo-code">${discount.code}</div>
                    </div>
                    <div style="font-size: 24px; font-weight: 800;">
                        ${discount.percentage ? discount.percentage + '%' : discount.value + ' ₽'}
                    </div>
                </div>
            </div>
        `).join('');
        html += '</div>';
    }
    
    if (html === '') {
        html = `
            <div class="empty-state">
                <div class="empty-state-icon">📢</div>
                <p>Нет активных акций</p>
            </div>
        `;
    }
    
    container.innerHTML = html;
}

// === БАЛЛЫ ЛОЯЛЬНОСТИ ===
async function loadLoyalty() {
    try {
        const data = await apiCall("/loyalty/balance");
        document.getElementById("points").innerText = data.points;
        userData = data;
        console.log('✅ Loyalty loaded:', data.points, 'points');
    } catch (error) {
        console.warn('⚠️ Could not load loyalty points:', error);
        document.getElementById("points").innerText = '0';
    }
}

// === КОРЗИНА ===
function loadCartFromStorage() {
    try {
        const stored = localStorage.getItem(STORAGE_KEY);
        cart = stored ? JSON.parse(stored) : [];
    } catch (error) {
        console.error('❌ Error loading cart:', error);
        cart = [];
    }
}

function saveCartToStorage() {
    try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(cart));
    } catch (error) {
        console.error('❌ Error saving cart:', error);
    }
}

function addToCart(itemId) {
    const menuItem = menuItems.find(i => i.id === itemId);
    
    if (!menuItem) {
        showError('Товар не найден');
        return;
    }
    
    const existingItem = cart.find(c => c.menu_item_id === itemId);
    
    if (existingItem) {
        existingItem.quantity++;
    } else {
        cart.push({
            menu_item_id: itemId,
            quantity: 1,
            name: menuItem.name,
            price: parseFloat(menuItem.price)
        });
    }
    
    saveCartToStorage();
    updateCartBadge();
    updateCartDisplay();
    
    // Тактильная обратная связь
    if (window.Telegram?.WebApp?.HapticFeedback) {
        Telegram.WebApp.HapticFeedback.impactOccurred('light');
    }
    
    console.log('✅ Added to cart:', menuItem.name);
}

function updateQuantity(itemId, change) {
    const item = cart.find(c => c.menu_item_id === itemId);
    
    if (!item) return;
    
    item.quantity += change;
    
    if (item.quantity <= 0) {
        cart = cart.filter(c => c.menu_item_id !== itemId);
    }
    
    saveCartToStorage();
    updateCartBadge();
    updateCartDisplay();
    
    if (window.Telegram?.WebApp?.HapticFeedback) {
        Telegram.WebApp.HapticFeedback.impactOccurred('light');
    }
}

function updateCartBadge() {
    const count = cart.reduce((sum, item) => sum + item.quantity, 0);
    document.getElementById("cart-count").innerText = count;
}

function updateCartDisplay() {
    const container = document.getElementById("cart-items");
    const form = document.getElementById("cart-form");
    
    if (cart.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">🛍️</div>
                <p>Корзина пуста</p>
            </div>
        `;
        form.style.display = 'none';
        return;
    }
    
    const totalPrice = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    
    container.innerHTML = cart.map(item => `
        <div class="cart-item">
            <div class="cart-item-info">
                <strong>${item.name}</strong>
                <div class="cart-item-quantity">
                    <button class="qty-btn" onclick="updateQuantity(${item.menu_item_id}, -1)">−</button>
                    <span style="min-width: 30px; text-align: center; font-weight: 700;">${item.quantity}</span>
                    <button class="qty-btn" onclick="updateQuantity(${item.menu_item_id}, 1)">+</button>
                </div>
            </div>
            <div class="cart-item-price">
                <div class="price">${(item.price * item.quantity).toFixed(2)} ₽</div>
            </div>
        </div>
    `).join('');
    
    document.getElementById("total-price").innerText = `${totalPrice.toFixed(2)} ₽`;
    form.style.display = 'block';
}

// === ОФОРМЛЕНИЕ ЗАКАЗА ===
function setMinPickupTime() {
    const input = document.getElementById("pickup-time");
    const now = new Date();
    now.setMinutes(now.getMinutes() + 15);
    
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    
    input.min = `${year}-${month}-${day}T${hours}:${minutes}`;
}

document.getElementById("place-order")?.addEventListener("click", async () => {
    if (cart.length === 0) {
        showError("Корзина пуста");
        return;
    }
    
    const pickupTime = document.getElementById("pickup-time").value;
    if (!pickupTime) {
        showError("Выберите время самовывоза");
        return;
    }
    
    const discountCode = document.getElementById("discount-code").value.trim() || null;
    
    const orderData = {
        items: cart.map(item => ({
            menu_item_id: item.menu_item_id,
            quantity: item.quantity
        })),
        discount_code: discountCode,
        pickup_time: new Date(pickupTime).toISOString(),
        store_id: 1
    };
    
    try {
        // Показываем индикатор загрузки
        const btn = document.getElementById("place-order");
        const originalText = btn.innerText;
        btn.disabled = true;
        btn.innerText = "Оформление...";
        
        const order = await apiCall("/orders/", {
            method: "POST",
            body: JSON.stringify(orderData)
        });
        
        console.log('✅ Order created:', order);
        
        // Очищаем корзину
        cart = [];
        saveCartToStorage();
        updateCartBadge();
        updateCartDisplay();
        
        // Обновляем баллы
        await loadLoyalty();
        
        // Показываем уведомление
        if (window.Telegram?.WebApp) {
            Telegram.WebApp.showAlert(
                `🎉 Заказ №${order.id} оформлен!\n\n` +
                `Сумма: ${order.total_price} ₽\n` +
                `Начислено баллов: ${Math.floor(order.total_price / 100)}\n\n` +
                `Заберите ваш заказ ${new Date(order.pickup_time).toLocaleString('ru-RU')}`
            );
        } else {
            alert(`Заказ №${order.id} оформлен!`);
        }
        
        // Переходим на экран баллов
        showSection('loyalty');
        
        btn.disabled = false;
        btn.innerText = originalText;
        
    } catch (error) {
        showError(`Ошибка оформления: ${error.message}`);
        document.getElementById("place-order").disabled = false;
        document.getElementById("place-order").innerText = "Оформить заказ";
    }
});

// === ЛЮБИМЫЙ ЗАКАЗ ===
async function loadFavorite() {
    try {
        const favorite = await apiCall("/loyalty/favorite");
        
        if (!favorite || !favorite.order_details || favorite.order_details.length === 0) {
            showError("Любимый заказ не сохранён");
            return;
        }
        
        // Загружаем заказ в корзину
        cart = favorite.order_details.map(item => {
            const menuItem = menuItems.find(m => m.id === item.menu_item_id);
            return {
                menu_item_id: item.menu_item_id,
                quantity: item.quantity,
                name: menuItem?.name || "Неизвестный товар",
                price: menuItem?.price ? parseFloat(menuItem.price) : 0
            };
        });
        
        saveCartToStorage();
        updateCartBadge();
        updateCartDisplay();
        showSection('order');
        
        if (window.Telegram?.WebApp) {
            Telegram.WebApp.showAlert("✅ Любимый заказ загружен!");
        } else {
            alert("Любимый заказ загружен!");
        }
        
        console.log('✅ Favorite order loaded');
        
    } catch (error) {
        showError(`Не удалось загрузить: ${error.message}`);
    }
}

// === НАВИГАЦИЯ ===
function showSection(sectionId) {
    // Скрываем все секции
    document.querySelectorAll('.section').forEach(section => {
        section.classList.remove('active');
    });
    
    // Показываем нужную секцию
    document.getElementById(sectionId).classList.add('active');
    
    // Обновляем навигацию
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    const activeBtn = Array.from(document.querySelectorAll('.nav-btn')).find(
        btn => btn.onclick.toString().includes(sectionId)
    );
    
    if (activeBtn) {
        activeBtn.classList.add('active');
    }
    
    // Обновляем отображение корзины при переходе
    if (sectionId === 'order') {
        updateCartDisplay();
    }
    
    // Тактильная обратная связь
    if (window.Telegram?.WebApp?.HapticFeedback) {
        Telegram.WebApp.HapticFeedback.impactOccurred('light');
    }
}

// === УТИЛИТЫ ===
function showError(message) {
    console.error('❌', message);
    
    if (window.Telegram?.WebApp) {
        Telegram.WebApp.showAlert(message);
    } else {
        alert(message);
    }
}

function copyInitData() {
    const initData = Telegram.WebApp.initData;
    if (!initData) {
        alert("initData ещё не загружено. Подожди секунду и попробуй снова.");
        return;
    }
    navigator.clipboard.writeText(initData).then(() => {
        alert("initData скопирована в буфер!\nТеперь вставь её в Swagger UI в заголовок X-Telegram-Init-Data");
    }).catch(() => {
        alert("Не удалось скопировать. initData в консоли (F12 если на ПК).");
        console.log(initData);
    });
}

// === ЗАПУСК ПРИЛОЖЕНИЯ ===
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    initApp();
}

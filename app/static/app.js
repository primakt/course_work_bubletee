let currentUser = null;
let cart = [];

function showSection(section) {
    document.querySelectorAll('#menu, #promotions, #order, #loyalty').forEach(el => el.classList.remove('active'));
    document.getElementById(section).classList.add('active');
    document.querySelectorAll('nav button').forEach(btn => btn.classList.remove('active'));
    document.querySelector(`nav button[onclick="showSection('${section}')"]`).classList.add('active');

    if (section === 'menu') loadMenu();
    if (section === 'promotions') loadPromotions();
    if (section === 'loyalty') loadLoyalty();
}

Telegram.WebApp.ready();
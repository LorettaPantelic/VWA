const burgerBtn = document.querySelector('.burger-btn');
const menuItems = document.querySelector('.menu-items');

burgerBtn.addEventListener('click', () => {
    menuItems.classList.toggle('active');
    burgerBtn.classList.toggle('open');
});
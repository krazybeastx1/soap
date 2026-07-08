/* Dashboard page behavior */
(function () {
  // Small touch: animate cards in on load.
  const cards = document.querySelectorAll('.dash-card');
  if (!cards.length) return;
  cards.forEach((card, idx) => {
    card.style.opacity = '0';
    card.style.transform = 'translateY(8px)';
    card.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
    setTimeout(() => {
      card.style.opacity = '1';
      card.style.transform = 'translateY(0)';
    }, 60 * idx);
  });
})();

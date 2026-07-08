/* Login page behavior */
(function () {
  const form = document.querySelector('.login-form');
  if (!form) return;
  const input = form.querySelector('input[name="queue_number"]');
  if (!input) return;

  input.addEventListener('input', () => {
    input.value = input.value.toUpperCase();
  });

  form.addEventListener('submit', () => {
    const btn = form.querySelector('button[type="submit"]');
    if (btn) {
      btn.disabled = true;
      btn.textContent = 'Verifying...';
    }
  });
})();

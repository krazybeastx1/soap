/* Queue page behavior */
(function () {
  const config = window.QUEUE_CONFIG || { countdown: 5, redirectUrl: '/login' };
  const statusEl = document.getElementById('status-message');
  const progressEl = document.getElementById('progress-bar');
  const countdownEl = document.getElementById('countdown');
  const queueEl = document.getElementById('queue-number');

  const messages = [
    'Arriving at the queue...',
    'Verifying your request...',
    'Allocating a SOAP handler...',
    'Almost there...',
    'Forwarding you to the portal...',
  ];

  let elapsed = 0;
  const total = Math.max(1, config.countdown);

  function render() {
    if (progressEl) {
      const pct = Math.min(100, Math.round((elapsed / total) * 100));
      progressEl.style.width = pct + '%';
    }
    if (countdownEl) {
      countdownEl.textContent = Math.max(0, total - elapsed);
    }
    if (statusEl && elapsed <= messages.length) {
      statusEl.textContent = messages[elapsed] || messages[messages.length - 1];
    }
  }

  render();

  const interval = setInterval(() => {
    elapsed += 1;
    render();
    if (elapsed >= total) {
      clearInterval(interval);
      window.location.href = config.redirectUrl;
    }
  }, 1000);
})();

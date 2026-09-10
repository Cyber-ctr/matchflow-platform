(function () {
  const toggle = document.querySelector('[data-menu-toggle]');
  const nav = document.querySelector('[data-nav]');
  if (toggle && nav) {
    toggle.addEventListener('click', function () {
      nav.classList.toggle('open');
    });
  }

  const roles = document.querySelectorAll('[data-role-switch]');
  const talentFields = document.querySelector('[data-register-role="talent"]');
  const employerFields = document.querySelector('[data-register-role="employer"]');
  function updateRoleFields() {
    const selected = document.querySelector('[data-role-switch]:checked');
    if (!selected) return;
    const isTalent = selected.value === 'talent';
    if (talentFields) talentFields.classList.toggle('hidden', !isTalent);
    if (employerFields) employerFields.classList.toggle('hidden', isTalent);
  }
  roles.forEach((role) => role.addEventListener('change', updateRoleFields));
  updateRoleFields();

  if ('serviceWorker' in navigator) {
    window.addEventListener('load', function () {
      navigator.serviceWorker.register('/static/sw.js').catch(function () {});
    });
  }
})();

  let deferredPrompt;
  const installButton = document.querySelector('[data-install-app]');
  window.addEventListener('beforeinstallprompt', (event) => {
    event.preventDefault();
    deferredPrompt = event;
    if (installButton) installButton.classList.remove('hidden');
  });
  if (installButton) {
    installButton.addEventListener('click', async () => {
      if (!deferredPrompt) return;
      deferredPrompt.prompt();
      await deferredPrompt.userChoice;
      deferredPrompt = null;
      installButton.classList.add('hidden');
    });
  }

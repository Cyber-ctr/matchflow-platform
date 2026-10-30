(function () {
  const toggle = document.querySelector('[data-menu-toggle]');
  const nav = document.querySelector('[data-nav]');
  if (toggle && nav) {
    function setMenuOpen(isOpen) {
      nav.classList.toggle('open', isOpen);
      toggle.setAttribute('aria-expanded', String(isOpen));
      toggle.setAttribute(
        'aria-label',
        isOpen ? 'Close navigation menu' : 'Open navigation menu'
      );
    }

    toggle.addEventListener('click', function () {
      setMenuOpen(toggle.getAttribute('aria-expanded') !== 'true');
    });

    nav.addEventListener('click', function (event) {
      if (event.target.closest('a, form button')) setMenuOpen(false);
    });

    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') {
        setMenuOpen(false);
        toggle.focus();
      }
    });

    document.addEventListener('click', function (event) {
      if (!nav.contains(event.target) && !toggle.contains(event.target)) {
        setMenuOpen(false);
      }
    });
  }

  const roles = document.querySelectorAll('[data-role-switch]');
  const talentFields = document.querySelector('[data-register-role="talent"]');
  const employerFields = document.querySelector('[data-register-role="employer"]');
  function updateRoleFields() {
    const selected = document.querySelector('[data-role-switch]:checked');
    if (!selected) return;
    const isTalent = selected.value === 'talent';
    if (talentFields) {
      talentFields.hidden = !isTalent;
      talentFields.inert = !isTalent;
      talentFields.classList.toggle('hidden', !isTalent);
    }
    if (employerFields) {
      employerFields.hidden = isTalent;
      employerFields.inert = isTalent;
      employerFields.classList.toggle('hidden', isTalent);
    }
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

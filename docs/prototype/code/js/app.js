// SUPMEAL — interactions prototype (démonstration, pas de logique métier réelle)

document.addEventListener('click', (e) => {
  // Ouvre/ferme les menus "..." (dropdown)
  const trigger = e.target.closest('[data-menu-trigger]');
  document.querySelectorAll('.dropdown-menu.open').forEach((menu) => {
    if (!trigger || menu !== trigger.closest('.menu-wrap')?.querySelector('.dropdown-menu')) {
      menu.classList.remove('open');
    }
  });
  if (trigger) {
    const menu = trigger.closest('.menu-wrap')?.querySelector('.dropdown-menu');
    menu?.classList.toggle('open');
    e.stopPropagation();
  }

  // Ouvre une modale
  const openBtn = e.target.closest('[data-modal-open]');
  if (openBtn) {
    document.getElementById(openBtn.dataset.modalOpen)?.classList.add('open');
  }

  // Ferme une modale
  const closeBtn = e.target.closest('[data-modal-close]');
  if (closeBtn) {
    closeBtn.closest('.modal-overlay')?.classList.remove('open');
  }
  if (e.target.classList.contains('modal-overlay')) {
    e.target.classList.remove('open');
  }

  // Onglets (tabs-underline / tabs-inline)
  const tabBtn = e.target.closest('[data-tab-target]');
  if (tabBtn) {
    const group = tabBtn.closest('[data-tab-group]');
    group?.querySelectorAll('[data-tab-target]').forEach((b) => b.classList.remove('active'));
    tabBtn.classList.add('active');
    group?.querySelectorAll('[data-tab-panel]').forEach((panel) => {
      panel.style.display = panel.dataset.tabPanel === tabBtn.dataset.tabTarget ? '' : 'none';
    });
  }

  // Affiche/masque un mot de passe
  const toggleBtn = e.target.closest('[data-toggle-password]');
  if (toggleBtn) {
    const input = toggleBtn.closest('.password-field').querySelector('input');
    input.type = input.type === 'password' ? 'text' : 'password';
  }
});

// Confirmation de suppression par saisie du mot "suppression"
document.addEventListener('input', (e) => {
  if (e.target.matches('[data-confirm-delete-input]')) {
    const confirmBtn = document.querySelector(e.target.dataset.confirmDeleteInput);
    if (confirmBtn) {
      confirmBtn.disabled = e.target.value.trim().toLowerCase() !== 'suppression';
    }
  }
});

// Simule le glisser-déposer sur la zone d'import
document.querySelectorAll('.dropzone').forEach((zone) => {
  ['dragenter', 'dragover'].forEach((evt) =>
    zone.addEventListener(evt, (e) => { e.preventDefault(); zone.style.borderColor = 'var(--primary-dark)'; })
  );
  ['dragleave', 'drop'].forEach((evt) =>
    zone.addEventListener(evt, (e) => { e.preventDefault(); zone.style.borderColor = 'var(--border)'; })
  );
});

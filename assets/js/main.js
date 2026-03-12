/* main.js — lightweight UI enhancements */

// ── Active nav link ──────────────────────────────────────────────────────
(function () {
  const page = window.location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.nav-links a').forEach(a => {
    const href = a.getAttribute('href');
    if (href === page || (page === '' && href === 'index.html')) {
      a.classList.add('active');
    }
  });
})();

// ── Publication type filter (publications.html) ──────────────────────────
(function () {
  const filterBtns = document.querySelectorAll('[data-pub-filter]');
  if (!filterBtns.length) return;

  filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const type = btn.dataset.pubFilter;

      // Toggle active state on buttons
      filterBtns.forEach(b => b.classList.remove('filter-active'));
      btn.classList.add('filter-active');

      // Show/hide sections
      document.querySelectorAll('[data-pub-type]').forEach(section => {
        if (type === 'all' || section.dataset.pubType === type) {
          section.style.display = '';
        } else {
          section.style.display = 'none';
        }
      });
    });
  });
})();

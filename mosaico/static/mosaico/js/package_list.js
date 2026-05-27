/* ═══════════════════════════════════════════════════════
   MosaicoIG — Package List Page JS
   ═══════════════════════════════════════════════════════ */

(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', () => {
    initCreatePackage();
  });

  function initCreatePackage() {
    const createBtn = document.getElementById('createPackageBtn');
    if (!createBtn) return;

    createBtn.addEventListener('click', async () => {
      const title = document.getElementById('pkg-title').value.trim();
      const filter1 = document.getElementById('pkg-filter1').value;
      const filter2 = document.getElementById('pkg-filter2').value;
      const errorDiv = document.getElementById('create-error');
      const errorMsg = document.getElementById('create-error-msg');

      // Client-side validation: filter_1 != filter_2
      if (filter1 !== 'none' && filter2 !== 'none' && filter1 === filter2) {
        errorDiv.classList.remove('d-none');
        errorMsg.textContent = 'Filtro 1 y Filtro 2 no pueden ser iguales.';
        return;
      }

      // Clear errors
      errorDiv.classList.add('d-none');

      // Disable button & show spinner
      createBtn.disabled = true;
      createBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Creando…';

      try {
        const pkg = await MosaicoAPI.createPackage(title, filter1, filter2);
        showToast('¡Mosaico creado exitosamente!', 'success');

        // Redirect to detail page
        // The API returns the package with an id; build the URL
        // We'll use the standard Django URL pattern
        setTimeout(() => {
          window.location.href = `/packages/${pkg.id}/`;
        }, 300);
      } catch (err) {
        const detail = err.data
          ? Object.values(err.data).flat().join(' ')
          : err.message;

        errorDiv.classList.remove('d-none');
        errorMsg.textContent = detail || 'Error al crear el mosaico.';

        createBtn.disabled = false;
        createBtn.innerHTML = '<i class="bi bi-plus-lg me-1"></i>Crear Mosaico';
      }
    });
  }

})();

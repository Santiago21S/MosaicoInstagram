/* ═══════════════════════════════════════════════════════
   MosaicoIG — Package Detail Page JS
   ═══════════════════════════════════════════════════════ */

(function () {
  'use strict';

  const PKG = window.PACKAGE_DATA || {};
  const packageId = PKG.id;
  let currentStatus = PKG.status;
  let pollingTimer = null;

  // ──────── DOM Ready ────────
  document.addEventListener('DOMContentLoaded', () => {
    initDropzone();
    initFileInput();
    initDeleteImageButtons();
    initGenerateButton();
    initRegenerateButton();
    initRetryButton();
    initDeletePackage();
    initEditPackage();
    initEditTitle();

    // Auto-poll if already processing
    if (currentStatus === 'processing') {
      startPolling();
    }
  });

  // ════════════════════════════════════════════
  //  DRAG & DROP UPLOAD
  // ════════════════════════════════════════════

  function initDropzone() {
    const dropzone = document.getElementById('dropzone');
    if (!dropzone) return;

    const fileInput = document.getElementById('fileInput');

    // Click to open file dialog
    dropzone.addEventListener('click', (e) => {
      if (e.target.closest('.progress')) return;
      fileInput.click();
    });

    // Drag events
    ['dragenter', 'dragover'].forEach(evt => {
      dropzone.addEventListener(evt, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.add('drag-over');
      });
    });

    ['dragleave', 'drop'].forEach(evt => {
      dropzone.addEventListener(evt, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.remove('drag-over');
      });
    });

    dropzone.addEventListener('drop', (e) => {
      const files = Array.from(e.dataTransfer.files).filter(f => f.type.startsWith('image/'));
      if (files.length) uploadFiles(files);
    });
  }

  function initFileInput() {
    const fileInput = document.getElementById('fileInput');
    if (!fileInput) return;

    fileInput.addEventListener('change', () => {
      const files = Array.from(fileInput.files);
      if (files.length) uploadFiles(files);
      fileInput.value = ''; // Reset
    });
  }

  async function uploadFiles(files) {
    const maxSlots = 4 - PKG.imageCount;
    const toUpload = files.slice(0, Math.max(0, maxSlots));

    if (toUpload.length === 0) {
      showToast('Ya tienes el máximo de 4 imágenes.', 'warning');
      return;
    }

    const progressWrap = document.getElementById('uploadProgress');
    const progressBar = document.getElementById('uploadProgressBar');

    if (progressWrap) progressWrap.classList.remove('d-none');

    let uploaded = 0;

    for (const file of toUpload) {
      try {
        if (progressBar) {
          const pct = Math.round(((uploaded) / toUpload.length) * 100);
          progressBar.style.width = pct + '%';
        }

        const nextOrder = PKG.imageCount + uploaded + 1;
        await MosaicoAPI.uploadImage(packageId, file, nextOrder);
        uploaded++;
        showToast(`Imagen "${file.name}" subida correctamente.`, 'success');

        if (progressBar) {
          const pct = Math.round((uploaded / toUpload.length) * 100);
          progressBar.style.width = pct + '%';
        }
      } catch (err) {
        showToast(`Error al subir "${file.name}": ${err.message}`, 'error');
      }
    }

    // Small delay so user sees 100%
    if (progressBar) progressBar.style.width = '100%';
    setTimeout(() => {
      location.reload();
    }, 600);
  }

  // ════════════════════════════════════════════
  //  DELETE IMAGE
  // ════════════════════════════════════════════

  function initDeleteImageButtons() {
    document.querySelectorAll('.delete-image-btn').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        e.preventDefault();
        e.stopPropagation();

        const imageId = btn.dataset.imageId;
        if (!imageId) return;

        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';

        try {
          await MosaicoAPI.deleteImage(packageId, imageId);
          showToast('Imagen eliminada.', 'success');

          // Animate out and reload
          const card = btn.closest('[data-image-id]');
          if (card) {
            card.style.transition = 'opacity .3s, transform .3s';
            card.style.opacity = '0';
            card.style.transform = 'scale(.8)';
          }
          setTimeout(() => location.reload(), 400);
        } catch (err) {
          showToast('Error al eliminar la imagen: ' + err.message, 'error');
          btn.disabled = false;
          btn.innerHTML = '<i class="bi bi-x-lg"></i>';
        }
      });
    });
  }

  // ════════════════════════════════════════════
  //  GENERATE MOSAIC
  // ════════════════════════════════════════════

  function initGenerateButton() {
    const btn = document.getElementById('generateBtn');
    if (!btn) return;

    btn.addEventListener('click', async () => {
      btn.disabled = true;
      btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Generando…';

      try {
        await MosaicoAPI.triggerGenerate(packageId);
        showToast('¡Generación iniciada!', 'success');
        currentStatus = 'processing';
        location.reload();
      } catch (err) {
        showToast('Error: ' + err.message, 'error');
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-stars me-2"></i>Generar Mosaico';
      }
    });
  }

  function initRegenerateButton() {
    const btn = document.getElementById('regenerateBtn');
    if (!btn) return;

    btn.addEventListener('click', async () => {
      btn.disabled = true;
      btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Regenerando…';

      try {
        await MosaicoAPI.triggerGenerate(packageId);
        showToast('Regeneración iniciada.', 'success');
        location.reload();
      } catch (err) {
        showToast('Error: ' + err.message, 'error');
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-arrow-clockwise me-2"></i>Regenerar';
      }
    });
  }

  function initRetryButton() {
    const btn = document.getElementById('retryBtn');
    if (!btn) return;

    btn.addEventListener('click', async () => {
      btn.disabled = true;
      btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Reintentando…';

      try {
        await MosaicoAPI.triggerGenerate(packageId);
        showToast('Reintentando generación…', 'success');
        location.reload();
      } catch (err) {
        showToast('Error: ' + err.message, 'error');
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-arrow-clockwise me-2"></i>Reintentar';
      }
    });
  }

  // ════════════════════════════════════════════
  //  STATUS POLLING
  // ════════════════════════════════════════════

  function startPolling() {
    if (pollingTimer) return;

    pollingTimer = setInterval(async () => {
      try {
        const data = await MosaicoAPI.checkStatus(packageId);
        if (data.status && data.status !== 'processing') {
          clearInterval(pollingTimer);
          pollingTimer = null;
          currentStatus = data.status;

          if (data.status === 'completed') {
            showToast('¡Mosaico generado exitosamente!', 'success');
          } else if (data.status === 'failed') {
            showToast('Error al generar el mosaico.', 'error');
          }

          // Reload to show new state
          location.reload();
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 2000);
  }

  // ════════════════════════════════════════════
  //  DELETE PACKAGE
  // ════════════════════════════════════════════

  function initDeletePackage() {
    const deleteBtn = document.getElementById('deletePackageBtn');
    const confirmBtn = document.getElementById('confirmDeleteBtn');
    const modal = document.getElementById('deleteConfirmModal');

    if (!deleteBtn || !confirmBtn || !modal) return;

    const bsModal = new bootstrap.Modal(modal);

    deleteBtn.addEventListener('click', () => bsModal.show());

    confirmBtn.addEventListener('click', async () => {
      confirmBtn.disabled = true;
      confirmBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Eliminando…';

      try {
        await MosaicoAPI.deletePackage(packageId);
        showToast('Mosaico eliminado.', 'success');
        setTimeout(() => {
          window.location.href = PKG.listUrl;
        }, 500);
      } catch (err) {
        showToast('Error al eliminar: ' + err.message, 'error');
        confirmBtn.disabled = false;
        confirmBtn.innerHTML = '<i class="bi bi-trash me-1"></i>Eliminar';
      }
    });
  }

  // ════════════════════════════════════════════
  //  EDIT PACKAGE (Modal)
  // ════════════════════════════════════════════

  function initEditPackage() {
    const saveBtn = document.getElementById('saveEditBtn');
    if (!saveBtn) return;

    saveBtn.addEventListener('click', async () => {
      const title = document.getElementById('edit-title').value.trim();
      const filter1 = document.getElementById('edit-filter1').value;
      const filter2 = document.getElementById('edit-filter2').value;
      const errorDiv = document.getElementById('edit-error');
      const errorMsg = document.getElementById('edit-error-msg');

      // Validate filters
      if (filter1 !== 'none' && filter2 !== 'none' && filter1 === filter2) {
        errorDiv.classList.remove('d-none');
        errorMsg.textContent = 'Filtro 1 y Filtro 2 no pueden ser iguales.';
        return;
      }

      errorDiv.classList.add('d-none');
      saveBtn.disabled = true;
      saveBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Guardando…';

      try {
        await MosaicoAPI.updatePackage(packageId, {
          title,
          filter_1: filter1,
          filter_2: filter2,
        });
        showToast('Cambios guardados.', 'success');
        setTimeout(() => location.reload(), 500);
      } catch (err) {
        showToast('Error al guardar: ' + err.message, 'error');
        saveBtn.disabled = false;
        saveBtn.innerHTML = '<i class="bi bi-check-lg me-1"></i>Guardar cambios';
      }
    });
  }

  // ════════════════════════════════════════════
  //  INLINE TITLE EDIT
  // ════════════════════════════════════════════

  function initEditTitle() {
    const editBtn = document.getElementById('editTitleBtn');
    const titleEl = document.getElementById('packageTitle');
    if (!editBtn || !titleEl) return;

    editBtn.addEventListener('click', () => {
      const currentTitle = titleEl.textContent.trim();
      const input = document.createElement('input');
      input.type = 'text';
      input.className = 'form-control glass-input d-inline-block';
      input.style.maxWidth = '300px';
      input.value = currentTitle === 'Paquete sin título' ? '' : currentTitle;
      input.maxLength = 200;

      titleEl.replaceWith(input);
      input.focus();
      input.select();

      const save = async () => {
        const newTitle = input.value.trim();
        try {
          await MosaicoAPI.updatePackage(packageId, { title: newTitle });
          showToast('Título actualizado.', 'success');
          location.reload();
        } catch (err) {
          showToast('Error: ' + err.message, 'error');
          input.replaceWith(titleEl);
        }
      };

      input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') { e.preventDefault(); save(); }
        if (e.key === 'Escape') { input.replaceWith(titleEl); }
      });

      input.addEventListener('blur', save);
    });
  }

})();

/* ═══════════════════════════════════════════════════════
   MosaicoIG — API Client (vanilla JS, no module)
   ═══════════════════════════════════════════════════════ */

const MosaicoAPI = (() => {
  'use strict';

  // ──────── CSRF helper ────────
  function getCSRFToken() {
    // 1. Try meta tag
    const meta = document.querySelector('meta[name="csrf-token"]');
    if (meta) return meta.getAttribute('content');

    // 2. Try cookie
    const cookie = document.cookie
      .split('; ')
      .find(row => row.startsWith('csrftoken='));
    return cookie ? cookie.split('=')[1] : '';
  }

  // ──────── Base fetch wrapper ────────
  async function request(url, options = {}) {
    const defaults = {
      credentials: 'same-origin',
      headers: {
        'X-CSRFToken': getCSRFToken(),
      },
    };

    // Merge headers
    const headers = { ...defaults.headers, ...options.headers };

    // Don't set Content-Type for FormData (browser sets boundary)
    if (options.body instanceof FormData) {
      delete headers['Content-Type'];
    } else if (options.body && typeof options.body === 'object') {
      headers['Content-Type'] = 'application/json';
      options.body = JSON.stringify(options.body);
    }

    const response = await fetch(url, {
      ...defaults,
      ...options,
      headers,
    });

    // 204 No Content
    if (response.status === 204) return null;

    // Error handling
    if (!response.ok) {
      let errorData;
      try {
        errorData = await response.json();
      } catch {
        errorData = { detail: response.statusText };
      }
      const err = new Error(errorData.detail || 'Error en la solicitud');
      err.status = response.status;
      err.data = errorData;
      throw err;
    }

    return response.json();
  }

  // ──────── API Functions ────────

  /**
   * Create a new package.
   * POST /api/v1/packages/
   */
  function createPackage(title, filter1, filter2) {
    return request('/api/v1/packages/', {
      method: 'POST',
      body: { title, filter_1: filter1, filter_2: filter2 },
    });
  }

  /**
   * Upload an image to a package.
   * POST /api/v1/packages/{id}/images/
   */
  function uploadImage(packageId, file, order) {
    const formData = new FormData();
    formData.append('image', file);
    if (order !== undefined && order !== null) {
      formData.append('order', order);
    }
    return request(`/api/v1/packages/${packageId}/images/`, {
      method: 'POST',
      body: formData,
    });
  }

  /**
   * Delete an image from a package.
   * DELETE /api/v1/packages/{id}/images/{imgId}/
   */
  function deleteImage(packageId, imageId) {
    return request(`/api/v1/packages/${packageId}/images/${imageId}/`, {
      method: 'DELETE',
    });
  }

  /**
   * Replace an image in a package.
   * PUT /api/v1/packages/{id}/images/{imgId}/
   */
  function replaceImage(packageId, imageId, file) {
    const formData = new FormData();
    formData.append('image', file);
    return request(`/api/v1/packages/${packageId}/images/${imageId}/`, {
      method: 'PUT',
      body: formData,
    });
  }

  /**
   * Trigger mosaic generation.
   * POST /api/v1/packages/{id}/generate/
   */
  function triggerGenerate(packageId) {
    return request(`/api/v1/packages/${packageId}/generate/`, {
      method: 'POST',
    });
  }

  /**
   * Check package status.
   * GET /api/v1/packages/{id}/status/
   */
  function checkStatus(packageId) {
    return request(`/api/v1/packages/${packageId}/status/`, {
      method: 'GET',
    });
  }

  /**
   * Delete a package.
   * DELETE /api/v1/packages/{id}/
   */
  function deletePackage(packageId) {
    return request(`/api/v1/packages/${packageId}/`, {
      method: 'DELETE',
    });
  }

  /**
   * Update a package (partial).
   * PATCH /api/v1/packages/{id}/
   */
  function updatePackage(packageId, data) {
    return request(`/api/v1/packages/${packageId}/`, {
      method: 'PATCH',
      body: data,
    });
  }

  // ──────── Public API ────────
  return {
    createPackage,
    uploadImage,
    deleteImage,
    replaceImage,
    triggerGenerate,
    checkStatus,
    deletePackage,
    updatePackage,
  };
})();

/* ──────── Toast Utility ──────── */
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const icons = {
    success: 'bi-check-circle-fill',
    error: 'bi-exclamation-triangle-fill',
    warning: 'bi-exclamation-circle-fill',
    info: 'bi-info-circle-fill',
  };

  const colors = {
    success: '#4ade80',
    error: '#f87171',
    warning: '#facc15',
    info: '#60a5fa',
  };

  const id = 'toast-' + Date.now();
  const html = `
    <div id="${id}" class="toast align-items-center text-white border-0 mb-2" role="alert"
         aria-live="assertive" aria-atomic="true" data-bs-delay="4000"
         style="border-left: 3px solid ${colors[type]} !important;">
      <div class="d-flex">
        <div class="toast-body d-flex align-items-center gap-2">
          <i class="bi ${icons[type] || icons.info}" style="color:${colors[type]};"></i>
          ${message}
        </div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Cerrar"></button>
      </div>
    </div>`;

  container.insertAdjacentHTML('beforeend', html);

  const toastEl = document.getElementById(id);
  const toast = new bootstrap.Toast(toastEl);
  toast.show();

  // Clean up after hidden
  toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
}

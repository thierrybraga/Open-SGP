/**
 * main.js - JavaScript principal do ISP ERP
 * Funcionalidades globais e utilitários
 */

// Namespace global para evitar conflitos
const ISP_ERP = window.ISP_ERP || {};

/**
 * Inicialização quando o DOM está pronto
 */
document.addEventListener('DOMContentLoaded', function() {
  ISP_ERP.init();
});

/**
 * Inicialização principal
 */
ISP_ERP.init = function() {
  console.log('ISP ERP - Sistema inicializado');

  // Inicializar componentes
  ISP_ERP.initTooltips();
  ISP_ERP.initModals();
  ISP_ERP.initForms();
  ISP_ERP.initTables();
  ISP_ERP.updateActiveNavLink();
};

/**
 * Tooltips
 */
ISP_ERP.initTooltips = function() {
  const tooltipElements = document.querySelectorAll('[data-tooltip]');

  tooltipElements.forEach(element => {
    element.addEventListener('mouseenter', function(e) {
      const tooltip = document.createElement('div');
      tooltip.className = 'tooltip';
      tooltip.textContent = this.getAttribute('data-tooltip');
      tooltip.style.cssText = `
        position: absolute;
        background: var(--text-primary);
        color: white;
        padding: var(--spacing-xs) var(--spacing-sm);
        border-radius: var(--radius-md);
        font-size: var(--font-size-xs);
        white-space: nowrap;
        z-index: 9999;
        pointer-events: none;
      `;

      document.body.appendChild(tooltip);

      const rect = this.getBoundingClientRect();
      tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
      tooltip.style.top = rect.top - tooltip.offsetHeight - 8 + 'px';

      this._tooltip = tooltip;
    });

    element.addEventListener('mouseleave', function() {
      if (this._tooltip) {
        this._tooltip.remove();
        delete this._tooltip;
      }
    });
  });
};

/**
 * Modals
 */
ISP_ERP.initModals = function() {
  // Abrir modals
  document.addEventListener('click', function(e) {
    const trigger = e.target.closest('[data-modal-target]');
    if (trigger) {
      e.preventDefault();
      const modalId = trigger.getAttribute('data-modal-target');
      ISP_ERP.openModal(modalId);
    }
  });

  // Fechar modals
  document.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal-overlay') ||
        e.target.closest('.modal-close') ||
        e.target.closest('[data-modal-close]')) {
      const modal = e.target.closest('.modal-overlay');
      if (modal) {
        ISP_ERP.closeModal(modal);
      }
    }
  });

  // Fechar com ESC
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
      const openModals = document.querySelectorAll('.modal-overlay');
      openModals.forEach(modal => ISP_ERP.closeModal(modal));
    }
  });
};

ISP_ERP.openModal = function(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
  }
};

ISP_ERP.closeModal = function(modal) {
  if (typeof modal === 'string') {
    modal = document.getElementById(modal);
  }
  if (modal) {
    modal.style.display = 'none';
    document.body.style.overflow = '';
  }
};

/**
 * Formulários
 */
ISP_ERP.initForms = function() {
  // Validação básica
  const forms = document.querySelectorAll('form[data-validate]');

  forms.forEach(form => {
    form.addEventListener('submit', function(e) {
      if (!ISP_ERP.validateForm(this)) {
        e.preventDefault();
      }
    });
  });

  // Auto-submit em filtros
  const filterSelects = document.querySelectorAll('select[name="status"], select[name="technician"]');
  filterSelects.forEach(select => {
    select.addEventListener('change', function() {
      const form = this.closest('form');
      if (form && form.getAttribute('data-auto-submit') !== 'false') {
        form.submit();
      }
    });
  });
};

ISP_ERP.validateForm = function(form) {
  let isValid = true;
  const requiredFields = form.querySelectorAll('[required]');

  requiredFields.forEach(field => {
    if (!field.value.trim()) {
      isValid = false;
      field.classList.add('error');
      ISP_ERP.showFieldError(field, 'Este campo é obrigatório');
    } else {
      field.classList.remove('error');
      ISP_ERP.hideFieldError(field);
    }
  });

  return isValid;
};

ISP_ERP.showFieldError = function(field, message) {
  let errorElement = field.parentElement.querySelector('.field-error');

  if (!errorElement) {
    errorElement = document.createElement('div');
    errorElement.className = 'field-error';
    errorElement.style.cssText = `
      color: var(--danger-color);
      font-size: var(--font-size-xs);
      margin-top: var(--spacing-xs);
    `;
    field.parentElement.appendChild(errorElement);
  }

  errorElement.textContent = message;
  field.style.borderColor = 'var(--danger-color)';
};

ISP_ERP.hideFieldError = function(field) {
  const errorElement = field.parentElement.querySelector('.field-error');
  if (errorElement) {
    errorElement.remove();
  }
  field.style.borderColor = '';
};

/**
 * Tabelas
 */
ISP_ERP.initTables = function() {
  // Ordenação de colunas
  const sortableHeaders = document.querySelectorAll('th[data-sortable]');

  sortableHeaders.forEach(header => {
    header.style.cursor = 'pointer';
    header.addEventListener('click', function() {
      const table = this.closest('table');
      const column = Array.from(this.parentElement.children).indexOf(this);
      ISP_ERP.sortTable(table, column);
    });
  });

  // Seleção de linhas
  const selectableRows = document.querySelectorAll('tr[data-selectable]');

  selectableRows.forEach(row => {
    row.addEventListener('click', function(e) {
      if (!e.target.closest('button') && !e.target.closest('a')) {
        this.classList.toggle('selected');
      }
    });
  });
};

ISP_ERP.sortTable = function(table, column) {
  const tbody = table.querySelector('tbody');
  const rows = Array.from(tbody.querySelectorAll('tr'));
  const isAscending = table.dataset.sortDirection !== 'asc';

  rows.sort((a, b) => {
    const aValue = a.children[column].textContent.trim();
    const bValue = b.children[column].textContent.trim();

    const aNum = parseFloat(aValue.replace(/[^0-9.-]/g, ''));
    const bNum = parseFloat(bValue.replace(/[^0-9.-]/g, ''));

    if (!isNaN(aNum) && !isNaN(bNum)) {
      return isAscending ? aNum - bNum : bNum - aNum;
    }

    return isAscending
      ? aValue.localeCompare(bValue, 'pt-BR')
      : bValue.localeCompare(aValue, 'pt-BR');
  });

  rows.forEach(row => tbody.appendChild(row));
  table.dataset.sortDirection = isAscending ? 'asc' : 'desc';
};

/**
 * Navegação - Marcar link ativo
 */
ISP_ERP.updateActiveNavLink = function() {
  const currentPath = window.location.pathname;
  const navLinks = document.querySelectorAll('.navbar-menu-link');

  navLinks.forEach(link => {
    if (link.getAttribute('href') === currentPath) {
      link.classList.add('active');
    } else {
      link.classList.remove('active');
    }
  });
};

/**
 * Notificações toast
 */
ISP_ERP.showToast = function(message, type = 'info', duration = 3000) {
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  toast.style.cssText = `
    position: fixed;
    top: 80px;
    right: 20px;
    min-width: 280px;
    padding: var(--spacing-md) var(--spacing-lg);
    background: var(--bg-primary);
    border-left: 4px solid var(--${type}-color);
    border-radius: var(--radius-md);
    box-shadow: var(--shadow-lg);
    z-index: 9999;
    animation: slideInRight 0.3s ease-out;
  `;

  document.body.appendChild(toast);

  setTimeout(() => {
    toast.style.animation = 'slideOutRight 0.3s ease-in';
    setTimeout(() => toast.remove(), 300);
  }, duration);
};

/**
 * Confirmar ação
 */
ISP_ERP.confirm = function(message, callback) {
  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay';
  overlay.style.display = 'flex';

  const modal = document.createElement('div');
  modal.className = 'modal';
  modal.style.maxWidth = '400px';
  modal.innerHTML = `
    <div class="modal-header">
      <h3 class="modal-title">Confirmação</h3>
    </div>
    <div class="modal-body">
      <p>${message}</p>
    </div>
    <div class="modal-footer">
      <button class="btn btn-secondary" data-action="cancel">Cancelar</button>
      <button class="btn btn-primary" data-action="confirm">Confirmar</button>
    </div>
  `;

  overlay.appendChild(modal);
  document.body.appendChild(overlay);
  document.body.style.overflow = 'hidden';

  modal.querySelector('[data-action="confirm"]').addEventListener('click', function() {
    overlay.remove();
    document.body.style.overflow = '';
    if (callback) callback(true);
  });

  modal.querySelector('[data-action="cancel"]').addEventListener('click', function() {
    overlay.remove();
    document.body.style.overflow = '';
    if (callback) callback(false);
  });
};

/**
 * Loading overlay
 */
ISP_ERP.showLoading = function(container) {
  const overlay = document.createElement('div');
  overlay.className = 'loading-overlay';
  overlay.innerHTML = '<div class="spinner large"></div>';

  if (typeof container === 'string') {
    container = document.querySelector(container);
  }

  if (!container) {
    container = document.body;
  }

  container.style.position = 'relative';
  container.appendChild(overlay);

  return overlay;
};

ISP_ERP.hideLoading = function(overlay) {
  if (overlay && overlay.parentElement) {
    overlay.remove();
  }
};

/**
 * Formatação de números
 */
ISP_ERP.formatCurrency = function(value) {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  }).format(value);
};

ISP_ERP.formatNumber = function(value, decimals = 2) {
  return new Intl.NumberFormat('pt-BR', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  }).format(value);
};

ISP_ERP.formatDate = function(date) {
  if (!(date instanceof Date)) {
    date = new Date(date);
  }
  return new Intl.DateTimeFormat('pt-BR').format(date);
};

ISP_ERP.formatDateTime = function(date) {
  if (!(date instanceof Date)) {
    date = new Date(date);
  }
  return new Intl.DateTimeFormat('pt-BR', {
    dateStyle: 'short',
    timeStyle: 'short'
  }).format(date);
};

/**
 * Debounce function para otimizar eventos
 */
ISP_ERP.debounce = function(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};

/**
 * AJAX helper
 */
ISP_ERP.ajax = async function(url, options = {}) {
  try {
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('AJAX error:', error);
    ISP_ERP.showToast('Erro ao processar requisição', 'danger');
    throw error;
  }
};

// Exportar para uso global
window.ISP_ERP = ISP_ERP;

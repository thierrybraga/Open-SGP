/**
 * components.js - Advanced Reusable Components Library
 * ISP ERP Admin Panel
 */

const ISP_Components = window.ISP_Components || {};

/**
 * Filter Component - Reusable advanced filtering system
 */
ISP_Components.FilterPanel = class {
  constructor(config) {
    this.container = config.container;
    this.filters = config.filters || [];
    this.onApply = config.onApply;
    this.onReset = config.onReset;

    this.render();
  }

  render() {
    const html = `
      <div class="filter-panel">
        <div class="filter-panel-header">
          <h3 class="filter-panel-title">Filtros</h3>
          <button class="btn btn-link btn-sm" data-filter-toggle aria-label="Recolher filtros">
            <span class="filter-toggle-icon">▼</span>
          </button>
        </div>
        <div class="filter-panel-body">
          <div class="filter-grid">
            ${this.filters.map(filter => this.renderFilter(filter)).join('')}
          </div>
          <div class="filter-panel-actions">
            <button type="button" class="btn btn-secondary btn-sm" data-filter-reset>
              Limpar Filtros
            </button>
            <button type="button" class="btn btn-primary btn-sm" data-filter-apply>
              Aplicar Filtros
            </button>
          </div>
        </div>
      </div>
    `;

    if (typeof this.container === 'string') {
      this.container = document.querySelector(this.container);
    }

    this.container.innerHTML = html;
    this.attachEvents();
  }

  renderFilter(filter) {
    const id = `filter-${filter.name}`;

    switch (filter.type) {
      case 'select':
        return `
          <div class="filter-group">
            <label for="${id}" class="filter-label">${filter.label}</label>
            <select id="${id}" name="${filter.name}" class="form-select form-select-sm" aria-label="${filter.label}">
              <option value="">Todos</option>
              ${(filter.options || []).map(opt =>
                `<option value="${opt.value}">${opt.label}</option>`
              ).join('')}
            </select>
          </div>
        `;

      case 'date':
        return `
          <div class="filter-group">
            <label for="${id}" class="filter-label">${filter.label}</label>
            <input type="date" id="${id}" name="${filter.name}" class="form-control form-control-sm" aria-label="${filter.label}" />
          </div>
        `;

      case 'daterange':
        return `
          <div class="filter-group filter-group-daterange">
            <label class="filter-label">${filter.label}</label>
            <div class="daterange-inputs">
              <input type="date" name="${filter.name}_start" class="form-control form-control-sm" placeholder="De" aria-label="${filter.label} início" />
              <span class="daterange-separator">até</span>
              <input type="date" name="${filter.name}_end" class="form-control form-control-sm" placeholder="Até" aria-label="${filter.label} fim" />
            </div>
          </div>
        `;

      case 'number':
        return `
          <div class="filter-group">
            <label for="${id}" class="filter-label">${filter.label}</label>
            <input type="number" id="${id}" name="${filter.name}" class="form-control form-control-sm"
                   placeholder="${filter.placeholder || ''}" aria-label="${filter.label}" />
          </div>
        `;

      case 'text':
      default:
        return `
          <div class="filter-group">
            <label for="${id}" class="filter-label">${filter.label}</label>
            <input type="text" id="${id}" name="${filter.name}" class="form-control form-control-sm"
                   placeholder="${filter.placeholder || ''}" aria-label="${filter.label}" />
          </div>
        `;
    }
  }

  attachEvents() {
    // Toggle collapse
    const toggleBtn = this.container.querySelector('[data-filter-toggle]');
    if (toggleBtn) {
      toggleBtn.addEventListener('click', () => {
        const body = this.container.querySelector('.filter-panel-body');
        const icon = toggleBtn.querySelector('.filter-toggle-icon');
        body.classList.toggle('collapsed');
        icon.textContent = body.classList.contains('collapsed') ? '▶' : '▼';
        toggleBtn.setAttribute('aria-label',
          body.classList.contains('collapsed') ? 'Expandir filtros' : 'Recolher filtros'
        );
      });
    }

    // Apply filters
    const applyBtn = this.container.querySelector('[data-filter-apply]');
    if (applyBtn && this.onApply) {
      applyBtn.addEventListener('click', () => {
        const values = this.getValues();
        this.onApply(values);
      });
    }

    // Reset filters
    const resetBtn = this.container.querySelector('[data-filter-reset]');
    if (resetBtn) {
      resetBtn.addEventListener('click', () => {
        this.reset();
        if (this.onReset) {
          this.onReset();
        }
      });
    }
  }

  getValues() {
    const values = {};
    const inputs = this.container.querySelectorAll('input, select');

    inputs.forEach(input => {
      if (input.value) {
        values[input.name] = input.value;
      }
    });

    return values;
  }

  reset() {
    const inputs = this.container.querySelectorAll('input, select');
    inputs.forEach(input => {
      input.value = '';
    });
  }

  setValues(values) {
    Object.keys(values).forEach(name => {
      const input = this.container.querySelector(`[name="${name}"]`);
      if (input) {
        input.value = values[name];
      }
    });
  }
};

/**
 * Pagination Component - Advanced pagination with page size and navigation
 */
ISP_Components.Pagination = class {
  constructor(config) {
    this.container = config.container;
    this.total = config.total || 0;
    this.currentPage = config.currentPage || 1;
    this.pageSize = config.pageSize || 10;
    this.maxButtons = config.maxButtons || 5;
    this.onPageChange = config.onPageChange;

    this.render();
  }

  render() {
    const totalPages = Math.ceil(this.total / this.pageSize);
    const startItem = (this.currentPage - 1) * this.pageSize + 1;
    const endItem = Math.min(this.currentPage * this.pageSize, this.total);

    const html = `
      <div class="pagination-container">
        <div class="pagination-info">
          Mostrando ${startItem} a ${endItem} de ${this.total} registros
        </div>
        <div class="pagination">
          <button class="pagination-button" data-page="first" ${this.currentPage === 1 ? 'disabled' : ''}
                  aria-label="Primeira página">
            ⟪
          </button>
          <button class="pagination-button" data-page="prev" ${this.currentPage === 1 ? 'disabled' : ''}
                  aria-label="Página anterior">
            ⟨
          </button>
          ${this.renderPageButtons(totalPages)}
          <button class="pagination-button" data-page="next" ${this.currentPage === totalPages ? 'disabled' : ''}
                  aria-label="Próxima página">
            ⟩
          </button>
          <button class="pagination-button" data-page="last" ${this.currentPage === totalPages ? 'disabled' : ''}
                  aria-label="Última página">
            ⟫
          </button>
        </div>
        <div class="pagination-size">
          <label for="page-size-select" class="pagination-size-label">Por página:</label>
          <select id="page-size-select" class="form-select form-select-sm" data-page-size aria-label="Itens por página">
            ${[10, 25, 50, 100].map(size =>
              `<option value="${size}" ${size === this.pageSize ? 'selected' : ''}>${size}</option>`
            ).join('')}
          </select>
        </div>
      </div>
    `;

    if (typeof this.container === 'string') {
      this.container = document.querySelector(this.container);
    }

    this.container.innerHTML = html;
    this.attachEvents();
  }

  renderPageButtons(totalPages) {
    let buttons = [];
    let startPage = Math.max(1, this.currentPage - Math.floor(this.maxButtons / 2));
    let endPage = Math.min(totalPages, startPage + this.maxButtons - 1);

    if (endPage - startPage + 1 < this.maxButtons) {
      startPage = Math.max(1, endPage - this.maxButtons + 1);
    }

    for (let i = startPage; i <= endPage; i++) {
      buttons.push(`
        <button class="pagination-button ${i === this.currentPage ? 'active' : ''}"
                data-page="${i}"
                aria-label="Página ${i}"
                aria-current="${i === this.currentPage ? 'page' : 'false'}">
          ${i}
        </button>
      `);
    }

    return buttons.join('');
  }

  attachEvents() {
    const buttons = this.container.querySelectorAll('[data-page]');
    buttons.forEach(btn => {
      btn.addEventListener('click', () => {
        const page = btn.dataset.page;
        let newPage;

        const totalPages = Math.ceil(this.total / this.pageSize);

        switch(page) {
          case 'first':
            newPage = 1;
            break;
          case 'prev':
            newPage = Math.max(1, this.currentPage - 1);
            break;
          case 'next':
            newPage = Math.min(totalPages, this.currentPage + 1);
            break;
          case 'last':
            newPage = totalPages;
            break;
          default:
            newPage = parseInt(page);
        }

        if (newPage !== this.currentPage && this.onPageChange) {
          this.currentPage = newPage;
          this.onPageChange(newPage, this.pageSize);
          this.render();
        }
      });
    });

    const sizeSelect = this.container.querySelector('[data-page-size]');
    if (sizeSelect) {
      sizeSelect.addEventListener('change', () => {
        const newSize = parseInt(sizeSelect.value);
        if (newSize !== this.pageSize && this.onPageChange) {
          this.pageSize = newSize;
          this.currentPage = 1;
          this.onPageChange(1, newSize);
          this.render();
        }
      });
    }
  }

  update(config) {
    this.total = config.total !== undefined ? config.total : this.total;
    this.currentPage = config.currentPage !== undefined ? config.currentPage : this.currentPage;
    this.pageSize = config.pageSize !== undefined ? config.pageSize : this.pageSize;
    this.render();
  }
};

/**
 * Data Table Component - Enhanced table with sorting, selection, and actions
 */
ISP_Components.DataTable = class {
  constructor(config) {
    this.container = config.container;
    this.columns = config.columns || [];
    this.data = config.data || [];
    this.selectable = config.selectable || false;
    this.sortable = config.sortable !== false;
    this.actions = config.actions || [];
    this.onSort = config.onSort;
    this.onSelect = config.onSelect;
    this.emptyMessage = config.emptyMessage || 'Nenhum registro encontrado';

    this.sortColumn = null;
    this.sortDirection = 'asc';
    this.selectedRows = new Set();

    this.render();
  }

  render() {
    const html = `
      <div class="data-table-wrapper">
        <div class="table-responsive">
          <table class="table" role="table">
            <thead>
              <tr role="row">
                ${this.selectable ? '<th scope="col"><input type="checkbox" data-select-all aria-label="Selecionar todos" /></th>' : ''}
                ${this.columns.map(col => this.renderHeader(col)).join('')}
                ${this.actions.length > 0 ? '<th scope="col" class="text-end">Ações</th>' : ''}
              </tr>
            </thead>
            <tbody>
              ${this.data.length === 0 ? this.renderEmptyState() : this.data.map((row, idx) => this.renderRow(row, idx)).join('')}
            </tbody>
          </table>
        </div>
      </div>
    `;

    if (typeof this.container === 'string') {
      this.container = document.querySelector(this.container);
    }

    this.container.innerHTML = html;
    this.attachEvents();
  }

  renderHeader(column) {
    const sortable = this.sortable && column.sortable !== false;
    const isSorted = this.sortColumn === column.field;
    const sortIcon = isSorted ? (this.sortDirection === 'asc' ? '▲' : '▼') : '';

    return `
      <th scope="col" ${sortable ? `class="sortable" data-sort="${column.field}"` : ''}
          ${sortable ? 'role="button" tabindex="0"' : ''}
          ${sortable ? `aria-sort="${isSorted ? (this.sortDirection === 'ascending' ? 'ascending' : 'descending') : 'none'}"` : ''}>
        ${column.label}
        ${sortable ? `<span class="sort-icon" aria-hidden="true">${sortIcon}</span>` : ''}
      </th>
    `;
  }

  renderRow(row, index) {
    const rowId = row.id || index;
    const isSelected = this.selectedRows.has(rowId);

    return `
      <tr data-row-id="${rowId}" ${isSelected ? 'class="selected"' : ''} role="row">
        ${this.selectable ? `<td><input type="checkbox" data-select-row="${rowId}" ${isSelected ? 'checked' : ''} aria-label="Selecionar linha" /></td>` : ''}
        ${this.columns.map(col => this.renderCell(row, col)).join('')}
        ${this.actions.length > 0 ? `<td class="table-actions-cell">${this.renderActions(row)}</td>` : ''}
      </tr>
    `;
  }

  renderCell(row, column) {
    let value = row[column.field];

    if (column.render) {
      value = column.render(value, row);
    } else if (column.type === 'date' && value) {
      value = ISP_ERP.formatDate(new Date(value));
    } else if (column.type === 'currency' && value !== null && value !== undefined) {
      value = ISP_ERP.formatCurrency(value);
    } else if (column.type === 'status') {
      value = this.renderStatus(value);
    }

    return `<td>${value !== null && value !== undefined ? value : '-'}</td>`;
  }

  renderStatus(status) {
    const statusMap = {
      active: { label: 'Ativo', class: 'success' },
      inactive: { label: 'Inativo', class: 'danger' },
      pending: { label: 'Pendente', class: 'warning' },
      open: { label: 'Aberto', class: 'primary' },
      closed: { label: 'Fechado', class: 'secondary' },
      completed: { label: 'Concluído', class: 'success' },
    };

    const info = statusMap[status] || { label: status, class: 'secondary' };

    return `
      <span class="status-indicator ${info.class}">
        <span class="status-dot" aria-hidden="true"></span>
        ${info.label}
      </span>
    `;
  }

  renderActions(row) {
    return this.actions.map(action => {
      const icon = action.icon ? `<span aria-hidden="true">${action.icon}</span>` : '';
      return `
        <button class="action-button ${action.variant || ''}"
                data-action="${action.name}"
                data-row-id="${row.id}"
                aria-label="${action.label}">
          ${icon}
          ${action.showLabel !== false ? action.label : ''}
        </button>
      `;
    }).join('');
  }

  renderEmptyState() {
    return `
      <tr>
        <td colspan="${this.columns.length + (this.selectable ? 1 : 0) + (this.actions.length > 0 ? 1 : 0)}"
            class="text-center py-5">
          <div class="empty-state">
            <div class="empty-state-icon" aria-hidden="true">📋</div>
            <div class="empty-state-title">${this.emptyMessage}</div>
          </div>
        </td>
      </tr>
    `;
  }

  attachEvents() {
    // Sorting
    if (this.sortable) {
      const sortHeaders = this.container.querySelectorAll('[data-sort]');
      sortHeaders.forEach(header => {
        const sortHandler = () => {
          const field = header.dataset.sort;
          if (this.sortColumn === field) {
            this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
          } else {
            this.sortColumn = field;
            this.sortDirection = 'asc';
          }

          if (this.onSort) {
            this.onSort(this.sortColumn, this.sortDirection);
          } else {
            this.sortData();
          }

          this.render();
        };

        header.addEventListener('click', sortHandler);
        header.addEventListener('keydown', (e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            sortHandler();
          }
        });
      });
    }

    // Row selection
    if (this.selectable) {
      const selectAll = this.container.querySelector('[data-select-all]');
      if (selectAll) {
        selectAll.addEventListener('change', (e) => {
          if (e.target.checked) {
            this.data.forEach((row, idx) => {
              this.selectedRows.add(row.id || idx);
            });
          } else {
            this.selectedRows.clear();
          }

          this.render();

          if (this.onSelect) {
            this.onSelect(Array.from(this.selectedRows));
          }
        });
      }

      this.container.addEventListener('change', (e) => {
        const selectRow = e.target.closest('[data-select-row]');
        if (selectRow) {
          const rowId = selectRow.dataset.selectRow;

          if (e.target.checked) {
            this.selectedRows.add(rowId);
          } else {
            this.selectedRows.delete(rowId);
          }

          if (this.onSelect) {
            this.onSelect(Array.from(this.selectedRows));
          }
        }
      });
    }

    // Actions
    this.container.addEventListener('click', (e) => {
      const actionBtn = e.target.closest('[data-action]');
      if (actionBtn) {
        const actionName = actionBtn.dataset.action;
        const rowId = actionBtn.dataset.rowId;
        const row = this.data.find(r => r.id == rowId);
        const action = this.actions.find(a => a.name === actionName);

        if (action && action.handler) {
          action.handler(row, rowId);
        }
      }
    });
  }

  sortData() {
    const column = this.columns.find(c => c.field === this.sortColumn);
    if (!column) return;

    this.data.sort((a, b) => {
      let aVal = a[this.sortColumn];
      let bVal = b[this.sortColumn];

      if (column.type === 'number' || column.type === 'currency') {
        aVal = parseFloat(aVal) || 0;
        bVal = parseFloat(bVal) || 0;
        return this.sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
      }

      if (column.type === 'date') {
        aVal = new Date(aVal).getTime() || 0;
        bVal = new Date(bVal).getTime() || 0;
        return this.sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
      }

      aVal = String(aVal || '');
      bVal = String(bVal || '');

      return this.sortDirection === 'asc'
        ? aVal.localeCompare(bVal, 'pt-BR')
        : bVal.localeCompare(aVal, 'pt-BR');
    });
  }

  update(data) {
    this.data = data;
    this.render();
  }

  getSelectedRows() {
    return Array.from(this.selectedRows);
  }

  clearSelection() {
    this.selectedRows.clear();
    this.render();
  }
};

/**
 * Advanced Form Validation Component
 */
ISP_Components.FormValidator = class {
  constructor(form, rules) {
    this.form = typeof form === 'string' ? document.querySelector(form) : form;
    this.rules = rules || {};
    this.errors = {};

    this.attachEvents();
  }

  attachEvents() {
    this.form.addEventListener('submit', (e) => {
      if (!this.validate()) {
        e.preventDefault();
      }
    });

    // Real-time validation
    Object.keys(this.rules).forEach(fieldName => {
      const field = this.form.querySelector(`[name="${fieldName}"]`);
      if (field) {
        field.addEventListener('blur', () => {
          this.validateField(fieldName);
        });

        field.addEventListener('input', ISP_ERP.debounce(() => {
          if (this.errors[fieldName]) {
            this.validateField(fieldName);
          }
        }, 300));
      }
    });
  }

  validate() {
    this.errors = {};
    let isValid = true;

    Object.keys(this.rules).forEach(fieldName => {
      if (!this.validateField(fieldName)) {
        isValid = false;
      }
    });

    return isValid;
  }

  validateField(fieldName) {
    const field = this.form.querySelector(`[name="${fieldName}"]`);
    if (!field) return true;

    const rules = this.rules[fieldName];
    const value = field.value.trim();

    // Required
    if (rules.required && !value) {
      this.setError(field, rules.messages?.required || 'Este campo é obrigatório');
      return false;
    }

    // Skip other validations if field is empty and not required
    if (!value && !rules.required) {
      this.clearError(field);
      return true;
    }

    // Min length
    if (rules.minLength && value.length < rules.minLength) {
      this.setError(field, rules.messages?.minLength || `Mínimo de ${rules.minLength} caracteres`);
      return false;
    }

    // Max length
    if (rules.maxLength && value.length > rules.maxLength) {
      this.setError(field, rules.messages?.maxLength || `Máximo de ${rules.maxLength} caracteres`);
      return false;
    }

    // Email
    if (rules.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
      this.setError(field, rules.messages?.email || 'E-mail inválido');
      return false;
    }

    // CPF
    if (rules.cpf && !this.validateCPF(value)) {
      this.setError(field, rules.messages?.cpf || 'CPF inválido');
      return false;
    }

    // CNPJ
    if (rules.cnpj && !this.validateCNPJ(value)) {
      this.setError(field, rules.messages?.cnpj || 'CNPJ inválido');
      return false;
    }

    // Phone
    if (rules.phone && !/^\(\d{2}\)\s?\d{4,5}-?\d{4}$/.test(value)) {
      this.setError(field, rules.messages?.phone || 'Telefone inválido');
      return false;
    }

    // Number
    if (rules.number && isNaN(value)) {
      this.setError(field, rules.messages?.number || 'Número inválido');
      return false;
    }

    // Min value
    if (rules.min !== undefined && parseFloat(value) < rules.min) {
      this.setError(field, rules.messages?.min || `Valor mínimo: ${rules.min}`);
      return false;
    }

    // Max value
    if (rules.max !== undefined && parseFloat(value) > rules.max) {
      this.setError(field, rules.messages?.max || `Valor máximo: ${rules.max}`);
      return false;
    }

    // Pattern
    if (rules.pattern && !new RegExp(rules.pattern).test(value)) {
      this.setError(field, rules.messages?.pattern || 'Formato inválido');
      return false;
    }

    // Custom validation
    if (rules.custom && !rules.custom(value, field)) {
      this.setError(field, rules.messages?.custom || 'Valor inválido');
      return false;
    }

    this.clearError(field);
    return true;
  }

  validateCPF(cpf) {
    cpf = cpf.replace(/[^\d]/g, '');
    if (cpf.length !== 11 || /^(\d)\1+$/.test(cpf)) return false;

    let sum = 0;
    for (let i = 0; i < 9; i++) {
      sum += parseInt(cpf.charAt(i)) * (10 - i);
    }
    let digit = 11 - (sum % 11);
    if (digit > 9) digit = 0;
    if (parseInt(cpf.charAt(9)) !== digit) return false;

    sum = 0;
    for (let i = 0; i < 10; i++) {
      sum += parseInt(cpf.charAt(i)) * (11 - i);
    }
    digit = 11 - (sum % 11);
    if (digit > 9) digit = 0;
    if (parseInt(cpf.charAt(10)) !== digit) return false;

    return true;
  }

  validateCNPJ(cnpj) {
    cnpj = cnpj.replace(/[^\d]/g, '');
    if (cnpj.length !== 14 || /^(\d)\1+$/.test(cnpj)) return false;

    let length = cnpj.length - 2;
    let numbers = cnpj.substring(0, length);
    let digits = cnpj.substring(length);
    let sum = 0;
    let pos = length - 7;

    for (let i = length; i >= 1; i--) {
      sum += numbers.charAt(length - i) * pos--;
      if (pos < 2) pos = 9;
    }

    let result = sum % 11 < 2 ? 0 : 11 - sum % 11;
    if (result != digits.charAt(0)) return false;

    length++;
    numbers = cnpj.substring(0, length);
    sum = 0;
    pos = length - 7;

    for (let i = length; i >= 1; i--) {
      sum += numbers.charAt(length - i) * pos--;
      if (pos < 2) pos = 9;
    }

    result = sum % 11 < 2 ? 0 : 11 - sum % 11;
    if (result != digits.charAt(1)) return false;

    return true;
  }

  setError(field, message) {
    this.errors[field.name] = message;
    field.classList.add('is-invalid');
    field.setAttribute('aria-invalid', 'true');

    let errorDiv = field.parentElement.querySelector('.invalid-feedback');
    if (!errorDiv) {
      errorDiv = document.createElement('div');
      errorDiv.className = 'invalid-feedback';
      errorDiv.setAttribute('role', 'alert');
      field.parentElement.appendChild(errorDiv);
    }
    errorDiv.textContent = message;
  }

  clearError(field) {
    delete this.errors[field.name];
    field.classList.remove('is-invalid');
    field.removeAttribute('aria-invalid');

    const errorDiv = field.parentElement.querySelector('.invalid-feedback');
    if (errorDiv) {
      errorDiv.remove();
    }
  }

  reset() {
    this.errors = {};
    this.form.querySelectorAll('.is-invalid').forEach(field => {
      this.clearError(field);
    });
  }
};

// Export to global namespace
window.ISP_Components = ISP_Components;

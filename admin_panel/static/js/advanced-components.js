/**
 * advanced-components.js - Additional Advanced Components
 * ISP ERP Admin Panel
 *
 * Components: Tabs, Accordion, Toast, FileUpload, Stepper
 */

const ISP_AdvancedComponents = window.ISP_AdvancedComponents || {};

/**
 * Tabs Component - Tabbed navigation interface
 */
ISP_AdvancedComponents.Tabs = class {
  constructor(config) {
    this.container = config.container;
    this.tabs = config.tabs || [];
    this.activeTab = config.activeTab || 0;
    this.onChange = config.onChange;
    this.variant = config.variant || 'default'; // default, pills, underline

    this.render();
  }

  render() {
    if (typeof this.container === 'string') {
      this.container = document.querySelector(this.container);
    }

    const html = `
      <div class="tabs tabs-${this.variant}">
        <div class="tabs-nav" role="tablist">
          ${this.tabs.map((tab, index) => this.renderTab(tab, index)).join('')}
        </div>
        <div class="tabs-content">
          ${this.tabs.map((tab, index) => this.renderPanel(tab, index)).join('')}
        </div>
      </div>
    `;

    this.container.innerHTML = html;
    this.attachEvents();
  }

  renderTab(tab, index) {
    const isActive = index === this.activeTab;
    const disabled = tab.disabled ? 'disabled' : '';
    const icon = tab.icon ? `<span class="tab-icon" aria-hidden="true">${tab.icon}</span>` : '';
    const badge = tab.badge ? `<span class="tab-badge">${tab.badge}</span>` : '';

    return `
      <button
        class="tab ${isActive ? 'active' : ''}"
        role="tab"
        id="tab-${index}"
        aria-controls="panel-${index}"
        aria-selected="${isActive}"
        ${disabled}
        data-tab-index="${index}">
        ${icon}
        <span class="tab-label">${tab.label}</span>
        ${badge}
      </button>
    `;
  }

  renderPanel(tab, index) {
    const isActive = index === this.activeTab;

    return `
      <div
        class="tab-panel ${isActive ? 'active' : ''}"
        role="tabpanel"
        id="panel-${index}"
        aria-labelledby="tab-${index}"
        ${!isActive ? 'hidden' : ''}>
        ${typeof tab.content === 'function' ? tab.content() : tab.content}
      </div>
    `;
  }

  attachEvents() {
    const tabs = this.container.querySelectorAll('.tab');

    tabs.forEach((tab, index) => {
      tab.addEventListener('click', () => {
        if (!tab.disabled) {
          this.setActiveTab(index);
        }
      });

      // Keyboard navigation
      tab.addEventListener('keydown', (e) => {
        let newIndex = this.activeTab;

        if (e.key === 'ArrowRight') {
          newIndex = Math.min(this.tabs.length - 1, this.activeTab + 1);
        } else if (e.key === 'ArrowLeft') {
          newIndex = Math.max(0, this.activeTab - 1);
        } else if (e.key === 'Home') {
          newIndex = 0;
        } else if (e.key === 'End') {
          newIndex = this.tabs.length - 1;
        } else {
          return;
        }

        e.preventDefault();
        this.setActiveTab(newIndex);
        this.container.querySelector(`.tab[data-tab-index="${newIndex}"]`).focus();
      });
    });
  }

  setActiveTab(index) {
    if (index === this.activeTab || this.tabs[index].disabled) {
      return;
    }

    // Update state
    const oldIndex = this.activeTab;
    this.activeTab = index;

    // Update UI
    const tabs = this.container.querySelectorAll('.tab');
    const panels = this.container.querySelectorAll('.tab-panel');

    tabs.forEach((tab, i) => {
      if (i === index) {
        tab.classList.add('active');
        tab.setAttribute('aria-selected', 'true');
      } else {
        tab.classList.remove('active');
        tab.setAttribute('aria-selected', 'false');
      }
    });

    panels.forEach((panel, i) => {
      if (i === index) {
        panel.classList.add('active');
        panel.removeAttribute('hidden');
      } else {
        panel.classList.remove('active');
        panel.setAttribute('hidden', '');
      }
    });

    // Callback
    if (this.onChange) {
      this.onChange(index, this.tabs[index], oldIndex);
    }
  }

  getActiveTab() {
    return this.activeTab;
  }

  disableTab(index) {
    this.tabs[index].disabled = true;
    const tab = this.container.querySelector(`.tab[data-tab-index="${index}"]`);
    if (tab) {
      tab.disabled = true;
    }
  }

  enableTab(index) {
    this.tabs[index].disabled = false;
    const tab = this.container.querySelector(`.tab[data-tab-index="${index}"]`);
    if (tab) {
      tab.disabled = false;
    }
  }
};

/**
 * Accordion Component - Collapsible content sections
 */
ISP_AdvancedComponents.Accordion = class {
  constructor(config) {
    this.container = config.container;
    this.items = config.items || [];
    this.allowMultiple = config.allowMultiple !== false;
    this.defaultOpen = config.defaultOpen || [];
    this.onChange = config.onChange;

    this.openItems = new Set(this.defaultOpen);

    this.render();
  }

  render() {
    if (typeof this.container === 'string') {
      this.container = document.querySelector(this.container);
    }

    const html = `
      <div class="accordion">
        ${this.items.map((item, index) => this.renderItem(item, index)).join('')}
      </div>
    `;

    this.container.innerHTML = html;
    this.attachEvents();
  }

  renderItem(item, index) {
    const isOpen = this.openItems.has(index);
    const icon = isOpen ? '▼' : '▶';

    return `
      <div class="accordion-item ${isOpen ? 'open' : ''}">
        <button
          class="accordion-header"
          id="accordion-header-${index}"
          aria-expanded="${isOpen}"
          aria-controls="accordion-panel-${index}"
          data-accordion-index="${index}">
          <span class="accordion-icon" aria-hidden="true">${icon}</span>
          <span class="accordion-title">${item.title}</span>
          ${item.badge ? `<span class="accordion-badge">${item.badge}</span>` : ''}
        </button>
        <div
          class="accordion-panel ${isOpen ? 'open' : ''}"
          id="accordion-panel-${index}"
          role="region"
          aria-labelledby="accordion-header-${index}"
          ${!isOpen ? 'hidden' : ''}>
          <div class="accordion-content">
            ${typeof item.content === 'function' ? item.content() : item.content}
          </div>
        </div>
      </div>
    `;
  }

  attachEvents() {
    const headers = this.container.querySelectorAll('.accordion-header');

    headers.forEach((header) => {
      header.addEventListener('click', () => {
        const index = parseInt(header.dataset.accordionIndex);
        this.toggle(index);
      });

      header.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          const index = parseInt(header.dataset.accordionIndex);
          this.toggle(index);
        }
      });
    });
  }

  toggle(index) {
    const isOpen = this.openItems.has(index);

    if (isOpen) {
      this.close(index);
    } else {
      if (!this.allowMultiple) {
        // Close all others
        this.openItems.forEach(i => {
          if (i !== index) {
            this.close(i);
          }
        });
      }
      this.open(index);
    }

    if (this.onChange) {
      this.onChange(index, !isOpen);
    }
  }

  open(index) {
    this.openItems.add(index);

    const item = this.container.querySelector(`[data-accordion-index="${index}"]`).parentElement;
    const header = item.querySelector('.accordion-header');
    const panel = item.querySelector('.accordion-panel');
    const icon = header.querySelector('.accordion-icon');

    item.classList.add('open');
    header.setAttribute('aria-expanded', 'true');
    panel.classList.add('open');
    panel.removeAttribute('hidden');
    icon.textContent = '▼';
  }

  close(index) {
    this.openItems.delete(index);

    const item = this.container.querySelector(`[data-accordion-index="${index}"]`).parentElement;
    const header = item.querySelector('.accordion-header');
    const panel = item.querySelector('.accordion-panel');
    const icon = header.querySelector('.accordion-icon');

    item.classList.remove('open');
    header.setAttribute('aria-expanded', 'false');
    panel.classList.remove('open');
    panel.setAttribute('hidden', '');
    icon.textContent = '▶';
  }

  openAll() {
    this.items.forEach((_, index) => this.open(index));
  }

  closeAll() {
    this.items.forEach((_, index) => this.close(index));
  }
};

/**
 * Toast Component - Advanced notification system
 */
ISP_AdvancedComponents.Toast = class {
  static container = null;
  static queue = [];
  static maxVisible = 5;

  static init() {
    if (!this.container) {
      this.container = document.createElement('div');
      this.container.className = 'toast-container';
      this.container.setAttribute('aria-live', 'polite');
      this.container.setAttribute('aria-atomic', 'true');
      document.body.appendChild(this.container);
    }
  }

  static show(message, options = {}) {
    this.init();

    const toast = {
      id: Date.now() + Math.random(),
      message: message,
      type: options.type || 'info',
      duration: options.duration !== undefined ? options.duration : 5000,
      closable: options.closable !== false,
      action: options.action,
      icon: options.icon,
      position: options.position || 'top-right'
    };

    this.queue.push(toast);
    this.render();

    if (toast.duration > 0) {
      setTimeout(() => {
        this.hide(toast.id);
      }, toast.duration);
    }

    return toast.id;
  }

  static hide(id) {
    this.queue = this.queue.filter(t => t.id !== id);
    this.render();
  }

  static success(message, options = {}) {
    return this.show(message, { ...options, type: 'success' });
  }

  static error(message, options = {}) {
    return this.show(message, { ...options, type: 'danger' });
  }

  static warning(message, options = {}) {
    return this.show(message, { ...options, type: 'warning' });
  }

  static info(message, options = {}) {
    return this.show(message, { ...options, type: 'info' });
  }

  static render() {
    const visible = this.queue.slice(-this.maxVisible);

    this.container.innerHTML = visible.map(toast => {
      const icon = this.getIcon(toast.type, toast.icon);
      const actionBtn = toast.action ? `
        <button class="toast-action" data-toast-action="${toast.id}">
          ${toast.action.label}
        </button>
      ` : '';

      return `
        <div class="toast toast-${toast.type}" data-toast-id="${toast.id}" role="alert">
          <div class="toast-content">
            ${icon ? `<span class="toast-icon" aria-hidden="true">${icon}</span>` : ''}
            <span class="toast-message">${toast.message}</span>
          </div>
          <div class="toast-actions">
            ${actionBtn}
            ${toast.closable ? `<button class="toast-close" data-toast-close="${toast.id}" aria-label="Fechar">✕</button>` : ''}
          </div>
        </div>
      `;
    }).join('');

    // Attach events
    this.container.querySelectorAll('[data-toast-close]').forEach(btn => {
      btn.addEventListener('click', () => {
        this.hide(parseFloat(btn.dataset.toastClose));
      });
    });

    this.container.querySelectorAll('[data-toast-action]').forEach(btn => {
      btn.addEventListener('click', () => {
        const id = parseFloat(btn.dataset.toastAction);
        const toast = this.queue.find(t => t.id === id);
        if (toast && toast.action && toast.action.onClick) {
          toast.action.onClick();
        }
        this.hide(id);
      });
    });
  }

  static getIcon(type, customIcon) {
    if (customIcon) return customIcon;

    const icons = {
      success: '✓',
      danger: '✗',
      warning: '⚠',
      info: 'ℹ'
    };

    return icons[type] || '';
  }

  static clear() {
    this.queue = [];
    this.render();
  }
};

/**
 * FileUpload Component - Advanced file upload with preview
 */
ISP_AdvancedComponents.FileUpload = class {
  constructor(config) {
    this.container = config.container;
    this.multiple = config.multiple !== false;
    this.accept = config.accept || '*/*';
    this.maxSize = config.maxSize || 10 * 1024 * 1024; // 10MB
    this.maxFiles = config.maxFiles || 10;
    this.onUpload = config.onUpload;
    this.onRemove = config.onRemove;
    this.showPreview = config.showPreview !== false;

    this.files = [];

    this.render();
  }

  render() {
    if (typeof this.container === 'string') {
      this.container = document.querySelector(this.container);
    }

    const html = `
      <div class="file-upload">
        <div class="file-upload-dropzone">
          <input
            type="file"
            id="file-input"
            class="file-upload-input"
            ${this.multiple ? 'multiple' : ''}
            accept="${this.accept}"
            aria-label="Selecionar arquivos" />
          <label for="file-input" class="file-upload-label">
            <svg class="file-upload-icon" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="17 8 12 3 7 8"></polyline>
              <line x1="12" y1="3" x2="12" y2="15"></line>
            </svg>
            <span class="file-upload-text">
              Arraste arquivos aqui ou <strong>clique para selecionar</strong>
            </span>
            <span class="file-upload-hint">
              Tamanho máximo: ${this.formatSize(this.maxSize)}
              ${this.maxFiles > 1 ? `· Máximo ${this.maxFiles} arquivos` : ''}
            </span>
          </label>
        </div>
        <div class="file-upload-list"></div>
      </div>
    `;

    this.container.innerHTML = html;
    this.attachEvents();
  }

  attachEvents() {
    const input = this.container.querySelector('.file-upload-input');
    const dropzone = this.container.querySelector('.file-upload-dropzone');

    // File selection
    input.addEventListener('change', (e) => {
      this.handleFiles(Array.from(e.target.files));
      input.value = ''; // Reset
    });

    // Drag and drop
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
      });
    });

    ['dragenter', 'dragover'].forEach(eventName => {
      dropzone.addEventListener(eventName, () => {
        dropzone.classList.add('dragging');
      });
    });

    ['dragleave', 'drop'].forEach(eventName => {
      dropzone.addEventListener(eventName, () => {
        dropzone.classList.remove('dragging');
      });
    });

    dropzone.addEventListener('drop', (e) => {
      const files = Array.from(e.dataTransfer.files);
      this.handleFiles(files);
    });
  }

  handleFiles(newFiles) {
    // Validate count
    if (this.files.length + newFiles.length > this.maxFiles) {
      ISP_AdvancedComponents.Toast.error(`Máximo de ${this.maxFiles} arquivos permitido`);
      return;
    }

    // Validate each file
    const validFiles = [];
    for (const file of newFiles) {
      if (file.size > this.maxSize) {
        ISP_AdvancedComponents.Toast.error(`Arquivo ${file.name} muito grande (máx: ${this.formatSize(this.maxSize)})`);
        continue;
      }
      validFiles.push(file);
    }

    if (validFiles.length === 0) return;

    // Add files
    validFiles.forEach(file => {
      const fileObj = {
        id: Date.now() + Math.random(),
        file: file,
        name: file.name,
        size: file.size,
        type: file.type,
        progress: 0,
        status: 'pending' // pending, uploading, success, error
      };

      this.files.push(fileObj);
      this.renderFile(fileObj);

      // Auto-upload
      if (this.onUpload) {
        this.uploadFile(fileObj);
      }
    });
  }

  renderFile(fileObj) {
    const list = this.container.querySelector('.file-upload-list');

    const preview = this.showPreview && fileObj.type.startsWith('image/')
      ? `<img src="${URL.createObjectURL(fileObj.file)}" alt="" class="file-preview-image" />`
      : `<div class="file-preview-icon">${this.getFileIcon(fileObj.type)}</div>`;

    const html = `
      <div class="file-item" data-file-id="${fileObj.id}">
        <div class="file-preview">
          ${preview}
        </div>
        <div class="file-info">
          <div class="file-name">${fileObj.name}</div>
          <div class="file-meta">
            <span class="file-size">${this.formatSize(fileObj.size)}</span>
            <span class="file-status" data-status="${fileObj.status}">
              ${this.getStatusText(fileObj.status)}
            </span>
          </div>
          <div class="file-progress">
            <div class="file-progress-bar" style="width: ${fileObj.progress}%"></div>
          </div>
        </div>
        <button class="file-remove" data-file-remove="${fileObj.id}" aria-label="Remover arquivo">✕</button>
      </div>
    `;

    const div = document.createElement('div');
    div.innerHTML = html;
    const fileItem = div.firstElementChild;

    fileItem.querySelector('[data-file-remove]').addEventListener('click', () => {
      this.removeFile(fileObj.id);
    });

    list.appendChild(fileItem);
  }

  async uploadFile(fileObj) {
    fileObj.status = 'uploading';
    this.updateFileStatus(fileObj);

    try {
      // Simulate progress
      const progressInterval = setInterval(() => {
        if (fileObj.progress < 90) {
          fileObj.progress += 10;
          this.updateFileProgress(fileObj);
        }
      }, 200);

      // Call upload callback
      await this.onUpload(fileObj.file, (progress) => {
        fileObj.progress = progress;
        this.updateFileProgress(fileObj);
      });

      clearInterval(progressInterval);

      fileObj.progress = 100;
      fileObj.status = 'success';
      this.updateFileProgress(fileObj);
      this.updateFileStatus(fileObj);

      ISP_AdvancedComponents.Toast.success(`${fileObj.name} enviado com sucesso`);
    } catch (error) {
      fileObj.status = 'error';
      this.updateFileStatus(fileObj);
      ISP_AdvancedComponents.Toast.error(`Erro ao enviar ${fileObj.name}: ${error.message}`);
    }
  }

  updateFileProgress(fileObj) {
    const item = this.container.querySelector(`[data-file-id="${fileObj.id}"]`);
    if (item) {
      const bar = item.querySelector('.file-progress-bar');
      bar.style.width = `${fileObj.progress}%`;
    }
  }

  updateFileStatus(fileObj) {
    const item = this.container.querySelector(`[data-file-id="${fileObj.id}"]`);
    if (item) {
      const status = item.querySelector('.file-status');
      status.dataset.status = fileObj.status;
      status.textContent = this.getStatusText(fileObj.status);
    }
  }

  removeFile(id) {
    const fileObj = this.files.find(f => f.id === id);
    if (fileObj && this.onRemove) {
      this.onRemove(fileObj);
    }

    this.files = this.files.filter(f => f.id !== id);

    const item = this.container.querySelector(`[data-file-id="${id}"]`);
    if (item) {
      item.remove();
    }
  }

  getFiles() {
    return this.files;
  }

  clear() {
    this.files = [];
    const list = this.container.querySelector('.file-upload-list');
    list.innerHTML = '';
  }

  formatSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  }

  getFileIcon(type) {
    if (type.startsWith('image/')) return '🖼️';
    if (type.startsWith('video/')) return '🎥';
    if (type.startsWith('audio/')) return '🎵';
    if (type.includes('pdf')) return '📄';
    if (type.includes('word')) return '📝';
    if (type.includes('excel') || type.includes('spreadsheet')) return '📊';
    if (type.includes('zip') || type.includes('rar')) return '📦';
    return '📄';
  }

  getStatusText(status) {
    const texts = {
      pending: 'Aguardando',
      uploading: 'Enviando...',
      success: 'Concluído',
      error: 'Erro'
    };
    return texts[status] || status;
  }
};

// Export to global namespace
window.ISP_AdvancedComponents = ISP_AdvancedComponents;

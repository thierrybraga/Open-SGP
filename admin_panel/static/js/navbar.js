/**
 * navbar.js - Funcionalidades da barra de navegação
 * Controle de menu mobile, dropdowns e interações
 */

(function() {
  'use strict';

  const Navbar = {
    init: function() {
      this.setupMobileToggle();
      this.setupDropdowns();
      this.setupScrollBehavior();
      this.setupNotifications();
      
      // Initial badge check
      if (window.apiToken) {
        this.checkUnreadCount();
        // Poll every minute
        setInterval(() => this.checkUnreadCount(), 60000);
      }
    },

    /**
     * Toggle do menu mobile
     */
    setupMobileToggle: function() {
      const toggle = document.querySelector('.navbar-toggle');
      const menu = document.querySelector('.navbar-menu');

      if (!toggle || !menu) return;

      toggle.addEventListener('click', function(e) {
        e.stopPropagation();
        this.classList.toggle('active');
        menu.classList.toggle('active');
        document.body.style.overflow = menu.classList.contains('active') ? 'hidden' : '';
      });

      // Fechar menu ao clicar fora
      document.addEventListener('click', function(e) {
        if (menu.classList.contains('active') &&
            !e.target.closest('.navbar-menu') &&
            !e.target.closest('.navbar-toggle')) {
          toggle.classList.remove('active');
          menu.classList.remove('active');
          document.body.style.overflow = '';
        }
      });

      // Fechar menu ao redimensionar para desktop
      window.addEventListener('resize', function() {
        if (window.innerWidth > 768 && menu.classList.contains('active')) {
          toggle.classList.remove('active');
          menu.classList.remove('active');
          document.body.style.overflow = '';
        }
      });
    },

    /**
     * Dropdowns
     */
    setupDropdowns: function() {
      const dropdowns = document.querySelectorAll('.navbar-dropdown');

      dropdowns.forEach(dropdown => {
        const toggle = dropdown.querySelector('.navbar-menu-link');
        const menu = dropdown.querySelector('.navbar-dropdown-menu');

        if (!toggle || !menu) return;

        // Mobile: toggle ao clicar
        if (window.innerWidth <= 768) {
          toggle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            dropdown.classList.toggle('active');
          });
        } else {
          // Desktop: hover já funciona via CSS
          // Adicionar seta para indicar dropdown
          if (!toggle.querySelector('.dropdown-arrow')) {
            const arrow = document.createElement('span');
            arrow.className = 'dropdown-arrow';
            arrow.innerHTML = '▾';
            arrow.style.marginLeft = '4px';
            toggle.appendChild(arrow);
          }
        }
      });

      // Atualizar comportamento ao redimensionar
      // Use lodash debounce if available, or simple timeout
      let timeout;
      window.addEventListener('resize', function() {
        clearTimeout(timeout);
        timeout = setTimeout(function() {
          Navbar.setupDropdowns();
        }, 250);
      });
    },

    /**
     * Comportamento ao rolar a página
     */
    setupScrollBehavior: function() {
      const navbar = document.querySelector('.navbar');
      if (!navbar) return;

      let lastScroll = 0;
      const scrollThreshold = 10;

      window.addEventListener('scroll', function() {
        const currentScroll = window.pageYOffset;

        // Adicionar sombra ao rolar
        if (currentScroll > scrollThreshold) {
          navbar.style.boxShadow = 'var(--shadow-md)';
        } else {
          navbar.style.boxShadow = 'var(--shadow-sm)';
        }

        lastScroll = currentScroll;
      });
    },

    /**
     * Sistema de notificações
     */
    setupNotifications: function() {
      const notificationButton = document.querySelector('[data-notifications]');
      if (!notificationButton) return;

      notificationButton.addEventListener('click', function(e) {
        e.preventDefault();
        Navbar.toggleNotificationsPanel();
      });
    },

    checkUnreadCount: function() {
      if (!window.apiToken) return;

      const baseUrl = window.apiBaseUrl || '';
      fetch(`${baseUrl}/api/notifications/unread-count`, {
        headers: {
          'Authorization': 'Bearer ' + window.apiToken
        }
      })
      .then(response => {
        if (response.ok) return response.json();
        throw new Error('Failed to fetch count');
      })
      .then(data => {
        const badge = document.querySelector('.notification-badge');
        if (badge) {
          if (data.count > 0) {
            badge.textContent = data.count > 99 ? '99+' : data.count;
            badge.style.display = 'flex';
          } else {
            badge.style.display = 'none';
          }
        }
      })
      .catch(err => console.error('Notification count error:', err));
    },

    toggleNotificationsPanel: function() {
      let panel = document.getElementById('notifications-panel');

      if (!panel) {
        panel = this.createNotificationsPanel();
        document.body.appendChild(panel);
      }

      panel.classList.toggle('active');

      if (panel.classList.contains('active')) {
        this.loadNotifications(); // Load when opening
        
        // Fechar ao clicar fora
        setTimeout(() => {
          document.addEventListener('click', function closePanel(e) {
            if (!e.target.closest('#notifications-panel') &&
                !e.target.closest('[data-notifications]')) {
              panel.classList.remove('active');
              document.removeEventListener('click', closePanel);
            }
          });
        }, 100);
      }
    },

    createNotificationsPanel: function() {
      const panel = document.createElement('div');
      panel.id = 'notifications-panel';
      panel.className = 'notifications-panel';
      panel.style.cssText = `
        position: fixed;
        top: 64px;
        right: 20px;
        width: 360px;
        max-height: 480px;
        background: var(--bg-primary);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-lg);
        overflow: hidden;
        transform: translateY(-10px);
        opacity: 0;
        visibility: hidden;
        transition: all var(--transition-base);
        z-index: 1500;
      `;

      panel.innerHTML = `
        <div style="padding: var(--spacing-lg); border-bottom: 1px solid var(--border-color);">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <h3 style="margin: 0; font-size: var(--font-size-lg);">Notificações</h3>
            <button class="btn btn-sm btn-secondary" onclick="Navbar.markAllAsRead()">
              Marcar todas como lidas
            </button>
          </div>
        </div>
        <div id="notifications-list" style="max-height: 360px; overflow-y: auto;">
          <div style="padding: var(--spacing-lg); text-align: center; color: var(--text-muted);">
            Carregando...
          </div>
        </div>
        <div style="padding: var(--spacing-md); border-top: 1px solid var(--border-color); text-align: center;">
          <a href="/notifications" style="font-size: var(--font-size-sm); color: var(--primary-color);">
            Ver todas as notificações
          </a>
        </div>
      `;

      // Adicionar classe active ao panel
      const style = document.createElement('style');
      style.textContent = `
        .notifications-panel.active {
          transform: translateY(0);
          opacity: 1;
          visibility: visible;
        }
        @media (max-width: 768px) {
          .notifications-panel {
            right: 10px;
            left: 10px;
            width: auto;
            top: 56px;
          }
        }
      `;
      document.head.appendChild(style);

      return panel;
    },

    loadNotifications: function() {
      if (!window.apiToken) {
        this.renderError('Faça login para ver as notificações');
        return;
      }

      const list = document.getElementById('notifications-list');
      if (!list) return;
      
      list.innerHTML = `
          <div style="padding: var(--spacing-lg); text-align: center; color: var(--text-muted);">
            Carregando...
          </div>
      `;

      const baseUrl = window.apiBaseUrl || '';
      fetch(`${baseUrl}/api/notifications/?limit=10`, {
        headers: {
          'Authorization': 'Bearer ' + window.apiToken
        }
      })
      .then(response => {
        if (response.ok) return response.json();
        throw new Error('Failed to fetch notifications');
      })
      .then(data => {
        this.renderNotificationsList(data);
        // Also update count
        this.checkUnreadCount();
      })
      .catch(err => {
        console.error(err);
        this.renderError('Erro ao carregar notificações');
      });
    },

    renderError: function(msg) {
      const list = document.getElementById('notifications-list');
      if (list) {
        list.innerHTML = `
          <div style="padding: var(--spacing-2xl); text-align: center; color: var(--text-danger);">
            <p>${msg}</p>
          </div>
        `;
      }
    },

    renderNotificationsList: function(notifications) {
      const list = document.getElementById('notifications-list');
      if (!list) return;

      if (!notifications || notifications.length === 0) {
        list.innerHTML = `
          <div style="padding: var(--spacing-2xl); text-align: center; color: var(--text-muted);">
            <p>Nenhuma notificação</p>
          </div>
        `;
        return;
      }

      list.innerHTML = notifications.map(notif => {
        // Format relative time (simplistic)
        const date = new Date(notif.created_at);
        const now = new Date();
        const diff = Math.floor((now - date) / 1000); // seconds
        let timeStr = '';
        if (diff < 60) timeStr = 'agora';
        else if (diff < 3600) timeStr = Math.floor(diff/60) + ' min atrás';
        else if (diff < 86400) timeStr = Math.floor(diff/3600) + ' h atrás';
        else timeStr = Math.floor(diff/86400) + ' dias atrás';

        return `
        <div class="notification-item ${notif.read ? 'read' : 'unread'}"
             onclick="Navbar.markAsRead(${notif.id}, '${notif.link || ''}')"
             style="padding: var(--spacing-md); border-bottom: 1px solid var(--border-color);
                    cursor: pointer; transition: background-color var(--transition-fast);
                    ${notif.read ? '' : 'background-color: var(--bg-secondary);'}">
          <div style="display: flex; gap: var(--spacing-md);">
            <div style="width: 40px; height: 40px; border-radius: 50%;
                        background: var(--${notif.type === 'success' ? 'success' : notif.type === 'warning' ? 'warning' : notif.type === 'error' ? 'danger' : 'info'}-color);
                        opacity: 0.2; flex-shrink: 0;"></div>
            <div style="flex: 1;">
              <div style="font-weight: 600; margin-bottom: var(--spacing-xs); color: var(--text-primary);">
                ${notif.title}
              </div>
              <div style="font-size: var(--font-size-sm); color: var(--text-secondary); margin-bottom: var(--spacing-xs);">
                ${notif.message}
              </div>
              <div style="font-size: var(--font-size-xs); color: var(--text-muted);">
                ${timeStr}
              </div>
            </div>
            ${!notif.read ? '<div style="width: 8px; height: 8px; border-radius: 50%; background: var(--primary-color); flex-shrink: 0;"></div>' : ''}
          </div>
        </div>
      `}).join('');
    },

    markAsRead: function(id, link) {
      if (window.apiToken) {
        const baseUrl = window.apiBaseUrl || '';
        fetch(`${baseUrl}/api/notifications/${id}/read`, {
          method: 'POST',
          headers: {
            'Authorization': 'Bearer ' + window.apiToken
          }
        }).then(() => {
          // Update UI
          this.loadNotifications();
        });
      }
      
      if (link && link !== 'null' && link !== '') {
        window.location.href = link;
      }
    },

    markAllAsRead: function() {
       if (!window.apiToken) return;

       const baseUrl = window.apiBaseUrl || '';
       fetch(`${baseUrl}/api/notifications/read-all`, {
         method: 'POST',
         headers: {
           'Authorization': 'Bearer ' + window.apiToken
         }
       })
       .then(response => {
         if (response.ok) {
           this.loadNotifications();
         } else {
           console.error('Failed to mark all as read');
         }
       })
       .catch(err => console.error('Error marking all as read:', err));
    }
  };

  // Expose Navbar globally
  window.Navbar = Navbar;

  // Initialize when DOM is ready
  document.addEventListener('DOMContentLoaded', function() {
    Navbar.init();
  });

})();

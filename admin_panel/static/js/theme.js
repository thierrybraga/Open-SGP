/**
 * theme.js - Dark Mode Toggle Implementation
 * ISP ERP Admin Panel
 */

const ThemeManager = {
  STORAGE_KEY: 'isp-erp-theme',
  THEME_ATTR: 'data-theme',

  /**
   * Initialize theme system
   */
  init() {
    this.loadTheme();
    this.attachToggleListener();
    this.watchSystemPreference();
  },

  /**
   * Get current theme
   * @returns {string} 'light' or 'dark'
   */
  getTheme() {
    // Check localStorage first
    const stored = localStorage.getItem(this.STORAGE_KEY);
    if (stored) {
      return stored;
    }

    // Check system preference
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return 'dark';
    }

    return 'light';
  },

  /**
   * Set theme
   * @param {string} theme - 'light' or 'dark'
   */
  setTheme(theme) {
    // Validate theme
    if (!['light', 'dark'].includes(theme)) {
      console.error(`Invalid theme: ${theme}`);
      return;
    }

    // Apply theme
    if (theme === 'dark') {
      document.documentElement.setAttribute(this.THEME_ATTR, 'dark');
    } else {
      document.documentElement.removeAttribute(this.THEME_ATTR);
    }

    // Save to localStorage
    localStorage.setItem(this.STORAGE_KEY, theme);

    // Dispatch event for other components
    window.dispatchEvent(new CustomEvent('themechange', {
      detail: { theme }
    }));

    // Update toggle button state
    this.updateToggleButton();
  },

  /**
   * Toggle between light and dark themes
   */
  toggleTheme() {
    const current = this.getTheme();
    const newTheme = current === 'dark' ? 'light' : 'dark';
    this.setTheme(newTheme);
  },

  /**
   * Load theme on page load
   */
  loadTheme() {
    const theme = this.getTheme();
    this.setTheme(theme);
  },

  /**
   * Attach click listener to toggle button
   */
  attachToggleListener() {
    // Find all theme toggle buttons
    const toggleButtons = document.querySelectorAll('.theme-toggle');

    toggleButtons.forEach(button => {
      button.addEventListener('click', () => {
        this.toggleTheme();
      });

      // Keyboard support
      button.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          this.toggleTheme();
        }
      });
    });
  },

  /**
   * Update toggle button ARIA label and icon
   */
  updateToggleButton() {
    const theme = this.getTheme();
    const toggleButtons = document.querySelectorAll('.theme-toggle');

    toggleButtons.forEach(button => {
      const label = theme === 'dark' ? 'Ativar modo claro' : 'Ativar modo escuro';
      button.setAttribute('aria-label', label);
      button.setAttribute('title', label);
    });
  },

  /**
   * Watch for system preference changes
   */
  watchSystemPreference() {
    if (!window.matchMedia) return;

    const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)');

    // Modern browsers
    if (darkModeQuery.addEventListener) {
      darkModeQuery.addEventListener('change', (e) => {
        // Only auto-switch if user hasn't manually set a preference
        if (!localStorage.getItem(this.STORAGE_KEY)) {
          this.setTheme(e.matches ? 'dark' : 'light');
        }
      });
    }
    // Legacy browsers
    else if (darkModeQuery.addListener) {
      darkModeQuery.addListener((e) => {
        if (!localStorage.getItem(this.STORAGE_KEY)) {
          this.setTheme(e.matches ? 'dark' : 'light');
        }
      });
    }
  },

  /**
   * Clear user preference (will use system preference)
   */
  clearPreference() {
    localStorage.removeItem(this.STORAGE_KEY);
    this.loadTheme();
  }
};

// Initialize on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    ThemeManager.init();
  });
} else {
  ThemeManager.init();
}

// Export to global namespace
window.ThemeManager = ThemeManager;

// Theme change event listener example
// window.addEventListener('themechange', (e) => {
//   console.log('Theme changed to:', e.detail.theme);
// });

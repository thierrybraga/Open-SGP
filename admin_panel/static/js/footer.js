/**
 * footer.js - Funcionalidades do rodapé
 * Newsletter, voltar ao topo, etc.
 */

(function() {
  'use strict';

  const Footer = {
    init: function() {
      this.setupNewsletter();
      this.setupBackToTop();
      this.updateYear();
    },

    /**
     * Newsletter
     */
    setupNewsletter: function() {
      const form = document.querySelector('.footer-newsletter-form');
      if (!form) return;

      form.addEventListener('submit', function(e) {
        e.preventDefault();
        const emailInput = this.querySelector('.footer-newsletter-input');
        const email = emailInput.value.trim();

        if (Footer.validateEmail(email)) {
          Footer.subscribeNewsletter(email);
          emailInput.value = '';
        } else {
          ISP_ERP.showToast('Por favor, insira um e-mail válido', 'warning');
        }
      });
    },

    validateEmail: function(email) {
      const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      return re.test(email);
    },

    subscribeNewsletter: async function(email) {
      try {
        // Simular chamada à API
        // const response = await ISP_ERP.ajax('/api/newsletter/subscribe', {
        //   method: 'POST',
        //   body: JSON.stringify({ email })
        // });

        // Simulação
        await new Promise(resolve => setTimeout(resolve, 500));

        ISP_ERP.showToast('Inscrição realizada com sucesso!', 'success');
      } catch (error) {
        ISP_ERP.showToast('Erro ao realizar inscrição. Tente novamente.', 'danger');
      }
    },

    /**
     * Botão "Voltar ao topo"
     */
    setupBackToTop: function() {
      // Criar botão se não existir
      let backToTopBtn = document.getElementById('back-to-top');

      if (!backToTopBtn) {
        backToTopBtn = document.createElement('button');
        backToTopBtn.id = 'back-to-top';
        backToTopBtn.className = 'back-to-top';
        backToTopBtn.innerHTML = '↑';
        backToTopBtn.setAttribute('aria-label', 'Voltar ao topo');
        backToTopBtn.style.cssText = `
          position: fixed;
          bottom: 30px;
          right: 30px;
          width: 48px;
          height: 48px;
          border-radius: 50%;
          background-color: var(--primary-color);
          color: white;
          border: none;
          font-size: 24px;
          cursor: pointer;
          box-shadow: var(--shadow-lg);
          opacity: 0;
          visibility: hidden;
          transform: translateY(20px);
          transition: all var(--transition-base);
          z-index: 1000;
        `;

        document.body.appendChild(backToTopBtn);
      }

      // Mostrar/ocultar baseado no scroll
      window.addEventListener('scroll', function() {
        if (window.pageYOffset > 300) {
          backToTopBtn.style.opacity = '1';
          backToTopBtn.style.visibility = 'visible';
          backToTopBtn.style.transform = 'translateY(0)';
        } else {
          backToTopBtn.style.opacity = '0';
          backToTopBtn.style.visibility = 'hidden';
          backToTopBtn.style.transform = 'translateY(20px)';
        }
      });

      // Ação de voltar ao topo
      backToTopBtn.addEventListener('click', function() {
        window.scrollTo({
          top: 0,
          behavior: 'smooth'
        });
      });

      // Hover effect
      backToTopBtn.addEventListener('mouseenter', function() {
        this.style.backgroundColor = 'var(--primary-hover)';
      });

      backToTopBtn.addEventListener('mouseleave', function() {
        this.style.backgroundColor = 'var(--primary-color)';
      });
    },

    /**
     * Atualizar ano automaticamente
     */
    updateYear: function() {
      const yearElements = document.querySelectorAll('[data-year]');
      const currentYear = new Date().getFullYear();

      yearElements.forEach(element => {
        element.textContent = currentYear;
      });
    },

    /**
     * Links do footer com analytics
     */
    setupAnalytics: function() {
      const footerLinks = document.querySelectorAll('.footer-link, .footer-bottom-link');

      footerLinks.forEach(link => {
        link.addEventListener('click', function(e) {
          const linkText = this.textContent.trim();
          const linkHref = this.getAttribute('href');

          // Aqui você pode enviar dados para seu sistema de analytics
          console.log('Footer link clicked:', { text: linkText, href: linkHref });

          // Exemplo com Google Analytics
          // if (typeof gtag !== 'undefined') {
          //   gtag('event', 'footer_link_click', {
          //     'link_text': linkText,
          //     'link_url': linkHref
          //   });
          // }
        });
      });
    },

    /**
     * Lazy loading de redes sociais (para performance)
     */
    setupSocialLinks: function() {
      const socialLinks = document.querySelectorAll('.footer-social-link');

      socialLinks.forEach(link => {
        link.addEventListener('mouseenter', function() {
          // Pré-carregar o destino do link
          const href = this.getAttribute('href');
          if (href && !this.dataset.preloaded) {
            const linkElement = document.createElement('link');
            linkElement.rel = 'prefetch';
            linkElement.href = href;
            document.head.appendChild(linkElement);
            this.dataset.preloaded = 'true';
          }
        });
      });
    }
  };

  // Inicializar quando o DOM estiver pronto
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
      Footer.init();
    });
  } else {
    Footer.init();
  }

  // Exportar para uso global
  window.Footer = Footer;

})();

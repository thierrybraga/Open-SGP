#!/usr/bin/env python3
"""
Script para gerar páginas modernizadas automaticamente
Uso: python generate_modern_pages.py
"""

TEMPLATE_BASE = '''<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title} - ISP ERP</title>
  <link rel="stylesheet" href="{{{{ url_for('static', filename='css/main.css') }}}}" />
  <link rel="stylesheet" href="{{{{ url_for('static', filename='css/navbar.css') }}}}" />
  <link rel="stylesheet" href="{{{{ url_for('static', filename='css/footer.css') }}}}" />
  <link rel="stylesheet" href="{{{{ url_for('static', filename='css/components.css') }}}}" />
  <link rel="stylesheet" href="{{{{ url_for('static', filename='css/accessibility.css') }}}}" />
  <link rel="stylesheet" href="{{{{ url_for('static', filename='css/dark-mode.css') }}}}" />
  <link rel="stylesheet" href="{{{{ url_for('static', filename='css/advanced-components.css') }}}}" />
</head>
<body>
  <a href="#main-content" class="skip-link">Pular para o conteúdo principal</a>
  {{%% include 'components/navbar.html' %%}}

  <main id="main-content" class="main-content">
    <div class="container">
      <nav aria-label="Breadcrumb" class="breadcrumb">
        <span class="breadcrumb-item"><a href="/">Home</a></span>
        <span class="breadcrumb-separator" aria-hidden="true">/</span>
        {breadcrumbs}
        <span class="breadcrumb-item">{page_name}</span>
      </nav>

      <header class="page-header">
        <div class="page-header-content">
          <h1 class="page-title">{page_name}</h1>
          <p class="page-subtitle">{subtitle}</p>
        </div>
        <div class="page-header-actions">
          <button type="button" class="btn btn-primary" data-modal-target="modal-{entity}">
            <span aria-hidden="true">➕</span>
            Novo {entity_singular}
          </button>
        </div>
      </header>

      {filters}

      <div class="card">
        <div class="card-body">
          <div id="table-container"></div>
        </div>
      </div>
      <div id="pagination-container"></div>
    </div>
  </main>

  <div id="modal-{entity}" class="modal-overlay" style="display: none;">
    <div class="modal">
      <div class="modal-header">
        <h2 class="modal-title" id="modal-title">Novo {entity_singular}</h2>
        <button class="modal-close" aria-label="Fechar modal">✕</button>
      </div>
      <div class="modal-body">
        <form id="form-{entity}" method="post" data-validate>
          <input type="hidden" name="id" id="{entity}-id" />
          {form_fields}
        </form>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" data-modal-close>Cancelar</button>
        <button type="submit" form="form-{entity}" class="btn btn-primary">Salvar</button>
      </div>
    </div>
  </div>

  {{%% include 'components/footer.html' %%}}
  <script src="{{{{ url_for('static', filename='js/main.js') }}}}"></script>
  <script src="{{{{ url_for('static', filename='js/navbar.js') }}}}"></script>
  <script src="{{{{ url_for('static', filename='js/footer.js') }}}}"></script>
  <script src="{{{{ url_for('static', filename='js/components.js') }}}}"></script>
  <script src="{{{{ url_for('static', filename='js/advanced-components.js') }}}}"></script>
  <script src="{{{{ url_for('static', filename='js/theme.js') }}}}"></script>

  <script>
    const sampleData = {{{{ items|tojson|safe if items else '[]' }}}};
    document.addEventListener('DOMContentLoaded', function() {{
      {js_datatable}
      {js_pagination}
      {js_validator}
      {js_handlers}
    }});
  </script>
</body>
</html>
'''

# Definição de páginas para modernizar
PAGES = {
    'network_blocked': {
        'title': 'Rede Bloqueada',
        'subtitle': 'Visualize e gerencie IPs bloqueados na rede',
        'entity': 'blocked',
        'entity_singular': 'Bloqueio',
        'breadcrumbs': '<span class="breadcrumb-item"><a href="/network">Rede</a></span><span class="breadcrumb-separator" aria-hidden="true">/</span>',
        'columns': ['id', 'ip_address', 'mac_address', 'reason', 'blocked_at'],
        'form_fields': ['ip_address', 'mac_address', 'reason'],
        'has_filters': True
    },
    'admin_network_pools': {
        'title': 'Pools IP',
        'subtitle': 'Gerencie os pools de endereços IP',
        'entity': 'pool',
        'entity_singular': 'Pool',
        'breadcrumbs': '<span class="breadcrumb-item"><a href="/admin/network">Rede</a></span><span class="breadcrumb-separator" aria-hidden="true">/</span>',
        'columns': ['id', 'name', 'network', 'gateway', 'vlan_id'],
        'form_fields': ['name', 'network', 'gateway', 'vlan_id'],
        'has_filters': False
    },
    'admin_network_profiles': {
        'title': 'Perfis de Rede',
        'subtitle': 'Gerencie os perfis de velocidade e QoS',
        'entity': 'profile',
        'entity_singular': 'Perfil',
        'breadcrumbs': '<span class="breadcrumb-item"><a href="/admin/network">Rede</a></span><span class="breadcrumb-separator" aria-hidden="true">/</span>',
        'columns': ['id', 'name', 'download_speed', 'upload_speed', 'priority'],
        'form_fields': ['name', 'download_speed', 'upload_speed', 'priority'],
        'has_filters': False
    },
    'admin_network_vlans': {
        'title': 'VLANs',
        'subtitle': 'Gerencie as VLANs da rede',
        'entity': 'vlan',
        'entity_singular': 'VLAN',
        'breadcrumbs': '<span class="breadcrumb-item"><a href="/admin/network">Rede</a></span><span class="breadcrumb-separator" aria-hidden="true">/</span>',
        'columns': ['id', 'vlan_id', 'name', 'description'],
        'form_fields': ['vlan_id', 'name', 'description'],
        'has_filters': False
    },
    'network_tech_history': {
        'title': 'Histórico Técnico',
        'subtitle': 'Visualize o histórico de intervenções técnicas',
        'entity': 'history',
        'entity_singular': 'Registro',
        'breadcrumbs': '<span class="breadcrumb-item"><a href="/network">Rede</a></span><span class="breadcrumb-separator" aria-hidden="true">/</span>',
        'columns': ['id', 'contract_id', 'technician', 'action', 'description', 'created_at'],
        'form_fields': ['contract_id', 'technician', 'action', 'description'],
        'has_filters': True
    },
    'admin_pops': {
        'title': 'POPs',
        'subtitle': 'Gerencie os Pontos de Presença',
        'entity': 'pop',
        'entity_singular': 'POP',
        'breadcrumbs': '<span class="breadcrumb-item"><a href="/admin">Administração</a></span><span class="breadcrumb-separator" aria-hidden="true">/</span>',
        'columns': ['id', 'name', 'address', 'city', 'state'],
        'form_fields': ['name', 'address', 'city', 'state', 'zipcode'],
        'has_filters': False
    },
    'admin_nas': {
        'title': 'NAS',
        'subtitle': 'Gerencie os Network Access Servers',
        'entity': 'nas',
        'entity_singular': 'NAS',
        'breadcrumbs': '<span class="breadcrumb-item"><a href="/admin">Administração</a></span><span class="breadcrumb-separator" aria-hidden="true">/</span>',
        'columns': ['id', 'name', 'ip_address', 'secret', 'type', 'pop_id'],
        'form_fields': ['name', 'ip_address', 'secret', 'type', 'pop_id'],
        'has_filters': False
    },
    'admin_variables': {
        'title': 'Variáveis do Sistema',
        'subtitle': 'Configure as variáveis globais do sistema',
        'entity': 'variable',
        'entity_singular': 'Variável',
        'breadcrumbs': '<span class="breadcrumb-item"><a href="/admin">Administração</a></span><span class="breadcrumb-separator" aria-hidden="true">/</span>',
        'columns': ['id', 'key', 'value', 'description'],
        'form_fields': ['key', 'value', 'description'],
        'has_filters': False
    },
    'admin_backups': {
        'title': 'Backups',
        'subtitle': 'Gerencie os backups do sistema',
        'entity': 'backup',
        'entity_singular': 'Backup',
        'breadcrumbs': '<span class="breadcrumb-item"><a href="/admin">Administração</a></span><span class="breadcrumb-separator" aria-hidden="true">/</span>',
        'columns': ['id', 'filename', 'size', 'created_at', 'status'],
        'form_fields': [],
        'has_filters': True
    },
    'communication_history': {
        'title': 'Histórico de Comunicação',
        'subtitle': 'Visualize o histórico de mensagens enviadas',
        'entity': 'communication',
        'entity_singular': 'Mensagem',
        'breadcrumbs': '<span class="breadcrumb-item"><a href="/communication">Comunicação</a></span><span class="breadcrumb-separator" aria-hidden="true">/</span>',
        'columns': ['id', 'client_id', 'type', 'subject', 'sent_at', 'status'],
        'form_fields': ['client_id', 'type', 'subject', 'message'],
        'has_filters': True
    },
    'service_orders': {
        'title': 'Ordens de Serviço',
        'subtitle': 'Gerencie as ordens de serviço técnicas',
        'entity': 'order',
        'entity_singular': 'Ordem',
        'breadcrumbs': '<span class="breadcrumb-item"><a href="/service">Serviços</a></span><span class="breadcrumb-separator" aria-hidden="true">/</span>',
        'columns': ['id', 'contract_id', 'technician', 'type', 'status', 'scheduled_date'],
        'form_fields': ['contract_id', 'technician', 'type', 'description', 'scheduled_date'],
        'has_filters': True
    }
}

def generate_page(page_id, config):
    """Gera uma página moderna baseada na configuração"""

    # Gerar campos do formulário
    form_fields_html = ''
    for field in config.get('form_fields', []):
        form_fields_html += f'''
          <div class="form-group">
            <label for="{field}" class="form-label required">{field.replace('_', ' ').title()}</label>
            <input type="text" id="{field}" name="{field}" class="form-control" required />
          </div>'''

    # Gerar filtros se necessário
    filters_html = ''
    if config.get('has_filters', False):
        filters_html = '<div id="filter-container"></div>'

    # Gerar DataTable columns
    columns_js = []
    for col in config.get('columns', []):
        columns_js.append(f"{{ field: '{col}', label: '{col.replace('_', ' ').title()}', sortable: true }}")

    js_datatable = f'''
      const dataTable = new ISP_Components.DataTable({{
        container: '#table-container',
        columns: [{', '.join(columns_js)}],
        data: sampleData,
        actions: [
          {{ name: 'edit', label: 'Editar', icon: '✏️', handler: (row) => edit{config['entity'].title()}(row) }},
          {{ name: 'delete', label: 'Excluir', icon: '🗑️', variant: 'danger', handler: (row) => delete{config['entity'].title()}(row) }}
        ],
        emptyMessage: 'Nenhum registro encontrado'
      }});'''

    js_pagination = '''
      new ISP_Components.Pagination({
        container: '#pagination-container',
        total: sampleData.length,
        currentPage: 1,
        pageSize: 10
      });'''

    js_validator = f'''
      const formValidator = new ISP_Components.FormValidator('#form-{config["entity"]}', {{}});'''

    js_handlers = f'''
      window.edit{config['entity'].title()} = (row) => {{
        ISP_ERP.openModal('modal-{config["entity"]}');
      }};
      window.delete{config['entity'].title()} = (row) => {{
        ISP_ERP.confirm('Excluir este registro?', (c) => {{ if(c) location.reload(); }});
      }};'''

    # Substituir no template
    page_html = TEMPLATE_BASE.format(
        title=config['title'],
        page_name=config['title'],
        subtitle=config['subtitle'],
        entity=config['entity'],
        entity_singular=config['entity_singular'],
        breadcrumbs=config.get('breadcrumbs', ''),
        filters=filters_html,
        form_fields=form_fields_html,
        js_datatable=js_datatable,
        js_pagination=js_pagination,
        js_validator=js_validator,
        js_handlers=js_handlers
    )

    return page_html

def main():
    """Gera todas as páginas"""
    import os

    output_dir = os.path.join(os.path.dirname(__file__), 'templates')

    for page_id, config in PAGES.items():
        output_file = os.path.join(output_dir, f'{page_id}.html')
        page_html = generate_page(page_id, config)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(page_html)

        print(f'[OK] Gerado: {page_id}.html')

    print(f'\n[SUCCESS] {len(PAGES)} paginas geradas com sucesso!')

if __name__ == '__main__':
    main()

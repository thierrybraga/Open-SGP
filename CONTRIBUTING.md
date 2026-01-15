# Contribuindo para o Open-SGP

Obrigado pelo interesse em contribuir para o Open-SGP! Queremos tornar este projeto uma referência em ERP para provedores de internet, e sua ajuda é fundamental.

## 🚀 Como Contribuir

### 1. Reportando Bugs
Se você encontrou um bug, por favor, abra uma **Issue** detalhando:
- Passos para reproduzir o problema.
- Comportamento esperado vs. comportamento real.
- Screenshots ou logs de erro, se possível.
- Ambiente (SO, versão do Docker/Python, etc.).

### 2. Sugerindo Melhorias
Tem uma ideia de funcionalidade? Abra uma **Issue** com a tag `enhancement` explicando sua ideia e como ela beneficiaria a comunidade.

### 3. Enviando Código (Pull Requests)

1.  **Fork** o repositório.
2.  Crie uma branch para sua feature ou correção: `git checkout -b feature/minha-feature`.
3.  Siga os padrões de código do projeto (veja abaixo).
4.  Adicione testes para cobrir suas alterações.
5.  Faça o commit das suas alterações: `git commit -m 'feat: adiciona nova funcionalidade'`.
6.  Faça o push para a branch: `git push origin feature/minha-feature`.
7.  Abra um **Pull Request**.

## 💻 Padrões de Desenvolvimento

### Estilo de Código
Seguimos as convenções do **PEP 8**. Utilizamos as seguintes ferramentas para manter a qualidade:
- **Black**: Para formatação de código.
- **Isort**: Para ordenação de imports.
- **Flake8**: Para linting.

Recomendamos instalar o `pre-commit` para rodar essas verificações automaticamente:

```bash
pip install pre-commit
pre-commit install
```

### Commits
Utilizamos a convenção **Conventional Commits**:
- `feat:` Nova funcionalidade
- `fix:` Correção de bug
- `docs:` Alterações na documentação
- `style:` Formatação, pontos e vírgulas, etc.
- `refactor:` Refatoração de código
- `test:` Adição ou correção de testes
- `chore:` Atualizações de build, dependências, etc.

Exemplo: `feat: adiciona integração com gateway de pagamento X`

## 🧪 Testes
Certifique-se de que todos os testes passem antes de enviar seu PR. Execute:

```bash
pytest
```

---
Dúvidas? Entre em contato através das Issues ou Discussions.

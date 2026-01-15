"""
Arquivo: app/shared/boleto.py

Responsabilidade:
Geração de boletos bancários seguindo padrão Febraban.
Implementa código de barras, linha digitável e dígitos verificadores.

Integrações:
- Padrão Febraban para boletos bancários
- Módulo 10 e Módulo 11 para dígitos verificadores

Referências:
- Febraban: Layout Padrão de Arrecadação/Pagamento
- Código de Barras: 44 posições
- Linha Digitável: 47 posições
"""
from datetime import datetime, date
from typing import Optional


class BoletoGenerator:
    """Gerador de boletos bancários no padrão Febraban"""

    # Data base para cálculo do fator de vencimento (07/10/1997)
    DATA_BASE = datetime(1997, 10, 7).date()

    @staticmethod
    def calcular_digito_modulo10(codigo: str) -> str:
        """
        Calcula dígito verificador usando módulo 10.

        Algoritmo:
        1. Multiplica cada dígito por 2,1,2,1... da direita para esquerda
        2. Soma os dígitos dos produtos
        3. DV = (10 - (soma % 10)) % 10

        Args:
            codigo: Código numérico para calcular DV

        Returns:
            Dígito verificador (0-9)
        """
        multiplicador = 2
        soma = 0

        for digito in reversed(codigo):
            produto = int(digito) * multiplicador
            soma += produto // 10 + produto % 10
            multiplicador = 3 - multiplicador  # Alterna entre 2 e 1

        resultado = (10 - (soma % 10)) % 10
        return str(resultado)

    @staticmethod
    def calcular_digito_modulo11(codigo: str, pesos: list[int], base: int = 11) -> str:
        """
        Calcula dígito verificador usando módulo 11.

        Algoritmo:
        1. Multiplica cada dígito pelos pesos da direita para esquerda
        2. Soma os produtos
        3. Resto = soma % base
        4. DV = base - resto
        5. Se DV >= 10, DV = 0 ou 1 conforme regra Febraban

        Args:
            codigo: Código numérico para calcular DV
            pesos: Lista de pesos (ex: [2,3,4,5,6,7,8,9])
            base: Base para módulo (padrão 11)

        Returns:
            Dígito verificador (0-9 ou 1)
        """
        soma = 0
        peso_idx = 0

        for digito in reversed(codigo):
            soma += int(digito) * pesos[peso_idx % len(pesos)]
            peso_idx += 1

        resto = soma % base
        dv = base - resto

        # Regra Febraban: DV 0, 10 ou 11 vira 1
        if dv in [0, 10, 11]:
            dv = 1

        return str(dv)

    @staticmethod
    def calcular_fator_vencimento(data_vencimento: date) -> int:
        """
        Calcula fator de vencimento (posições 6-9 do código de barras).

        Fator = número de dias entre 07/10/1997 e data de vencimento.
        Válido até 21/02/2025 (fator 9999).
        Após essa data, usar fator absoluto ou renovar base.

        Args:
            data_vencimento: Data de vencimento do boleto

        Returns:
            Fator de vencimento (1-9999)
        """
        if data_vencimento < BoletoGenerator.DATA_BASE:
            raise ValueError("Data de vencimento não pode ser anterior a 07/10/1997")

        delta = data_vencimento - BoletoGenerator.DATA_BASE
        fator = delta.days

        if fator > 9999:
            # Após 21/02/2025, usar fator cíclico ou implementar nova base
            fator = fator % 9999
            if fator == 0:
                fator = 1

        return fator

    @staticmethod
    def gerar_codigo_barras(
        banco: str,
        moeda: str,
        vencimento: date,
        valor: float,
        campo_livre: str
    ) -> str:
        """
        Gera código de barras de 44 posições no padrão Febraban.

        Estrutura:
        - Posições 1-3: Código do banco (237 = Bradesco, 341 = Itaú, etc)
        - Posição 4: Código da moeda (9 = Real)
        - Posição 5: Dígito verificador (módulo 11)
        - Posições 6-9: Fator de vencimento
        - Posições 10-19: Valor (10 posições, sem vírgula)
        - Posições 20-44: Campo livre (25 posições, específico do banco)

        Args:
            banco: Código do banco (3 dígitos)
            moeda: Código da moeda (1 dígito, normalmente '9')
            vencimento: Data de vencimento
            valor: Valor do boleto em reais
            campo_livre: Campo livre de 25 dígitos (específico do banco)

        Returns:
            Código de barras de 44 dígitos

        Raises:
            ValueError: Se parâmetros inválidos
        """
        # Validações
        if len(banco) != 3:
            raise ValueError("Código do banco deve ter 3 dígitos")
        if len(moeda) != 1:
            raise ValueError("Código da moeda deve ter 1 dígito")
        if len(campo_livre) != 25:
            raise ValueError("Campo livre deve ter 25 dígitos")

        # Calcula fator de vencimento
        fator = BoletoGenerator.calcular_fator_vencimento(vencimento)
        fator_str = f"{fator:04d}"

        # Formata valor (10 posições, sem vírgula)
        valor_centavos = int(valor * 100)
        valor_str = f"{valor_centavos:010d}"

        # Monta código sem DV (posições 1-4, 6-44)
        codigo_sem_dv = banco + moeda + fator_str + valor_str + campo_livre

        # Calcula DV da posição 5 usando módulo 11
        pesos = [2, 3, 4, 5, 6, 7, 8, 9]
        dv = BoletoGenerator.calcular_digito_modulo11(codigo_sem_dv, pesos)

        # Monta código completo
        codigo_barras = banco + moeda + dv + fator_str + valor_str + campo_livre

        return codigo_barras

    @staticmethod
    def gerar_linha_digitavel(codigo_barras: str) -> str:
        """
        Gera linha digitável de 47 posições a partir do código de barras.

        Estrutura (5 campos):
        - Campo 1: AAABC.CCCCX (10 posições)
          - AAA: Código do banco
          - B: Código da moeda
          - CCCCC: Primeiras 5 posições do campo livre
          - X: DV módulo 10 do campo
        - Campo 2: CCCCC.CCCCCY (11 posições)
          - CCCCCCCCCC: Posições 6-15 do campo livre
          - Y: DV módulo 10 do campo
        - Campo 3: CCCCC.CCCCZ (11 posições)
          - CCCCCCCCCC: Posições 16-25 do campo livre
          - Z: DV módulo 10 do campo
        - Campo 4: D (1 posição)
          - D: DV geral (posição 5 do código de barras)
        - Campo 5: FFFFVVVVVVVVVV (14 posições)
          - FFFF: Fator de vencimento
          - VVVVVVVVVV: Valor

        Args:
            codigo_barras: Código de barras de 44 dígitos

        Returns:
            Linha digitável de 47 dígitos formatada

        Raises:
            ValueError: Se código de barras inválido
        """
        if len(codigo_barras) != 44:
            raise ValueError("Código de barras deve ter 44 dígitos")

        # Extrai componentes do código de barras
        banco = codigo_barras[0:3]
        moeda = codigo_barras[3:4]
        dv_geral = codigo_barras[4:5]
        fator = codigo_barras[5:9]
        valor = codigo_barras[9:19]
        campo_livre = codigo_barras[19:44]

        # Campo 1: Banco + Moeda + Primeiros 5 do campo livre + DV
        campo1_sem_dv = banco + moeda + campo_livre[0:5]
        campo1_dv = BoletoGenerator.calcular_digito_modulo10(campo1_sem_dv)
        campo1 = f"{campo1_sem_dv[0:5]}.{campo1_sem_dv[5:9]}{campo1_dv}"

        # Campo 2: Posições 6-15 do campo livre + DV
        campo2_sem_dv = campo_livre[5:15]
        campo2_dv = BoletoGenerator.calcular_digito_modulo10(campo2_sem_dv)
        campo2 = f"{campo2_sem_dv[0:5]}.{campo2_sem_dv[5:10]}{campo2_dv}"

        # Campo 3: Posições 16-25 do campo livre + DV
        campo3_sem_dv = campo_livre[15:25]
        campo3_dv = BoletoGenerator.calcular_digito_modulo10(campo3_sem_dv)
        campo3 = f"{campo3_sem_dv[0:5]}.{campo3_sem_dv[5:10]}{campo3_dv}"

        # Campo 4: DV geral
        campo4 = dv_geral

        # Campo 5: Fator + Valor
        campo5 = fator + valor

        # Linha digitável completa
        linha_digitavel = f"{campo1} {campo2} {campo3} {campo4} {campo5}"

        return linha_digitavel

    @staticmethod
    def gerar_campo_livre_generico(
        agencia: str,
        conta: str,
        carteira: str,
        nosso_numero: str
    ) -> str:
        """
        Gera campo livre genérico de 25 dígitos.

        ATENÇÃO: Cada banco tem seu próprio layout de campo livre.
        Esta é uma implementação genérica. Para produção, implemente
        o layout específico de cada banco.

        Layouts específicos:
        - Banco do Brasil (001): Layout próprio
        - Bradesco (237): Layout próprio
        - Itaú (341): Layout próprio
        - Santander (033): Layout próprio
        - Caixa (104): Layout próprio

        Args:
            agencia: Código da agência (4 dígitos)
            conta: Número da conta (máx 10 dígitos)
            carteira: Código da carteira (2 dígitos)
            nosso_numero: Nosso número (máx 11 dígitos)

        Returns:
            Campo livre de 25 dígitos

        Raises:
            ValueError: Se parâmetros inválidos
        """
        # Remove caracteres não numéricos
        agencia = ''.join(filter(str.isdigit, agencia))
        conta = ''.join(filter(str.isdigit, conta))
        carteira = ''.join(filter(str.isdigit, carteira))
        nosso_numero = ''.join(filter(str.isdigit, nosso_numero))

        # Preenche com zeros à esquerda
        agencia = agencia.zfill(4)
        conta = conta.zfill(10)
        carteira = carteira.zfill(2)
        nosso_numero = nosso_numero.zfill(11)

        # Campo livre genérico: carteira(2) + nosso_numero(11) + agencia(4) + conta(7) + zero(1)
        campo_livre = carteira + nosso_numero[:11] + agencia[:4] + conta[:7] + "0"

        if len(campo_livre) != 25:
            raise ValueError("Erro ao gerar campo livre")

        return campo_livre

    @staticmethod
    def validar_codigo_barras(codigo_barras: str) -> bool:
        """
        Valida código de barras verificando o dígito verificador.

        Args:
            codigo_barras: Código de barras de 44 dígitos

        Returns:
            True se válido, False caso contrário
        """
        if len(codigo_barras) != 44:
            return False

        # Extrai componentes
        banco = codigo_barras[0:3]
        moeda = codigo_barras[3:4]
        dv_informado = codigo_barras[4:5]
        resto = codigo_barras[5:44]

        # Recalcula DV
        codigo_sem_dv = banco + moeda + resto
        pesos = [2, 3, 4, 5, 6, 7, 8, 9]
        dv_calculado = BoletoGenerator.calcular_digito_modulo11(codigo_sem_dv, pesos)

        return dv_informado == dv_calculado


class BoletoData:
    """Classe auxiliar para dados de boleto"""

    def __init__(
        self,
        banco_codigo: str,
        agencia: str,
        conta: str,
        carteira: str,
        nosso_numero: str,
        vencimento: date,
        valor: float,
        cedente_nome: str,
        cedente_documento: str,
        sacado_nome: str,
        sacado_documento: str,
        sacado_endereco: str = "",
        instrucoes: str = "",
        demonstrativo: str = "",
        aceite: str = "N",
        especie: str = "R$",
        especie_doc: str = "DM"
    ):
        self.banco_codigo = banco_codigo
        self.agencia = agencia
        self.conta = conta
        self.carteira = carteira
        self.nosso_numero = nosso_numero
        self.vencimento = vencimento
        self.valor = valor
        self.cedente_nome = cedente_nome
        self.cedente_documento = cedente_documento
        self.sacado_nome = sacado_nome
        self.sacado_documento = sacado_documento
        self.sacado_endereco = sacado_endereco
        self.instrucoes = instrucoes
        self.demonstrativo = demonstrativo
        self.aceite = aceite
        self.especie = especie
        self.especie_doc = especie_doc

    def gerar_boleto(self) -> dict:
        """
        Gera dados completos do boleto.

        Returns:
            Dicionário com código de barras, linha digitável e dados
        """
        # Gera campo livre
        campo_livre = BoletoGenerator.gerar_campo_livre_generico(
            self.agencia,
            self.conta,
            self.carteira,
            self.nosso_numero
        )

        # Gera código de barras
        codigo_barras = BoletoGenerator.gerar_codigo_barras(
            banco=self.banco_codigo,
            moeda="9",  # Real
            vencimento=self.vencimento,
            valor=self.valor,
            campo_livre=campo_livre
        )

        # Gera linha digitável
        linha_digitavel = BoletoGenerator.gerar_linha_digitavel(codigo_barras)

        return {
            "codigo_barras": codigo_barras,
            "linha_digitavel": linha_digitavel,
            "banco_codigo": self.banco_codigo,
            "agencia": self.agencia,
            "conta": self.conta,
            "carteira": self.carteira,
            "nosso_numero": self.nosso_numero,
            "vencimento": self.vencimento.strftime("%d/%m/%Y"),
            "valor": f"R$ {self.valor:,.2f}",
            "cedente_nome": self.cedente_nome,
            "cedente_documento": self.cedente_documento,
            "sacado_nome": self.sacado_nome,
            "sacado_documento": self.sacado_documento,
            "sacado_endereco": self.sacado_endereco,
            "instrucoes": self.instrucoes,
            "demonstrativo": self.demonstrativo,
            "aceite": self.aceite,
            "especie": self.especie,
            "especie_doc": self.especie_doc
        }

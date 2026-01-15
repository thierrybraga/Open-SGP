"""
Arquivo: app/shared/cnab.py

Responsabilidade:
Geração de arquivos CNAB 240 e CNAB 400 no padrão Febraban.
Implementa remessa e retorno para principais bancos brasileiros.

Integrações:
- Padrão Febraban CNAB 240 (Layout 2022)
- Padrão Febraban CNAB 400 (Layout legado)

Referências:
- Febraban: Layout de Arquivos CNAB
- CNAB 240: 240 caracteres por linha
- CNAB 400: 400 caracteres por linha
"""
from datetime import datetime, date
from typing import List, Dict, Optional
from decimal import Decimal


class CNAB240Generator:
    """Gerador de arquivos CNAB 240 (padrão Febraban)"""

    @staticmethod
    def formatar_texto(texto: str, tamanho: int, preencher: str = " ", alinhar_direita: bool = False) -> str:
        """Formata texto com tamanho fixo"""
        texto = str(texto)[:tamanho]
        if alinhar_direita:
            return texto.rjust(tamanho, preencher)
        return texto.ljust(tamanho, preencher)

    @staticmethod
    def formatar_numero(numero: float, tamanho: int, decimais: int = 0) -> str:
        """Formata número com tamanho fixo (sem vírgula)"""
        if decimais > 0:
            numero = numero * (10 ** decimais)
        numero_str = str(int(numero)).zfill(tamanho)
        return numero_str[-tamanho:]

    @staticmethod
    def formatar_data(data: date, formato: str = "ddmmaaaa") -> str:
        """Formata data conforme padrão CNAB"""
        if formato == "ddmmaaaa":
            return data.strftime("%d%m%Y")
        elif formato == "aaaammdd":
            return data.strftime("%Y%m%d")
        return ""

    @staticmethod
    def gerar_header_arquivo(
        banco_codigo: str,
        empresa_tipo_inscricao: str,
        empresa_numero_inscricao: str,
        empresa_nome: str,
        agencia: str,
        conta: str,
        conta_dv: str,
        sequencial_arquivo: int,
        data_geracao: date
    ) -> str:
        """
        Gera Header de Arquivo (Registro 0) - 240 caracteres.

        Args:
            banco_codigo: Código do banco (3 dígitos)
            empresa_tipo_inscricao: 1=CPF, 2=CNPJ
            empresa_numero_inscricao: CPF/CNPJ sem formatação
            empresa_nome: Razão social da empresa
            agencia: Código da agência (5 dígitos)
            conta: Número da conta (12 dígitos)
            conta_dv: Dígito verificador da conta (1 dígito)
            sequencial_arquivo: Número sequencial do arquivo
            data_geracao: Data de geração do arquivo

        Returns:
            Linha de 240 caracteres
        """
        linha = ""
        linha += CNAB240Generator.formatar_numero(banco_codigo, 3)  # 1-3: Código do banco
        linha += "0000"  # 4-7: Lote de serviço (0000 = header)
        linha += "0"  # 8: Tipo de registro (0 = header arquivo)
        linha += " " * 9  # 9-17: Uso exclusivo FEBRABAN
        linha += empresa_tipo_inscricao  # 18: Tipo inscrição (1=CPF, 2=CNPJ)
        linha += CNAB240Generator.formatar_numero(empresa_numero_inscricao, 14)  # 19-32: CNPJ/CPF
        linha += " " * 20  # 33-52: Convênio (uso banco)
        linha += CNAB240Generator.formatar_numero(agencia, 5)  # 53-57: Agência
        linha += " "  # 58: DV agência
        linha += CNAB240Generator.formatar_numero(conta, 12)  # 59-70: Conta
        linha += conta_dv  # 71: DV conta
        linha += " "  # 72: DV agência/conta
        linha += CNAB240Generator.formatar_texto(empresa_nome, 30)  # 73-102: Nome da empresa
        linha += CNAB240Generator.formatar_texto("BANCO", 30)  # 103-132: Nome do banco
        linha += " " * 10  # 133-142: Uso exclusivo FEBRABAN
        linha += "1"  # 143: Código remessa (1) / retorno (2)
        linha += CNAB240Generator.formatar_data(data_geracao, "ddmmaaaa")  # 144-151: Data geração
        linha += datetime.now().strftime("%H%M%S")  # 152-157: Hora geração
        linha += CNAB240Generator.formatar_numero(sequencial_arquivo, 6)  # 158-163: Sequencial arquivo
        linha += "103"  # 164-166: Versão layout (103 = v10.3)
        linha += "00000"  # 167-171: Densidade (00000)
        linha += " " * 20  # 172-191: Uso banco
        linha += " " * 20  # 192-211: Uso empresa
        linha += " " * 29  # 212-240: Uso exclusivo FEBRABAN
        return linha

    @staticmethod
    def gerar_header_lote(
        banco_codigo: str,
        lote: int,
        empresa_tipo_inscricao: str,
        empresa_numero_inscricao: str,
        empresa_nome: str,
        agencia: str,
        conta: str,
        conta_dv: str,
        tipo_operacao: str = "C"  # C=Crédito, D=Débito, E=Extrato
    ) -> str:
        """
        Gera Header de Lote (Registro 1) - 240 caracteres.

        Args:
            banco_codigo: Código do banco
            lote: Número do lote (sequencial a partir de 1)
            empresa_tipo_inscricao: 1=CPF, 2=CNPJ
            empresa_numero_inscricao: CPF/CNPJ
            empresa_nome: Nome da empresa
            agencia: Agência
            conta: Conta
            conta_dv: DV da conta
            tipo_operacao: Tipo de operação (C, D, E)

        Returns:
            Linha de 240 caracteres
        """
        linha = ""
        linha += CNAB240Generator.formatar_numero(banco_codigo, 3)  # 1-3: Código banco
        linha += CNAB240Generator.formatar_numero(lote, 4)  # 4-7: Lote
        linha += "1"  # 8: Tipo registro (1 = header lote)
        linha += "R"  # 9: Tipo operação (R=Remessa, T=Retorno)
        linha += "01"  # 10-11: Tipo serviço (01=Cobrança)
        linha += "  "  # 12-13: Uso exclusivo
        linha += "060"  # 14-16: Versão layout lote
        linha += " "  # 17: Uso exclusivo
        linha += empresa_tipo_inscricao  # 18: Tipo inscrição
        linha += CNAB240Generator.formatar_numero(empresa_numero_inscricao, 15)  # 19-33: CNPJ/CPF
        linha += " " * 20  # 34-53: Convênio
        linha += CNAB240Generator.formatar_numero(agencia, 5)  # 54-58: Agência
        linha += " "  # 59: DV agência
        linha += CNAB240Generator.formatar_numero(conta, 12)  # 60-71: Conta
        linha += conta_dv  # 72: DV conta
        linha += " "  # 73: DV agência/conta
        linha += CNAB240Generator.formatar_texto(empresa_nome, 30)  # 74-103: Nome empresa
        linha += " " * 40  # 104-143: Mensagem 1
        linha += " " * 40  # 144-183: Mensagem 2
        linha += "00000000"  # 184-191: Número remessa/retorno
        linha += CNAB240Generator.formatar_data(date.today(), "ddmmaaaa")  # 192-199: Data gravação
        linha += "00000000"  # 200-207: Data crédito (zeros)
        linha += " " * 33  # 208-240: Uso exclusivo
        return linha

    @staticmethod
    def gerar_segmento_p(
        banco_codigo: str,
        lote: int,
        sequencial: int,
        agencia: str,
        conta: str,
        conta_dv: str,
        nosso_numero: str,
        carteira: str,
        documento_numero: str,
        vencimento: date,
        valor_titulo: float,
        especie_titulo: str = "02",  # 02=Duplicata Mercantil
        aceite: str = "N",
        data_emissao: date = None,
        codigo_juros: str = "0",  # 0=Isento
        data_juros: date = None,
        valor_juros: float = 0.0,
        codigo_desconto: str = "0",  # 0=Sem desconto
        data_desconto: date = None,
        valor_desconto: float = 0.0,
        valor_iof: float = 0.0,
        valor_abatimento: float = 0.0,
        codigo_protesto: str = "0",  # 0=Não protestar
        prazo_protesto: int = 0,
        codigo_baixa: str = "0",  # 0=Não baixar
        prazo_baixa: int = 0
    ) -> str:
        """
        Gera Segmento P - Dados do título (Registro 3 tipo P) - 240 caracteres.

        Args:
            Diversos parâmetros do título

        Returns:
            Linha de 240 caracteres
        """
        if data_emissao is None:
            data_emissao = date.today()
        if data_juros is None:
            data_juros = vencimento
        if data_desconto is None:
            data_desconto = vencimento

        linha = ""
        linha += CNAB240Generator.formatar_numero(banco_codigo, 3)  # 1-3: Código banco
        linha += CNAB240Generator.formatar_numero(lote, 4)  # 4-7: Lote
        linha += "3"  # 8: Tipo registro (3 = detalhe)
        linha += CNAB240Generator.formatar_numero(sequencial, 5)  # 9-13: Sequencial
        linha += "P"  # 14: Segmento (P)
        linha += " "  # 15: Uso exclusivo
        linha += "01"  # 16-17: Código movimento (01=Entrada de títulos)
        linha += CNAB240Generator.formatar_numero(agencia, 5)  # 18-22: Agência
        linha += " "  # 23: DV agência
        linha += CNAB240Generator.formatar_numero(conta, 12)  # 24-35: Conta
        linha += conta_dv  # 36: DV conta
        linha += " "  # 37: DV agência/conta
        linha += CNAB240Generator.formatar_numero(nosso_numero, 20)  # 38-57: Nosso número
        linha += carteira  # 58-59: Carteira
        linha += "1"  # 60: Forma cadastramento (1=Com registro)
        linha += " "  # 61: Tipo documento
        linha += "2"  # 62: Identificação emissão (2=Cliente)
        linha += "2"  # 63: Identificação distribuição (2=Cliente)
        linha += CNAB240Generator.formatar_texto(documento_numero, 15)  # 64-78: Número documento
        linha += CNAB240Generator.formatar_data(vencimento, "ddmmaaaa")  # 79-86: Vencimento
        linha += CNAB240Generator.formatar_numero(valor_titulo, 15, 2)  # 87-101: Valor título
        linha += "00000"  # 102-106: Agência cobradora (zeros = automático)
        linha += " "  # 107: DV agência cobradora
        linha += especie_titulo  # 108-109: Espécie do título
        linha += aceite  # 110: Aceite (A=Aceite, N=Não aceite)
        linha += CNAB240Generator.formatar_data(data_emissao, "ddmmaaaa")  # 111-118: Data emissão
        linha += codigo_juros  # 119: Código juros mora (0=Isento, 1=Valor dia, 2=Taxa mensal)
        linha += CNAB240Generator.formatar_data(data_juros, "ddmmaaaa")  # 120-127: Data juros
        linha += CNAB240Generator.formatar_numero(valor_juros, 15, 2)  # 128-142: Juros mora
        linha += codigo_desconto  # 143: Código desconto 1
        linha += CNAB240Generator.formatar_data(data_desconto, "ddmmaaaa")  # 144-151: Data desconto 1
        linha += CNAB240Generator.formatar_numero(valor_desconto, 15, 2)  # 152-166: Valor desconto 1
        linha += CNAB240Generator.formatar_numero(valor_iof, 15, 2)  # 167-181: Valor IOF
        linha += CNAB240Generator.formatar_numero(valor_abatimento, 15, 2)  # 182-196: Valor abatimento
        linha += CNAB240Generator.formatar_texto("", 25)  # 197-221: Identificação título empresa
        linha += codigo_protesto  # 222: Código protesto
        linha += CNAB240Generator.formatar_numero(prazo_protesto, 2)  # 223-224: Prazo protesto
        linha += codigo_baixa  # 225: Código baixa/devolução
        linha += CNAB240Generator.formatar_numero(prazo_baixa, 3)  # 226-228: Prazo baixa
        linha += "09"  # 229-230: Código moeda (09=Real)
        linha += "0000000000"  # 231-240: Uso exclusivo
        return linha

    @staticmethod
    def gerar_segmento_q(
        banco_codigo: str,
        lote: int,
        sequencial: int,
        sacado_tipo_inscricao: str,
        sacado_numero_inscricao: str,
        sacado_nome: str,
        sacado_endereco: str,
        sacado_bairro: str,
        sacado_cep: str,
        sacado_cidade: str,
        sacado_uf: str
    ) -> str:
        """
        Gera Segmento Q - Dados do sacado (Registro 3 tipo Q) - 240 caracteres.

        Args:
            Dados do sacado (pagador)

        Returns:
            Linha de 240 caracteres
        """
        linha = ""
        linha += CNAB240Generator.formatar_numero(banco_codigo, 3)  # 1-3: Código banco
        linha += CNAB240Generator.formatar_numero(lote, 4)  # 4-7: Lote
        linha += "3"  # 8: Tipo registro (3 = detalhe)
        linha += CNAB240Generator.formatar_numero(sequencial, 5)  # 9-13: Sequencial
        linha += "Q"  # 14: Segmento (Q)
        linha += " "  # 15: Uso exclusivo
        linha += "01"  # 16-17: Código movimento
        linha += sacado_tipo_inscricao  # 18: Tipo inscrição (1=CPF, 2=CNPJ)
        linha += CNAB240Generator.formatar_numero(sacado_numero_inscricao, 15)  # 19-33: CNPJ/CPF
        linha += CNAB240Generator.formatar_texto(sacado_nome, 40)  # 34-73: Nome
        linha += CNAB240Generator.formatar_texto(sacado_endereco, 40)  # 74-113: Endereço
        linha += CNAB240Generator.formatar_texto(sacado_bairro, 15)  # 114-128: Bairro
        linha += CNAB240Generator.formatar_numero(sacado_cep.replace("-", ""), 8)  # 129-136: CEP
        linha += CNAB240Generator.formatar_texto(sacado_cidade, 15)  # 137-151: Cidade
        linha += sacado_uf  # 152-153: UF
        linha += "0"  # 154: Tipo inscrição sacador/avalista
        linha += "000000000000000"  # 155-169: CNPJ/CPF sacador
        linha += CNAB240Generator.formatar_texto("", 40)  # 170-209: Nome sacador
        linha += "000"  # 210-212: Código banco correspondente
        linha += CNAB240Generator.formatar_texto("", 20)  # 213-232: Nosso número banco correspondente
        linha += " " * 8  # 233-240: Uso exclusivo
        return linha

    @staticmethod
    def gerar_trailer_lote(
        banco_codigo: str,
        lote: int,
        quantidade_registros: int,
        valor_total: float
    ) -> str:
        """
        Gera Trailer de Lote (Registro 5) - 240 caracteres.

        Args:
            banco_codigo: Código do banco
            lote: Número do lote
            quantidade_registros: Quantidade de registros no lote (excluindo header e trailer)
            valor_total: Valor total dos títulos do lote

        Returns:
            Linha de 240 caracteres
        """
        linha = ""
        linha += CNAB240Generator.formatar_numero(banco_codigo, 3)  # 1-3: Código banco
        linha += CNAB240Generator.formatar_numero(lote, 4)  # 4-7: Lote
        linha += "5"  # 8: Tipo registro (5 = trailer lote)
        linha += " " * 9  # 9-17: Uso exclusivo
        linha += CNAB240Generator.formatar_numero(quantidade_registros + 2, 6)  # 18-23: Qtd registros (inclui header/trailer)
        linha += CNAB240Generator.formatar_numero(quantidade_registros // 2, 6)  # 24-29: Qtd títulos cobrança simples
        linha += CNAB240Generator.formatar_numero(valor_total, 17, 2)  # 30-46: Valor total títulos simples
        linha += "000000"  # 47-52: Qtd títulos cobrança vinculada
        linha += "00000000000000000"  # 53-69: Valor total vinculada
        linha += "000000"  # 70-75: Qtd títulos cobrança caucionada
        linha += "00000000000000000"  # 76-92: Valor total caucionada
        linha += "000000"  # 93-98: Qtd títulos cobrança descontada
        linha += "00000000000000000"  # 99-115: Valor total descontada
        linha += " " * 8  # 116-123: Aviso bancário
        linha += " " * 117  # 124-240: Uso exclusivo
        return linha

    @staticmethod
    def gerar_trailer_arquivo(
        banco_codigo: str,
        quantidade_lotes: int,
        quantidade_registros: int
    ) -> str:
        """
        Gera Trailer de Arquivo (Registro 9) - 240 caracteres.

        Args:
            banco_codigo: Código do banco
            quantidade_lotes: Quantidade de lotes no arquivo
            quantidade_registros: Quantidade total de registros (todos)

        Returns:
            Linha de 240 caracteres
        """
        linha = ""
        linha += CNAB240Generator.formatar_numero(banco_codigo, 3)  # 1-3: Código banco
        linha += "9999"  # 4-7: Lote (9999 = trailer arquivo)
        linha += "9"  # 8: Tipo registro (9 = trailer arquivo)
        linha += " " * 9  # 9-17: Uso exclusivo
        linha += CNAB240Generator.formatar_numero(quantidade_lotes, 6)  # 18-23: Qtd lotes
        linha += CNAB240Generator.formatar_numero(quantidade_registros, 6)  # 24-29: Qtd registros
        linha += "000000"  # 30-35: Qtd contas para conciliação
        linha += " " * 205  # 36-240: Uso exclusivo
        return linha

    @staticmethod
    def gerar_remessa_completa(
        banco_codigo: str,
        empresa_dados: Dict,
        titulos: List[Dict],
        sequencial_arquivo: int = 1
    ) -> str:
        """
        Gera arquivo CNAB 240 de remessa completo.

        Args:
            banco_codigo: Código do banco (3 dígitos)
            empresa_dados: Dicionário com dados da empresa (nome, cpf/cnpj, agencia, conta, etc)
            titulos: Lista de dicionários com dados dos títulos
            sequencial_arquivo: Número sequencial do arquivo

        Returns:
            Conteúdo completo do arquivo CNAB 240 (múltiplas linhas)
        """
        linhas = []
        data_geracao = date.today()

        # Header do arquivo
        header_arquivo = CNAB240Generator.gerar_header_arquivo(
            banco_codigo=banco_codigo,
            empresa_tipo_inscricao=empresa_dados["tipo_inscricao"],
            empresa_numero_inscricao=empresa_dados["numero_inscricao"],
            empresa_nome=empresa_dados["nome"],
            agencia=empresa_dados["agencia"],
            conta=empresa_dados["conta"],
            conta_dv=empresa_dados["conta_dv"],
            sequencial_arquivo=sequencial_arquivo,
            data_geracao=data_geracao
        )
        linhas.append(header_arquivo)

        # Lote único (pode ter múltiplos lotes)
        lote = 1
        header_lote = CNAB240Generator.gerar_header_lote(
            banco_codigo=banco_codigo,
            lote=lote,
            empresa_tipo_inscricao=empresa_dados["tipo_inscricao"],
            empresa_numero_inscricao=empresa_dados["numero_inscricao"],
            empresa_nome=empresa_dados["nome"],
            agencia=empresa_dados["agencia"],
            conta=empresa_dados["conta"],
            conta_dv=empresa_dados["conta_dv"]
        )
        linhas.append(header_lote)

        # Detalhes (Segmentos P e Q para cada título)
        sequencial = 1
        valor_total = 0.0
        for titulo in titulos:
            # Segmento P
            seg_p = CNAB240Generator.gerar_segmento_p(
                banco_codigo=banco_codigo,
                lote=lote,
                sequencial=sequencial,
                agencia=empresa_dados["agencia"],
                conta=empresa_dados["conta"],
                conta_dv=empresa_dados["conta_dv"],
                nosso_numero=titulo["nosso_numero"],
                carteira=titulo.get("carteira", "09"),
                documento_numero=titulo["documento_numero"],
                vencimento=titulo["vencimento"],
                valor_titulo=titulo["valor"],
                especie_titulo=titulo.get("especie", "02"),
                aceite=titulo.get("aceite", "N"),
                data_emissao=titulo.get("data_emissao", date.today()),
                codigo_juros=titulo.get("codigo_juros", "0"),
                valor_juros=titulo.get("valor_juros", 0.0),
                codigo_desconto=titulo.get("codigo_desconto", "0"),
                valor_desconto=titulo.get("valor_desconto", 0.0),
                valor_iof=titulo.get("valor_iof", 0.0),
                valor_abatimento=titulo.get("valor_abatimento", 0.0),
                codigo_protesto=titulo.get("codigo_protesto", "0"),
                prazo_protesto=titulo.get("prazo_protesto", 0),
                codigo_baixa=titulo.get("codigo_baixa", "0"),
                prazo_baixa=titulo.get("prazo_baixa", 0)
            )
            linhas.append(seg_p)
            sequencial += 1

            # Segmento Q
            sacado = titulo["sacado"]
            seg_q = CNAB240Generator.gerar_segmento_q(
                banco_codigo=banco_codigo,
                lote=lote,
                sequencial=sequencial,
                sacado_tipo_inscricao=sacado["tipo_inscricao"],
                sacado_numero_inscricao=sacado["numero_inscricao"],
                sacado_nome=sacado["nome"],
                sacado_endereco=sacado.get("endereco", ""),
                sacado_bairro=sacado.get("bairro", ""),
                sacado_cep=sacado.get("cep", "00000000"),
                sacado_cidade=sacado.get("cidade", ""),
                sacado_uf=sacado.get("uf", "SP")
            )
            linhas.append(seg_q)
            sequencial += 1

            valor_total += titulo["valor"]

        # Trailer do lote
        trailer_lote = CNAB240Generator.gerar_trailer_lote(
            banco_codigo=banco_codigo,
            lote=lote,
            quantidade_registros=len(titulos) * 2,  # P + Q para cada título
            valor_total=valor_total
        )
        linhas.append(trailer_lote)

        # Trailer do arquivo
        trailer_arquivo = CNAB240Generator.gerar_trailer_arquivo(
            banco_codigo=banco_codigo,
            quantidade_lotes=1,
            quantidade_registros=len(linhas) + 1  # +1 pelo próprio trailer
        )
        linhas.append(trailer_arquivo)

        return "\r\n".join(linhas) + "\r\n"


class CNAB400Generator:
    """
    Gerador de arquivos CNAB 400 (layout legado).

    Nota: Implementação simplificada. Para produção, verificar
    layout específico de cada banco.
    """

    @staticmethod
    def gerar_remessa_simples(
        banco_codigo: str,
        empresa_dados: Dict,
        titulos: List[Dict]
    ) -> str:
        """
        Gera arquivo CNAB 400 de remessa (simplificado).

        IMPORTANTE: CNAB 400 tem layouts específicos por banco.
        Esta é uma implementação genérica que deve ser adaptada
        para o banco específico em produção.

        Args:
            banco_codigo: Código do banco
            empresa_dados: Dados da empresa
            titulos: Lista de títulos

        Returns:
            Conteúdo do arquivo CNAB 400
        """
        linhas = []

        # Header (Registro 0)
        header = "0"  # Tipo registro
        header += "1"  # Tipo arquivo (1=Remessa)
        header += "REMESSA".ljust(7)
        header += "01"  # Código serviço
        header += "COBRANCA".ljust(15)
        header += empresa_dados["conta"].zfill(20)
        header += empresa_dados["nome"][:30].ljust(30)
        header += banco_codigo.zfill(3)
        header += "BANCO".ljust(15)
        header += date.today().strftime("%d%m%y")
        header += " " * 294
        header += "000001"  # Sequencial
        linhas.append(header[:400])

        # Detalhes (Registro 1)
        seq = 2
        for titulo in titulos:
            detalhe = "1"  # Tipo registro
            detalhe += empresa_dados.get("tipo_inscricao", "02").zfill(2)
            detalhe += empresa_dados.get("numero_inscricao", "").zfill(14)
            detalhe += empresa_dados.get("agencia", "").zfill(4)
            detalhe += empresa_dados.get("conta", "").zfill(8)
            detalhe += titulo.get("nosso_numero", "").zfill(25)
            detalhe += "01"  # Código ocorrência (01=Entrada)
            detalhe += titulo.get("documento_numero", "").ljust(10)
            detalhe += titulo["vencimento"].strftime("%d%m%y")
            detalhe += str(int(titulo["valor"] * 100)).zfill(13)
            detalhe += banco_codigo.zfill(3)
            detalhe += "00000"  # Agência cobradora
            detalhe += "02"  # Espécie título
            detalhe += "N"  # Aceite
            detalhe += date.today().strftime("%d%m%y")  # Data emissão
            detalhe += " " * 300
            detalhe += str(seq).zfill(6)
            linhas.append(detalhe[:400])
            seq += 1

        # Trailer (Registro 9)
        trailer = "9"
        trailer += " " * 393
        trailer += str(seq).zfill(6)
        linhas.append(trailer[:400])

        return "\r\n".join(linhas) + "\r\n"

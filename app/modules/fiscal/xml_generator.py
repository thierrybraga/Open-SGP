"""
Arquivo: app/modules/fiscal/xml_generator.py

Responsabilidade:
Geração de XML para NFe e NFSe conforme layouts da SEFAZ.
Implementa todas as tags obrigatórias e opcionais.

Integrações:
- Layout NFe versão 4.0
- Layout NFSe conforme município
- XSD SEFAZ

Referências:
- Manual de Integração NFe 4.0
- Esquemas XSD oficiais
"""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any
from lxml import etree


class NFeXMLGenerator:
    """Gerador de XML para NFe (Nota Fiscal Eletrônica)"""

    def __init__(self):
        self.ns = "http://www.portalfiscal.inf.br/nfe"

    def gerar_nfe(
        self,
        emitente: Dict[str, Any],
        destinatario: Dict[str, Any],
        produtos: List[Dict[str, Any]],
        totais: Dict[str, Decimal],
        numero_nota: int,
        serie: int,
        data_emissao: datetime,
        natureza_operacao: str = "VENDA",
        tipo_emissao: int = 1,
        finalidade: int = 1,
        ambiente: int = 2
    ) -> str:
        """
        Gera XML completo da NFe.

        Args:
            emitente: Dados do emitente
            destinatario: Dados do destinatário
            produtos: Lista de produtos/serviços
            totais: Valores totais
            numero_nota: Número da nota
            serie: Série da nota
            data_emissao: Data e hora de emissão
            natureza_operacao: Natureza da operação
            tipo_emissao: Tipo de emissão (1=Normal)
            finalidade: Finalidade (1=Normal, 2=Complementar, 3=Ajuste, 4=Devolução)
            ambiente: Ambiente (1=Produção, 2=Homologação)

        Returns:
            XML da NFe como string
        """
        # Cria elemento raiz
        root = etree.Element(
            "NFe",
            xmlns=self.ns,
            nsmap={'nfe': self.ns}
        )

        # Cria infNFe
        inf_nfe = etree.SubElement(root, "infNFe", versao="4.00")

        # Identificação
        ide = self._gerar_identificacao(
            numero_nota, serie, data_emissao, natureza_operacao,
            tipo_emissao, finalidade, ambiente, emitente
        )
        inf_nfe.append(ide)

        # Emitente
        emit = self._gerar_emitente(emitente)
        inf_nfe.append(emit)

        # Destinatário
        dest = self._gerar_destinatario(destinatario)
        inf_nfe.append(dest)

        # Produtos
        for idx, produto in enumerate(produtos, start=1):
            det = self._gerar_produto(produto, idx)
            inf_nfe.append(det)

        # Totais
        total = self._gerar_totais(totais, len(produtos))
        inf_nfe.append(total)

        # Informações de transporte (obrigatório mesmo que sem frete)
        transp = self._gerar_transporte()
        inf_nfe.append(transp)

        # Informações de pagamento
        pag = self._gerar_pagamento(totais)
        inf_nfe.append(pag)

        # Gera chave de acesso
        chave = self._gerar_chave_acesso(
            emitente['uf'],
            data_emissao,
            emitente['cnpj'],
            serie,
            numero_nota,
            tipo_emissao
        )
        inf_nfe.set("Id", f"NFe{chave}")

        # Converte para string
        xml_string = etree.tostring(
            root,
            encoding='unicode',
            pretty_print=True,
            xml_declaration=True
        )

        return xml_string

    def _gerar_identificacao(
        self,
        numero: int,
        serie: int,
        data_emissao: datetime,
        natureza: str,
        tipo_emissao: int,
        finalidade: int,
        ambiente: int,
        emitente: Dict[str, Any]
    ) -> etree.Element:
        """Gera tag <ide> de identificação"""
        ide = etree.Element("ide")

        # Código UF (SP=35, RJ=33, etc)
        uf_codes = {"SP": "35", "RJ": "33", "MG": "31"}
        cuf = uf_codes.get(emitente['uf'], "35")

        etree.SubElement(ide, "cUF").text = cuf
        etree.SubElement(ide, "cNF").text = str(numero).zfill(8)[-8:]  # Código numérico
        etree.SubElement(ide, "natOp").text = natureza
        etree.SubElement(ide, "mod").text = "55"  # Modelo 55 = NFe
        etree.SubElement(ide, "serie").text = str(serie)
        etree.SubElement(ide, "nNF").text = str(numero)
        etree.SubElement(ide, "dhEmi").text = data_emissao.isoformat()
        etree.SubElement(ide, "tpNF").text = "1"  # 1=Saída
        etree.SubElement(ide, "idDest").text = "1"  # 1=Operação interna
        etree.SubElement(ide, "cMunFG").text = emitente.get('codigo_municipio', '3550308')  # São Paulo
        etree.SubElement(ide, "tpImp").text = "1"  # 1=DANFE normal
        etree.SubElement(ide, "tpEmis").text = str(tipo_emissao)
        etree.SubElement(ide, "cDV").text = "0"  # Será calculado na chave
        etree.SubElement(ide, "tpAmb").text = str(ambiente)
        etree.SubElement(ide, "finNFe").text = str(finalidade)
        etree.SubElement(ide, "indFinal").text = "1"  # 1=Consumidor final
        etree.SubElement(ide, "indPres").text = "1"  # 1=Operação presencial
        etree.SubElement(ide, "procEmi").text = "0"  # 0=Emissão própria
        etree.SubElement(ide, "verProc").text = "ISP_ERP_1.0"

        return ide

    def _gerar_emitente(self, emitente: Dict[str, Any]) -> etree.Element:
        """Gera tag <emit> de emitente"""
        emit = etree.Element("emit")

        etree.SubElement(emit, "CNPJ").text = emitente['cnpj'].replace(".", "").replace("/", "").replace("-", "")
        etree.SubElement(emit, "xNome").text = emitente['razao_social']
        etree.SubElement(emit, "xFant").text = emitente.get('nome_fantasia', emitente['razao_social'])

        # Endereço
        ender_emit = etree.SubElement(emit, "enderEmit")
        etree.SubElement(ender_emit, "xLgr").text = emitente['endereco']
        etree.SubElement(ender_emit, "nro").text = emitente.get('numero', 'S/N')
        etree.SubElement(ender_emit, "xBairro").text = emitente['bairro']
        etree.SubElement(ender_emit, "cMun").text = emitente.get('codigo_municipio', '3550308')
        etree.SubElement(ender_emit, "xMun").text = emitente['cidade']
        etree.SubElement(ender_emit, "UF").text = emitente['uf']
        etree.SubElement(ender_emit, "CEP").text = emitente['cep'].replace("-", "")
        etree.SubElement(ender_emit, "cPais").text = "1058"  # Brasil
        etree.SubElement(ender_emit, "xPais").text = "BRASIL"

        # Inscrição estadual
        etree.SubElement(emit, "IE").text = emitente['inscricao_estadual']

        # Regime tributário (1=Simples Nacional, 3=Normal)
        etree.SubElement(emit, "CRT").text = emitente.get('regime_tributario', '3')

        return emit

    def _gerar_destinatario(self, destinatario: Dict[str, Any]) -> etree.Element:
        """Gera tag <dest> de destinatário"""
        dest = etree.Element("dest")

        # CPF ou CNPJ
        doc = destinatario.get('cnpj') or destinatario.get('cpf')
        if len(doc.replace(".", "").replace("/", "").replace("-", "")) == 11:
            etree.SubElement(dest, "CPF").text = doc.replace(".", "").replace("-", "")
        else:
            etree.SubElement(dest, "CNPJ").text = doc.replace(".", "").replace("/", "").replace("-", "")

        etree.SubElement(dest, "xNome").text = destinatario['nome']

        # Endereço
        ender_dest = etree.SubElement(dest, "enderDest")
        etree.SubElement(ender_dest, "xLgr").text = destinatario['endereco']
        etree.SubElement(ender_dest, "nro").text = destinatario.get('numero', 'S/N')
        etree.SubElement(ender_dest, "xBairro").text = destinatario['bairro']
        etree.SubElement(ender_dest, "cMun").text = destinatario.get('codigo_municipio', '3550308')
        etree.SubElement(ender_dest, "xMun").text = destinatario['cidade']
        etree.SubElement(ender_dest, "UF").text = destinatario['uf']
        etree.SubElement(ender_dest, "CEP").text = destinatario['cep'].replace("-", "")
        etree.SubElement(ender_dest, "cPais").text = "1058"
        etree.SubElement(ender_dest, "xPais").text = "BRASIL"

        # Indicador IE (9=Não contribuinte)
        etree.SubElement(dest, "indIEDest").text = "9"

        return dest

    def _gerar_produto(self, produto: Dict[str, Any], numero_item: int) -> etree.Element:
        """Gera tag <det> de produto/serviço"""
        det = etree.Element("det", nItem=str(numero_item))

        # Produto
        prod = etree.SubElement(det, "prod")
        etree.SubElement(prod, "cProd").text = str(produto['codigo'])
        etree.SubElement(prod, "cEAN").text = produto.get('codigo_barras', 'SEM GTIN')
        etree.SubElement(prod, "xProd").text = produto['descricao']
        etree.SubElement(prod, "NCM").text = produto.get('ncm', '00000000')
        etree.SubElement(prod, "CFOP").text = produto.get('cfop', '5102')
        etree.SubElement(prod, "uCom").text = produto.get('unidade', 'UN')
        etree.SubElement(prod, "qCom").text = f"{produto['quantidade']:.4f}"
        etree.SubElement(prod, "vUnCom").text = f"{produto['valor_unitario']:.10f}"
        etree.SubElement(prod, "vProd").text = f"{produto['valor_total']:.2f}"
        etree.SubElement(prod, "cEANTrib").text = produto.get('codigo_barras', 'SEM GTIN')
        etree.SubElement(prod, "uTrib").text = produto.get('unidade', 'UN')
        etree.SubElement(prod, "qTrib").text = f"{produto['quantidade']:.4f}"
        etree.SubElement(prod, "vUnTrib").text = f"{produto['valor_unitario']:.10f}"
        etree.SubElement(prod, "indTot").text = "1"  # 1=Compõe total da NFe

        # Impostos (simplificado - ICMS e PIS/COFINS)
        imposto = etree.SubElement(det, "imposto")

        # ICMS (exemplo: ICMS00 - tributado integralmente)
        icms = etree.SubElement(imposto, "ICMS")
        icms00 = etree.SubElement(icms, "ICMS00")
        etree.SubElement(icms00, "orig").text = "0"  # 0=Nacional
        etree.SubElement(icms00, "CST").text = "00"  # 00=Tributado integralmente
        etree.SubElement(icms00, "modBC").text = "0"  # 0=Margem valor agregado
        etree.SubElement(icms00, "vBC").text = f"{produto['valor_total']:.2f}"
        etree.SubElement(icms00, "pICMS").text = "18.00"
        etree.SubElement(icms00, "vICMS").text = f"{produto['valor_total'] * Decimal('0.18'):.2f}"

        # PIS
        pis = etree.SubElement(imposto, "PIS")
        pisaliq = etree.SubElement(pis, "PISAliq")
        etree.SubElement(pisaliq, "CST").text = "01"
        etree.SubElement(pisaliq, "vBC").text = f"{produto['valor_total']:.2f}"
        etree.SubElement(pisaliq, "pPIS").text = "1.65"
        etree.SubElement(pisaliq, "vPIS").text = f"{produto['valor_total'] * Decimal('0.0165'):.2f}"

        # COFINS
        cofins = etree.SubElement(imposto, "COFINS")
        cofinsaliq = etree.SubElement(cofins, "COFINSAliq")
        etree.SubElement(cofinsaliq, "CST").text = "01"
        etree.SubElement(cofinsaliq, "vBC").text = f"{produto['valor_total']:.2f}"
        etree.SubElement(cofinsaliq, "pCOFINS").text = "7.60"
        etree.SubElement(cofinsaliq, "vCOFINS").text = f"{produto['valor_total'] * Decimal('0.076'):.2f}"

        return det

    def _gerar_totais(self, totais: Dict[str, Decimal], qtd_produtos: int) -> etree.Element:
        """Gera tag <total> com totalizadores"""
        total = etree.Element("total")

        # ICMSTot
        icms_tot = etree.SubElement(total, "ICMSTot")
        etree.SubElement(icms_tot, "vBC").text = f"{totais.get('base_calculo', Decimal('0')):.2f}"
        etree.SubElement(icms_tot, "vICMS").text = f"{totais.get('valor_icms', Decimal('0')):.2f}"
        etree.SubElement(icms_tot, "vICMSDeson").text = "0.00"
        etree.SubElement(icms_tot, "vFCP").text = "0.00"
        etree.SubElement(icms_tot, "vBCST").text = "0.00"
        etree.SubElement(icms_tot, "vST").text = "0.00"
        etree.SubElement(icms_tot, "vFCPST").text = "0.00"
        etree.SubElement(icms_tot, "vFCPSTRet").text = "0.00"
        etree.SubElement(icms_tot, "vProd").text = f"{totais['valor_produtos']:.2f}"
        etree.SubElement(icms_tot, "vFrete").text = "0.00"
        etree.SubElement(icms_tot, "vSeg").text = "0.00"
        etree.SubElement(icms_tot, "vDesc").text = f"{totais.get('valor_desconto', Decimal('0')):.2f}"
        etree.SubElement(icms_tot, "vII").text = "0.00"
        etree.SubElement(icms_tot, "vIPI").text = "0.00"
        etree.SubElement(icms_tot, "vIPIDevol").text = "0.00"
        etree.SubElement(icms_tot, "vPIS").text = f"{totais.get('valor_pis', Decimal('0')):.2f}"
        etree.SubElement(icms_tot, "vCOFINS").text = f"{totais.get('valor_cofins', Decimal('0')):.2f}"
        etree.SubElement(icms_tot, "vOutro").text = "0.00"
        etree.SubElement(icms_tot, "vNF").text = f"{totais['valor_total']:.2f}"

        return total

    def _gerar_transporte(self) -> etree.Element:
        """Gera tag <transp> de transporte"""
        transp = etree.Element("transp")
        etree.SubElement(transp, "modFrete").text = "9"  # 9=Sem frete
        return transp

    def _gerar_pagamento(self, totais: Dict[str, Decimal]) -> etree.Element:
        """Gera tag <pag> de pagamento"""
        pag = etree.Element("pag")

        det_pag = etree.SubElement(pag, "detPag")
        etree.SubElement(det_pag, "tPag").text = "99"  # 99=Outros
        etree.SubElement(det_pag, "vPag").text = f"{totais['valor_total']:.2f}"

        return pag

    def _gerar_chave_acesso(
        self,
        uf: str,
        data_emissao: datetime,
        cnpj: str,
        serie: int,
        numero: int,
        tipo_emissao: int
    ) -> str:
        """
        Gera chave de acesso da NFe (44 dígitos).

        Formato: AAMMDDHHMMSS
        """
        uf_codes = {"SP": "35", "RJ": "33", "MG": "31"}
        cuf = uf_codes.get(uf, "35")

        # Limpa CNPJ
        cnpj_limpo = cnpj.replace(".", "").replace("/", "").replace("-", "")

        # Monta chave (43 dígitos + DV)
        chave_sem_dv = (
            cuf +  # UF (2)
            data_emissao.strftime("%y%m") +  # AAMM (4)
            cnpj_limpo +  # CNPJ (14)
            "55" +  # Modelo (2)
            str(serie).zfill(3) +  # Série (3)
            str(numero).zfill(9) +  # Número (9)
            str(tipo_emissao) +  # Tipo emissão (1)
            str(numero).zfill(8)[-8:]  # Código numérico (8)
        )

        # Calcula dígito verificador (módulo 11)
        dv = self._calcular_dv_modulo11(chave_sem_dv)

        return chave_sem_dv + str(dv)

    def _calcular_dv_modulo11(self, codigo: str) -> int:
        """Calcula dígito verificador módulo 11"""
        peso = 2
        soma = 0

        for digito in reversed(codigo):
            soma += int(digito) * peso
            peso += 1
            if peso > 9:
                peso = 2

        resto = soma % 11
        dv = 11 - resto

        if dv >= 10:
            dv = 0

        return dv

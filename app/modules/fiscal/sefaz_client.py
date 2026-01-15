"""
Arquivo: app/modules/fiscal/sefaz_client.py

Responsabilidade:
Cliente para comunicação com webservices da SEFAZ (Secretaria da Fazenda).
Implementa envio e consulta de NFe e NFSe.

Integrações:
- SEFAZ via SOAP/REST
- Certificado Digital A1
- XML de NFe/NFSe

Referências:
- Manual de Integração NFe versão 4.0
- Manual de Integração NFSe
- Layout XML conforme XSD da SEFAZ
"""
import os
import base64
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

import requests
from zeep import Client
from zeep.transports import Transport
from requests import Session
from lxml import etree


class SefazEnvironment(Enum):
    """Ambiente SEFAZ"""
    PRODUCAO = 1
    HOMOLOGACAO = 2


class SefazUF(Enum):
    """UFs com webservices próprios"""
    SP = "35"  # São Paulo
    RJ = "33"  # Rio de Janeiro
    MG = "31"  # Minas Gerais
    # ... outros estados


class SefazWebService(Enum):
    """Webservices disponíveis"""
    NFE_AUTORIZACAO = "NFeAutorizacao4"
    NFE_CONSULTA_PROTOCOLO = "NFeConsultaProtocolo4"
    NFE_STATUS_SERVICO = "NFeStatusServico4"
    NFE_INUTILIZACAO = "NFeInutilizacao4"
    NFE_EVENTO_CANCELAMENTO = "NFeRecepcaoEvento4"
    NFSE_ENVIO = "NFSeEnvioLote"
    NFSE_CONSULTA = "NFSeConsulta"


class SefazClient:
    """Cliente para comunicação com SEFAZ"""

    # URLs dos webservices (Homologação e Produção)
    WEBSERVICES_URLS = {
        SefazEnvironment.HOMOLOGACAO: {
            "SP": {
                SefazWebService.NFE_AUTORIZACAO: "https://homologacao.nfe.fazenda.sp.gov.br/ws/nfeautorizacao4.asmx?wsdl",
                SefazWebService.NFE_CONSULTA_PROTOCOLO: "https://homologacao.nfe.fazenda.sp.gov.br/ws/nfeconsultaprotocolo4.asmx?wsdl",
                SefazWebService.NFE_STATUS_SERVICO: "https://homologacao.nfe.fazenda.sp.gov.br/ws/nfestatusservico4.asmx?wsdl",
            }
        },
        SefazEnvironment.PRODUCAO: {
            "SP": {
                SefazWebService.NFE_AUTORIZACAO: "https://nfe.fazenda.sp.gov.br/ws/nfeautorizacao4.asmx?wsdl",
                SefazWebService.NFE_CONSULTA_PROTOCOLO: "https://nfe.fazenda.sp.gov.br/ws/nfeconsultaprotocolo4.asmx?wsdl",
                SefazWebService.NFE_STATUS_SERVICO: "https://nfe.fazenda.sp.gov.br/ws/nfestatusservico4.asmx?wsdl",
            }
        }
    }

    def __init__(
        self,
        certificate_path: str,
        certificate_password: str,
        environment: SefazEnvironment = SefazEnvironment.HOMOLOGACAO,
        uf: str = "SP"
    ):
        """
        Inicializa cliente SEFAZ.

        Args:
            certificate_path: Caminho para certificado A1 (.pfx)
            certificate_password: Senha do certificado
            environment: Ambiente (produção ou homologação)
            uf: UF do emitente
        """
        self.certificate_path = certificate_path
        self.certificate_password = certificate_password
        self.environment = environment
        self.uf = uf

        # Configura sessão com certificado
        self.session = Session()
        self.session.cert = self._extract_certificate()

        # Configura timeout
        self.timeout = 30

    def _extract_certificate(self) -> tuple[str, str]:
        """
        Extrai certificado e chave privada do arquivo .pfx.

        Returns:
            Tupla (cert_file, key_file) com caminhos dos arquivos temporários
        """
        from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PrivateFormat, NoEncryption
        import tempfile

        # Lê arquivo .pfx
        with open(self.certificate_path, 'rb') as f:
            pfx_data = f.read()

        # Extrai chave privada e certificado
        private_key, certificate, _ = pkcs12.load_key_and_certificates(
            pfx_data,
            self.certificate_password.encode()
        )

        # Salva em arquivos temporários
        cert_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pem')
        key_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pem')

        # Escreve certificado
        cert_file.write(certificate.public_bytes(Encoding.PEM))
        cert_file.close()

        # Escreve chave privada
        key_file.write(private_key.private_bytes(
            encoding=Encoding.PEM,
            format=PrivateFormat.PKCS8,
            encryption_algorithm=NoEncryption()
        ))
        key_file.close()

        return (cert_file.name, key_file.name)

    def _get_webservice_url(self, service: SefazWebService) -> str:
        """
        Obtém URL do webservice.

        Args:
            service: Tipo de webservice

        Returns:
            URL do webservice

        Raises:
            ValueError: Se webservice não disponível para UF
        """
        try:
            return self.WEBSERVICES_URLS[self.environment][self.uf][service]
        except KeyError:
            raise ValueError(f"Webservice {service.value} não disponível para UF {self.uf} em ambiente {self.environment.name}")

    def _create_soap_client(self, service: SefazWebService) -> Client:
        """
        Cria cliente SOAP para webservice.

        Args:
            service: Tipo de webservice

        Returns:
            Cliente SOAP configurado
        """
        url = self._get_webservice_url(service)
        transport = Transport(session=self.session, timeout=self.timeout)
        return Client(url, transport=transport)

    def verificar_status_servico(self) -> Dict[str, Any]:
        """
        Verifica status do serviço SEFAZ.

        Returns:
            Dicionário com status do serviço
        """
        client = self._create_soap_client(SefazWebService.NFE_STATUS_SERVICO)

        # Monta XML de consulta
        xml_consulta = f"""<?xml version="1.0" encoding="UTF-8"?>
<consStatServ versao="4.00" xmlns="http://www.portalfiscal.inf.br/nfe">
    <tpAmb>{self.environment.value}</tpAmb>
    <cUF>{SefazUF[self.uf].value}</cUF>
    <xServ>STATUS</xServ>
</consStatServ>"""

        # Envia consulta
        response = client.service.nfeStatusServicoNF(xml_consulta)

        # Parseia resposta
        return self._parse_status_response(response)

    def enviar_nfe(self, xml_nfe: str, lote: int = 1) -> Dict[str, Any]:
        """
        Envia NFe para autorização na SEFAZ.

        Args:
            xml_nfe: XML da NFe assinado
            lote: Número do lote (padrão: 1)

        Returns:
            Dicionário com resultado do envio
        """
        client = self._create_soap_client(SefazWebService.NFE_AUTORIZACAO)

        # Monta XML de envio
        xml_lote = f"""<?xml version="1.0" encoding="UTF-8"?>
<enviNFe versao="4.00" xmlns="http://www.portalfiscal.inf.br/nfe">
    <idLote>{lote}</idLote>
    <indSinc>1</indSinc>
    {xml_nfe}
</enviNFe>"""

        # Envia lote
        response = client.service.nfeAutorizacaoLote(xml_lote)

        # Parseia resposta
        return self._parse_authorization_response(response)

    def consultar_recibo(self, recibo: str) -> Dict[str, Any]:
        """
        Consulta processamento de lote pelo número do recibo.

        Args:
            recibo: Número do recibo retornado no envio

        Returns:
            Dicionário com resultado do processamento
        """
        client = self._create_soap_client(SefazWebService.NFE_CONSULTA_PROTOCOLO)

        # Monta XML de consulta
        xml_consulta = f"""<?xml version="1.0" encoding="UTF-8"?>
<consReciNFe versao="4.00" xmlns="http://www.portalfiscal.inf.br/nfe">
    <tpAmb>{self.environment.value}</tpAmb>
    <nRec>{recibo}</nRec>
</consReciNFe>"""

        # Consulta recibo
        response = client.service.nfeRetAutorizacao(xml_consulta)

        # Parseia resposta
        return self._parse_receipt_response(response)

    def consultar_nfe(self, chave: str) -> Dict[str, Any]:
        """
        Consulta situação de NFe pela chave de acesso.

        Args:
            chave: Chave de acesso da NFe (44 dígitos)

        Returns:
            Dicionário com situação da NFe
        """
        client = self._create_soap_client(SefazWebService.NFE_CONSULTA_PROTOCOLO)

        # Monta XML de consulta
        xml_consulta = f"""<?xml version="1.0" encoding="UTF-8"?>
<consSitNFe versao="4.00" xmlns="http://www.portalfiscal.inf.br/nfe">
    <tpAmb>{self.environment.value}</tpAmb>
    <xServ>CONSULTAR</xServ>
    <chNFe>{chave}</chNFe>
</consSitNFe>"""

        # Consulta NFe
        response = client.service.nfeConsultaNF(xml_consulta)

        # Parseia resposta
        return self._parse_query_response(response)

    def cancelar_nfe(
        self,
        chave: str,
        protocolo: str,
        justificativa: str,
        cnpj: str,
        sequencial: int = 1
    ) -> Dict[str, Any]:
        """
        Cancela NFe autorizada.

        Args:
            chave: Chave de acesso da NFe (44 dígitos)
            protocolo: Número do protocolo de autorização
            justificativa: Justificativa do cancelamento (mín 15 caracteres)
            cnpj: CNPJ do emitente
            sequencial: Número sequencial do evento

        Returns:
            Dicionário com resultado do cancelamento
        """
        if len(justificativa) < 15:
            raise ValueError("Justificativa deve ter no mínimo 15 caracteres")

        client = self._create_soap_client(SefazWebService.NFE_EVENTO_CANCELAMENTO)

        # Monta XML de evento de cancelamento
        xml_evento = f"""<?xml version="1.0" encoding="UTF-8"?>
<envEvento versao="1.00" xmlns="http://www.portalfiscal.inf.br/nfe">
    <idLote>1</idLote>
    <evento versao="1.00">
        <infEvento Id="ID110111{chave}{str(sequencial).zfill(2)}">
            <cOrgao>{SefazUF[self.uf].value}</cOrgao>
            <tpAmb>{self.environment.value}</tpAmb>
            <CNPJ>{cnpj}</CNPJ>
            <chNFe>{chave}</chNFe>
            <dhEvento>{datetime.now().isoformat()}</dhEvento>
            <tpEvento>110111</tpEvento>
            <nSeqEvento>{sequencial}</nSeqEvento>
            <verEvento>1.00</verEvento>
            <detEvento versao="1.00">
                <descEvento>Cancelamento</descEvento>
                <nProt>{protocolo}</nProt>
                <xJust>{justificativa}</xJust>
            </detEvento>
        </infEvento>
    </evento>
</envEvento>"""

        # Envia evento
        response = client.service.nfeRecepcaoEvento(xml_evento)

        # Parseia resposta
        return self._parse_event_response(response)

    def _parse_status_response(self, response: str) -> Dict[str, Any]:
        """Parseia resposta de status do serviço"""
        root = etree.fromstring(response.encode())
        ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}

        return {
            'status_code': root.find('.//nfe:cStat', ns).text,
            'status_message': root.find('.//nfe:xMotivo', ns).text,
            'uf': root.find('.//nfe:cUF', ns).text,
            'ambiente': root.find('.//nfe:tpAmb', ns).text,
            'timestamp': datetime.now().isoformat()
        }

    def _parse_authorization_response(self, response: str) -> Dict[str, Any]:
        """Parseia resposta de autorização"""
        root = etree.fromstring(response.encode())
        ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}

        result = {
            'status_code': root.find('.//nfe:cStat', ns).text,
            'status_message': root.find('.//nfe:xMotivo', ns).text
        }

        # Se processamento assíncrono, retorna número do recibo
        recibo = root.find('.//nfe:nRec', ns)
        if recibo is not None:
            result['recibo'] = recibo.text

        # Se processamento síncrono, retorna protocolo
        protocolo = root.find('.//nfe:nProt', ns)
        if protocolo is not None:
            result['protocolo'] = protocolo.text

        return result

    def _parse_receipt_response(self, response: str) -> Dict[str, Any]:
        """Parseia resposta de consulta de recibo"""
        root = etree.fromstring(response.encode())
        ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}

        result = {
            'status_code': root.find('.//nfe:cStat', ns).text,
            'status_message': root.find('.//nfe:xMotivo', ns).text
        }

        # Protocolo de autorização
        protocolo = root.find('.//nfe:nProt', ns)
        if protocolo is not None:
            result['protocolo'] = protocolo.text

        # Chave de acesso
        chave = root.find('.//nfe:chNFe', ns)
        if chave is not None:
            result['chave'] = chave.text

        return result

    def _parse_query_response(self, response: str) -> Dict[str, Any]:
        """Parseia resposta de consulta de NFe"""
        root = etree.fromstring(response.encode())
        ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}

        return {
            'status_code': root.find('.//nfe:cStat', ns).text,
            'status_message': root.find('.//nfe:xMotivo', ns).text,
            'protocolo': root.find('.//nfe:nProt', ns).text if root.find('.//nfe:nProt', ns) is not None else None,
            'situacao': root.find('.//nfe:cSitNFe', ns).text if root.find('.//nfe:cSitNFe', ns) is not None else None
        }

    def _parse_event_response(self, response: str) -> Dict[str, Any]:
        """Parseia resposta de evento (cancelamento, carta de correção, etc)"""
        root = etree.fromstring(response.encode())
        ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}

        return {
            'status_code': root.find('.//nfe:cStat', ns).text,
            'status_message': root.find('.//nfe:xMotivo', ns).text,
            'protocolo': root.find('.//nfe:nProt', ns).text if root.find('.//nfe:nProt', ns) is not None else None
        }

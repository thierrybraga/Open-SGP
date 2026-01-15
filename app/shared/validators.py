"""
Arquivo: app/shared/validators.py

Responsabilidade:
Validadores de dados brasileiros (CPF, CNPJ, Email, Telefone).
Implementa validação real conforme padrões oficiais.

Integrações:
- validate_docbr para CPF/CNPJ
- re para regex patterns
"""
import re
from validate_docbr import CPF, CNPJ
from typing import Optional


class DocumentValidator:
    """Validador de documentos brasileiros (CPF e CNPJ)"""

    @staticmethod
    def validate_cpf(cpf: str) -> bool:
        """
        Valida CPF brasileiro.

        Args:
            cpf: CPF no formato XXX.XXX.XXX-XX ou apenas números

        Returns:
            True se CPF válido, False caso contrário
        """
        if not cpf:
            return False

        cpf_validator = CPF()
        cpf_clean = re.sub(r'[^0-9]', '', cpf)

        # CPF deve ter exatamente 11 dígitos
        if len(cpf_clean) != 11:
            return False

        return cpf_validator.validate(cpf_clean)

    @staticmethod
    def validate_cnpj(cnpj: str) -> bool:
        """
        Valida CNPJ brasileiro.

        Args:
            cnpj: CNPJ no formato XX.XXX.XXX/XXXX-XX ou apenas números

        Returns:
            True se CNPJ válido, False caso contrário
        """
        if not cnpj:
            return False

        cnpj_validator = CNPJ()
        cnpj_clean = re.sub(r'[^0-9]', '', cnpj)

        # CNPJ deve ter exatamente 14 dígitos
        if len(cnpj_clean) != 14:
            return False

        return cnpj_validator.validate(cnpj_clean)

    @staticmethod
    def format_cpf(cpf: str) -> Optional[str]:
        """
        Formata CPF no padrão XXX.XXX.XXX-XX.

        Args:
            cpf: CPF apenas com números

        Returns:
            CPF formatado ou None se inválido
        """
        cpf_clean = re.sub(r'[^0-9]', '', cpf)

        if len(cpf_clean) != 11:
            return None

        return f"{cpf_clean[:3]}.{cpf_clean[3:6]}.{cpf_clean[6:9]}-{cpf_clean[9:]}"

    @staticmethod
    def format_cnpj(cnpj: str) -> Optional[str]:
        """
        Formata CNPJ no padrão XX.XXX.XXX/XXXX-XX.

        Args:
            cnpj: CNPJ apenas com números

        Returns:
            CNPJ formatado ou None se inválido
        """
        cnpj_clean = re.sub(r'[^0-9]', '', cnpj)

        if len(cnpj_clean) != 14:
            return None

        return f"{cnpj_clean[:2]}.{cnpj_clean[2:5]}.{cnpj_clean[5:8]}/{cnpj_clean[8:12]}-{cnpj_clean[12:]}"


class EmailValidator:
    """Validador de endereços de email"""

    # RFC 5322 Official Standard
    EMAIL_PATTERN = re.compile(
        r'^[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'
    )

    @staticmethod
    def validate(email: str) -> bool:
        """
        Valida endereço de email.

        Args:
            email: Endereço de email

        Returns:
            True se email válido, False caso contrário
        """
        if not email:
            return False

        # Remove espaços
        email = email.strip()

        # Verifica comprimento
        if len(email) > 254:
            return False

        # Verifica pattern
        if not EmailValidator.EMAIL_PATTERN.match(email):
            return False

        # Verifica parte local (antes do @)
        local_part = email.split('@')[0]
        if len(local_part) > 64:
            return False

        return True

    @staticmethod
    def normalize(email: str) -> str:
        """
        Normaliza email (lowercase, remove espaços).

        Args:
            email: Endereço de email

        Returns:
            Email normalizado
        """
        return email.strip().lower()


class PhoneValidator:
    """Validador de telefones brasileiros"""

    # Padrões aceitos:
    # (11) 98765-4321
    # (11) 3456-7890
    # 11987654321
    # 1134567890
    PHONE_PATTERN = re.compile(r'^\(?([1-9]{2})\)?[ ]?([9]?[0-9]{4})[-]?([0-9]{4})$')

    @staticmethod
    def validate(phone: str) -> bool:
        """
        Valida telefone brasileiro.

        Args:
            phone: Telefone no formato (XX) XXXXX-XXXX ou (XX) XXXX-XXXX

        Returns:
            True se telefone válido, False caso contrário
        """
        if not phone:
            return False

        phone_clean = re.sub(r'[^0-9]', '', phone)

        # Telefone deve ter 10 ou 11 dígitos (com DDD)
        if len(phone_clean) not in [10, 11]:
            return False

        # DDD deve ser válido (11-99)
        ddd = int(phone_clean[:2])
        if ddd < 11 or ddd > 99:
            return False

        # Se tiver 11 dígitos, o terceiro deve ser 9 (celular)
        if len(phone_clean) == 11 and phone_clean[2] != '9':
            return False

        return True

    @staticmethod
    def format(phone: str) -> Optional[str]:
        """
        Formata telefone no padrão (XX) XXXXX-XXXX ou (XX) XXXX-XXXX.

        Args:
            phone: Telefone apenas com números

        Returns:
            Telefone formatado ou None se inválido
        """
        phone_clean = re.sub(r'[^0-9]', '', phone)

        if len(phone_clean) == 11:
            # Celular: (XX) 9XXXX-XXXX
            return f"({phone_clean[:2]}) {phone_clean[2:7]}-{phone_clean[7:]}"
        elif len(phone_clean) == 10:
            # Fixo: (XX) XXXX-XXXX
            return f"({phone_clean[:2]}) {phone_clean[2:6]}-{phone_clean[6:]}"
        else:
            return None

    @staticmethod
    def extract_ddd(phone: str) -> Optional[str]:
        """
        Extrai DDD do telefone.

        Args:
            phone: Telefone completo

        Returns:
            DDD (2 dígitos) ou None se inválido
        """
        phone_clean = re.sub(r'[^0-9]', '', phone)

        if len(phone_clean) in [10, 11]:
            return phone_clean[:2]

        return None


class CEPValidator:
    """Validador de CEP brasileiro"""

    CEP_PATTERN = re.compile(r'^[0-9]{5}-?[0-9]{3}$')

    @staticmethod
    def validate(cep: str) -> bool:
        """
        Valida CEP brasileiro.

        Args:
            cep: CEP no formato XXXXX-XXX ou apenas números

        Returns:
            True se CEP válido, False caso contrário
        """
        if not cep:
            return False

        cep_clean = re.sub(r'[^0-9]', '', cep)

        # CEP deve ter exatamente 8 dígitos
        if len(cep_clean) != 8:
            return False

        # CEP não pode ser 00000-000
        if cep_clean == '00000000':
            return False

        return True

    @staticmethod
    def format(cep: str) -> Optional[str]:
        """
        Formata CEP no padrão XXXXX-XXX.

        Args:
            cep: CEP apenas com números

        Returns:
            CEP formatado ou None se inválido
        """
        cep_clean = re.sub(r'[^0-9]', '', cep)

        if len(cep_clean) != 8:
            return None

        return f"{cep_clean[:5]}-{cep_clean[5:]}"


# Funções auxiliares para uso direto
def validate_cpf(cpf: str) -> bool:
    """Valida CPF"""
    return DocumentValidator.validate_cpf(cpf)


def validate_cnpj(cnpj: str) -> bool:
    """Valida CNPJ"""
    return DocumentValidator.validate_cnpj(cnpj)


def validate_email(email: str) -> bool:
    """Valida email"""
    return EmailValidator.validate(email)


def validate_phone(phone: str) -> bool:
    """Valida telefone"""
    return PhoneValidator.validate(phone)


def validate_cep(cep: str) -> bool:
    """Valida CEP"""
    return CEPValidator.validate(cep)

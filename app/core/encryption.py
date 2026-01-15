"""
Arquivo: app/core/encryption.py

Responsabilidade:
Módulo de criptografia centralizado usando Fernet (simétrico).
Usado para criptografar/descriptografar senhas e credenciais sensíveis.

Integrações:
- cryptography.fernet
- core.config

Segurança:
- Fernet usa AES 128 em modo CBC com HMAC para autenticação
- Muito mais seguro que base64
- Chave deve estar em variável de ambiente
"""

import os
import base64
from cryptography.fernet import Fernet, InvalidToken
from .config import settings


class EncryptionError(Exception):
    """Erro genérico de criptografia"""
    pass


class EncryptionKeyNotFound(EncryptionError):
    """Chave de criptografia não configurada"""
    pass


def get_encryption_key() -> bytes:
    """
    Obtém chave de criptografia das variáveis de ambiente.

    Returns:
        bytes: Chave Fernet (32 bytes URL-safe base64-encoded)

    Raises:
        EncryptionKeyNotFound: Se ENCRYPTION_KEY não estiver configurada

    Note:
        Para gerar uma nova chave:
        python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    """
    key = os.getenv("ENCRYPTION_KEY")

    if not key:
        # Em desenvolvimento, gera chave temporária (NUNCA fazer em produção!)
        if settings.is_development() or settings.is_testing():
            # Chave fixa para desenvolvimento (NÃO usar em produção)
            key = "development-key-DO-NOT-USE-IN-PRODUCTION-" + "=" * 12
            key = base64.urlsafe_b64encode(key.encode()[:32]).decode()
        else:
            raise EncryptionKeyNotFound(
                "ENCRYPTION_KEY not set in environment. "
                "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
            )

    return key.encode() if isinstance(key, str) else key


def encrypt(plaintext: str) -> str:
    """
    Criptografa uma string usando Fernet.

    Args:
        plaintext: Texto em claro a ser criptografado

    Returns:
        str: Texto criptografado (base64)

    Example:
        >>> encrypted = encrypt("minha-senha-secreta")
        >>> print(encrypted)
        'gAAAAABhk...'
    """
    if not plaintext:
        return ""

    try:
        key = get_encryption_key()
        f = Fernet(key)
        encrypted_bytes = f.encrypt(plaintext.encode())
        return encrypted_bytes.decode()
    except Exception as e:
        raise EncryptionError(f"Failed to encrypt: {str(e)}")


def decrypt(ciphertext: str) -> str:
    """
    Descriptografa uma string criptografada com Fernet.

    Args:
        ciphertext: Texto criptografado (base64)

    Returns:
        str: Texto original em claro

    Raises:
        EncryptionError: Se falhar ao descriptografar

    Example:
        >>> decrypted = decrypt("gAAAAABhk...")
        >>> print(decrypted)
        'minha-senha-secreta'
    """
    if not ciphertext:
        return ""

    try:
        key = get_encryption_key()
        f = Fernet(key)
        decrypted_bytes = f.decrypt(ciphertext.encode())
        return decrypted_bytes.decode()
    except InvalidToken:
        raise EncryptionError(
            "Failed to decrypt: Invalid token. "
            "This usually means the ENCRYPTION_KEY has changed or the data is corrupted."
        )
    except Exception as e:
        raise EncryptionError(f"Failed to decrypt: {str(e)}")


def is_encrypted(value: str) -> bool:
    """
    Verifica se um valor parece estar criptografado com Fernet.

    Args:
        value: Valor a verificar

    Returns:
        bool: True se parece estar criptografado

    Note:
        Tokens Fernet começam com 'gAAAAA' após base64
    """
    if not value:
        return False

    # Fernet tokens sempre começam com o timestamp + random bytes
    # Após base64, geralmente começam com 'gAAAAA'
    return value.startswith("gAAAAA")


def migrate_from_base64(old_value: str) -> str:
    """
    Migra credencial de base64 (inseguro) para Fernet (seguro).

    Args:
        old_value: Valor em base64

    Returns:
        str: Valor criptografado com Fernet

    Example:
        >>> # Migrar senha antiga
        >>> old_encrypted = "cGFzc3dvcmQxMjM="  # base64 de "password123"
        >>> new_encrypted = migrate_from_base64(old_encrypted)
    """
    try:
        # Tentar decodificar base64
        import base64 as b64
        decrypted = b64.b64decode(old_value.encode()).decode()

        # Re-criptografar com Fernet
        return encrypt(decrypted)
    except Exception:
        # Se falhar, assume que já está em Fernet ou é texto plano
        if is_encrypted(old_value):
            return old_value
        else:
            # Texto plano, criptografar
            return encrypt(old_value)


# Funções de conveniência para tipos específicos

def encrypt_password(password: str) -> str:
    """
    Criptografa uma senha.

    Alias para encrypt() com nome mais descritivo.
    """
    return encrypt(password)


def decrypt_password(encrypted_password: str) -> str:
    """
    Descriptografa uma senha.

    Alias para decrypt() com nome mais descritivo.
    """
    return decrypt(encrypted_password)


def encrypt_api_key(api_key: str) -> str:
    """
    Criptografa uma API key.

    Alias para encrypt() com nome mais descritivo.
    """
    return encrypt(api_key)


def decrypt_api_key(encrypted_api_key: str) -> str:
    """
    Descriptografa uma API key.

    Alias para decrypt() com nome mais descritivo.
    """
    return decrypt(encrypted_api_key)

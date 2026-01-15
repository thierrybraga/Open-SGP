"""
Arquivo: app/modules/auth/twofa.py

Responsabilidade:
Autenticação de dois fatores (2FA) usando TOTP.
"""

import pyotp
import qrcode
import io
import base64
from typing import Optional


class TwoFactorAuth:
    """Gerenciador de autenticação de dois fatores"""

    @staticmethod
    def generate_secret() -> str:
        """Gera um novo secret para TOTP"""
        return pyotp.random_base32()

    @staticmethod
    def get_totp_uri(secret: str, email: str, issuer: str = "ISP ERP") -> str:
        """
        Gera URI para configuração de TOTP.
        Usado para gerar QR Code.
        """
        return pyotp.totp.TOTP(secret).provisioning_uri(
            name=email,
            issuer_name=issuer
        )

    @staticmethod
    def generate_qr_code(secret: str, email: str, issuer: str = "ISP ERP") -> str:
        """
        Gera QR Code em base64 para o usuário escanear.

        Returns:
            String base64 da imagem PNG do QR Code
        """
        uri = TwoFactorAuth.get_totp_uri(secret, email, issuer)

        # Gera QR Code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Converte para base64
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        img_base64 = base64.b64encode(buf.getvalue()).decode()

        return f"data:image/png;base64,{img_base64}"

    @staticmethod
    def verify_token(secret: str, token: str) -> bool:
        """
        Verifica se o token TOTP é válido.

        Args:
            secret: Secret do usuário
            token: Token de 6 dígitos fornecido pelo usuário

        Returns:
            True se o token é válido, False caso contrário
        """
        if not token or len(token) != 6 or not token.isdigit():
            return False

        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)  # Aceita 1 período antes/depois (30s)

    @staticmethod
    def generate_backup_codes(count: int = 10) -> list[str]:
        """
        Gera códigos de backup para recuperação.
        Cada código pode ser usado uma única vez.

        Returns:
            Lista de códigos de backup (formato: XXXX-XXXX-XXXX)
        """
        import secrets
        codes = []
        for _ in range(count):
            # Gera código de 12 dígitos (3 grupos de 4)
            code = f"{secrets.randbelow(10000):04d}-{secrets.randbelow(10000):04d}-{secrets.randbelow(10000):04d}"
            codes.append(code)
        return codes

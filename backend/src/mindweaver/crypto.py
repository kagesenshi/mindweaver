"""
Cryptographic utilities for encrypting and decrypting sensitive data.

This module provides Fernet-based encryption for passwords and other sensitive
data stored in the database.
"""

from cryptography.fernet import Fernet, InvalidToken
from mindweaver.config import settings
from typing import Optional


class EncryptionError(Exception):
    """Raised when encryption or decryption operations fail."""

    pass


def generate_fernet_key() -> str:
    """
    Generate a new Fernet encryption key.

    Returns:
        str: A new Fernet key encoded as a base64 string

    Example:
        >>> key = generate_fernet_key()
        >>> print(key)
        'gAAAAABh...'
    """
    return Fernet.generate_key().decode("utf-8")


def _get_fernet_instance(key: Optional[str] = None) -> Fernet:
    """
    Get a Fernet instance using the provided key or the configured key.

    Args:
        key: Optional encryption key. If not provided, uses settings.fernet_key

    Returns:
        Fernet: A Fernet instance for encryption/decryption

    Raises:
        EncryptionError: If no key is provided or configured
    """
    encryption_key = key or settings.fernet_key
    if not encryption_key:
        raise EncryptionError(
            "No encryption key configured. Set MINDWEAVER_FERNET_KEY environment variable."
        )

    try:
        return Fernet(encryption_key.encode("utf-8"))
    except Exception as e:
        raise EncryptionError(f"Invalid encryption key: {str(e)}")


def encrypt_password(password: str, key: Optional[str] = None) -> str:
    """
    Encrypt a password using Fernet symmetric encryption.

    Args:
        password: The plaintext password to encrypt
        key: Optional encryption key. If not provided, uses settings.fernet_key

    Returns:
        str: The encrypted password as a base64-encoded string

    Raises:
        EncryptionError: If encryption fails

    Example:
        >>> encrypted = encrypt_password("my_secret_password")
        >>> print(encrypted)
        'gAAAAABh...'
    """
    if not password:
        return ""

    try:
        fernet = _get_fernet_instance(key)
        encrypted_bytes = fernet.encrypt(password.encode("utf-8"))
        return encrypted_bytes.decode("utf-8")
    except Exception as e:
        raise EncryptionError(f"Failed to encrypt password: {str(e)}")


def decrypt_password(encrypted_password: str, key: Optional[str] = None) -> str:
    """
    Decrypt a password that was encrypted with Fernet.

    Args:
        encrypted_password: The encrypted password as a base64-encoded string
        key: Optional encryption key. If not provided, uses settings.fernet_key

    Returns:
        str: The decrypted plaintext password

    Raises:
        EncryptionError: If decryption fails (e.g., wrong key, corrupted data)

    Example:
        >>> decrypted = decrypt_password("gAAAAABh...")
        >>> print(decrypted)
        'my_secret_password'
    """
    if not encrypted_password:
        return ""

    try:
        fernet = _get_fernet_instance(key)
        decrypted_bytes = fernet.decrypt(encrypted_password.encode("utf-8"))
        return decrypted_bytes.decode("utf-8")
    except InvalidToken:
        raise EncryptionError(
            "Failed to decrypt password: Invalid token or wrong encryption key"
        )
    except Exception as e:
        raise EncryptionError(f"Failed to decrypt password: {str(e)}")


def rotate_key(old_key: str, new_key: str, encrypted_password: str) -> str:
    """
    Re-encrypt a password with a new encryption key.

    This is used during key rotation to migrate encrypted data from an old key
    to a new key without exposing the plaintext password.

    Args:
        old_key: The current encryption key used to decrypt the password
        new_key: The new encryption key to use for re-encryption
        encrypted_password: The password encrypted with the old key

    Returns:
        str: The password re-encrypted with the new key

    Raises:
        EncryptionError: If decryption or re-encryption fails

    Example:
        >>> old_encrypted = encrypt_password("secret", old_key)
        >>> new_encrypted = rotate_key(old_key, new_key, old_encrypted)
        >>> decrypted = decrypt_password(new_encrypted, new_key)
        >>> print(decrypted)
        'secret'
    """
    if not encrypted_password:
        return ""

    try:
        # Decrypt with old key
        plaintext = decrypt_password(encrypted_password, old_key)
        # Re-encrypt with new key
        return encrypt_password(plaintext, new_key)
    except Exception as e:
        raise EncryptionError(f"Failed to rotate encryption key: {str(e)}")

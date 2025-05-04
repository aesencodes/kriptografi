from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Hash import SHA256
import base64
from typing import Union

def generate_keys():
    key = RSA.generate(2048)
    return key.export_key(), key.publickey().export_key()

def encrypt_message(message: str, public_key: bytes, as_bytes=False) -> Union[str, bytes]:
    """Encrypt message using RSA-OAEP with SHA-256"""
    try:
        if not isinstance(message, str):
            raise ValueError("Message must be a string")
            
        if len(message) > 190:
            raise ValueError("Message too long for RSA 2048 with OAEP padding")
            
        pub_key = RSA.import_key(public_key)
        cipher = PKCS1_OAEP.new(pub_key, hashAlgo=SHA256.new())
        encrypted = cipher.encrypt(message.encode('utf-8'))

        if as_bytes:
            return encrypted
        return base64.b64encode(encrypted).decode('utf-8')
    except Exception as e:
        raise ValueError(f"Encryption failed: {str(e)}")


def decrypt_message(encrypted_b64: str, private_key: bytes) -> str:
    priv_key = RSA.import_key(private_key)
    cipher = PKCS1_OAEP.new(priv_key, hashAlgo=SHA256.new())
    decrypted = cipher.decrypt(base64.b64decode(encrypted_b64))
    return decrypted.decode('utf-8')

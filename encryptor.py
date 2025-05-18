from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Hash import SHA256
import base64
from typing import Union

def generate_keys():
    """Generate RSA key pair 2048-bit"""
    key = RSA.generate(2048)
    return key.export_key(), key.publickey().export_key()

def encrypt_message(message: str, public_key: bytes, as_bytes=False) -> Union[str, bytes]:
    """Enkripsi pesan menggunakan RSA-OAEP dengan SHA-256
    
    Args:
        message: Pesan teks yang akan dienkripsi
        public_key: Kunci publik dalam format bytes
        as_bytes: Jika True, kembalikan hasil dalam bytes, jika False kembalikan base64 string
    
    Returns:
        Hasil enkripsi dalam format bytes atau base64 string
    
    Raises:
        ValueError: Jika pesan terlalu panjang atau terjadi error enkripsi
    """
    try:
        if not isinstance(message, str):
            raise ValueError("Pesan harus berupa string")
            
        if len(message) > 190:
            raise ValueError("Pesan terlalu panjang untuk RSA 2048 dengan padding OAEP")
            
        pub_key = RSA.import_key(public_key)
        cipher = PKCS1_OAEP.new(pub_key, hashAlgo=SHA256)
        encrypted = cipher.encrypt(message.encode('utf-8'))

        return encrypted if as_bytes else base64.b64encode(encrypted).decode('utf-8')
    except Exception as e:
        raise ValueError(f"Gagal enkripsi: {str(e)}")

def decrypt_message(encrypted_b64: str, private_key: bytes) -> str:
    """Dekripsi pesan menggunakan RSA-OAEP
    
    Args:
        encrypted_b64: Pesan terenkripsi dalam format base64
        private_key: Kunci privat dalam format bytes
    
    Returns:
        Pesan asli yang sudah didekripsi
    
    Raises:
        ValueError: Jika terjadi error dekripsi
    """
    try:
        priv_key = RSA.import_key(private_key)
        cipher = PKCS1_OAEP.new(priv_key, hashAlgo=SHA256)
        decrypted = cipher.decrypt(base64.b64decode(encrypted_b64))
        return decrypted.decode('utf-8')
    except Exception as e:
        raise ValueError(f"Gagal dekripsi: {str(e)}")
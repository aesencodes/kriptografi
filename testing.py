import os
import time
import numpy as np
import soundfile as sf
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from scipy.fftpack import dct, idct

# ======== RSA Functions ========
def generate_rsa_keys():
    key = RSA.generate(2048)
    return key.publickey(), key

def encrypt_rsa(data_bytes, public_key):
    cipher = PKCS1_OAEP.new(public_key)
    return cipher.encrypt(data_bytes)

def decrypt_rsa(cipher_bytes, private_key):
    cipher = PKCS1_OAEP.new(private_key)
    return cipher.decrypt(cipher_bytes)

# ======== Steganografi DCT ========
def embed_data_dct(audio_path, output_path, data_bytes, bits_per_coeff=1):
    audio, sr = sf.read(audio_path)
    if audio.ndim > 1:
        audio = audio[:,0]

    audio = audio.astype(np.float64)
    audio_dct = dct(audio, norm='ortho')

    total_bits = len(data_bytes) * 8
    start_index = 1000  # Lewati frekuensi rendah
    end_index = start_index + total_bits
    if end_index > len(audio_dct):
        raise ValueError("Data terlalu besar untuk disisipkan pada audio ini")

    # Konversi data_bytes ke bit array
    data_bits = []
    for byte in data_bytes:
        bits = bin(byte)[2:].rjust(8, '0')
        data_bits.extend([int(b) for b in bits])

    # Embed bit halus ke koefisien DCT (dengan gangguan minimum)
    for i, bit in enumerate(data_bits):
        idx = start_index + i
        coeff = audio_dct[idx]
        if coeff == 0:
            coeff = 1e-10  # Hindari pembulatan 0

        if bit == 1:
            coeff += 0.0001 if coeff > 0 else -0.0001
        else:
            coeff -= 0.0001 if coeff > 0 else -0.0001

        audio_dct[idx] = coeff

    stego_audio = idct(audio_dct, norm='ortho')

    # Simpan hasil steganografi
    if np.issubdtype(audio.dtype, np.floating):
        stego_audio = np.clip(stego_audio, -1.0, 1.0)
        sf.write(output_path, stego_audio.astype(np.float32), sr)
    else:
        stego_audio = np.clip(stego_audio, -32768, 32767)
        sf.write(output_path, stego_audio.astype(np.int16), sr)

    return True

def extract_data_dct(stego_path, data_length):
    audio, sr = sf.read(stego_path)
    if audio.ndim > 1:
        audio = audio[:,0]

    audio = audio.astype(np.float64)
    audio_dct = dct(audio, norm='ortho')

    total_bits = data_length * 8
    start_index = 1000
    bits = []

    for i in range(total_bits):
        idx = start_index + i
        coeff = audio_dct[idx]
        bits.append(1 if coeff > 0 else 0)

    data_bytes = bytearray()
    for i in range(0, len(bits), 8):
        byte = 0
        for j in range(8):
            byte = (byte << 1) | bits[i + j]
        data_bytes.append(byte)

    return bytes(data_bytes)

# ======== Pengujian ========
def avalanche_effect_test(public_key):
    original = b'Hello World!'
    modified = bytearray(original)
    modified[0] ^= 0x01
    
    cipher1 = encrypt_rsa(original, public_key)
    cipher2 = encrypt_rsa(modified, public_key)
    
    diff_bits = sum(bin(a ^ b).count('1') for a, b in zip(cipher1, cipher2))
    total_bits = len(cipher1) * 8
    return (diff_bits / total_bits) * 100

def timing_test(data, pub_key, priv_key):
    start = time.time()
    encrypted = encrypt_rsa(data, pub_key)
    enc_time = time.time() - start
    
    start = time.time()
    decrypted = decrypt_rsa(encrypted, priv_key)
    dec_time = time.time() - start
    
    return enc_time, dec_time

def snr_test(original_audio_path, stego_audio_path):
    try:
        original, sr1 = sf.read(original_audio_path)
        stego, sr2 = sf.read(stego_audio_path)
        if sr1 != sr2:
            raise ValueError("Sample rate berbeda antara original dan stego")
        
        if original.ndim > 1:
            original = original[:,0]
        if stego.ndim > 1:
            stego = stego[:,0]
        
        min_len = min(len(original), len(stego))
        original = original[:min_len].astype(np.float64)
        stego = stego[:min_len].astype(np.float64)
        
        noise = original - stego
        signal_power = np.mean(original**2)
        noise_power = np.mean(noise**2)
        if noise_power == 0:
            return float('inf')
        
        snr = 10 * np.log10(signal_power / noise_power)
        return snr
    except Exception:
        return None

def max_capacity_test(audio_path, bits_per_coeff=1):
    audio, _ = sf.read(audio_path)
    if audio.ndim > 1:
        audio = audio[:,0]
    length = len(audio)
    capacity_bits = (length - 1000) * bits_per_coeff
    capacity_bytes = capacity_bits // 8
    return capacity_bytes

# ======== Eksekusi Batch Pengujian ========
def run_tests_on_all_audio(audio_folder, data_path):
    with open(data_path, 'rb') as f:
        data_bytes = f.read()

    pub_key, priv_key = generate_rsa_keys()
    audio_files = [f for f in os.listdir(audio_folder) if f.lower().endswith(('.wav', '.flac'))]

    print("=== HASIL PENGUJIAN BATCH AUDIO ===\n")
    for audio_file in audio_files:
        print(f'\n--- Menguji: {audio_file} ---')
        full_path = os.path.join(audio_folder, audio_file)

        try:
            avalanche = avalanche_effect_test(pub_key)
            enc_time, dec_time = timing_test(data_bytes, pub_key, priv_key)

            encrypted_data = encrypt_rsa(data_bytes, pub_key)
            embed_data_dct(full_path, 'temp_stego.wav', encrypted_data)

            snr = snr_test(full_path, 'temp_stego.wav')
            max_cap = max_capacity_test(full_path, bits_per_coeff=1)

            print(f'Avalanche Effect       : {avalanche:.2f}%')
            print(f'Waktu Enkripsi         : {enc_time:.4f} detik')
            print(f'Waktu Dekripsi         : {dec_time:.4f} detik')
            print(f'SNR Audio              : {snr:.2f} dB' if snr is not None else "SNR Audio              : Gagal dihitung")
            print(f'Kapasitas Maksimum DCT : {max_cap} byte')
        except Exception as e:
            print(f'[ERROR] Gagal menguji {audio_file}: {e}')

# ======== Main Entry Point ========
if __name__ == '__main__':
    run_tests_on_all_audio('audio_files', 'plainteks3.txt')

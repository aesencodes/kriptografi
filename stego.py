import numpy as np
import soundfile as sf
from scipy.fftpack import dct, idct
import logging
import os

# Konfigurasi logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def calculate_max_capacity_dct(audio_path):
    """Menghitung kapasitas maksimal bit yang dapat disisipkan
    
    Args:
        audio_path: Path ke file audio
    
    Returns:
        Jumlah bit maksimal yang dapat disisipkan
    """
    try:
        data, samplerate = sf.read(audio_path)
        if len(data.shape) > 1:  # Jika stereo, konversi ke mono
            data = data.mean(axis=1)
        return int(len(data) * 0.75)  # Gunakan 75% kapasitas untuk margin error
    except Exception as e:
        logging.error(f"Error menghitung kapasitas: {str(e)}")
        return 0

def embed_message_dct(audio_path, message_bits, output_path):
    """Sisipkan pesan ke dalam audio menggunakan DCT
    
    Args:
        audio_path: Path ke file audio asli
        message_bits: Pesan dalam bentuk bit string
        output_path: Path untuk menyimpan audio dengan pesan tersembunyi
    
    Returns:
        True jika berhasil, False jika gagal
    """
    try:
        # Baca file audio
        data, samplerate = sf.read(audio_path)
        original_dtype = data.dtype
        
        # Konversi ke mono jika stereo
        if len(data.shape) > 1:
            data = data.mean(axis=1)
        
        # Normalisasi data audio
        if np.issubdtype(original_dtype, np.integer):
            max_val = np.iinfo(original_dtype).max
            data = data.astype(np.float32) / max_val
        
        # Tambah padding ke pesan jika perlu
        padding_length = 8 - (len(message_bits) % 8)
        padded_bits = message_bits + '0' * padding_length
        
        # Hitung DCT
        dct_coeffs = dct(data, norm='ortho')
        
        # Pilih frekuensi tengah untuk penyisipan
        start_idx = len(dct_coeffs) // 4
        end_idx = start_idx + len(padded_bits)
        
        if end_idx > len(dct_coeffs):
            logging.error("Pesan terlalu panjang untuk file audio ini")
            return False
        
        # Hitung scaling factor adaptif
        scaling = np.percentile(np.abs(dct_coeffs[start_idx:end_idx]), 90) * 0.05
        
        # Sisipkan setiap bit
        for i, bit in enumerate(padded_bits):
            idx = start_idx + i
            if bit == '1':
                dct_coeffs[idx] = abs(dct_coeffs[idx]) + scaling
            else:
                dct_coeffs[idx] = -abs(dct_coeffs[idx]) - scaling
        
        # Transformasi balik ke domain waktu
        stego_data = idct(dct_coeffs, norm='ortho')
        
        # Kembalikan ke format asli
        if np.issubdtype(original_dtype, np.integer):
            stego_data = np.clip(stego_data * max_val, np.iinfo(original_dtype).min, np.iinfo(original_dtype).max)
            stego_data = stego_data.astype(original_dtype)
        
        # Simpan file output
        sf.write(output_path, stego_data, samplerate, subtype='PCM_24')
        logging.info("Pesan berhasil disisipkan ke audio")
        return True
    
    except Exception as e:
        logging.error(f"Gagal menyisipkan pesan: {str(e)}")
        return False

def extract_message_dct(audio_path):
    """Ekstrak pesan dari audio menggunakan DCT
    
    Args:
        audio_path: Path ke file audio dengan pesan tersembunyi
    
    Returns:
        String bit yang berisi pesan, atau None jika gagal
    """
    try:
        # Baca file audio
        data, _ = sf.read(audio_path)
        
        # Konversi ke mono jika stereo
        if len(data.shape) > 1:
            data = data.mean(axis=1)
        
        # Normalisasi data audio
        if np.issubdtype(data.dtype, np.integer):
            max_val = np.iinfo(data.dtype).max
            data = data.astype(np.float32) / max_val
        
        # Hitung DCT
        dct_coeffs = dct(data, norm='ortho')
        
        # Temukan start index (sama dengan saat penyisipan)
        start_idx = len(dct_coeffs) // 4
        
        # Ekstrak bit sampai menemukan terminasi
        extracted_bits = []
        threshold = np.percentile(np.abs(dct_coeffs[start_idx:]), 90) * 0.03
        
        # Ekstrak minimal 256 bytes (untuk RSA 2048-bit)
        min_bits = 2048
        max_bits = 2048 + 64  # Margin kecil
        
        for i in range(start_idx, len(dct_coeffs)):
            val = dct_coeffs[i]
            if abs(val) > threshold:
                extracted_bits.append('1' if val > 0 else '0')
                # Hentikan setelah mendapat cukup bit
                if len(extracted_bits) >= max_bits:
                    break
            elif len(extracted_bits) >= min_bits:
                break
        
        if len(extracted_bits) < min_bits:
            logging.warning("Tidak cukup bit yang diekstrak")
            return None
        
        # Potong ke panjang yang tepat (2048 bit untuk RSA 2048-bit)
        extracted_bits = extracted_bits[:2048]
        
        return ''.join(extracted_bits)
    
    except Exception as e:
        logging.error(f"Gagal ekstrak pesan: {str(e)}")
        return None
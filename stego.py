import numpy as np
import soundfile as sf
from scipy.fftpack import dct, idct
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def calculate_max_capacity_dct(audio_path):
    """Calculate maximum number of bits that can be embedded"""
    try:
        data, _ = sf.read(audio_path)
        return int(len(data) * 0.7)  # Extend capacity to 70%
    except Exception as e:
        print(f"Capacity calculation error: {str(e)}")
        return 0


def embed_message_dct(audio_path, message_bits, output_path):
    """Optimized embedding for FLAC/WAV"""
    try:
        # Pad message bits to make the length divisible by 8
        if len(message_bits) % 8 != 0:
            padding_length = 8 - (len(message_bits) % 8)
            message_bits += '0' * padding_length
            logging.debug(f"Padded message bits with {padding_length} zeros.")

        data, samplerate = sf.read(audio_path)
        
        # Convert to mono and normalize
        if len(data.shape) > 1:  # Check if stereo
            data = data.mean(axis=1)
        data = data / (2**23 - 1) if data.dtype == np.int32 else data

        # Apply DCT
        dct_data = dct(data, norm='ortho')
        
        # Calculate embedding parameters
        msg_len = len(message_bits)
        start_idx = len(dct_data) // 3  # Use middle third of spectrum
        scaling = np.max(np.abs(dct_data)) * 0.01  # 1% of max coefficient
        
        if msg_len > len(dct_data) - start_idx:
            logging.error("Message too large to embed in the audio file.")
            return False

        # Embed each bit
        for i in range(msg_len):
            idx = start_idx + i
            if message_bits[i] == '1':
                dct_data[idx] = abs(dct_data[idx]) + scaling
            else:
                dct_data[idx] = -abs(dct_data[idx]) - scaling
        
        # Inverse DCT and save
        stego_data = idct(dct_data, norm='ortho')
        if data.dtype == np.int32:
            stego_data = np.clip(stego_data * (2**23-1), -2**23, 2**23-1).astype('int32')
        
        sf.write(output_path, stego_data, samplerate, subtype='PCM_24')
        logging.info("Message successfully embedded into the audio file.")
        return True
        
    except Exception as e:
        logging.error(f"Embedding failed: {str(e)}")
        return False

def extract_message_dct(audio_path):
    """Robust extraction for 24-bit FLAC"""
    try:
        data, _ = sf.read(audio_path)
        
        # Mono conversion and normalization
        if len(data.shape) > 1:
            data = data.mean(axis=1)
        data = data / (2**23 - 1) if data.dtype == np.int32 else data

        # Apply DCT
        dct_data = dct(data, norm='ortho')
        
        # Detection parameters
        start_idx = len(dct_data) // 3
        threshold = np.median(np.abs(dct_data)) * 0.3  # Lower threshold for better detection
        
        # Extract bits
        extracted = []
        for i in range(start_idx, len(dct_data)):
            if abs(dct_data[i]) > threshold:
                extracted.append('1' if dct_data[i] > 0 else '0')
            elif extracted:  # Stop at first non-message coefficient
                break

        # Log extracted bits and their length
        logging.debug(f"Extracted bits: {''.join(extracted)}")
        logging.debug(f"Number of extracted bits: {len(extracted)}")

        if not extracted:
            logging.warning("No message bits were extracted from the audio file.")
            return None

        # Ensure extracted bits are divisible by 8
        if len(extracted) % 8 != 0:
            extra_bits = len(extracted) % 8
            logging.warning(f"Truncating {extra_bits} extra bits to make the length divisible by 8.")
            extracted = extracted[:-(extra_bits)]

        if len(extracted) % 8 == 0:
            logging.info("Message bits successfully extracted from the audio file.")
            return ''.join(extracted)
        else:
            logging.error("Extracted bits are still not a valid length (not divisible by 8).")
            return None
        
    except Exception as e:
        logging.error(f"Extraction failed: {str(e)}")
        return None


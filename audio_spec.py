import os
from pydub.utils import mediainfo

# Fungsi untuk membaca informasi audio dalam folder
def read_audio_info(directory):
    # Daftar untuk menyimpan informasi file audio
    audio_info_list = []
    
    # Pastikan folder ada
    if not os.path.exists(directory):
        print(f"Folder {directory} tidak ditemukan!")
        return
    
    # Loop untuk membaca file dalam folder
    for filename in os.listdir(directory):
        # Periksa jika file memiliki ekstensi audio yang valid (misalnya mp3, wav, dll.)
        if filename.endswith(('.mp3', '.wav', '.flac', '.ogg', '.m4a')):
            file_path = os.path.join(directory, filename)
            
            # Mendapatkan informasi dari file audio menggunakan pydub
            info = mediainfo(file_path)
            
            # Mengonversi durasi dalam detik ke format menit dan detik
            duration_seconds = float(info['duration'])
            minutes = int(duration_seconds // 60)
            seconds = int(duration_seconds % 60)
            
            # Menyimpan informasi dalam list
            audio_info_list.append({
                'File Name': filename,
                'Duration': f"{minutes} menit {seconds} detik",
                'Channels': int(info['channels']),
                'Sample Rate': int(info['sample_rate']),
                'Bitrate': info.get('bit_rate', 'N/A')
            })
    
    return audio_info_list

# Tentukan folder yang berisi file audio
audio_folder = 'audio_files'

# Membaca dan menampilkan informasi
audio_files_info = read_audio_info(audio_folder)

# Menampilkan informasi
if audio_files_info:
    for audio_info in audio_files_info:
        print(f"File: {audio_info['File Name']}")
        print(f"  Duration: {audio_info['Duration']}")
        print(f"  Channels: {audio_info['Channels']}")
        print(f"  Sample Rate: {audio_info['Sample Rate']} Hz")
        print(f"  Bitrate: {audio_info['Bitrate']}")
        print('-' * 40)
else:
    print("Tidak ada file audio yang ditemukan di folder tersebut.")

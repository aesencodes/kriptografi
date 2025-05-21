# 🔐 Audio Steganografi dengan Enkripsi RSA

Aplikasi web ini memungkinkan pengguna untuk menyisipkan pesan rahasia ke dalam file audio (FLAC/WAV) menggunakan teknik steganografi berbasis DCT (Discrete Cosine Transform), serta mengenkripsi pesan menggunakan RSA-OAEP dengan SHA-256. Proyek ini dibangun menggunakan **Flask** dan dapat melakukan proses **penyisipan** dan **dekripsi** secara langsung melalui antarmuka web.

---

## 🚀 Fitur Utama

- ✅ Menyisipkan pesan rahasia ke dalam file audio (FLAC/WAV)
- 🔐 Enkripsi pesan dengan RSA 2048-bit dan OAEP (SHA-256)
- 📦 Estimasi kapasitas maksimum pesan dalam file audio
- 🧠 Transformasi DCT untuk menyisipkan bit pesan secara tersembunyi
- 🖥️ Antarmuka web berbasis Flask yang mudah digunakan
- 🧼 File sementara dibersihkan otomatis saat server ditutup

---

## 🛠️ Teknologi yang Digunakan

- **Python 3.8+**
- **Flask**
- **NumPy**
- **SciPy**
- **PyCryptodome**
- **SoundFile (pysoundfile)**

Install semua dependensi yang diperlukan:

```bash
pip3 install -r requirements.txt
```

---

## 📂 Struktur Direktori

```
kriptografi/
│
├── audio_files/            # Direktori untuk menyimpan file audio
│
├── app.py                  # Aplikasi utama berbasis Flask
├── encryptor.py            # Modul untuk proses enkripsi dan dekripsi RSA
├── stego.py                # Modul untuk proses steganografi audio berbasis DCT
├── testing.py              # Script untuk melakukan pengujian sistem
├── audio_spec.py           # Script untuk menampilkan spesifikasi file audio
├── plainteks1.txt          # File teks contoh untuk pengujian enkripsi
├── plainteks2.txt          # File teks contoh untuk pengujian enkripsi
├── plaintext3.txt          # File teks contoh untuk pengujian enkripsi
│
├── templates/              # Folder berisi file HTML untuk antarmuka web
│   ├── index.html
│   ├── embed_result.html
│   ├── decrypt.html
│   └── decrypt_result.html
│
├── static/                 # Folder untuk aset statis
│   └── style.css           # File CSS untuk styling halaman web
│   └── uploads/            # Folder untuk menyimpan file audio yang telah dienkripsi
│   └── keys/               # Folder sementara untuk menyimpan kunci privat RSA
│
├── README.md               # Dokumentasi proyek ini
└── requirements.txt        # Daftar dependensi Python yang diperlukan
```

---

## 📥 Proses Penyisipan

1. Masukkan pesan rahasia melalui antarmuka web.

2. Upload file audio berformat .flac atau .wav. (Saat ini hanya support .flac dengan spesifikasi 24Bit / 44.1 kHz)

3. Aplikasi akan:

   - Menghasilkan pasangan kunci RSA 2048-bit

   - Mengenkripsi pesan menggunakan public key (RSA + OAEP + SHA-256)

   - Menyisipkan ciphertext ke dalam blok DCT file audio

4. Hasil:

   - File audio yang telah disisipi pesan

   - File kunci privat (.pem) untuk proses dekripsi

---

## 🔓 Proses Dekripsi

1. Upload file audio berisi pesan rahasia.

2. Upload file private key yang diberikan saat proses penyisipan.

3. Aplikasi akan:

   - Mengekstrak bit dari DCT blok audio

   - Mendekripsi ciphertext menggunakan RSA

   - Menampilkan pesan asli di halaman hasil

---

## 📄 Format Input yang Didukung

- Audio: .flac, .wav

- Kunci privat: .pem (RSA 2048-bit)

## 👤 Kontributor

- Adjie Surya Nugraha (118140146) - Kriptografi RB
- Slamet Nugroho (118140189) - Kriptografi RB

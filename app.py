# app.py
import os
import uuid
import shutil
import base64
import sys
import atexit
from flask import Flask, render_template, request, redirect, flash, url_for, send_from_directory
from werkzeug.utils import secure_filename
from encryptor import generate_keys, encrypt_message
from stego import embed_message_dct, extract_message_dct, calculate_max_capacity_dct
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Hash import SHA256
from Crypto import Random

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['KEY_FOLDER'] = 'static/keys'
app.config['ALLOWED_EXTENSIONS'] = {'flac', 'wav'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.secret_key = os.urandom(24)

# Create directories if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['KEY_FOLDER'], exist_ok=True)

def allowed_file(filename):
    """Check if the file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def cleanup():
    """Clean up upload directories when app exits"""
    try:
        shutil.rmtree(app.config['UPLOAD_FOLDER'])
        shutil.rmtree(app.config['KEY_FOLDER'])
    except:
        pass

atexit.register(cleanup)

@app.route('/')
def index():
    """Home page for encryption"""
    return render_template('index.html')

@app.route('/upload_audio', methods=['POST'])
def upload_audio():
    """Endpoint for audio upload (AJAX)"""
    if 'audio_file' not in request.files:
        return {'error': 'No audio file selected'}, 400
    
    audio_file = request.files['audio_file']
    if audio_file.filename == '':
        return {'error': 'No file selected'}, 400
    
    if not allowed_file(audio_file.filename):
        return {'error': 'Only WAV and FLAC files are supported'}, 400
    
    # Save temporary file
    filename = secure_filename(f"temp_{uuid.uuid4()}.{audio_file.filename.rsplit('.', 1)[1].lower()}")
    audio_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    audio_file.save(audio_path)
    
    # Calculate maximum capacity
    try:
        capacity = calculate_max_capacity_dct(audio_path)
        return {
            'filename': filename,
            'capacity': capacity,
            'message': f'Max capacity: {capacity} bits ({capacity//8} characters)'
        }
    except Exception as e:
        return {'error': f'Error calculating capacity: {str(e)}'}, 500

@app.route('/encrypt', methods=['POST'])
def encrypt():
    """Encrypt and embed message into audio"""
    try:
        message = request.form.get('message')
        audio_filename = request.form.get('audio_filename')
        
        if not message or not audio_filename:
            flash('Please provide both message and audio file', 'error')
            return redirect(url_for('index'))
        
        audio_path = os.path.join(app.config['UPLOAD_FOLDER'], audio_filename)
        
        # Generate RSA 2048-bit key pair
        private_key, public_key = generate_keys()
        key_id = str(uuid.uuid4())
        private_key_path = os.path.join(app.config['KEY_FOLDER'], f"{key_id}_private.pem")
        
        # Save private key
        with open(private_key_path, 'wb') as f:
            f.write(private_key)
        
        # Encrypt message with RSA-OAEP
        encrypted_bytes = encrypt_message(message, public_key, as_bytes=True)
        message_bits = ''.join(format(byte, '08b') for byte in encrypted_bytes)
        
        # Check audio capacity
        capacity = calculate_max_capacity_dct(audio_path)
        if len(message_bits) > capacity:
            flash(f'Message too long. Max capacity: {capacity} bits', 'error')
            return redirect(url_for('index'))
        
        # Embed message into audio
        output_filename = f"encrypted_{audio_filename}"
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        
        if not embed_message_dct(audio_path, message_bits, output_path):
            flash('Failed to embed message into audio', 'error')
            return redirect(url_for('index'))
        
        # Remove temporary audio file
        if os.path.exists(audio_path):
            os.remove(audio_path)
        
        return render_template('embed_result.html',
                             encrypted_message=base64.b64encode(encrypted_bytes).decode(),
                             audio_path=output_filename,
                             private_key_file=f"{key_id}_private.pem")
    
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/decrypt', methods=['GET', 'POST'])
def decrypt():
    """Halaman dan proses dekripsi"""
    if request.method == 'POST':
        try:
            audio_file = request.files.get('audio_file_decrypt')
            private_key_file = request.files.get('private_key_file')
            
            if not audio_file or not private_key_file:
                flash('Harap unggah file audio dan kunci privat', 'error')
                return redirect(url_for('decrypt'))
            
            # Simpan file sementara
            temp_audio = os.path.join(app.config['UPLOAD_FOLDER'], f"temp_{uuid.uuid4()}.flac")
            audio_file.save(temp_audio)
            
            try:
                # Baca kunci privat
                private_key = private_key_file.read()
                priv_key = RSA.import_key(private_key)
                
                # Ekstrak pesan dari audio
                bits = extract_message_dct(temp_audio)
                if not bits:
                    flash('Tidak ditemukan pesan dalam file audio', 'error')
                    return redirect(url_for('decrypt'))
                
                # Pastikan panjang bit sesuai dengan kelipatan 8
                if len(bits) % 8 != 0:
                    bits = bits[:-(len(bits) % 8)]
                
                # Konversi bit ke byte
                ciphertext = bytes(int(bits[i:i+8], 2) for i in range(0, len(bits), 8))
                
                # Verifikasi panjang ciphertext
                key_size = priv_key.size_in_bytes()
                if len(ciphertext) != key_size:
                    flash(f'Panjang ciphertext tidak valid. Harus {key_size} bytes, dapat {len(ciphertext)} bytes', 'error')
                    return redirect(url_for('decrypt'))
                
                # Dekripsi pesan
                cipher = PKCS1_OAEP.new(priv_key, hashAlgo=SHA256)
                decrypted = cipher.decrypt(ciphertext)
                
                return render_template('decrypt_result.html', decrypted_message=decrypted.decode('utf-8'))
            
            finally:
                # Hapus file sementara
                if os.path.exists(temp_audio):
                    os.remove(temp_audio)
        
        except Exception as e:
            flash(f'Error dekripsi: {str(e)}', 'error')
            return redirect(url_for('decrypt'))
    
    return render_template('decrypt.html')

@app.route('/download/<path:filename>')
def download(filename):
    """Download endpoint for files"""
    directory = os.path.dirname(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return send_from_directory(directory, os.path.basename(filename), as_attachment=True)

@app.route('/download_key/<path:filename>')
def download_key(filename):
    """Download endpoint for keys"""
    directory = os.path.dirname(os.path.join(app.config['KEY_FOLDER'], filename))
    return send_from_directory(directory, os.path.basename(filename), as_attachment=True)

if __name__ == '__main__':
    # Remove SSL context if you don't have certificates
    app.run(debug=True)
    
    # If you have SSL certificates, use this instead:
    # context = ('cert.pem', 'key.pem')  # Path to your SSL certificates
    # app.run(debug=True, ssl_context=context)
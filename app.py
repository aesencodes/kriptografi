import os
import uuid
import shutil
import base64
import sys
import atexit
from flask import Flask, render_template, request, redirect, flash, url_for
from werkzeug.utils import secure_filename
from encryptor import generate_keys, encrypt_message
from stego import embed_message_dct, extract_message_dct, calculate_max_capacity_dct
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Hash import SHA256

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['KEY_FOLDER'] = 'keys'
app.config['ALLOWED_EXTENSIONS'] = {'flac', 'wav'}
app.secret_key = os.urandom(24)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['KEY_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def cleanup():
    try:
        shutil.rmtree(app.config['UPLOAD_FOLDER'])
        shutil.rmtree(app.config['KEY_FOLDER'])
    except:
        pass

atexit.register(cleanup)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            message = request.form.get('message')
            audio_file = request.files.get('audio_file')

            if not message or not audio_file or audio_file.filename == '':
                flash('Please provide both a message and an audio file.', 'error')
                return redirect(request.url)

            if not allowed_file(audio_file.filename):
                flash('Only WAV and FLAC files are supported.', 'error')
                return redirect(request.url)

            filename = secure_filename(f"{uuid.uuid4()}.{audio_file.filename.rsplit('.', 1)[1].lower()}")
            audio_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            audio_file.save(audio_path)

            private_key, public_key = generate_keys()
            key_id = str(uuid.uuid4())
            private_key_path = os.path.join(app.config['KEY_FOLDER'], f"{key_id}_private.pem")
            with open(private_key_path, 'wb') as f:
                f.write(private_key)

            encrypted_bytes = encrypt_message(message, public_key, as_bytes=True)
            message_bits = ''.join(format(byte, '08b') for byte in encrypted_bytes)

            capacity = calculate_max_capacity_dct(audio_path)
            if len(message_bits) > capacity:
                flash(f'Message too long. Max capacity: {capacity} bits', 'error')
                return redirect(request.url)

            output_filename = f"output_{filename}"
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)

            if embed_message_dct(audio_path, message_bits, output_path):
                encrypted_message = base64.b64encode(encrypted_bytes).decode()
                return render_template('embed_result.html',
                                       encrypted_message=encrypted_message,
                                       audio_path=output_filename,
                                       private_key_file=f"{key_id}_private.pem")
            else:
                flash('Failed to embed message.', 'error')
                return redirect(request.url)

        except Exception as e:
            flash(f"Error: {str(e)}", 'error')
            return redirect(request.url)

    return render_template('index.html')

@app.route('/decrypt', methods=['GET', 'POST'])
def decrypt():
    if request.method == 'POST':
        try:
            audio_file = request.files.get('audio_file_decrypt')
            private_key_file = request.files.get('private_key_file')

            if not audio_file or not private_key_file:
                flash('Both audio and private key files are required.', 'error')
                return redirect(url_for('decrypt'))

            # Save the uploaded audio file temporarily
            temp_audio = os.path.join(app.config['UPLOAD_FOLDER'], f"temp_{uuid.uuid4()}.flac")
            audio_file.save(temp_audio)

            try:
                # Read the private key file
                private_key = private_key_file.read()
                priv_key = RSA.import_key(private_key)

                # Extract the message bits from the audio file
                bits = extract_message_dct(temp_audio)
                if not bits:
                    flash('No message bits were extracted from the audio file. Ensure you are using the correct audio file.', 'error')
                    return redirect(url_for('decrypt'))

                # Convert bits to bytes
                ciphertext = bytes(int(bits[i:i+8], 2) for i in range(0, len(bits), 8))

                # Decrypt the message
                cipher = PKCS1_OAEP.new(priv_key, hashAlgo=SHA256)
                decrypted = cipher.decrypt(ciphertext)
                return render_template('decrypt_result.html', decrypted_message=decrypted.decode('utf-8'))

            finally:
                os.remove(temp_audio)

        except Exception as e:
            flash(f"Decryption error: {str(e)}", 'error')
            return redirect(url_for('decrypt'))

    return render_template('decrypt.html')


if __name__ == '__main__':
    if sys.version_info >= (3, 8):
        import time
        if not hasattr(time, 'clock'):
            time.clock = time.time
    app.run(debug=True)

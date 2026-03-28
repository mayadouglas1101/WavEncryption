#!/usr/bin/env python3
import sys, os, hashlib, struct
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
MAGIC = b'WAVENC1\x00'
def derive_key(wav_path):
    with open(wav_path, 'rb') as f:
        data = f.read()
    if data[:4] != b'RIFF' or data[8:12] != b'WAVE':
        raise ValueError(f"'{wav_path}' is not a valid WAV file.")
    offset = data.find(b'data')
    if offset == -1:
        raise ValueError("No audio data found in WAV file.")
    return hashlib.sha256(data[offset+8:]).digest()
def pad(data):
    n = 16 - len(data) % 16
    return data + bytes([n]*n)
def unpad(data):
    n = data[-1]
    if n < 1 or n > 16:
        raise ValueError("Bad padding — wrong WAV key or corrupted file.")
    return data[:-n]
def encrypt(key, src, dst):
    with open(src, 'rb') as f:
        plain = f.read()
    iv = os.urandom(16)
    enc = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend()).encryptor()
    cipher = enc.update(pad(plain)) + enc.finalize()
    with open(dst, 'wb') as f:
        f.write(MAGIC + iv + struct.pack('>Q', len(plain)) + cipher)
    print(f"✓ Encrypted: {src} → {dst}")
def decrypt(key, src, dst):
    with open(src, 'rb') as f:
        raw = f.read()
    if raw[:8] != MAGIC:
        raise ValueError("Not a wav_encrypt file, or corrupted.")
    iv = raw[8:24]
    size = struct.unpack('>Q', raw[24:32])[0]
    dec = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend()).decryptor()
    plain = unpad(dec.update(raw[32:]) + dec.finalize())[:size]
    with open(dst, 'wb') as f:
        f.write(plain)
    print(f"✓ Decrypted: {src} → {dst}")
def usage():
    print("Usage: python wav_encrypt.py encrypt|decrypt <key.wav> <input> <output>")
    sys.exit(1)
if len(sys.argv) != 5: usage()
cmd, wav, src, dst = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
if cmd not in ('encrypt','decrypt'): usage()
if not os.path.isfile(wav): print(f"WAV not found: {wav}"); sys.exit(1)
if not os.path.isfile(src): print(f"Input not found: {src}"); sys.exit(1)
key = derive_key(wav)
(encrypt if cmd == 'encrypt' else decrypt)(key, src, dst)

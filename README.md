# wav_encrypt

AES-256 encryption using a WAV file as the key.

## How it works

Instead of typing a password, you use a WAV audio file as your encryption key. The script reads the raw PCM audio samples from the WAV file, hashes them with SHA-256 to produce a 256-bit key, then uses that key with AES-256-CBC to encrypt or decrypt any file.

The key insight is that SHA-256 is deterministic — the same WAV file always produces the same key, so you never need to store the key anywhere. The WAV file itself is the key.

### Encryption process

1. Load the WAV file and skip the 44-byte header
2. SHA-256 hash the raw PCM audio samples → 256-bit key
3. Generate a random 16-byte IV (unique per encryption)
4. Pad the plaintext to a 16-byte block boundary (PKCS#7)
5. Encrypt with AES-256-CBC using the key and IV
6. Write output file: `[MAGIC 8B][IV 16B][original size 8B][ciphertext]`

### Decryption process

1. Load the same WAV file and derive the identical key via SHA-256
2. Read the IV from bytes 8–24 of the encrypted file
3. Decrypt with AES-256-CBC
4. Strip padding and trim to original file size

The encrypted file stores the IV alongside the ciphertext — this is safe to do publicly. The IV only needs to be unique, not secret. Security comes entirely from the WAV key.

## Requirements

```bash
python3 -m venv ~/wav-enc-env
source ~/wav-enc-env/bin/activate
pip install cryptography
```

## Usage

```bash
# Encrypt
python wav_encrypt.py encrypt <key.wav> <input_file> <output_file>

# Decrypt
python wav_encrypt.py decrypt <key.wav> <input_file> <output_file>
```

### Example

```bash
python wav_encrypt.py encrypt secret.wav document.pdf document.enc
python wav_encrypt.py decrypt secret.wav document.enc document_recovered.pdf
```

## Output file format

| Field | Size | Description |
|---|---|---|
| MAGIC | 8 bytes | `WAVENC1\x00` — identifies the file format |
| IV | 16 bytes | Random initialisation vector |
| Original size | 8 bytes | Size of the original file before padding |
| Ciphertext | N bytes | AES-256-CBC encrypted content |

## Try the demo

This repo includes a sample encrypted file `cottage.enc`, locked with `heatedrivalryattss.wav` as the key. To decrypt it:

**1. Clone the repo**
```bash
git clone https://github.com/mayadouglas1101/WavEncryption.git
cd WavEncryption
```

**2. Set up the environment**
```bash
python3 -m venv wav-enc-env
source wav-enc-env/bin/activate
pip install cryptography
```

**3. Decrypt the demo file**
```bash
python wav_encrypt.py decrypt heatedrivalryattss.wav cottage.enc cottage.txt
cat cottage.txt
```

You should see a quote from the HBO show *Heated Rivalry*.

---

## Important warnings

**Never commit your WAV key file to this repository.** The WAV file is your private key — anyone who has it can decrypt your files. The `.gitignore` in this repo excludes `.wav` files for this reason.

**Never re-export or re-encode your WAV key.** Even re-saving it in the same format can alter metadata or audio data, producing a different SHA-256 hash and a different key — permanently locking you out of your encrypted files.

**Back up your WAV file.** Store a copy on an external drive or USB stick. If you lose the WAV file, your encrypted data is unrecoverable.

**The WAV file should be kept secret.** Security is only as strong as keeping the audio file private. Treat it like a password file.

## Why skip the WAV header?

Standard WAV files have a 44-byte header containing metadata like sample rate, channel count, and bit depth. By skipping the header and hashing only the raw PCM audio data, the key is more stable — minor metadata changes (such as a tagging application updating the file) won't silently invalidate your key.

## Why AES-256-CBC?

AES-256 is the industry standard for symmetric encryption and is considered computationally infeasible to brute-force. CBC (Cipher Block Chaining) mode means each block of ciphertext depends on the previous one, so identical plaintext blocks produce different ciphertext — preventing pattern leakage.

A fresh random IV is generated for every encryption operation, meaning the same file encrypted twice with the same WAV key will produce different ciphertext each time.

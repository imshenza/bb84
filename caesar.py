def caesar_encrypt(plaintext, key_bits):
    if not key_bits:
        shift = 0
    else:
        shift = sum(key_bits) % 26

    out = []
    for ch in plaintext:
        if ch.isalpha():
            base = ord('A') if ch.isupper() else ord('a')
            out.append(chr((ord(ch) - base + shift) % 26 + base))
        else:
            out.append(ch)
    return "".join(out)

def caesar_decrypt(ciphertext, key_bits):
    if not key_bits:
        shift = 0
    else:
        shift = sum(key_bits) % 26

    out = []
    for ch in ciphertext:
        if ch.isalpha():
            base = ord('A') if ch.isupper() else ord('a')
            out.append(chr((ord(ch) - base - shift) % 26 + base))
        else:
            out.append(ch)
    return "".join(out)

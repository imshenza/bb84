import random

def generate_bits(n):
    return [random.randint(0, 1) for _ in range(n)]

def generate_bases(n):
    return [random.choice(['X', 'Z']) for _ in range(n)]

def measure_bits_no_eve(alice_bits, alice_bases, bob_bases):
    results = []
    for a_bit, a_basis, b_basis in zip(alice_bits, alice_bases, bob_bases):
        if a_basis == b_basis:
            results.append(a_bit)
        else:
            results.append(random.randint(0, 1))
    return results

def measure_bits_with_eve(alice_bits, alice_bases, bob_bases, eve_prob=1.0):
    n = len(alice_bits)
    qubits_after_eve = []
    eve_info = []

    for a_bit, a_basis in zip(alice_bits, alice_bases):
        if random.random() < eve_prob:
            e_basis = random.choice(['X', 'Z'])
            e_meas = a_bit if e_basis == a_basis else random.randint(0, 1)
            qubits_after_eve.append((e_meas, e_basis))
            eve_info.append({"intercepted": True, "eve_basis": e_basis, "eve_meas": e_meas})
        else:
            qubits_after_eve.append((a_bit, a_basis))
            eve_info.append({"intercepted": False, "eve_basis": None, "eve_meas": None})

    bob_results = []
    for (bit_prep, basis_prep), b_basis in zip(qubits_after_eve, bob_bases):
        if basis_prep == b_basis:
            bob_results.append(bit_prep)
        else:
            bob_results.append(random.randint(0, 1))
    return bob_results, eve_info

def sift_keys(alice_bits, alice_bases, bob_bases, bob_results):
    alice_key = []
    bob_key = []
    for a_bit, a_basis, b_basis, b_res in zip(alice_bits, alice_bases, bob_bases, bob_results):
        if a_basis == b_basis:
            alice_key.append(a_bit)
            bob_key.append(b_res)
    return alice_key, bob_key

def calculate_qber(alice_key, bob_key):
    if not alice_key or not bob_key:
        return 0
    L = min(len(alice_key), len(bob_key))
    mismatches = sum(1 for i in range(L) if alice_key[i] != bob_key[i])
    return round((mismatches / L) * 100.0, 2)

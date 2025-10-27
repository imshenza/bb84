import random

# ---- helpers ----

def generate_bits(n):
    """Return list of 0/1 bits."""
    return [random.randint(0, 1) for _ in range(n)]


def generate_bases(n):
    """Return list of bases 'X' or 'Z'."""
    return [random.choice(['X', 'Z']) for _ in range(n)]


def measure_bits_no_eve(alice_bits, alice_bases, bob_bases):
    """
    Bob measures the qubits Alice sent (no Eve).
    If base matches -> returns alice bit; else random bit.
    """
    results = []
    for a_bit, a_basis, b_basis in zip(alice_bits, alice_bases, bob_bases):
        if a_basis == b_basis:
            results.append(a_bit)
        else:
            results.append(random.randint(0, 1))
    return results


def measure_bits_with_eve(alice_bits, alice_bases, bob_bases, eve_prob=1.0):
    """
    Simulate intercept-resend Eve before Bob measures.
    For each qubit:
      - with probability eve_prob: Eve chooses random basis, measures (random if mismatch),
        and resends measured bit in Eve's basis.
      - otherwise: qubit passes through unchanged.
    Then Bob measures the (possibly resent) qubits using his bob_bases.
    Returns (bob_results, eve_info_list)
    """
    n = len(alice_bits)
    # first build qubits after Eve: each as (bit, basis)
    qubits_after_eve = []
    eve_info = []
    for a_bit, a_basis in zip(alice_bits, alice_bases):
        if random.random() < eve_prob:
            # Eve intercepts
            e_basis = random.choice(['X', 'Z'])
            # Eve's measurement
            e_meas = a_bit if e_basis == a_basis else random.randint(0, 1)
            qubits_after_eve.append((e_meas, e_basis))
            eve_info.append({"intercepted": True, "eve_basis": e_basis, "eve_meas": e_meas})
        else:
            qubits_after_eve.append((a_bit, a_basis))
            eve_info.append({"intercepted": False, "eve_basis": None, "eve_meas": None})

    # Bob measures qubits_after_eve using his bob_bases
    bob_results = []
    for (bit_prep, basis_prep), b_basis in zip(qubits_after_eve, bob_bases):
        if basis_prep == b_basis:
            bob_results.append(bit_prep)
        else:
            bob_results.append(random.randint(0, 1))

    return bob_results, eve_info


def sift_keys(alice_bits, alice_bases, bob_bases, bob_results):
    """
    Return (alice_sifted_key, bob_sifted_key) where we keep positions
    where alice_bases == bob_bases.
    bob_results must be aligned with alice positions and bob_bases.
    """
    alice_key = []
    bob_key = []
    for a_bit, a_basis, b_basis, b_res in zip(alice_bits, alice_bases, bob_bases, bob_results):
        if a_basis == b_basis:
            alice_key.append(a_bit)
            bob_key.append(b_res)
    return alice_key, bob_key


def calculate_qber(alice_key_no_eve, bob_key_with_eve):
    """
    Compare two sifted keys (Alice's ideal key vs Bob's key when Eve intercepted).
    QBER = fraction mismatched.
    """
    if not alice_key_no_eve or not bob_key_with_eve:
        return 0.0
    # They should be same length; if not, compare min length
    L = min(len(alice_key_no_eve), len(bob_key_with_eve))
    if L == 0:
        return 0.0
    mismatches = sum(1 for i in range(L) if alice_key_no_eve[i] != bob_key_with_eve[i])
    return round((mismatches / L) * 100.0, 2)

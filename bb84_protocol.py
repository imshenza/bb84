import random
from qiskit import QuantumCircuit, transpile
from qiskit_aer import Aer

# Generate random bits (0 or 1)
def random_bits(n):
    return [random.randint(0, 1) for _ in range(n)]

# Generate random bases ('X' or 'Z')
def random_bases(n):
    return [random.choice(['X', 'Z']) for _ in range(n)]

# Encode qubits based on bits and bases
def encode_qubits(bits, bases):
    qubits = []
    for bit, base in zip(bits, bases):
        qc = QuantumCircuit(1, 1)
        if bit == 1:
            qc.x(0)
        if base == 'X':
            qc.h(0)
        qubits.append(qc)
    return qubits

# Measure qubits according to receiver's bases
def measure_qubits(bits, alice_bases, bob_bases):
    results = []
    simulator = Aer.get_backend('aer_simulator')

    for bit, a_base, b_base in zip(bits, alice_bases, bob_bases):
        qc = QuantumCircuit(1, 1)
        if bit == 1:
            qc.x(0)
        if a_base == 'X':
            qc.h(0)
        if b_base == 'X':
            qc.h(0)
        qc.measure(0, 0)
        qc = transpile(qc, simulator)
        counts = simulator.run(qc, shots=1).result().get_counts()
        result_bit = 1 if '1' in counts else 0
        results.append(result_bit)
    return results

# Sift key: keep only bits where both used same basis
def sift_key(bits, alice_bases, bob_bases):
    return [bit for bit, a_base, b_base in zip(bits, alice_bases, bob_bases) if a_base == b_base]

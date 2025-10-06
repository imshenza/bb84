from flask import Flask, render_template, request
import random
from bb84_protocol import (
    random_bits,
    random_bases,
    encode_qubits,
    measure_qubits,
    sift_key
)

app = Flask(__name__)

alice_bits = []
alice_bases = []
bob_bases = []
bob_results = []


@app.route('/')
def home():
    return render_template('alice.html')


@app.route('/send', methods=['POST'])
def send_bits():
    global alice_bits, alice_bases
    n = int(request.form.get('num_bits', 8))
    alice_bits = random_bits(n)
    alice_bases = random_bases(n)
    qubits = encode_qubits(alice_bits, alice_bases)
    return render_template(
        'bob.html',
        qubits=qubits,
        bob_bases=None,
        bob_results=None,
        alice_bits=alice_bits,
        alice_bases=alice_bases
    )


@app.route('/receive', methods=['POST'])
def receive_bits():
    global bob_bases, bob_results
    n = len(alice_bits)
    bob_bases = random_bases(n)
    bob_results = measure_qubits(alice_bits, alice_bases, bob_bases)

    # Compute the shared secret key
    secret_key = sift_key(alice_bits, alice_bases, bob_bases)

    return render_template(
        'bob.html',
        bob_bases=bob_bases,
        bob_results=bob_results,
        alice_bits=alice_bits,
        alice_bases=alice_bases,
        secret_key=secret_key
    )


if __name__ == '__main__':
    app.run(debug=True)

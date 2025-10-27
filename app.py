from flask import Flask, render_template, request, redirect, url_for, session
from bb84 import (
    generate_bits,
    generate_bases,
    measure_bits_no_eve,
    measure_bits_with_eve,
    sift_keys,
    calculate_qber
)
from caesar import caesar_encrypt, caesar_decrypt

import secrets

app = Flask(__name__)
# use a random secret for sessions (for demo it's fine)
app.secret_key = secrets.token_hex(16)


@app.route("/")
def index():
    return redirect(url_for("alice"))


# ---------- Alice: choose number of qubits and send ----------
@app.route("/alice", methods=["GET", "POST"])
def alice():
    if request.method == "POST":
        try:
            n = int(request.form.get("num_bits", 8))
            if n < 1:
                n = 8
        except ValueError:
            n = 8

        alice_bits = generate_bits(n)
        alice_bases = generate_bases(n)

        # store for the session
        session["n"] = n
        session["alice_bits"] = alice_bits
        session["alice_bases"] = alice_bases

        # clear any previous results
        for k in [
            "bob_bases", "bob_results_no_eve", "bob_results_with_eve",
            "alice_key_no_eve", "bob_key_no_eve", "alice_key_with_eve", "bob_key_with_eve",
            "qber", "ciphertext"
        ]:
            session.pop(k, None)

        return redirect(url_for("receive"))
    # GET
    return render_template("alice.html")


# ---------- Bob receive page: measure button ----------
@app.route("/receive", methods=["GET", "POST"])
def receive():
    alice_bits = session.get("alice_bits")
    alice_bases = session.get("alice_bases")
    n = session.get("n", None)
    if alice_bits is None or alice_bases is None:
        return redirect(url_for("alice"))

    if request.method == "POST":
        # generate bob bases (one set) and then measure two scenarios with same bob_bases
        bob_bases = generate_bases(n)

        # No Eve: Bob measures the original qubits (Alice -> Bob)
        bob_results_no_eve = measure_bits_no_eve(alice_bits, alice_bases, bob_bases)

        # With Eve: Eve intercept-resend before Bob; Bob measures what Eve resent
        bob_results_with_eve, eve_info = measure_bits_with_eve(alice_bits, alice_bases, bob_bases)

        # Sift keys (only positions where Alice and Bob bases match)
        alice_key_no_eve, bob_key_no_eve = sift_keys(alice_bits, alice_bases, bob_bases, bob_results_no_eve)
        alice_key_with_eve, bob_key_with_eve = sift_keys(alice_bits, alice_bases, bob_bases, bob_results_with_eve)

        # QBER: compare Alice's expected key (no-eve) vs Bob's key when Eve was present
        qber = calculate_qber(alice_key_no_eve, bob_key_with_eve)

        # store
        session["bob_bases"] = bob_bases
        session["bob_results_no_eve"] = bob_results_no_eve
        session["bob_results_with_eve"] = bob_results_with_eve
        session["eve_info"] = eve_info
        session["alice_key_no_eve"] = alice_key_no_eve
        session["bob_key_no_eve"] = bob_key_no_eve
        session["alice_key_with_eve"] = alice_key_with_eve
        session["bob_key_with_eve"] = bob_key_with_eve
        session["qber"] = qber

        return redirect(url_for("results"))

    return render_template("receive.html", alice_bits=alice_bits, alice_bases=alice_bases)


# ---------- Results page: show both cases and QBER ----------
@app.route("/results")
def results():
    alice_bits = session.get("alice_bits", [])
    alice_bases = session.get("alice_bases", [])
    bob_bases = session.get("bob_bases", [])
    bob_results_no_eve = session.get("bob_results_no_eve", [])
    bob_results_with_eve = session.get("bob_results_with_eve", [])
    eve_info = session.get("eve_info", [])
    alice_key_no_eve = session.get("alice_key_no_eve", [])
    bob_key_no_eve = session.get("bob_key_no_eve", [])
    alice_key_with_eve = session.get("alice_key_with_eve", [])
    bob_key_with_eve = session.get("bob_key_with_eve", [])
    qber = session.get("qber", 0.0)

    # Build per-index table rows
    rows = []
    n = session.get("n", 0)
    for i in range(n):
        row = {
            "index": i,
            "alice_bit": alice_bits[i],
            "alice_basis": alice_bases[i],
            "bob_basis": bob_bases[i] if i < len(bob_bases) else None,
            "bob_no_eve": bob_results_no_eve[i] if i < len(bob_results_no_eve) else None,
            "bob_with_eve": bob_results_with_eve[i] if i < len(bob_results_with_eve) else None,
            "eve_info": eve_info[i] if i < len(eve_info) else None,
            "bases_match": (alice_bases[i] == bob_bases[i]) if i < len(bob_bases) else False
        }
        rows.append(row)

    return render_template(
        "results.html",
        rows=rows,
        alice_key_no_eve=alice_key_no_eve,
        bob_key_no_eve=bob_key_no_eve,
        alice_key_with_eve=alice_key_with_eve,
        bob_key_with_eve=bob_key_with_eve,
        qber=qber
    )


# ---------- Message sending: Alice encrypts using agreed key (no Eve) ----------
@app.route("/message_send", methods=["GET", "POST"])
def message_send():
    alice_key_no_eve = session.get("alice_key_no_eve", [])
    if not alice_key_no_eve:
        # no key agreed -> go back to results
        return redirect(url_for("results"))

    if request.method == "POST":
        plaintext = request.form.get("plaintext", "")
        ciphertext = caesar_encrypt(plaintext, alice_key_no_eve)
        # store ciphertext so Bob can fetch it and decrypt with his key
        session["ciphertext"] = ciphertext
        session["plaintext"] = plaintext
        return redirect(url_for("message_receive"))

    return render_template("message_send.html", alice_key=alice_key_no_eve)


# ---------- Bob receives and decrypts ----------
@app.route("/message_receive")
def message_receive():
    ciphertext = session.get("ciphertext", None)
    if ciphertext is None:
        return redirect(url_for("message_send"))

    # choose Bob's key for decryption: we assume no Eve case since they agreed without Eve
    bob_key_no_eve = session.get("bob_key_no_eve", [])
    decrypted = caesar_decrypt(ciphertext, bob_key_no_eve)
    return render_template("message_receive.html", ciphertext=ciphertext, decrypted=decrypted)


# ---------- Restart flow ----------
@app.route("/restart")
def restart():
    session.clear()
    return redirect(url_for("alice"))


if __name__ == "__main__":
    app.run(debug=True)

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
app.secret_key = secrets.token_hex(16)


@app.route("/")
def index():
    return redirect(url_for("alice"))


# ---------- Alice Page ----------
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

        # Store in session
        session["n"] = n
        session["alice_bits"] = alice_bits
        session["alice_bases"] = alice_bases

        # Clear previous results
        for k in [
            "bob_bases", "bob_results_no_eve", "bob_results_with_eve",
            "alice_key_no_eve", "bob_key_no_eve", "alice_key_with_eve",
            "bob_key_with_eve", "qber_no_eve", "qber_with_eve",
            "ciphertext", "eve_info"
        ]:
            session.pop(k, None)

        return redirect(url_for("receive"))

    return render_template("alice.html")


# ---------- Bob Measurement ----------
@app.route("/receive", methods=["GET", "POST"])
def receive():
    alice_bits = session.get("alice_bits")
    alice_bases = session.get("alice_bases")
    n = session.get("n", None)
    if alice_bits is None or alice_bases is None:
        return redirect(url_for("alice"))

    if request.method == "POST":
        bob_bases = generate_bases(n)

        # No Eve case
        bob_results_no_eve = measure_bits_no_eve(alice_bits, alice_bases, bob_bases)
        alice_key_no_eve, bob_key_no_eve = sift_keys(alice_bits, alice_bases, bob_bases, bob_results_no_eve)
        qber_no_eve = calculate_qber(alice_key_no_eve, bob_key_no_eve)

        # With Eve case
        bob_results_with_eve, eve_info = measure_bits_with_eve(alice_bits, alice_bases, bob_bases)
        alice_key_with_eve, bob_key_with_eve = sift_keys(alice_bits, alice_bases, bob_bases, bob_results_with_eve)
        qber_with_eve = calculate_qber(alice_key_with_eve, bob_key_with_eve)

        # Store everything
        session.update({
            "bob_bases": bob_bases,
            "bob_results_no_eve": bob_results_no_eve,
            "bob_results_with_eve": bob_results_with_eve,
            "eve_info": eve_info,
            "alice_key_no_eve": alice_key_no_eve,
            "bob_key_no_eve": bob_key_no_eve,
            "alice_key_with_eve": alice_key_with_eve,
            "bob_key_with_eve": bob_key_with_eve,
            "qber_no_eve": qber_no_eve,
            "qber_with_eve": qber_with_eve,
        })

        return redirect(url_for("results"))

    return render_template("receive.html", alice_bits=alice_bits, alice_bases=alice_bases)


# ---------- Results ----------
@app.route("/results")
def results():
    alice_key_no_eve = session.get("alice_key_no_eve", [])
    bob_key_no_eve = session.get("bob_key_no_eve", [])
    alice_key_with_eve = session.get("alice_key_with_eve", [])
    bob_key_with_eve = session.get("bob_key_with_eve", [])
    eve_info = session.get("eve_info", [])

    qber_no_eve = session.get("qber_no_eve", 0.0)
    qber_with_eve = session.get("qber_with_eve", 0.0)

    # Build per-qubit row info
    rows = []
    alice_bits = session.get("alice_bits", [])
    alice_bases = session.get("alice_bases", [])
    bob_bases = session.get("bob_bases", [])
    bob_no_eve = session.get("bob_results_no_eve", [])
    bob_with_eve = session.get("bob_results_with_eve", [])

    for i in range(len(alice_bits)):
        row = {
            "index": i,
            "alice_bit": alice_bits[i],
            "alice_basis": alice_bases[i],
            "bob_basis": bob_bases[i],
            "bob_no_eve": bob_no_eve[i],
            "bob_with_eve": bob_with_eve[i],
            "bases_match": alice_bases[i] == bob_bases[i],
            "eve_info": eve_info[i] if i < len(eve_info) else None
        }
        rows.append(row)

    return render_template(
        "results.html",
        alice_key_no_eve=alice_key_no_eve,
        bob_key_no_eve=bob_key_no_eve,
        alice_key_with_eve=alice_key_with_eve,
        bob_key_with_eve=bob_key_with_eve,
        qber_no_eve=qber_no_eve,
        qber=qber_with_eve,
        rows=rows
    )


# ---------- Message Send ----------
@app.route("/message_send", methods=["GET", "POST"])
def message_send():
    alice_key_no_eve = session.get("alice_key_no_eve", [])
    if not alice_key_no_eve:
        return redirect(url_for("results"))

    if request.method == "POST":
        plaintext = request.form.get("plaintext", "")
        ciphertext = caesar_encrypt(plaintext, alice_key_no_eve)
        session["ciphertext"] = ciphertext
        session["plaintext"] = plaintext
        return redirect(url_for("message_receive"))

    return render_template("message_send.html", alice_key=alice_key_no_eve)


# ---------- Message Receive ----------
@app.route("/message_receive")
def message_receive():
    ciphertext = session.get("ciphertext", None)
    if ciphertext is None:
        return redirect(url_for("message_send"))

    bob_key_no_eve = session.get("bob_key_no_eve", [])
    decrypted = caesar_decrypt(ciphertext, bob_key_no_eve)
    return render_template("message_receive.html", ciphertext=ciphertext, decrypted=decrypted)


# ---------- Restart ----------
@app.route("/restart")
def restart():
    session.clear()
    return redirect(url_for("alice"))


if __name__ == "__main__":
    app.run(debug=True)

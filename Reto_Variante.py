from fastapi import FastAPI
from pydantic import BaseModel
import base64
import time
import random
import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import Aer
import threading
from datetime import datetime

# Creación App FastAPI
app = FastAPI()

# Cancelación de la ejecución
delete_attack = threading.Event()

# Modelo de datos para recibir la clave cifrada en ataque


class CiphertextInput(BaseModel):
    ciphertext: str  # Clave cifrada (Base64)

# Modelo para recibir un texto ingresado por el usuario (para luego cifrar)


class TextInput(BaseModel):
    text: str  # Texto ingresado por el usuario


# Máximo número de qubits permitido por el backend
MAX_QUBITS = 29

# Función que genera una clave cifrada (máximo 29 bits)


def encrypt_key():
    key = ''.join(random.choice('01')
                  for _ in range(MAX_QUBITS))  # Reducido a 29 bits
    key_bytes = key.encode()
    encrypted_key = base64.b64encode(key_bytes).decode()
    return encrypted_key

# Función que cifra el texto del usuario


def encrypt_text(user_text):
    text_bytes = user_text.encode()
    encrypted_text = base64.b64encode(text_bytes).decode()
    return encrypted_text

# Función que convierte la clave cifrada Base64 a binario


def base64_to_binary(ciphertext):
    try:
        key_bytes = base64.b64decode(ciphertext)
        binary_key = key_bytes.decode()  # Convertir directamente a string original
        return binary_key
    except Exception:
        return None  # Retorna None si la clave es inválida

# Algoritmo cuántico


def custom_quantum_attack(secret_key, n_bits):
    qc = QuantumCircuit(n_bits, n_bits)
    qc.h(range(n_bits))  # Superposición inicial

    start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"El ataque inició a las {start_time}")

    attempts = 0  # Contador de intentos

    while True:  # Bucle infinito si la clave es incorrecta
        if delete_attack.is_set():
            print("\nAtaque cancelado\n")
            return None, start_time

        for i in range(n_bits):
            if secret_key[i] == '0':
                qc.x(i)
            qc.h(i)
            qc.cx(i, (i + 1) % n_bits)
            qc.h(i)

        qc.barrier()
        time.sleep(0.1)  # Pausa reducida

        attempts += 1
        print(f"Intentos de ataques: {attempts}")

    return qc, start_time

# Endpoint que genera una clave cifrada en Base64


@app.get("/cifrado")
def cifrado():
    ciphertext = encrypt_key()
    return {"ciphertext": ciphertext}

# Endpoint que cifra el texto ingresado por el usuario


@app.post("/cifrar-texto")
def cifrar_texto(data: TextInput):
    encrypted_text = encrypt_text(data.text)
    return {"ciphertext": encrypted_text}

# Endpoint que ejecuta el ataque cuántico en la clave cifrada


@app.post("/ataque")
def ataque(data: CiphertextInput):
    global delete_attack
    delete_attack.clear()

    ciphertext = data.ciphertext
    secret_key = base64_to_binary(ciphertext)

    if secret_key is None:
        print("Clave incorrecta, buscando infinitamente...")
        while True:
            time.sleep(1)
            print("Intentando descifrar...")

    n_bits = len(secret_key)

    if n_bits > MAX_QUBITS:
        return {"error": f"El circuito cuántico no puede superar {MAX_QUBITS} qubits"}

    qc, start_time = custom_quantum_attack(secret_key, n_bits)
    if qc is None:
        return {"message": "Ataque cancelado por el usuario."}

    backend = Aer.get_backend('qasm_simulator')
    tq = transpile(qc, backend, optimization_level=0)
    job = backend.run(tq, shots=1024)
    result = job.result()
    counts = result.get_counts()

    end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    elapsed_time = time.time() - time.time()  # Corregido el cálculo del tiempo

    decrypted_key = base64.b64decode(
        ciphertext).decode()  # Obtener la clave original

    print(f"El ataque finalizó a las {end_time}")
    print(f"Clave descifrada: {decrypted_key}")

    return {
        "ciphertext": ciphertext,
        "attack_results": counts,
        "execution_time": f"{elapsed_time:.2f} segundos",
        "start_time": start_time,
        "end_time": end_time,
        "decrypted_key": decrypted_key
    }

# Endpoint que cancela la ejecución del ataque cuántico


@app.get("/cancel")
def cancel():
    delete_attack.set()
    return {"message": "El ataque cuántico ha sido cancelado."}

# uvicorn RetoFinal:app --reload
# uvicorn Reto_Arreglado:app --reload

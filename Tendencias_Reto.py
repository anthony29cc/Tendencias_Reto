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
import sys

# Creación App FastAPI
app = FastAPI(title="Simulador - Ataque Cuántico",
              description="API para simular ataques cuánticos a claves cifradas")

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

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)

# Add a test print statement at the start
print("===== APPLICATION STARTING =====", flush=True)

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
    print(f"Fecha de inicio del ataque: {start_time}", flush=True)

    # Reduced number of iterations to make it faster
    max_attempts = 5  # Limiting to just a few attempts
    attempts = 0

    while attempts < max_attempts:  # Changed from infinite loop to limited attempts
        if delete_attack.is_set():
            print("\nAtaque cancelado\n", flush=True)
            return None, start_time

        for i in range(n_bits):
            if secret_key[i] == '0':
                qc.x(i)
            qc.h(i)
            qc.cx(i, (i + 1) % n_bits)
            qc.h(i)

        qc.barrier()
        time.sleep(0.05)  # Reduced pause time

        attempts += 1
        print(f"Intentos de ataques: {attempts}", flush=True)

    # Add measurement operations to all qubits
    qc.measure(range(n_bits), range(n_bits))

    # Return after max_attempts instead of looping forever
    return qc, start_time

# Endpoint raíz para verificar que la API está funcionando


@app.get("/")
def read_root():
    return {"message": "API de Ataque Cuántico funcionando correctamente"}

# Endpoint que genera una clave cifrada en Base64


@app.get("/cifrado")
def cifrado():
    ciphertext = encrypt_key()
    print(f"Nueva clave generada: {ciphertext}", flush=True)
    return {"ciphertext": ciphertext}

# Endpoint que cifra el texto ingresado por el usuario


@app.post("/cifrar-texto")
def cifrar_texto(data: TextInput):
    encrypted_text = encrypt_text(data.text)
    print(f"Texto cifrado: {encrypted_text}", flush=True)
    return {"ciphertext": encrypted_text}

# Endpoint que ejecuta el ataque cuántico en la clave cifrada
# Modificación en las declaraciones cuando se activa el ataque


@app.post("/ataque")
def ataque(data: CiphertextInput):
    global delete_attack
    delete_attack.clear()

    sys.stdout.write("\n====== INICIANDO ATAQUE CUÁNTICO ======\n")

    sys.stdout.flush()

    ciphertext = data.ciphertext
    secret_key = base64_to_binary(ciphertext)

    if secret_key is None:
        print("Clave incorrecta, descifrando...", flush=True)
        attempts = 0
        while True:
            time.sleep(0.5)
            attempts += 1
            print(f"Intento de descifrado #{attempts}", flush=True)
            if delete_attack.is_set():
                print("\nAtaque cancelado\n", flush=True)
                return {"message": "Ataque cancelado por el usuario."}

    n_bits = len(secret_key)

    if n_bits > MAX_QUBITS:
        print(
            f"Error: El circuito cuántico no puede superar {MAX_QUBITS} qubits", flush=True)
        return {"error": f"El circuito cuántico no puede superar {MAX_QUBITS} qubits"}

    qc, start_time = custom_quantum_attack(secret_key, n_bits)
    if qc is None:
        return {"message": "Ataque cancelado por el usuario."}

    try:
        print("Ejecutando simulación cuántica...", flush=True)
        backend = Aer.get_backend('qasm_simulator')
        tq = transpile(qc, backend, optimization_level=0)
        job = backend.run(tq, shots=1024)
        result = job.result()
        counts = result.get_counts()
        print("Simulación completada con éxito", flush=True)
    except Exception as e:
        print(f"Error en la simulación cuántica: {str(e)}", flush=True)
        counts = {"error": str(e)}

        attempts = 0
        while True:
            time.sleep(0.5)
            attempts += 1
            print(f"Reintento #{attempts}", flush=True)
            if delete_attack.is_set():
                print("\nAtaque cancelado\n", flush=True)
                return {"message": "Ataque cancelado por el usuario."}

    end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Calcular el tiempo transcurrido

    start_datetime = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
    end_datetime = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
    elapsed_seconds = (end_datetime - start_datetime).total_seconds()

    decrypted_key = base64.b64decode(ciphertext).decode()

    # Salida clara de la terminal con la información

    print("\nRESULTADOS DEL ATAQUE:", flush=True)
    print(f"Fecha de inicio del ataque: {start_time}", flush=True)
    print(f"Fecha de fin del ataque: {end_time}", flush=True)
    print(f"Tiempo transcurrido: {elapsed_seconds:.2f} segundos", flush=True)
    print(f"Clave descifrada: {decrypted_key}", flush=True)
    print("====================================\n", flush=True)

    return {
        "ciphertext": ciphertext,
        "attack_results": counts,
        "execution_time": f"{elapsed_seconds:.2f} segundos",
        "start_time": start_time,
        "end_time": end_time,
        "decrypted_key": decrypted_key
    }

# Endpoint que cancela la ejecución del ataque cuántico


@app.get("/cancel")
def cancel():
    delete_attack.set()
    print("Solicitud de cancelación recibida", flush=True)
    return {"message": "El ataque cuántico ha sido cancelado."}


# uvicorn Reto_Arreglado:app --reload
# uvicorn Tendencias_Reto:app --reload --port 8001

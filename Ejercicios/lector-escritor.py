# MARTINEZ GALLEGOS JESUS

import threading
import time

def acceder(lock, numhilo): # Funcion que recibe el objeto candado y el numero del hilo que lo llama
    lock.acquire() # Pide acceso al candado
    try:
        print('El lector %i accedio a la BD'%numhilo)
        time.sleep(3) # simula la ejecución de una tarea
    finally:
        print("El lector %i dejó de usar la BD"%numhilo)
        lock.release() #Libera el candado


def lector(candado, numhilo):
    print('El lector %i intenta acceder a la BD'%numhilo)
    acceder(candado, numhilo)

lock = threading.Lock()

for i in range(4): #Crea 4 hilos
    t = threading.Thread(target=lector, args=(lock,i,)) # Ejecuta la función del lector en el hilo
    t.start()

main_thread = threading.currentThread()
for t in threading.enumerate():
    if t is not main_thread:
        t.join() #Espera a que terminen todos los hilos
        
print("Todos los lectores terminaron")

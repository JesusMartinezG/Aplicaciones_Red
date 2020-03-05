import socket
import sys
import threading

buff_size = 512

# Variables del juego
juego = None
tamtablero = 0
ganador = 0
primero = True
asignarTurno = 1
sigueJugando = True
tiros = 0
maxtiros = 0
NUM_JUGADORES = 5

def recibir(sock):
    global buff_size
    return sock.recv(buff_size).decode("utf-8")

def enviar(sock, cadena):
    cadena = cadena.encode()
    sock.sendall(cadena)

class Gato:
    tablero = None
    turno = 0

    def __init__(self, siz):
        self.tam = siz
        self.tablero = [[0 for x in range(siz)] for y in range(siz)]  # Crea un tablero de tam x tam lleno de ceros

    def tirar(self, simbolo, coord):
        aux = coord.split(',')
        if len(aux) is not 2: #Valida el formato de las cooredenadas
            return -1
        else:
            aux = [int(x) for x in aux]  # convierte la cadena en un arreglo de enteros
            if aux[0] < 0 or aux[1] < 0 or aux[0] >= self.tam or aux[1] >= self.tam:
                return -1


        if self.tablero[aux[0]][aux[1]] == 0: # Si la posicion elegida está vacía
            self.tablero[aux[0]][aux[1]] = simbolo # Registra el tiro en el tablero
            return self.win(simbolo)  # Retorna el numero del jugador si es que gana con su tiro, si no retorna 0
        else:
            return -1  # Retorna -1 cuando la casilla ya está ocupada

    def imprimir(self):
        for x in range(self.tam):
            for y in range(self.tam):
                print("%i \t" % self.tablero[x][y], end="", flush=True)
            print("\n")

    def win(self, jg):
        winner = False

        for x in range(self.tam):
            aux = True
            for y in range(self.tam):
                aux = aux and (self.tablero[x][y] == jg)  # Es linea vertical
            winner = winner or aux

        if winner:
            return jg

        for y in range(self.tam):
            aux = True
            for x in range(self.tam):
                aux = aux and (self.tablero[x][y] == jg)  # Es linea horizontal
            winner = winner or aux

        if winner:
            return jg

        aux = True
        for x in range(self.tam):
            aux = aux and (self.tablero[x][x] == jg)  # Es Diagonal \

        if aux:
            return jg

        aux = True
        for x in range(self.tam):
            aux = aux and (self.tablero[x][self.tam - 1 - x] == jg)  # es diagonal /

        if aux:
            return jg

        return 0

    def validar(self, arr):
        return arr[0] < 0 or arr[1] < 0 or arr[0] >= self.tam or arr[1] >= self.tam

def gestion_conexiones(listaconexiones):
    for conn in listaconexiones:
        if conn.fileno() == -1:
            listaconexiones.remove(conn)
    print("hilos activos:", threading.active_count())
    print("enum", threading.enumerate())
    print("conexiones: ", len(listaconexiones))
    print(listaconexiones)

def enviaratodos(cadena): # Envia una cadena a todos los clientes registrados en la lista de conexiones
    global listaConexiones # "importa" la lista de clientes conectados
    print("hay %i clientes"%len(listaConexiones))
    cadenabytes = cadena.encode() # convierte en bytes
    for conec in listaConexiones: # Para cada cliente conectado
        conec.sendall(cadenabytes) #Envía la cadena de bytes

def recibir_datos(conn, addr, barrera):  # Intercambio de mensajes con el cliente
    # "Importar" variables globales
    global juego
    global tamtablero
    global ganador
    global primero
    global asignarTurno
    global tiros
    global maxtiros
    global sigueJugando
    global NUM_JUGADORES
    valido = False
    respuesta = ""
    yo = 0

    try:
        cur_thread = threading.current_thread()
        print("Se conectó un cliente")
        print(cur_thread.name,
              'Esperando en la barrera con {} hilos más'.format(barrera.n_waiting))
        worker_id = barrera.wait() # Espera para que se conecten los NUM_JUGADORES clientes

        yo = asignarTurno
        asignarTurno += 1
        enviar(conn,"%i"%yo)
        print("Se han conectado los %i jugadores" % NUM_JUGADORES)

        print("Recibiendo datos del cliente {} en el {}".format(addr, cur_thread.name))
        if yo == 1: #Si es el primer cliente en conectarse
            print("Esperando parametros para crear el tablero")
            respuesta = recibir(conn) #Espera por los parametros del juego
            print("Creando tablero de juego")
            tamtablero = int(respuesta) # tamaño del tablero
            enviaratodos("%i"%(tamtablero)) # envía a todos los clientes el tamaño del tablero para que creen uno local
            juego = Gato(tamtablero)#Crea el tablero de juego con el tamaño elegido
            maxtiros = tamtablero * tamtablero
            print("Tablero creado")

        print("Esperando a que el cliente elija un caracter para usar en el tablero")
        misimbolo = recibir(conn)[0]

        #Intercambio de tiros
        while sigueJugando:
            valido = False
            while not valido: #mientras el tiro no sea valido
                respuesta = recibir(conn)  # Espera el tiro del cliente
                print("Intentando tiro %s"%respuesta)
                coord = respuesta.split(',') # separa las cooredenadas
                resTiro = juego.tirar(yo, respuesta)  # Intenta realizar el tiro
                print("resultado del tiro: %i"% resTiro)
                if resTiro < 0: #Si el tiro no es valido
                    print("Formato invalido recibido")
                    valido = False
                    enviar(conn, "n") #Indica solo al tirador

                else: #Cuando el tiro se recibio correctamente revisa el resultado
                    print("Tiro aceptado")
                    valido = True

            if resTiro == yo:  # Si el resultado es igual al numero de jugador del cliente, entonces él gana
                cadena = "y,n,%i,%s,%s,%s" % (yo, coord[0], coord[1], misimbolo)  # Formato de cadena de tiro [Valido?],[Pedir otro tiro?],[jugador],[coordenadax],[coordenaday],[simbolo]
                print("Enviando: %s"%cadena)
                ganador = yo
                sigueJugando = False
                enviaratodos(cadena) #envia a todos la actualizacion indicando que ganaste
                break;
            else:
                cadena = "y,y,%i,%s,%s,%s" % (yo, coord[0], coord[1], misimbolo)  # Formato de cadena de tiro [Valido?],[Pedir otro tiro?],[jugador],[coordenadax],[coordenaday],[simbolo]
                print("Enviando a todos: %s" % cadena)
                enviaratodos(cadena) #envia a todos la actualizacion
            if tiros == maxtiros: # Si nadie gana
                cadena = "y,n,0"
                print("Enviando a todos: %s" % cadena)
                sigueJugando = False
                break;

            #if not respuesta:
            #    print("Fin")
            #    break

            #conn.sendall(response)
    except Exception as e:
        print(e)
    finally:
        conn.close()


listaConexiones = []
if len(sys.argv) != 4:
    print("usage:", sys.argv[0], "<host> <port> <num_connections>")
    sys.exit(1)

host, port, numConn = sys.argv[1:4]

serveraddr = (host, int(port))

barrera = threading.Barrier(NUM_JUGADORES);

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as TCPServerSocket:
    TCPServerSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    TCPServerSocket.bind(serveraddr)
    TCPServerSocket.listen(int(numConn))
    print("El servidor TCP está disponible y en espera de solicitudes")

    try:
        while True: # Escuchar por infinitos clientes
            client_conn, client_addr = TCPServerSocket.accept() #Aceptar al cliente
            print("Conectado a", client_addr)

            listaConexiones.append(client_conn)
            thread_read = threading.Thread(target=recibir_datos, args=[client_conn, client_addr, barrera])  # Crea un hilo que ejecuta la función recivir_datos
            thread_read.start()  # Inicia la ejecución del hilo
            gestion_conexiones(listaConexiones)  # Añade un registro del hilo creado
    except Exception as e:
        print(e)

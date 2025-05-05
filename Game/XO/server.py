import socket
import threading
import random

HOST = '127.0.0.1'
PORT = 5555

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

try:
    server_socket.bind((HOST, PORT))
except OSError as e:
    print(f"[ERROR] Không thể bind port {PORT}: {e}")
    exit(1)

server_socket.listen()

rooms = {}
clients = {}

def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    room_id = None
    player = None

    try:
        while True:
            msg = conn.recv(1024).decode()
            if not msg:
                break

            print(f"[RECEIVED] {addr}: {msg}")

            if msg == "CREATE_ROOM":
                room_id = str(random.randint(1000, 9999))
                rooms[room_id] = [conn]
                clients[conn] = room_id
                conn.send(f"ROOM_CREATED {room_id}".encode())
                player = "X"
                conn.send(f"ASSIGN_ROLE {player}".encode())

            elif msg.startswith("JOIN_ROOM"):
                room_id = msg.split()[1]
                if room_id in rooms and len(rooms[room_id]) == 1:
                    rooms[room_id].append(conn)
                    clients[conn] = room_id
                    player = "O"
                    conn.send("JOIN_SUCCESS".encode())
                    conn.send(f"ASSIGN_ROLE {player}".encode())
                    rooms[room_id][0].send("OPPONENT_JOINED".encode())
                else:
                    conn.send("JOIN_FAILED".encode())

            elif msg.startswith("MOVE"):
                room_id = clients.get(conn)
                if room_id:
                    for client in rooms[room_id]:
                        if client != conn:
                            client.send(msg.encode())

            elif msg.startswith("RESET_GAME"):
                room_id = clients.get(conn)
                if room_id:
                    for client in rooms[room_id]:
                        client.send("GAME_RESET".encode())

    except Exception as e:
        print(f"[ERROR] Exception in client handler {addr}: {e}")
    finally:
        print(f"[DISCONNECT] {addr} disconnected.")
        if conn in clients:
            room_id = clients[conn]
            if room_id in rooms:
                rooms[room_id].remove(conn)
                if not rooms[room_id]:
                    del rooms[room_id]
                else:
                    other_client = rooms[room_id][0]
                    other_client.send("OPPONENT_LEFT".encode())
            del clients[conn]
        conn.close()

def start_server():
    print(f"[STARTED] Server listening on {HOST}:{PORT}")
    try:
        while True:
            conn, addr = server_socket.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
    finally:
        server_socket.close()

if __name__ == "__main__":
    start_server()

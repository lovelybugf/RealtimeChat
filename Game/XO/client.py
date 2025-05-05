import socket
import threading
from tkinter import *
from tkinter import simpledialog, messagebox
from PIL import Image, ImageTk
import random
import pygame

# ----- SOCKET SETUP -----
HOST = '127.0.0.1'
PORT = 5555
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))

player = ""
opponent = ""
turn = "X"
game_over = False
buttons = []
game_window = None
score = {"X": 0, "O": 0}

pygame.mixer.init()

background_music = pygame.mixer.Sound("Game/XO/sounds/nen.mp3")  
win_sound = pygame.mixer.Sound("Game/XO/sounds/win.mp3")  
lose_sound = pygame.mixer.Sound("Game/XO/sounds/lose.mp3") 
draw_sound = pygame.mixer.Sound("Game/XO/sounds/draw.mp3")


background_music.set_volume(0.2)
background_music.play()  


def create_room():
    client_socket.send("CREATE_ROOM".encode())

def join_room():
    room_id = simpledialog.askstring("Nhập mã phòng", "Nhập ID phòng muốn tham gia:")
    if room_id:
        client_socket.send(f"JOIN_ROOM {room_id}".encode())

def listen_server():
    global player, opponent, game_window
    while True:
        try:
            msg = client_socket.recv(1024).decode()
            print(f"[DEBUG] Received from server: {msg}")

            if msg.startswith("ROOM_CREATED"):
                room_id = msg.split()[1]
                room_label.config(text=f"Mã phòng: {room_id}")
                status_label.config(text="Chờ người chơi khác...")

            elif msg.startswith("ASSIGN_ROLE"):
                player = msg.split()[1]
                opponent = "O" if player == "X" else "X"
                print(f"[INFO] Bạn được gán là {player}")

            elif msg == "JOIN_SUCCESS" or msg == "OPPONENT_JOINED":
                root.after(0, update_game_start)

            elif msg.startswith("MOVE"):
                _, row, col, current_player = msg.split()
                handle_opponent_move(int(row), int(col), current_player)

            elif msg == "OPPONENT_LEFT":
                messagebox.showinfo("Thông báo", "Đối thủ đã thoát khỏi phòng.")
                if game_window:
                    game_window.destroy()

            elif msg == "GAME_RESET":
                reset_game()
        except Exception as e:
            print(f"[ERROR] {e}")
            break

def update_game_start():
    root.destroy()
    run_game_window()

def run_game_window():
    global buttons, label, turn_label, player_label, game_over, turn, game_window, score_label
    game_window = Tk()
    game_window.title("Caro Online")
    game_window.geometry("600x700")

    turn = random.choice(["X", "O"])
    game_over = False
    buttons = [[None for _ in range(10)] for _ in range(10)]

    Label(game_window, text="Lượt của bạn", font=('consolas', 20)).pack(side="top")
    player_label = Label(game_window, text=f"Bạn chơi: {player}", font=('consolas', 15))
    player_label.pack(side="top")
    turn_label = Label(game_window, text=f"Lượt của người chơi: {turn}", font=('consolas', 15))
    turn_label.pack(side="top", pady=10)
    score_label = Label(game_window, text=f"Điểm - X: {score['X']} | O: {score['O']}", font=('consolas', 14))
    score_label.pack()

    Button(game_window, text="Game mới", font=('consolas', 12), command=new_game).pack(pady=5)

    frame = Frame(game_window)
    frame.pack()

    for row in range(10):
        for col in range(10):
            buttons[row][col] = Button(frame, text="", font=('consolas', 15), width=3, height=1,
                                       command=lambda r=row, c=col: next_turn(r, c))
            buttons[row][col].grid(row=row, column=col, padx=1, pady=1)

    game_window.mainloop()

def next_turn(row, col):
    global turn, game_over
    if game_over:
        return
    if buttons[row][col]["text"] == "" and turn == player:
        buttons[row][col]["text"] = player
        client_socket.send(f"MOVE {row} {col} {player}".encode())
        result, cells = winner()
        if result is True:
            win_sound.play()
            turn_label.config(text="Bạn thắng!")
            for r, c in cells:
                buttons[r][c].config(bg="lightgreen")
            game_over = True
            score[player] += 1
            update_score()
        elif result == "Hòa":
            draw_sound.play()
            turn_label.config(text="Hòa")
            game_over = True
        else:
            turn = opponent
            turn_label.config(text=f"Lượt của người chơi: {turn}")

def handle_opponent_move(row, col, current_player):
    global turn, game_over
    if buttons[row][col]["text"] == "":
        buttons[row][col]["text"] = current_player
        result, cells = winner()
        if result is True:
            lose_sound.play()
            turn_label.config(text="Bạn thua!")
            for r, c in cells:
                buttons[r][c].config(bg="lightcoral")
            game_over = True
            score[current_player] += 1
            update_score()
        elif result == "Hòa":
            draw_sound.play()
            turn_label.config(text="Hòa")
            game_over = True
        else:
            turn = player
            turn_label.config(text=f"Lượt của người chơi: {turn}")

def update_score():
    score_label.config(text=f"Điểm - X: {score['X']} | O: {score['O']}")

def new_game():
    global turn, game_over
    turn = random.choice(["X", "O"])
    game_over = False
    client_socket.send("RESET_GAME".encode())
    for row in range(10):
        for col in range(10):
            buttons[row][col].config(text="", bg="SystemButtonFace")
    turn_label.config(text=f"Lượt của người chơi: {turn}")

    client_socket.send("OPPONENT_LEFT".encode())

def reset_game():
    global turn, game_over
    game_over = False
    turn = random.choice(["X", "O"])
    for row in range(10):
        for col in range(10):
            buttons[row][col].config(text="", bg="SystemButtonFace")
    turn_label.config(text=f"Lượt của người chơi: {turn}")

def winner():
    for row in range(10):
        for col in range(6):
            mark = buttons[row][col]["text"]
            if mark != "" and all(buttons[row][col + i]["text"] == mark for i in range(5)):
                return True, [(row, col + i) for i in range(5)]
    for col in range(10):
        for row in range(6):
            mark = buttons[row][col]["text"]
            if mark != "" and all(buttons[row + i][col]["text"] == mark for i in range(5)):
                return True, [(row + i, col) for i in range(5)]
    for row in range(6):
        for col in range(6):
            mark = buttons[row][col]["text"]
            if mark != "" and all(buttons[row + i][col + i]["text"] == mark for i in range(5)):
                return True, [(row + i, col + i) for i in range(5)]
    for row in range(6):
        for col in range(4, 10):
            mark = buttons[row][col]["text"]
            if mark != "" and all(buttons[row + i][col - i]["text"] == mark for i in range(5)):
                return True, [(row + i, col - i) for i in range(5)]
    full = all(buttons[row][col]["text"] != "" for row in range(10) for col in range(10))
    if full:
        return "Hòa", []
    return False, []

root = Tk()
root.title("Caro Online - Chọn chế độ")
root.geometry("600x650")

try:
    img = Image.open("Game/XO/logo.png")
    img = img.resize((400, 400))
    photo = ImageTk.PhotoImage(img)
    img_label = Label(root, image=photo)
    img_label.image = photo
    img_label.pack(pady=10)
except Exception as e:
    print(f"[ERROR] Không thể load ảnh: {e}")

Button(root, text="Tạo phòng", font=('consolas', 20), command=create_room).pack(pady=10)
Button(root, text="Tham gia phòng", font=('consolas', 20), command=join_room).pack(pady=10)

room_label = Label(root, text="", font=('consolas', 15))
room_label.pack()
status_label = Label(root, text="", font=('consolas', 15))
status_label.pack()

threading.Thread(target=listen_server, daemon=True).start()
root.mainloop()

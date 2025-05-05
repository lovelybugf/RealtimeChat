import pygame
import random
import asyncio
import uuid
from pygame import mixer
from PIL import Image
import io

pygame.init()
mixer.init()

eat_sound = mixer.Sound("Game/Ransanmoi/sound/eat.mp3")
death_sound = mixer.Sound("Game/Ransanmoi/sound/deadsound.mp3")
background_music = "Game/Ransanmoi/sound/background.mp3"

mixer.music.load(background_music)
mixer.music.play(loops=-1, start=0.0) 
mixer.music.set_volume(0.5)

Game_width = 1000
Game_height = 700
Space = 50
Body = 3
Speed = 50
Snake_Color = (0, 255, 0) 
Food_Color = (255, 0, 0)  

screen = pygame.display.set_mode((Game_width, Game_height))
pygame.display.set_caption("Rắn Săn Mồi")


snake_head_img = pygame.image.load('Game/Ransanmoi/image/snake.png')
snake_head_img = pygame.transform.scale(snake_head_img, (50, 50))
snake_head_images = {
    'down': snake_head_img,
    'up': pygame.transform.rotate(snake_head_img, 180),
    'left': pygame.transform.rotate(snake_head_img, 270),
    'right': pygame.transform.rotate(snake_head_img, 90)
}

body_img = pygame.image.load('Game/Ransanmoi/image/body.png')
body_img = pygame.transform.scale(body_img, (50, 50))

apple_img = pygame.image.load('Game/Ransanmoi/image/apple.png')
apple_img = pygame.transform.scale(apple_img, (50, 50))

additional_image = pygame.image.load('Game/Ransanmoi/image/rank.png')
additional_image = pygame.transform.scale(additional_image, (350, 350))

def load_gif_frames(gif_path):
    gif = Image.open(gif_path)
    frames = []
    try:
        while True:
            frame = gif.copy()
            frame = frame.convert('RGBA')  
            pygame_frame = pygame.image.fromstring(frame.tobytes(), frame.size, 'RGBA')  
            pygame_frame = pygame.transform.scale(pygame_frame, (Game_width, Game_height))
            frames.append(pygame_frame)
            gif.seek(gif.tell() + 1)
    except EOFError:
        pass
    return frames, gif.info.get('duration', 100) / 1000 


gif_frames, frame_duration = load_gif_frames('Game/Ransanmoi/image/menu.gif') 
current_frame = 0
last_frame_time = 0

background_png = pygame.image.load('Game/Ransanmoi/image/gameplay.png')
background_png = pygame.transform.scale(background_png, (Game_width, Game_height))

font = pygame.font.SysFont('consolas', 40)
small_font = pygame.font.SysFont('consolas', 20)

MENU = 0
PLAYING = 1
GAME_OVER = 2
RANKING = 3
game_state = MENU


score = 0
direction = 'down'
player_name = ""
input_text = ""
snake = None
food = None
scores = []

class Snake:
    def __init__(self):
        self.body = Body
        self.coordinates = [[0, 0] for _ in range(Body)]
        self.squares = []

class Food:
    def __init__(self):
        x = random.randrange(0, (Game_width // Space) - 1) * Space
        y = random.randrange(0, (Game_height // Space) - 1) * Space
        self.coordinates = [x, y]

def draw_grid():
    for x in range(0, Game_width, Space):
        pygame.draw.line(screen, (34, 34, 34), (x, 0), (x, Game_height))
    for y in range(0, Game_height, Space):
        pygame.draw.line(screen, (34, 34, 34), (0, y), (Game_width, y))

def generate_food(snake):
    while True:
        x = random.randint(0, (Game_width - Space) // Space) * Space
        y = random.randint(0, (Game_height - Space) // Space) * Space
        if [x, y] not in snake.coordinates:
            return [x, y]


def next_turn():
    global score, snake, food, game_state, Speed
    x, y = snake.coordinates[0]
    if direction == "up":
        y -= Space
    elif direction == "down":
        y += Space
    elif direction == "right":
        x += Space
    elif direction == "left":
        x -= Space
    
    snake.coordinates.insert(0, [x, y])
    
    if x == food.coordinates[0] and y == food.coordinates[1]:
        eat_sound.play()
        score += 1
        if Speed>=25:
            Speed -= 1
        food = Food()
        food.coordinates = generate_food(snake)

    else:
        snake.coordinates.pop()

    if check_collisions():
        gameover()
        game_state = GAME_OVER

def check_collisions():
    x, y = snake.coordinates[0]
    if x < 0 or x >= Game_width or y < 0 or y >= Game_height:
        return True
    for body in snake.coordinates[1:]:
        if x == body[0] and y == body[1]:
            return True
    return False

def gameover():
    global scores
    death_sound.play()
    scores.append((player_name, score))
    save_score(score, player_name)

def save_score(score, name):
    try:
        with open("Game/Ransanmoi/scores1.txt", "a") as file:
            file.write(f"{name}:{score}\n")
    except Exception as e:
        print(f"Không thể lưu điểm: {e}")

def load_scores():
    global scores
    try:
        with open("Game/Ransanmoi/scores1.txt", "r") as file:
            lines = file.readlines()
        scores = [(s.strip().split(':')[0], int(s.strip().split(':')[1])) for s in lines]
        scores.sort(key=lambda x: x[1], reverse=True)
    except Exception as e:
        print(f"Không thể đọc bảng xếp hạng: {e}")
        scores = []

def draw_menu():
    global current_frame, last_frame_time
    current_time = pygame.time.get_ticks() / 1000
    if current_time - last_frame_time >= frame_duration:
        current_frame = (current_frame + 1) % len(gif_frames)
        last_frame_time = current_time

    screen.blit(gif_frames[current_frame], (0, 0))

    title = font.render("RẮN SĂN MỒI", True, (255, 255, 255))
    screen.blit(title, (Game_width // 2 - title.get_width() // 2, Game_height // 2 - 100))

    name_label = small_font.render("Tên người chơi:", True, (255, 255, 255))
    screen.blit(name_label, (Game_width // 2 - name_label.get_width() // 2, Game_height // 2 - 20))

    pygame.draw.rect(screen, (255, 255, 255), (Game_width // 2 - 150, Game_height // 2 + 10, 300, 40), 2)
    input_surface = small_font.render(input_text, True, (255, 255, 255))
    screen.blit(input_surface, (Game_width // 2 - 140, Game_height // 2 + 20))

    play_button = pygame.Rect(Game_width // 2 - 50, Game_height // 2 + 70, 100, 40)
    pygame.draw.rect(screen, (255, 255, 255), play_button, 2)
    play_text = small_font.render("Chơi", True, (255, 255, 255))
    screen.blit(play_text, (play_button.x + 20, play_button.y + 10))

    return play_button

def draw_game():
    screen.blit(background_png, (0, 0))
    draw_grid()

    for i, (x, y) in enumerate(snake.coordinates):
        if i == 0:
            screen.blit(snake_head_images[direction], (x, y))
        else:
            #pygame.draw.rect(screen, Snake_Color, (x, y, Space, Space))
            screen.blit(body_img, (x, y))  

    screen.blit(apple_img, (food.coordinates[0], food.coordinates[1]))

    score_text = font.render(f"Score: {score}", True, (255, 255, 255))
    screen.blit(score_text, (Game_width // 2 - score_text.get_width() // 2, 10))

def draw_game_over():
    screen.blit(background_png, (0, 0))

    large_font = pygame.font.SysFont('consolas', 80) 
    game_over_text = large_font.render("GAME OVER", True, (255, 255, 255))
    screen.blit(game_over_text, (Game_width // 2 - game_over_text.get_width() // 2, Game_height // 2 - 100))

    restart_button = pygame.Rect(10, 10, 100, 40)
    pygame.draw.rect(screen, (255, 255, 255), restart_button, 2)
    restart_text = small_font.render("Restart", True, (255, 255, 255))
    screen.blit(restart_text, (restart_button.x + 10, restart_button.y + 10))

    rank_button = pygame.Rect(Game_width - 110, 10, 100, 40)
    pygame.draw.rect(screen, (255, 255, 255), rank_button, 2)
    rank_text = small_font.render("Xếp hạng", True, (255, 255, 255))
    screen.blit(rank_text, (rank_button.x + 10, rank_button.y + 10))

    return restart_button, rank_button


def draw_ranking():
    
    global current_frame, last_frame_time
    current_time = pygame.time.get_ticks() / 1000
    if current_time - last_frame_time >= frame_duration:
        current_frame = (current_frame + 1) % len(gif_frames)
        last_frame_time = current_time
    
    screen.blit(gif_frames[current_frame], (0, 0))
    screen.blit(additional_image, (Game_width // 2 - additional_image.get_width() // 2, Game_height // 2 - 130))
    
    title = small_font.render("Top 5 điểm cao nhất", True, (139, 69, 19))
    screen.blit(title, (Game_width // 2 - title.get_width() // 2, Game_height // 2 - 50))

    top_scores = scores[:5]
    for i, (name, s) in enumerate(top_scores):
        score_text = small_font.render(f"{i+1}. {name}: {s}", True, (139, 69, 19))
        screen.blit(score_text, (Game_width // 2 - score_text.get_width() // 2, Game_height // 2 + i * 30))

    back_button = pygame.Rect(Game_width // 2 - 50, Game_height // 2 + 150, 100, 40)
    pygame.draw.rect(screen, (139, 69, 19), back_button, 2)
    back_text = small_font.render("Quay lại", True, (139, 69, 19))
    screen.blit(back_text, (back_button.x + 10, back_button.y + 10))

    return back_button

async def main():
    global game_state, input_text, player_name, snake, food, score, direction, Speed
    clock = pygame.time.Clock()
    load_scores()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

            if game_state == MENU:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        player_name = input_text if input_text else f"Player_{uuid.uuid4().hex[:6]}"
                        game_state = PLAYING
                        score = 0
                        direction = 'down'
                        snake = Snake()
                        food = Food()
                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    else:
                        input_text += event.unicode

                if event.type == pygame.MOUSEBUTTONDOWN:
                    play_button = draw_menu()
                    if play_button.collidepoint(event.pos):
                        player_name = input_text if input_text else f"Player_{uuid.uuid4().hex[:6]}"
                        game_state = PLAYING
                        score = 0
                        direction = 'down'
                        snake = Snake()
                        food = Food()

            elif game_state == PLAYING:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT and direction != 'right':
                        direction = 'left'
                    elif event.key == pygame.K_RIGHT and direction != 'left':
                        direction = 'right'
                    elif event.key == pygame.K_UP and direction != 'down':
                        direction = 'up'
                    elif event.key == pygame.K_DOWN and direction != 'up':
                        direction = 'down'

            elif game_state == GAME_OVER:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    restart_button, rank_button = draw_game_over()
                    if restart_button.collidepoint(event.pos):
                        game_state = PLAYING
                        score = 0
                        Speed = 60
                        direction = 'down'
                        snake = Snake()
                        food = Food()
                    elif rank_button.collidepoint(event.pos):
                        game_state = RANKING
                        load_scores()

            elif game_state == RANKING:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    back_button = draw_ranking()
                    if back_button.collidepoint(event.pos):
                        game_state = MENU
                        input_text = ""

        if game_state == MENU:
            draw_menu()
        elif game_state == PLAYING:
            next_turn()
            draw_game()
        elif game_state == GAME_OVER:
            draw_game_over()
        elif game_state == RANKING:
            draw_ranking()

        pygame.display.flip()
        clock.tick(1000 // Speed)
        await asyncio.sleep(0)

asyncio.run(main())
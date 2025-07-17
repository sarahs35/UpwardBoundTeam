import pygame
import sys
import os
import random

pygame.init()

# --- Constants ---
WIDTH, HEIGHT = 1000, 600
FPS = 60
PLAYER_SPEED = 5
BALL_SPEED = 6
SCORE_LIMIT = 5
BALL_FRICTION = 0.98
BOUNCE_FACTOR = 1.05
SPEED_BOOST_TIME = 2000  # milliseconds

# --- Screen Setup ---
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("2-Player Soccer Pong")
clock = pygame.time.Clock()

# --- Fonts ---
font = pygame.font.SysFont("Arial", 36)
button_font = pygame.font.SysFont("Arial", 48)
emoji_font = pygame.font.SysFont("Segoe UI Emoji", 100)  # Windows fallback

# --- Load Assets ---
def load_image(name, size=(60, 60)):
    return pygame.transform.scale(pygame.image.load(os.path.join("assets", name)), size)

teams = {
    "blue": "player1.png",
    "red": "player2.png"
}
stadiums = {
    "grass": "background_grass.jpg"
}
player1_img = load_image(teams["blue"])
player2_img = load_image(teams["red"])
background_img = pygame.transform.scale(pygame.image.load(os.path.join("assets", stadiums["grass"])), (WIDTH, HEIGHT))

pygame.mixer.music.load(os.path.join("assets", "music.mp3"))
pygame.mixer.music.set_volume(0.5)
pygame.mixer.music.play(-1)

hit_sound = pygame.mixer.Sound(os.path.join("assets", "kick.mp3"))
hit_sound.set_volume(0.6)

# --- Game Classes ---
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, controls, image):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(center=(x, y))
        self.controls = controls
        self.prev_pos = self.rect.center
        self.speed_boost = False
        self.boost_timer = 0

    def update(self):
        self.prev_pos = self.rect.center
        keys = pygame.key.get_pressed()
        speed = PLAYER_SPEED * 2 if self.speed_boost else PLAYER_SPEED
        if self.speed_boost and pygame.time.get_ticks() - self.boost_timer > SPEED_BOOST_TIME:
            self.speed_boost = False

        if keys[self.controls['up']]: self.rect.y -= speed
        if keys[self.controls['down']]: self.rect.y += speed
        if keys[self.controls['left']]: self.rect.x -= speed
        if keys[self.controls['right']]: self.rect.x += speed
        self.rect.clamp_ip(screen.get_rect())

    def velocity(self):
        dx = self.rect.centerx - self.prev_pos[0]
        dy = self.rect.centery - self.prev_pos[1]
        return pygame.Vector2(dx, dy)

    def apply_boost(self):
        self.speed_boost = True
        self.boost_timer = pygame.time.get_ticks()

class Ball(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.transform.scale(pygame.image.load(os.path.join("assets", "ball.png")).convert_alpha(), (30, 30))
        self.rect = self.image.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        self.vel = pygame.Vector2(0, 0)

    def update(self):
        self.rect.x += self.vel.x
        self.rect.y += self.vel.y
        self.vel *= BALL_FRICTION

        # Bounce walls
        if self.rect.top <= 0 or self.rect.bottom >= HEIGHT:
            self.vel.y = -self.vel.y * BOUNCE_FACTOR

        if self.rect.left <= 0:
            self.rect.left = 0
            self.vel.x = -self.vel.x * BOUNCE_FACTOR
        elif self.rect.right >= WIDTH:
            self.rect.right = WIDTH
            self.vel.x = -self.vel.x * BOUNCE_FACTOR

        # Goal detection
        if self.rect.left <= 0 and HEIGHT * 0.25 <= self.rect.centery <= HEIGHT * 0.75:
            return "player2"
        if self.rect.right >= WIDTH and HEIGHT * 0.25 <= self.rect.centery <= HEIGHT * 0.75:
            return "player1"

        return None

    def apply_force(self, force):
        self.vel += force

    def reset(self):
        self.rect.center = (WIDTH // 2, HEIGHT // 2)
        self.vel = pygame.Vector2(0, 0)

# --- Setup ---
player1 = Player(80, HEIGHT // 2, {'up': pygame.K_w, 'down': pygame.K_s, 'left': pygame.K_a, 'right': pygame.K_d}, player1_img)
player2 = Player(WIDTH - 80, HEIGHT // 2, {'up': pygame.K_UP, 'down': pygame.K_DOWN, 'left': pygame.K_LEFT, 'right': pygame.K_RIGHT}, player2_img)
ball = Ball()
players = pygame.sprite.Group(player1, player2)
ball_group = pygame.sprite.Group(ball)
score = {"player1": 0, "player2": 0}

# --- State ---
game_state = "home"
winner = None
paused = False

# --- Buttons ---
start_text = button_font.render("Press Start", True, (255, 255, 255))
start_rect = start_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 100))

# --- Main Loop ---
running = True
while running:
    clock.tick(FPS)
    screen.fill((0, 0, 0))

    # Handle Events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if game_state == "home":
            if event.type == pygame.MOUSEBUTTONDOWN and start_rect.collidepoint(event.pos):
                score = {"player1": 0, "player2": 0}
                ball.reset()
                game_state = "play"
                pygame.mixer.music.play(-1)

        if game_state == "gameover":
            if event.type == pygame.MOUSEBUTTONDOWN:
                if replay_rect.collidepoint(event.pos):
                    score = {"player1": 0, "player2": 0}
                    ball.reset()
                    player1.rect.center = (80, HEIGHT // 2)
                    player2.rect.center = (WIDTH - 80, HEIGHT // 2)
                    game_state = "play"
                    winner = None
                    pygame.mixer.music.play(-1)
                elif quit_rect.collidepoint(event.pos):
                    running = False

        if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
            paused = not paused

    # --- HOME ---
    if game_state == "home":
        screen.fill((255, 182, 193))
        title = font.render("2-Player Soccer Pong", True, (255, 255, 255))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 2 - 100))
        pygame.draw.rect(screen, (50, 150, 50), start_rect.inflate(20, 20))
        screen.blit(start_text, start_rect)
        pygame.display.flip()
        continue

    # --- GAME OVER ---
    if game_state == "gameover":
        screen.fill((255, 224, 192))

        # Message only (no smiley)
        msg = font.render("Thanks for playing!", True, (80, 40, 0))
        screen.blit(msg, msg.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40)))


        # Quit button
        quit_text = button_font.render("Quit", True, (255, 255, 255))
        quit_rect = quit_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 100))
        pygame.draw.rect(screen, (200, 80, 80), quit_rect.inflate(30, 20))
        screen.blit(quit_text, quit_rect)

        # Replay button
        replay_text = button_font.render("Play Again", True, (255, 255, 255))
        replay_rect = replay_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 170))
        pygame.draw.rect(screen, (100, 150, 200), replay_rect.inflate(30, 20))
        screen.blit(replay_text, replay_rect)

        pygame.display.flip()
        continue

    # --- GAMEPLAY ---
    if not paused:
        screen.blit(background_img, (0, 0))
        pygame.draw.rect(screen, (0, 0, 255), (0, HEIGHT * 0.25, 10, HEIGHT * 0.5))  # Blue goal
        pygame.draw.rect(screen, (255, 0, 0), (WIDTH - 10, HEIGHT * 0.25, 10, HEIGHT * 0.5))  # Red goal

        players.update()
        scorer = ball.update()

        if scorer:
            score[scorer] += 1
            ball.reset()

        if score["player1"] >= SCORE_LIMIT:
            winner = "Blue"
            game_state = "gameover"
        elif score["player2"] >= SCORE_LIMIT:
            winner = "Red"
            game_state = "gameover"

        for player in [player1, player2]:
            if pygame.sprite.collide_rect(ball, player):
                direction = pygame.Vector2(ball.rect.center) - pygame.Vector2(player.rect.center)
                if direction.length() == 0:
                    direction = pygame.Vector2(1, 0)
                direction = direction.normalize() * BALL_SPEED
                ball.apply_force(direction + player.velocity())
                hit_sound.play()

        if pygame.sprite.collide_rect(player1, player2):
            overlap = pygame.Vector2(player2.rect.center) - pygame.Vector2(player1.rect.center)
            if overlap.length() > 0:
                overlap = overlap.normalize()
                player1.rect.x -= int(overlap.x)
                player1.rect.y -= int(overlap.y)
                player2.rect.x += int(overlap.x)
                player2.rect.y += int(overlap.y)

        for player in [player1, player2]:
            if pygame.sprite.collide_rect(ball, player):
                if player.velocity().length() > 3:
                    player.apply_boost()
    else:
        pause_text = font.render("Paused - Press P to Resume", True, (255, 255, 255))
        screen.blit(pause_text, (WIDTH // 2 - pause_text.get_width() // 2, HEIGHT // 2))

    players.draw(screen)
    ball_group.draw(screen)
    score_text = font.render(f"Blue: {score['player1']}   Red: {score['player2']}", True, (255, 255, 255))
    screen.blit(score_text, (WIDTH // 2 - 150, 20))

    pygame.display.flip()

pygame.quit()
sys.exit()

import pygame
import sys
import os
import math

pygame.init()

# --- Constants ---
WIDTH, HEIGHT = 1000, 600
FPS = 60
PLAYER_SPEED = 5
BALL_SPEED = 6
SCORE_LIMIT = 5
BALL_FRICTION = 0.98
BOUNCE_FACTOR = 1.05
GOAL_WIDTH = 100  # Goal zone width

# --- Screen ---
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("2-Player Soccer Pong")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 36)

# --- Load Assets ---
def load_image(name, size=(60, 60)):
    return pygame.transform.scale(pygame.image.load(os.path.join("assets", name)), size)

# Available teams and stadiums
teams = {
    "blue": "player1.png",
    "red": "player2.png"
}

stadiums = {
    "grass": "background_grass.jpg",
    "street": "background_grass.jpg"
}

player1_team = "blue"
player2_team = "red"
stadium_choice = "grass"

player1_img = load_image(teams[player1_team])
player2_img = load_image(teams[player2_team])
background_img = pygame.transform.scale(
    pygame.image.load(os.path.join("assets", stadiums[stadium_choice])), (WIDTH, HEIGHT)
)

# --- Load Sounds ---
pygame.mixer.music.load(os.path.join("assets", "music.mp3"))
pygame.mixer.music.set_volume(0.5)
pygame.mixer.music.play(-1)

hit_sound = pygame.mixer.Sound(os.path.join("assets", "kick.mp3"))
hit_sound.set_volume(0.6)

# --- Classes ---
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, controls, image):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(center=(x, y))
        self.controls = controls
        self.prev_pos = self.rect.center

    def update(self):
        self.prev_pos = self.rect.center
        keys = pygame.key.get_pressed()
        if keys[self.controls['up']]:
            self.rect.y -= PLAYER_SPEED
        if keys[self.controls['down']]:
            self.rect.y += PLAYER_SPEED
        if keys[self.controls['left']]:
            self.rect.x -= PLAYER_SPEED
        if keys[self.controls['right']]:
            self.rect.x += PLAYER_SPEED

        # Wall collision (full field boundaries)
        self.rect.left = max(self.rect.left, 0)
        self.rect.right = min(self.rect.right, WIDTH)
        self.rect.top = max(self.rect.top, 0)
        self.rect.bottom = min(self.rect.bottom, HEIGHT)

    def velocity(self):
        dx = self.rect.centerx - self.prev_pos[0]
        dy = self.rect.centery - self.prev_pos[1]
        return pygame.Vector2(dx, dy)

class Ball(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (255, 255, 255), (15, 15), 15)
        self.rect = self.image.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        self.vel = pygame.Vector2(0, 0)

    def update(self):
        self.rect.x += self.vel.x
        self.rect.y += self.vel.y
        self.vel *= BALL_FRICTION

        # Top/bottom bounce
        if self.rect.top <= 0 or self.rect.bottom >= HEIGHT:
            self.vel.y = -self.vel.y * BOUNCE_FACTOR

        # Left goal (Red team goal)
        if self.rect.left <= 0 and HEIGHT * 0.25 <= self.rect.centery <= HEIGHT * 0.75:
            return "player2"
        # Right goal (Blue team goal)
        if self.rect.right >= WIDTH and HEIGHT * 0.25 <= self.rect.centery <= HEIGHT * 0.75:
            return "player1"

        return None

    def apply_force(self, force):
        self.vel += force

    def reset(self):
        self.rect.center = (WIDTH // 2, HEIGHT // 2)
        self.vel = pygame.Vector2(0, 0)

# --- Setup ---
player1 = Player(80, HEIGHT // 2, {
    'up': pygame.K_w, 'down': pygame.K_s, 'left': pygame.K_a, 'right': pygame.K_d
}, player1_img)

player2 = Player(WIDTH - 80, HEIGHT // 2, {
    'up': pygame.K_UP, 'down': pygame.K_DOWN, 'left': pygame.K_LEFT, 'right': pygame.K_RIGHT
}, player2_img)

ball = Ball()

players = pygame.sprite.Group(player1, player2)
ball_group = pygame.sprite.Group(ball)
score = {"player1": 0, "player2": 0}

# --- Main Loop ---
running = True
while running:
    clock.tick(FPS)
    screen.blit(background_img, (0, 0))

    # Draw goal zones
    pygame.draw.rect(screen, (0, 0, 255, 50), (0, HEIGHT * 0.25, 10, HEIGHT * 0.5))  # Left goal
    pygame.draw.rect(screen, (255, 0, 0, 50), (WIDTH - 10, HEIGHT * 0.25, 10, HEIGHT * 0.5))  # Right goal

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    players.update()
    scorer = ball.update()

    if scorer:
        score[scorer] += 1
        ball.reset()

    # Ball collision with players
    for player in [player1, player2]:
        if pygame.sprite.collide_rect(ball, player):
            direction = pygame.Vector2(ball.rect.center) - pygame.Vector2(player.rect.center)
            if direction.length() == 0:
                direction = pygame.Vector2(1, 0)
            direction = direction.normalize() * BALL_SPEED
            ball.apply_force(direction + player.velocity())
            hit_sound.play()

    # Prevent player overlap
    if pygame.sprite.collide_rect(player1, player2):
        overlap = pygame.Vector2(player2.rect.center) - pygame.Vector2(player1.rect.center)
        if overlap.length() > 0:
            overlap = overlap.normalize()
            player1.rect.x -= int(overlap.x)
            player1.rect.y -= int(overlap.y)
            player2.rect.x += int(overlap.x)
            player2.rect.y += int(overlap.y)

    players.draw(screen)
    ball_group.draw(screen)

    score_text = font.render(f"Blue: {score['player1']}   Red: {score['player2']}", True, (255, 255, 255))
    screen.blit(score_text, (WIDTH // 2 - 150, 20))

    # Win condition
    if score['player1'] >= SCORE_LIMIT:
        win_text = font.render("Blue Wins!", True, (0, 200, 255))
        screen.blit(win_text, (WIDTH // 2 - 100, HEIGHT // 2))
    elif score['player2'] >= SCORE_LIMIT:
        win_text = font.render("Red Wins!", True, (255, 50, 50))
        screen.blit(win_text, (WIDTH // 2 - 100, HEIGHT // 2))

    pygame.display.flip()

pygame.quit()
sys.exit()

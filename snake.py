import pygame
import random
import os
import math
from collections import deque
import sys
import json

def load_high_score(filepath):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
                return data.get("high_score", 0)
        except Exception:
            return 0
    return 0

def save_high_score(filepath, score):
    try:
        with open(filepath, "w") as f:
            json.dump({"high_score": score}, f)
    except Exception as e:
        print(f"Could not save high score: {e}")


# --- CORE GAME ENGINE ---
class SnakeGame:
    def __init__(self, width=20, height=15):
        self.width = width
        self.height = height
        start_pos = (width // 2, height // 2)
        self.snake = deque([start_pos])
        self.snake_body_set = {start_pos}
        self.direction = "RIGHT"
        self.food = None
        self.score = 0
        self.game_over = False
        self.ate_food = False  # Flag for triggering effects on eat
        self.ate_golden = False  # Flag for golden apple eat
        self.ate_ice = False  # Flag for ice cube eat
        self.food_eaten_pos = None  # Position where food was eaten (for particles)
        self.golden_food = None  # Golden apple position (None = not active)
        self.ice_food = None  # Ice cube position (None = not active)
        self.grow_remaining = 0  # Extra segments to grow (for golden apple)
        self.spawn_food()

    def spawn_food(self):
        while True:
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            new_food_pos = (x, y)
            if new_food_pos not in self.snake_body_set and new_food_pos != self.golden_food and new_food_pos != self.ice_food:
                self.food = new_food_pos
                break

    def spawn_golden_food(self):
        """Spawn golden apple at a random free position."""
        while True:
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            pos = (x, y)
            if pos not in self.snake_body_set and pos != self.food and pos != self.ice_food:
                self.golden_food = pos
                break

    def spawn_ice_food(self):
        """Spawn ice cube at a random free position."""
        while True:
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            pos = (x, y)
            if pos not in self.snake_body_set and pos != self.food and pos != self.golden_food:
                self.ice_food = pos
                break

    def change_direction(self, new_direction):
        opposites = {"UP": "DOWN", "DOWN": "UP", "LEFT": "RIGHT", "RIGHT": "LEFT"}
        if new_direction != opposites.get(self.direction):
            self.direction = new_direction

    def move(self):
        if self.game_over:
            return
        self.ate_food = False
        self.ate_golden = False
        self.ate_ice = False
        head_x, head_y = self.snake[0]

        if self.direction == "UP":
            new_head = (head_x, head_y - 1)
        elif self.direction == "DOWN":
            new_head = (head_x, head_y + 1)
        elif self.direction == "LEFT":
            new_head = (head_x - 1, head_y)
        else:  # RIGHT
            new_head = (head_x + 1, head_y)

        if not (0 <= new_head[0] < self.width and 0 <= new_head[1] < self.height):
            self.game_over = True
            return

        if new_head in self.snake_body_set and new_head != self.snake[-1]:
            self.game_over = True
            return

        self.snake.appendleft(new_head)
        self.snake_body_set.add(new_head)

        if new_head == self.food:
            self.score += 1
            self.ate_food = True
            self.food_eaten_pos = new_head
            self.spawn_food()
        elif self.golden_food and new_head == self.golden_food:
            self.score += 3
            self.ate_golden = True
            self.food_eaten_pos = new_head
            self.golden_food = None
            self.grow_remaining += 2  # Already kept 1 by not popping, so +2 more
        elif self.ice_food and new_head == self.ice_food:
            self.ate_ice = True
            self.food_eaten_pos = new_head
            self.ice_food = None
            tail = self.snake.pop()
            if tail != new_head:
                self.snake_body_set.remove(tail)
        elif self.grow_remaining > 0:
            # Still growing from golden apple — don't pop tail
            self.grow_remaining -= 1
        else:
            tail = self.snake.pop()
            if tail != new_head:
                self.snake_body_set.remove(tail)


# --- PARTICLE SYSTEM ---
class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(2, 6)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.lifetime = random.randint(15, 30)  # frames
        self.size = random.randint(2, 5)
        self.color = color

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.15  # gravity
        self.lifetime -= 1
        self.size = max(1, self.size - 0.1)

    def draw(self, screen):
        color = (
            min(255, self.color[0]),
            min(255, self.color[1]),
            min(255, self.color[2]),
        )
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), int(self.size))

    def is_dead(self):
        return self.lifetime <= 0


# --- PYGAME GRAPHICAL UI ---
def main():
    pygame.init()
    pygame.mixer.init()

    # Settings
    CELL_SIZE = 30
    GRID_WIDTH = 25
    GRID_HEIGHT = 20

    # Speed settings
    START_SPEED = 5       # Starting FPS (nice and slow)
    SPEED_INCREMENT = 0.2 # FPS increase per food eaten
    MAX_SPEED = 15        # Cap so it stays playable
    current_speed = START_SPEED

    # Colors
    BG_COLOR_1 = (30, 30, 30)       # Checkerboard dark
    BG_COLOR_2 = (40, 40, 40)       # Checkerboard light
    TEXT_COLOR = (255, 255, 255)
    FOOD_COLOR = (255, 50, 50)
    BTN_COLOR = (50, 150, 50)
    BTN_HOVER_COLOR = (70, 200, 70)

    PARTICLE_COLORS = [
        (255, 80, 80),
        (255, 200, 50),
        (255, 120, 30),
        (255, 255, 100),
    ]

    GOLDEN_PARTICLE_COLORS = [
        (255, 215, 0),
        (255, 180, 0),
        (255, 255, 100),
        (255, 240, 60),
    ]

    ICE_PARTICLE_COLORS = [
        (150, 200, 255),
        (100, 255, 255),
        (200, 230, 255),
        (255, 255, 255),
    ]

    SCREEN_WIDTH = GRID_WIDTH * CELL_SIZE
    SCREEN_HEIGHT = GRID_HEIGHT * CELL_SIZE

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Snake Game 🐍")
    clock = pygame.time.Clock()
    
    font = pygame.font.SysFont("arial", 24, bold=True)
    title_font = pygame.font.SysFont("arial", 64, bold=True)
    game_over_font = pygame.font.SysFont("arial", 48, bold=True)
    small_font = pygame.font.SysFont("arial", 20)

    # --- PYINSTALLER & LOAD ASSETS ---
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        base_path = getattr(sys, '_MEIPASS')
        exe_dir = os.path.dirname(sys.executable)
    else:
        # Running as a script
        base_path = os.path.dirname(os.path.abspath(__file__))
        exe_dir = base_path

    asset_dir = os.path.join(base_path, "assets")
    try:
        raw_apple = pygame.image.load(os.path.join(asset_dir, "apple.png")).convert_alpha()
        img_apple = pygame.transform.scale(raw_apple, (CELL_SIZE, CELL_SIZE))

        raw_golden = pygame.image.load(os.path.join(asset_dir, "golden_apple.png")).convert_alpha()
        img_golden = pygame.transform.scale(raw_golden, (CELL_SIZE, CELL_SIZE))

        raw_ice = pygame.image.load(os.path.join(asset_dir, "ice_cube.png")).convert_alpha()
        img_ice = pygame.transform.scale(raw_ice, (CELL_SIZE, CELL_SIZE))
    except FileNotFoundError as e:
        print(f"Error loading image: {e}")
        print("Make sure the 'assets' folder has apple.png, golden_apple.png, and ice_cube.png")
        sys.exit(1)

    try:
        eat_sound = pygame.mixer.Sound(os.path.join(asset_dir, "eat.wav"))
        crash_sound = pygame.mixer.Sound(os.path.join(asset_dir, "crash.wav"))
    except FileNotFoundError as e:
        print(f"Error loading sound: {e}")
        print("Make sure the 'assets' folder has eat.wav and crash.wav")
        sys.exit(1)

    # Pre-render checkerboard background surface (drawn once for performance)
    bg_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    for row in range(GRID_HEIGHT):
        for col in range(GRID_WIDTH):
            color = BG_COLOR_1 if (row + col) % 2 == 0 else BG_COLOR_2
            pygame.draw.rect(bg_surface, color, (col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE))

    # --- INITIAL GAME STATE SETUP ---
    game_state = "MENU" # States: "MENU", "PLAYING", "PAUSED", "GAME_OVER"
    
    game = SnakeGame(width=GRID_WIDTH, height=GRID_HEIGHT)
    particles = []
    crash_sound_played = False
    
    highscore_filepath = os.path.join(exe_dir, "high_score.json")
    high_score = load_high_score(highscore_filepath)

    # Timers
    GOLDEN_SPAWN_MIN = 8000   
    GOLDEN_SPAWN_MAX = 20000  
    GOLDEN_DURATION = 4000    
    golden_spawn_timer = pygame.time.get_ticks() + random.randint(GOLDEN_SPAWN_MIN, GOLDEN_SPAWN_MAX)
    golden_expire_time = 0  

    ICE_SPAWN_MIN = 25000   
    ICE_SPAWN_MAX = 45000   
    ICE_DURATION = 5000     
    ice_spawn_timer = pygame.time.get_ticks() + random.randint(ICE_SPAWN_MIN, ICE_SPAWN_MAX)
    ice_expire_time = 0
    
    def reset_game():
        nonlocal game, crash_sound_played, current_speed, golden_spawn_timer, golden_expire_time, ice_spawn_timer, ice_expire_time
        game = SnakeGame(width=GRID_WIDTH, height=GRID_HEIGHT)
        particles.clear()
        crash_sound_played = False
        current_speed = START_SPEED
        golden_spawn_timer = pygame.time.get_ticks() + random.randint(GOLDEN_SPAWN_MIN, GOLDEN_SPAWN_MAX)
        golden_expire_time = 0
        ice_spawn_timer = pygame.time.get_ticks() + random.randint(ICE_SPAWN_MIN, ICE_SPAWN_MAX)
        ice_expire_time = 0

    # Button geometry for Game Over screen
    btn_width = 200
    btn_height = 50
    play_again_rect = pygame.Rect(SCREEN_WIDTH // 2 - btn_width // 2, SCREEN_HEIGHT // 2 + 50, btn_width, btn_height)

    # --- MAIN GAME LOOP ---
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        
        # 1. Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if game_state == "GAME_OVER":
                        if play_again_rect.collidepoint(event.pos):
                            reset_game()
                            game_state = "PLAYING"
                            
            elif event.type == pygame.KEYDOWN:
                if game_state == "MENU":
                    if event.key == pygame.K_SPACE:
                        reset_game()
                        game_state = "PLAYING"
                
                elif game_state == "PLAYING":
                    if event.key in [pygame.K_SPACE, pygame.K_p]:
                        game_state = "PAUSED"
                    elif event.key == pygame.K_UP:
                        game.change_direction("UP")
                    elif event.key == pygame.K_DOWN:
                        game.change_direction("DOWN")
                    elif event.key == pygame.K_LEFT:
                        game.change_direction("LEFT")
                    elif event.key == pygame.K_RIGHT:
                        game.change_direction("RIGHT")
                        
                elif game_state == "PAUSED":
                    if event.key in [pygame.K_SPACE, pygame.K_p]:
                        game_state = "PLAYING"
                        
                elif game_state == "GAME_OVER":
                    if event.key == pygame.K_SPACE or event.key == pygame.K_r:
                        reset_game()
                        game_state = "PLAYING"

        # 2. Update and Draw based on state
        
        # Always draw background
        screen.blit(bg_surface, (0, 0))

        if game_state == "MENU":
            title_text = title_font.render("SNAKE GAME", True, (0, 200, 80))
            prompt_text = font.render("Press SPACE to Start", True, TEXT_COLOR)
            
            screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, SCREEN_HEIGHT // 2 - 80))
            
            # Pulsing effect for the prompt text
            alpha = int(abs(math.sin(pygame.time.get_ticks() * 0.003)) * 255)
            prompt_surf = prompt_text.copy()
            prompt_surf.set_alpha(alpha)
            screen.blit(prompt_surf, (SCREEN_WIDTH // 2 - prompt_text.get_width() // 2, SCREEN_HEIGHT // 2 + 20))
            
        elif game_state in ["PLAYING", "PAUSED", "GAME_OVER"]:
            
            if game_state == "PLAYING":
                # --- Update logic ---
                game.move()

                if game.game_over:
                    game_state = "GAME_OVER"
                else:
                    # Spawn particles on eating regular food
                    if game.ate_food and game.food_eaten_pos:
                        eat_sound.play()
                        current_speed = min(MAX_SPEED, current_speed + SPEED_INCREMENT)
                        px = game.food_eaten_pos[0] * CELL_SIZE + CELL_SIZE // 2
                        py = game.food_eaten_pos[1] * CELL_SIZE + CELL_SIZE // 2
                        for _ in range(15):
                            color = random.choice(PARTICLE_COLORS)
                            particles.append(Particle(px, py, color))

                    # Spawn particles on eating golden apple
                    if game.ate_golden and game.food_eaten_pos:
                        eat_sound.play()
                        current_speed = min(MAX_SPEED, current_speed + SPEED_INCREMENT * 3)
                        px = game.food_eaten_pos[0] * CELL_SIZE + CELL_SIZE // 2
                        py = game.food_eaten_pos[1] * CELL_SIZE + CELL_SIZE // 2
                        for _ in range(30):
                            color = random.choice(GOLDEN_PARTICLE_COLORS)
                            particles.append(Particle(px, py, color))

                    # --- Golden Apple Timer Logic ---
                    now = pygame.time.get_ticks()
                    if game.golden_food is None:
                        if now >= golden_spawn_timer:
                            game.spawn_golden_food()
                            golden_expire_time = now + GOLDEN_DURATION
                    else:
                        if now >= golden_expire_time:
                            game.golden_food = None
                            golden_spawn_timer = now + random.randint(GOLDEN_SPAWN_MIN, GOLDEN_SPAWN_MAX)

                    if game.ate_golden:
                        golden_spawn_timer = now + random.randint(GOLDEN_SPAWN_MIN, GOLDEN_SPAWN_MAX)

                    # Spawn particles on eating ice cube
                    if game.ate_ice and game.food_eaten_pos:
                        eat_sound.play()
                        current_speed = max(START_SPEED, current_speed - 2.0)
                        px = game.food_eaten_pos[0] * CELL_SIZE + CELL_SIZE // 2
                        py = game.food_eaten_pos[1] * CELL_SIZE + CELL_SIZE // 2
                        for _ in range(20):
                            color = random.choice(ICE_PARTICLE_COLORS)
                            particles.append(Particle(px, py, color))

                    # --- Ice Cube Timer Logic ---
                    if game.ice_food is None:
                        if now >= ice_spawn_timer:
                            if game.score >= 15:
                                game.spawn_ice_food()
                                ice_expire_time = now + ICE_DURATION
                            else:
                                ice_spawn_timer = now + random.randint(ICE_SPAWN_MIN, ICE_SPAWN_MAX)
                    else:
                        if now >= ice_expire_time:
                            game.ice_food = None
                            ice_spawn_timer = now + random.randint(ICE_SPAWN_MIN, ICE_SPAWN_MAX)

                    if game.ate_ice:
                        ice_spawn_timer = now + random.randint(ICE_SPAWN_MIN, ICE_SPAWN_MAX)

            # --- Drawing for PLAYING, PAUSED, and GAME_OVER ---
            
            # Draw Food
            if game.food:
                screen.blit(img_apple, (game.food[0] * CELL_SIZE, game.food[1] * CELL_SIZE))

            # Draw Golden Apple (with pulsing glow)
            if game.golden_food:
                gx = game.golden_food[0] * CELL_SIZE
                gy = game.golden_food[1] * CELL_SIZE
                pulse = abs(math.sin(pygame.time.get_ticks() * 0.005)) * 8 if game_state == "PLAYING" else 4
                glow_rect = pygame.Rect(gx - pulse, gy - pulse, CELL_SIZE + pulse * 2, CELL_SIZE + pulse * 2)
                glow_surf = pygame.Surface((int(glow_rect.width), int(glow_rect.height)), pygame.SRCALPHA)
                glow_surf.fill((255, 215, 0, 60))
                screen.blit(glow_surf, glow_rect.topleft)
                screen.blit(img_golden, (gx, gy))

            # Draw Ice Cube
            if game.ice_food:
                ix = game.ice_food[0] * CELL_SIZE
                iy = game.ice_food[1] * CELL_SIZE
                pulse = abs(math.sin(pygame.time.get_ticks() * 0.005)) * 6 if game_state == "PLAYING" else 3
                glow_rect = pygame.Rect(ix - pulse, iy - pulse, CELL_SIZE + pulse * 2, CELL_SIZE + pulse * 2)
                glow_surf = pygame.Surface((int(glow_rect.width), int(glow_rect.height)), pygame.SRCALPHA)
                glow_surf.fill((100, 200, 255, 60))
                screen.blit(glow_surf, glow_rect.topleft)
                screen.blit(img_ice, (ix, iy))

            # Draw Snake
            for i, (x, y) in enumerate(game.snake):
                rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)

                if i == 0:
                    pygame.draw.rect(screen, (0, 200, 80), rect, border_radius=8)
                    eye_size = 5
                    cx, cy = rect.centerx, rect.centery
                    if game.direction == "RIGHT":
                        eye1 = (cx + 6, cy - 6)
                        eye2 = (cx + 6, cy + 6)
                    elif game.direction == "LEFT":
                        eye1 = (cx - 6, cy - 6)
                        eye2 = (cx - 6, cy + 6)
                    elif game.direction == "UP":
                        eye1 = (cx - 6, cy - 6)
                        eye2 = (cx + 6, cy - 6)
                    else:  # DOWN
                        eye1 = (cx - 6, cy + 6)
                        eye2 = (cx + 6, cy + 6)
                    pygame.draw.circle(screen, (255, 255, 255), eye1, eye_size)
                    pygame.draw.circle(screen, (255, 255, 255), eye2, eye_size)
                    pygame.draw.circle(screen, (0, 0, 0), eye1, 2)
                    pygame.draw.circle(screen, (0, 0, 0), eye2, 2)
                else:
                    pygame.draw.rect(screen, (0, 160, 60), rect, border_radius=6)
                    inner = rect.inflate(-6, -6)
                    pygame.draw.rect(screen, (0, 180, 70), inner, border_radius=4)

            # Draw Score
            score_text = font.render(f"Score: {game.score} | High Score: {max(game.score, high_score)}", True, TEXT_COLOR)
            screen.blit(score_text, (10, 10))
            
            # Draw Particles
            for p in particles[:]:
                if game_state == "PLAYING":
                    p.update()
                if p.is_dead():
                    particles.remove(p)
                else:
                    p.draw(screen)

            # Apply overlays for PAUSED or GAME_OVER
            if game_state == "PAUSED":
                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 150))
                screen.blit(overlay, (0, 0))
                
                pause_text = game_over_font.render("PAUSED", True, TEXT_COLOR)
                prompt_text = font.render("Press SPACE to Resume", True, TEXT_COLOR)
                screen.blit(pause_text, (SCREEN_WIDTH // 2 - pause_text.get_width() // 2, SCREEN_HEIGHT // 2 - 40))
                screen.blit(prompt_text, (SCREEN_WIDTH // 2 - prompt_text.get_width() // 2, SCREEN_HEIGHT // 2 + 20))
                
            elif game_state == "GAME_OVER":
                if not crash_sound_played:
                    crash_sound.play()
                    crash_sound_played = True
                    if game.score > high_score:
                        high_score = game.score
                        save_high_score(highscore_filepath, high_score)

                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 150))
                screen.blit(overlay, (0, 0))

                go_text = game_over_font.render("GAME OVER", True, FOOD_COLOR)
                final_score_text = font.render(f"Final Score: {game.score} | High Score: {high_score}", True, TEXT_COLOR)
                
                screen.blit(go_text, (SCREEN_WIDTH // 2 - go_text.get_width() // 2, SCREEN_HEIGHT // 2 - 80))
                screen.blit(final_score_text, (SCREEN_WIDTH // 2 - final_score_text.get_width() // 2, SCREEN_HEIGHT // 2 - 20))
                
                # Draw Play Again Button
                btn_color = BTN_HOVER_COLOR if play_again_rect.collidepoint(mouse_pos) else BTN_COLOR
                pygame.draw.rect(screen, btn_color, play_again_rect, border_radius=8)
                
                btn_text = font.render("Play Again", True, TEXT_COLOR)
                screen.blit(btn_text, (play_again_rect.centerx - btn_text.get_width() // 2, play_again_rect.centery - btn_text.get_height() // 2))
                
                # Alternate shortcut text
                sub_text = small_font.render("or press SPACE", True, (180, 180, 180))
                screen.blit(sub_text, (SCREEN_WIDTH // 2 - sub_text.get_width() // 2, play_again_rect.bottom + 10))


        # 8. Flip display
        pygame.display.flip()
        clock.tick(current_speed)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
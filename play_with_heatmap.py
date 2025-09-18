import pygame
import random
import time

from game_ai.mcts.mcts_wrapper import AIWrapperMCTS
from game_ai.state.dw_state import DucklingWarsState

# ---------------- CONFIG ----------------
BOARD_SIZE = 6
CELL_PIXEL = 100
PANEL_WIDTH = 600
WIDTH = BOARD_SIZE * CELL_PIXEL + PANEL_WIDTH
HEIGHT = BOARD_SIZE * CELL_PIXEL
FPS = 30
AI_ACTION_INTERVAL = 5
OPPONENT_ACTION_INTERVAL = 3
ACTIONS_PER_TURN = 2
PREVIEW_DELAY = 1000

# MCTS config
ROLLOUT_DEPTH = 25
ROLLOUTS = 500

# UI colors
BG = (30, 30, 30)
GRID = (200, 200, 200)
HEALTH_BAR_HEIGHT = 6
HEAT_ALPHA = 120
HIGHLIGHT_ALPHA = 180

# Army color mapping (RGB, name)
ARMY_COLORS = {
    "AI": ((30, 130, 230), "blue"),
    "Opponent": ((220, 60, 60), "red")
}

pygame.init()
FONT = pygame.font.SysFont("Consolas", 14)
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Duckling Wars - MCTS Demo")
CLOCK = pygame.time.Clock()


# ---------------- Random Opponent ----------------
class RandomOpponent:
    def choose(self, state):
        units = [u for u in state.get_units_of_army(state.current_army) if u.health > 0]
        candidates = []
        for u in units:
            moves = [m for m in state.get_legal_move_range_of_unit(u) if m.unit is None]
            attacks = [t for t in state.get_legal_attack_range_of_unit(u) if t.unit is not None]
            candidates += [("move", u, m) for m in moves] + [("attack", u, t) for t in attacks]
        if not candidates:
            return state, None
        kind, unit, target = random.choice(candidates)
        new_state = state.make_move(unit, target) if kind == "move" else state.attack(unit, target)
        return new_state, target


# ---------------- Drawing ----------------
def draw_grid(screen):
    for x in range(BOARD_SIZE):
        for y in range(BOARD_SIZE):
            rect = pygame.Rect(x * CELL_PIXEL, y * CELL_PIXEL, CELL_PIXEL, CELL_PIXEL)
            pygame.draw.rect(screen, GRID, rect, 1)


def draw_units(screen, state):
    for p in state.board:
        u = getattr(p, "unit", None)
        if u:
            color, _ = ARMY_COLORS[u.army]
            center = (p.x * CELL_PIXEL + CELL_PIXEL // 2, p.y * CELL_PIXEL + CELL_PIXEL // 2)
            pygame.draw.circle(screen, color, center, CELL_PIXEL // 3)
            # health bar
            ratio = max(u.health, 0) / u.max_health
            bar_width = int(CELL_PIXEL * 0.6 * ratio)
            bar_x = center[0] - CELL_PIXEL // 3
            bar_y = center[1] + CELL_PIXEL // 3 - HEALTH_BAR_HEIGHT
            pygame.draw.rect(screen, (0, 255, 0), (bar_x, bar_y, bar_width, HEALTH_BAR_HEIGHT))
            pygame.draw.rect(screen, (100, 100, 100),
                             (bar_x, bar_y, int(CELL_PIXEL * 0.6), HEALTH_BAR_HEIGHT), 1)


def clamp(x, lo=0, hi=255):
    return max(lo, min(int(x), hi))

def draw_heatmap(screen, heatmap):
    if not heatmap:
        return
    scores = list(heatmap.values())
    mn, mx = min(scores), max(scores)
    if mn == mx:
        mn, mx = 0.0, 1.0
    for (x, y), score in heatmap.items():
        norm = (score - mn) / (mx - mn)

        r = clamp(255 * norm)
        g = clamp(255 * (1 - norm))
        b = 0

        s = pygame.Surface((CELL_PIXEL, CELL_PIXEL), pygame.SRCALPHA)
        s.fill((r, g, b, HEAT_ALPHA))  # safe now
        screen.blit(s, (x * CELL_PIXEL, y * CELL_PIXEL))


def highlight_target(screen, target):
    if not target:
        return
    rect = pygame.Rect(target.x * CELL_PIXEL, target.y * CELL_PIXEL, CELL_PIXEL, CELL_PIXEL)
    pygame.draw.rect(screen, (255, 255, 255), rect, 4)


# ---------------- Self-play ----------------
def self_play():
    state = DucklingWarsState.generate_sample_game_state(
        board_size=BOARD_SIZE,
        armies=("AI", "Opponent")
    )
    ai = AIWrapperMCTS(rollouts=ROLLOUTS, rollout_depth=ROLLOUT_DEPTH)
    opponent = RandomOpponent()

    running = True
    paused = False
    last_time = {"AI": 0, "Opponent": 0}
    actions_taken = {"AI": 0, "Opponent": 0}
    heatmap, stats, chosen_target = {}, [], None

    while running:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_p:
                paused = not paused

        if not paused:
            now = time.time()
            interval = AI_ACTION_INTERVAL if state.current_army == "AI" else OPPONENT_ACTION_INTERVAL

            if actions_taken[state.current_army] < ACTIONS_PER_TURN and now - last_time[state.current_army] >= interval:
                # AI or opponent chooses
                if state.current_army == "AI":
                    next_state, target, hmap, st = ai.think(state)
                else:
                    next_state, target = opponent.choose(state)
                    hmap, st = {}, []

                # ---------------- PREVIEW ----------------
                SCREEN.fill(BG)
                draw_grid(SCREEN)
                draw_units(SCREEN, state)
                draw_heatmap(SCREEN, hmap)
                highlight_target(SCREEN, target)
                pygame.display.flip()
                pygame.time.delay(PREVIEW_DELAY)

                # ---------------- APPLY MOVE ----------------
                state = next_state
                chosen_target = target
                heatmap = hmap
                stats = st
                actions_taken[state.current_army] += 1
                last_time[state.current_army] = int(time.time())

            # switch turn if done
            if actions_taken[state.current_army] >= ACTIONS_PER_TURN:
                for u in state.get_units_of_army(state.current_army):
                    u.has_moved = False
                    u.already_attacked = False
                armies = state.get_all_armies()
                if len(armies) > 1:
                    state.current_army = next(a for a in armies if a != state.current_army)
                actions_taken[state.current_army] = 0

        # ---------------- DRAW FRAME ----------------
        SCREEN.fill(BG)
        draw_grid(SCREEN)
        draw_heatmap(SCREEN, heatmap)
        draw_units(SCREEN, state)
        highlight_target(SCREEN, chosen_target)

        # sidebar
        x0 = BOARD_SIZE * CELL_PIXEL + 10
        y0 = 10
        SCREEN.blit(FONT.render("AI stats & heatmap", True, (240, 240, 240)), (x0, y0))
        y0 += 26
        color_name = ARMY_COLORS[state.current_army][1]
        SCREEN.blit(FONT.render(f"Current army: {state.current_army} ({color_name})", True, (220, 220, 220)), (x0, y0))
        y0 += 24
        for kind, unit, target, score in stats:
            _, cname = ARMY_COLORS[unit.army]
            mark = "<-- chosen" if target == chosen_target else ""
            SCREEN.blit(FONT.render(
                f"{kind.upper()} {unit.unit_category} ({unit.army} ({cname})) -> "
                f"({target.x},{target.y}) | score: {(score*10):.2f} {mark}",
                True, (200, 200, 200)), (x0, y0))
            y0 += 18

        if paused:
            s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            s.fill((0, 0, 0, 100))
            SCREEN.blit(s, (0, 0))
            txt = FONT.render("PAUSED - Press P to resume", True, (255, 255, 255))
            SCREEN.blit(txt, (WIDTH // 2 - txt.get_width() // 2, HEIGHT // 2 - txt.get_height() // 2))

        pygame.display.flip()
        pygame.time.delay(3000)
        CLOCK.tick(FPS)


if __name__ == "__main__":
    self_play()
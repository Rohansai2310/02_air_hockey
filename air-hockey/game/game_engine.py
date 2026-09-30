"""
GameEngine: owns the puck, both paddles, the computer AI, and match state.
It runs one frame's worth of game logic and tracks the timed match result.
"""

import math
import random
import time

from game.puck import Puck
from game.paddle import Paddle
from game.ai import ComputerAI
from game.collisions import handle_paddle_collision
from game.renderer import WIDTH, HEIGHT, MARGIN, GOAL_TOP, GOAL_BOTTOM

PLAYER_SPEED = 6
PUCK_RADIUS = 12
PADDLE_RADIUS = 28
INITIAL_PUCK_SPEED = 4.5
MATCH_DURATION_SECONDS = 30.0


class GameEngine:
    def __init__(self):
        self.puck = Puck(WIDTH / 2, HEIGHT / 2, PUCK_RADIUS)
        self._launch_puck()

        self.player = Paddle(
            x=WIDTH * 0.15, y=HEIGHT / 2, radius=PADDLE_RADIUS,
            min_x=MARGIN + PADDLE_RADIUS, max_x=WIDTH / 2 - PADDLE_RADIUS,
            min_y=MARGIN + PADDLE_RADIUS, max_y=HEIGHT - MARGIN - PADDLE_RADIUS,
        )
        self.computer = Paddle(
            x=WIDTH * 0.85, y=HEIGHT / 2, radius=PADDLE_RADIUS,
            min_x=WIDTH / 2 + PADDLE_RADIUS, max_x=WIDTH - MARGIN - PADDLE_RADIUS,
            min_y=MARGIN + PADDLE_RADIUS, max_y=HEIGHT - MARGIN - PADDLE_RADIUS,
        )
        self.ai = ComputerAI()
        self.player_score = 0
        self.computer_score = 0
        self._match_started_at = time.monotonic()
        self.remaining_time = MATCH_DURATION_SECONDS
        self.match_over = False
        self.match_result = None

    def _launch_puck(self):
        angle_choices = [0.3, 0.6, -0.3, -0.6]
        direction = random.choice([-1, 1])
        vy_factor = random.choice(angle_choices)
        self.puck.vx = INITIAL_PUCK_SPEED * direction
        self.puck.vy = INITIAL_PUCK_SPEED * vy_factor

    def _update_match_timer(self):
        if self.match_over:
            return

        elapsed = time.monotonic() - self._match_started_at
        self.remaining_time = max(0.0, MATCH_DURATION_SECONDS - elapsed)
        if self.remaining_time == 0.0:
            self.match_over = True
            self.match_result = self.get_match_result()

    def handle_input(self, keys_pressed):
        self._update_match_timer()
        if self.match_over:
            return

        import pygame
        dx = dy = 0
        if keys_pressed[pygame.K_UP]:
            dy -= PLAYER_SPEED
        if keys_pressed[pygame.K_DOWN]:
            dy += PLAYER_SPEED
        if keys_pressed[pygame.K_LEFT]:
            dx -= PLAYER_SPEED
        if keys_pressed[pygame.K_RIGHT]:
            dx += PLAYER_SPEED
        self.player.move_by(dx, dy)

    def update(self):
        self._update_match_timer()
        if self.match_over:
            return

        self.ai.update(self.computer, self.puck)

        self.puck.move()
        self.puck.bounce_off_walls(HEIGHT, MARGIN)

        handle_paddle_collision(self.puck, self.player)
        handle_paddle_collision(self.puck, self.computer)

        self._handle_goals()

    def _puck_fits_goal(self):
        """Return whether the entire puck fits vertically through a goal."""
        return (
            GOAL_TOP + self.puck.radius <= self.puck.y
            <= GOAL_BOTTOM - self.puck.radius
        )

    def _handle_goals(self):
        if self.puck.x - self.puck.radius < MARGIN:
            if self._puck_fits_goal():
                # Score only after the whole puck has cleared the outer edge.
                if self.puck.x + self.puck.radius < 0:
                    self.computer_score += 1
                    self._reset_puck()
            else:
                self.puck.x = MARGIN + self.puck.radius
                self.puck.vx = abs(self.puck.vx)
        elif self.puck.x + self.puck.radius > WIDTH - MARGIN:
            if self._puck_fits_goal():
                if self.puck.x - self.puck.radius > WIDTH:
                    self.player_score += 1
                    self._reset_puck()
            else:
                self.puck.x = WIDTH - MARGIN - self.puck.radius
                self.puck.vx = -abs(self.puck.vx)

    def get_match_result(self):
        """Return the result implied by the current score."""
        if self.player_score > self.computer_score:
            return "Player wins!"
        if self.computer_score > self.player_score:
            return "Computer wins!"
        return "Draw"

    def _reset_puck(self):
        self.puck.x, self.puck.y = WIDTH / 2, HEIGHT / 2
        self.puck.vx = 0
        self.puck.vy = 0

    def draw(self, surface, font):
        from game import renderer
        self._update_match_timer()
        renderer.draw_table(surface)
        renderer.draw_text(
            surface, font, f"Player: {self.player_score}",
            (MARGIN + 12, MARGIN + 5), renderer.COLOR_PLAYER,
        )
        renderer.draw_text(
            surface, font, f"Computer: {self.computer_score}",
            (WIDTH - MARGIN - 190, MARGIN + 5), renderer.COLOR_COMPUTER,
        )
        displayed_seconds = math.ceil(self.remaining_time)
        renderer.draw_text(
            surface, font, f"Time: {displayed_seconds}",
            (WIDTH // 2 - 45, MARGIN + 5),
        )
        renderer.draw_paddle(surface, self.player, renderer.COLOR_PLAYER)
        renderer.draw_paddle(surface, self.computer, renderer.COLOR_COMPUTER)
        renderer.draw_puck(surface, self.puck)
        if self.match_over:
            renderer.draw_banner(surface, font, self.match_result)

"""Puck-versus-paddle collision handling."""

import math

POSITION_EPSILON = 1e-6


def handle_paddle_collision(puck, paddle):
    """
    Resolve a puck/paddle collision using a swept-circle check.

    The sweep uses the puck's previous and current positions, so a fast puck
    cannot pass through a paddle between frames. Returns True if a collision
    (or an existing overlap) was resolved.
    """
    radius = puck.radius + paddle.radius
    start_x = getattr(puck, "previous_x", puck.x)
    start_y = getattr(puck, "previous_y", puck.y)
    move_x = puck.x - start_x
    move_y = puck.y - start_y

    # Find the first point where the puck's path enters the combined-radius
    # circle around the paddle. If it starts overlapped, resolve at t = 0.
    offset_x = start_x - paddle.x
    offset_y = start_y - paddle.y
    c = offset_x * offset_x + offset_y * offset_y - radius * radius
    path_length_squared = move_x * move_x + move_y * move_y

    if c <= 0:
        impact_t = 0.0
    elif path_length_squared == 0:
        return False
    else:
        b = 2 * (offset_x * move_x + offset_y * move_y)
        discriminant = b * b - 4 * path_length_squared * c
        if discriminant < 0:
            return False

        impact_t = (-b - math.sqrt(discriminant)) / (2 * path_length_squared)
        if impact_t < 0 or impact_t > 1:
            return False

    # The contact normal points from the paddle center toward the puck.
    contact_x = start_x + move_x * impact_t
    contact_y = start_y + move_y * impact_t
    normal_x = contact_x - paddle.x
    normal_y = contact_y - paddle.y
    normal_length = math.hypot(normal_x, normal_y)

    if normal_length <= POSITION_EPSILON:
        speed = math.hypot(puck.vx, puck.vy)
        if speed <= POSITION_EPSILON:
            normal_x, normal_y = 1.0, 0.0
        else:
            normal_x = -puck.vx / speed
            normal_y = -puck.vy / speed
    else:
        normal_x /= normal_length
        normal_y /= normal_length

    # Reflect only when moving into the paddle. This avoids a second bounce
    # when the puck is already separating and only needs positional correction.
    velocity_into_normal = puck.vx * normal_x + puck.vy * normal_y
    if velocity_into_normal < 0:
        puck.vx -= 2 * velocity_into_normal * normal_x
        puck.vy -= 2 * velocity_into_normal * normal_y

    # Place the puck just outside the paddle, then advance through the part of
    # this frame that remained after impact using the resolved velocity.
    remaining_frame = 1.0 - impact_t
    puck.x = paddle.x + normal_x * (radius + POSITION_EPSILON)
    puck.y = paddle.y + normal_y * (radius + POSITION_EPSILON)
    puck.x += puck.vx * remaining_frame
    puck.y += puck.vy * remaining_frame

    # A later paddle check in this frame must start from the resolved position,
    # rather than detecting this same swept path a second time.
    puck.previous_x = puck.x
    puck.previous_y = puck.y
    return True

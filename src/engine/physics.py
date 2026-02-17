import pygame

def move_and_slide(rect, velocity, walls):
    # 1. Horizontal
    rect.x += velocity.x
    hit_list = [wall for wall in walls if rect.colliderect(wall)]
    for wall in hit_list:
        if velocity.x > 0: rect.right = wall.left
        elif velocity.x < 0: rect.left = wall.right
    
    # 2. Vertical
    rect.y += velocity.y
    hit_list = [wall for wall in walls if rect.colliderect(wall)]
    for wall in hit_list:
        if velocity.y > 0: rect.bottom = wall.top
        elif velocity.y < 0: rect.top = wall.bottom
            
    return rect
import pygame

def check_collision(rect, walls):
    """Returns the list of walls the rect is colliding with"""
    hit_list = []
    for wall in walls:
        if rect.colliderect(wall):
            hit_list.append(wall)
    return hit_list

def move(rect, velocity, walls):
    """
    Moves a rect by velocity (dx, dy) handling collisions separately 
    for X and Y axis to allow 'sliding'.
    """
    collision_types = {'top': False, 'bottom': False, 'right': False, 'left': False}
    
    # 1. Move X
    rect.x += velocity.x
    hit_list = check_collision(rect, walls)
    for wall in hit_list:
        if velocity.x > 0: # Moving Right
            rect.right = wall.left
            collision_types['right'] = True
        elif velocity.x < 0: # Moving Left
            rect.left = wall.right
            collision_types['left'] = True
            
    # 2. Move Y
    rect.y += velocity.y
    hit_list = check_collision(rect, walls)
    for wall in hit_list:
        if velocity.y > 0: # Moving Down
            rect.bottom = wall.top
            collision_types['bottom'] = True
        elif velocity.y < 0: # Moving Up
            rect.top = wall.bottom
            collision_types['top'] = True
            
    return rect, collision_types
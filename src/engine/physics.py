# src/engine/physics.py
import pygame

def move_and_slide(rect, velocity, walls):
    """
    Moves a rect by velocity (dx, dy) handling collisions separately 
    for X and Y axis to allow 'sliding' along walls.
    """
    # 1. Horizontal Movement
    rect.x += velocity.x
    hit_list = []
    for wall in walls:
        if rect.colliderect(wall):
            hit_list.append(wall)
            
    for wall in hit_list:
        if velocity.x > 0: # Moving Right
            rect.right = wall.left
        elif velocity.x < 0: # Moving Left
            rect.left = wall.right
    
    # 2. Vertical Movement
    rect.y += velocity.y
    hit_list = []
    for wall in walls:
        if rect.colliderect(wall):
            hit_list.append(wall)
            
    for wall in hit_list:
        if velocity.y > 0: # Moving Down
            rect.bottom = wall.top
        elif velocity.y < 0: # Moving Up
            rect.top = wall.bottom
            
    return rect
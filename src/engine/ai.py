# src/engine/ai.py
import heapq
import math
from pygame.math import Vector2
from settings import TILE_SIZE, CHUNK_SIZE

class Pathfinder:
    @staticmethod
    def get_path(start_pos, end_pos, world): 
        start_node = (int(start_pos.x // TILE_SIZE), int(start_pos.y // TILE_SIZE))
        end_node = (int(end_pos.x // TILE_SIZE), int(end_pos.y // TILE_SIZE))

        # Optimization: Straight line if far away
        if abs(start_node[0] - end_node[0]) + abs(start_node[1] - end_node[1]) > 50:
            return [end_pos]

        open_set = []
        heapq.heappush(open_set, (0, start_node))
        came_from = {}
        g_score = {start_node: 0}
        
        # Initial heuristic
        f_score = {start_node: abs(start_node[0]-end_node[0]) + abs(start_node[1]-end_node[1])}

        iterations = 0
        while open_set:
            iterations += 1
            if iterations > 300: break 

            current = heapq.heappop(open_set)[1]

            if current == end_node:
                return Pathfinder.reconstruct_path(came_from, current)

            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                neighbor = (current[0] + dx, current[1] + dy)
                
                cx = neighbor[0] // CHUNK_SIZE
                cy = neighbor[1] // CHUNK_SIZE
                
                # Retrieve the Chunk Object
                chunk = world.chunks.get((cx, cy))
                
                is_wall = False
                if chunk:
                    lx = neighbor[0] % CHUNK_SIZE
                    ly = neighbor[1] % CHUNK_SIZE
                    # Access .grid inside the object
                    # We check specifically for walking blockers
                    if chunk.grid[lx][ly] in [0, 1, 5, 6, 7]: 
                         is_wall = True
                else:
                    is_wall = True # Treat unloaded chunks as walls

                if is_wall: continue

                tentative_g = g_score[current] + 1
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + (abs(neighbor[0]-end_node[0]) + abs(neighbor[1]-end_node[1]))
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))

        return [] 

    @staticmethod
    def reconstruct_path(came_from, current):
        total_path = []
        while current in came_from:
            pixel_pos = Vector2(current[0] * TILE_SIZE + TILE_SIZE//2, 
                                current[1] * TILE_SIZE + TILE_SIZE//2)
            total_path.append(pixel_pos)
            current = came_from[current]
        return total_path[::-1]
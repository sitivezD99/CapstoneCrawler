# src/engine/ai.py
import heapq
import math
from pygame.math import Vector2  # <--- THIS WAS MISSING
from settings import TILE_SIZE, CHUNK_SIZE

class Pathfinder:
    @staticmethod
    def get_path(start_pos, end_pos, dungeon):
        """
        A* Algorithm Implementation.
        Input: Start/End (Pixel Coordinates), Dungeon (For Wall Checks)
        Output: List of Vector2 (Next steps)
        """
        # 1. Convert World Pixels -> Tile Grid Coordinates
        start_node = (int(start_pos.x // TILE_SIZE), int(start_pos.y // TILE_SIZE))
        end_node = (int(end_pos.x // TILE_SIZE), int(end_pos.y // TILE_SIZE))

        # Optimization: If target is too far, just return straight line
        # This saves CPU from searching massive paths
        dist = math.sqrt((start_node[0]-end_node[0])**2 + (start_node[1]-end_node[1])**2)
        if dist > 50:
            return [end_pos]

        # A* Setup
        open_set = []
        heapq.heappush(open_set, (0, start_node))
        came_from = {}
        g_score = {start_node: 0}
        f_score = {start_node: Pathfinder.heuristic(start_node, end_node)}

        # Search Loop
        iterations = 0
        while open_set:
            iterations += 1
            if iterations > 300: break # Safety Break (prevent lag spikes)

            current = heapq.heappop(open_set)[1]

            if current == end_node:
                return Pathfinder.reconstruct_path(came_from, current)

            # Check 4 Neighbors
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                neighbor = (current[0] + dx, current[1] + dy)
                
                # COLLISION CHECK: Is this neighbor a wall?
                # We need to find which chunk this tile belongs to
                cx = neighbor[0] // CHUNK_SIZE
                cy = neighbor[1] // CHUNK_SIZE
                
                # Access the chunk dictionary safely
                chunk = dungeon.chunks.get((cx, cy))
                
                is_wall = False
                if chunk:
                    # Calculate local coordinates within chunk
                    lx = neighbor[0] % CHUNK_SIZE
                    ly = neighbor[1] % CHUNK_SIZE
                    if chunk.grid[ly][lx] == 0: # 0 is Wall
                        is_wall = True
                else:
                    # If chunk isn't loaded, treat as wall to be safe
                    is_wall = True

                if is_wall: continue

                # A* Math
                tentative_g = g_score[current] + 1
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + Pathfinder.heuristic(neighbor, end_node)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))

        return [] # No path found

    @staticmethod
    def heuristic(a, b):
        # Manhattan Distance is faster for grid movement
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    @staticmethod
    def reconstruct_path(came_from, current):
        total_path = []
        while current in came_from:
            # Convert back to Pixel Coordinates (Center of tile)
            pixel_pos = Vector2(current[0] * TILE_SIZE + TILE_SIZE//2, 
                                current[1] * TILE_SIZE + TILE_SIZE//2)
            total_path.append(pixel_pos)
            current = came_from[current]
        return total_path[::-1] # Reverse to get Start->End
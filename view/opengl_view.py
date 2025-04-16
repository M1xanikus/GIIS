import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import multiprocessing
import time

def cube():
    """Определяет вершины и грани куба."""
    vertices = (
        (1, -1, -1), (1, 1, -1), (-1, 1, -1), (-1, -1, -1),
        (1, -1, 1), (1, 1, 1), (-1, -1, 1), (-1, 1, 1)
    )
    edges = (
        (0, 1), (0, 3), (0, 4), (2, 1), (2, 3), (2, 7),
        (6, 3), (6, 4), (6, 7), (5, 1), (5, 4), (5, 7)
    )
    surfaces = (
        (0, 1, 2, 3), (3, 2, 7, 6), (6, 7, 5, 4),
        (4, 5, 1, 0), (1, 5, 7, 2), (4, 0, 3, 6)
    )
    colors = (
        (1, 0, 0), (0, 1, 0), (0, 0, 1),
        (1, 1, 0), (0, 1, 1), (1, 0, 1)
    )

    glBegin(GL_QUADS)
    for i, surface in enumerate(surfaces):
        glColor3fv(colors[i % len(colors)])
        for vertex_index in surface:
            glVertex3fv(vertices[vertex_index])
    glEnd()

    # Draw edges (optional, for wireframe view)
    # glColor3fv((0, 0, 0)) # Black edges
    # glBegin(GL_LINES)
    # for edge in edges:
    #     for vertex_index in edge:
    #         glVertex3fv(vertices[vertex_index])
    # glEnd()

def run_opengl_view(command_queue: multiprocessing.Queue):
    """Основная функция для запуска окна OpenGL."""
    pygame.init()
    display = (800, 600)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    pygame.display.set_caption("3D View (OpenGL)")

    gluPerspective(45, (display[0] / display[1]), 0.1, 50.0)
    glTranslatef(0.0, 0.0, -5) # Move camera back

    # Enable depth testing
    glEnable(GL_DEPTH_TEST)

    # Transformation state
    translate_x, translate_y, translate_z = 0.0, 0.0, 0.0
    rotate_x, rotate_y, rotate_z = 0, 0, 0
    scale_x, scale_y, scale_z = 1.0, 1.0, 1.0

    running = True
    frame_count = 0 # For less frequent logging
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Check for commands from the queue
        transform_changed = False
        while not command_queue.empty():
            try:
                command = command_queue.get_nowait()
                # print(f"[OpenGL Process] Received command: {command}") # Already exists
                cmd_type = command.get("type")
                value = command.get("value")
                axis = command.get("axis")

                # --- Update state based on command --- 
                if cmd_type == "translate":
                    if axis == 'x': translate_x = value
                    elif axis == 'y': translate_y = value
                    elif axis == 'z': translate_z = value
                    transform_changed = True
                elif cmd_type == "rotate":
                    if axis == 'x': rotate_x = value
                    elif axis == 'y': rotate_y = value
                    elif axis == 'z': rotate_z = value
                    transform_changed = True
                elif cmd_type == "scale":
                    old_scale_x, old_scale_y, old_scale_z = scale_x, scale_y, scale_z
                    if axis == 'x': scale_x = max(0.01, value)
                    elif axis == 'y': scale_y = max(0.01, value)
                    elif axis == 'z': scale_z = max(0.01, value)
                    if (scale_x, scale_y, scale_z) != (old_scale_x, old_scale_y, old_scale_z):
                         transform_changed = True
                elif cmd_type == "quit":
                     running = False
                     break

            except multiprocessing.queues.Empty:
                break
            except Exception as e:
                 print(f"[OpenGL Process] Error processing command: {e}")
        # --- End Command Processing ---

        if not running: break

        # --- Debug Logging (less frequent) ---
        if transform_changed or frame_count % 60 == 0: # Log changes or every ~second
            print(f"[OpenGL Debug Frame {frame_count}] Translate:({translate_x:.2f}, {translate_y:.2f}, {translate_z:.2f}) "
                  f"Rotate:({rotate_x:.1f}, {rotate_y:.1f}, {rotate_z:.1f}) "
                  f"Scale:({scale_x:.2f}, {scale_y:.2f}, {scale_z:.2f})")
        # -------------------------------------

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glPushMatrix()

        # Apply transformations
        glTranslatef(translate_x, translate_y, translate_z)
        glRotatef(rotate_x, 1, 0, 0)
        glRotatef(rotate_y, 0, 1, 0)
        glRotatef(rotate_z, 0, 0, 1)
        glScalef(scale_x, scale_y, scale_z)

        cube()
        glPopMatrix()
        pygame.display.flip()
        pygame.time.wait(10)
        frame_count += 1

    print("[OpenGL Process] Выход.")
    pygame.quit()

if __name__ == '__main__':
    # Example usage (for testing this module directly)
    q = multiprocessing.Queue()
    run_opengl_view(q)
    # To test commands: you would need another script to put commands in q 
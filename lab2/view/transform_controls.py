import tkinter as tk
from tkinter import ttk
import multiprocessing

class TransformControls(tk.Toplevel):
    """Окно с элементами управления для 3D трансформаций."""
    def __init__(self, parent, command_queue: multiprocessing.Queue):
        super().__init__(parent)
        self.title("Управление 3D")
        self.geometry("300x450") # Adjust size as needed
        self.command_queue = command_queue
        self.parent = parent

        # Prevent closing via 'X' button sending wrong signal
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Store Scale widgets to access their values
        self.sliders = {}

        # Translation Controls
        translate_frame = ttk.LabelFrame(self, text="Перемещение")
        translate_frame.pack(pady=10, padx=10, fill=tk.X)
        self.create_slider(translate_frame, "translate", "x", -5.0, 5.0, 0.0)
        self.create_slider(translate_frame, "translate", "y", -5.0, 5.0, 0.0)
        self.create_slider(translate_frame, "translate", "z", -10.0, 10.0, 0.0)

        # Rotation Controls
        rotate_frame = ttk.LabelFrame(self, text="Вращение (градусы)")
        rotate_frame.pack(pady=10, padx=10, fill=tk.X)
        self.create_slider(rotate_frame, "rotate", "x", 0, 360, 0)
        self.create_slider(rotate_frame, "rotate", "y", 0, 360, 0)
        self.create_slider(rotate_frame, "rotate", "z", 0, 360, 0)

        # Scale Controls
        scale_frame = ttk.LabelFrame(self, text="Масштабирование")
        scale_frame.pack(pady=10, padx=10, fill=tk.X)
        # Use different range/resolution for scale if needed
        self.create_slider(scale_frame, "scale", "x", 0.1, 5.0, 1.0, resolution=0.1)
        self.create_slider(scale_frame, "scale", "y", 0.1, 5.0, 1.0, resolution=0.1)
        self.create_slider(scale_frame, "scale", "z", 0.1, 5.0, 1.0, resolution=0.1)

        # Reset Button
        reset_button = ttk.Button(self, text="Сбросить все", command=self.reset_all)
        reset_button.pack(pady=10)

    def create_slider(self, parent_frame, cmd_type, axis, from_, to, initial_value, resolution=0.01):
        """Создает метку и ползунок для управления параметром."""
        frame = ttk.Frame(parent_frame)
        frame.pack(fill=tk.X, padx=5, pady=2)

        label = ttk.Label(frame, text=f"{axis.upper()}:", width=3)
        label.pack(side=tk.LEFT)

        value_var = tk.DoubleVar(value=initial_value)
        # Use tk.Scale for sliders
        slider = tk.Scale(
            frame,
            variable=value_var,
            from_=from_,
            to=to,
            orient=tk.HORIZONTAL,
            resolution=resolution,
            length=180, # Adjust length
            showvalue=0, # Hide default value display
            command=lambda val, t=cmd_type, a=axis: self.send_command(t, a, float(val))
        )
        slider.pack(side=tk.LEFT, expand=True, fill=tk.X)
        self.sliders[(cmd_type, axis)] = slider # Store slider widget

        # Optional: Add an Entry to show/set precise value
        # entry = ttk.Entry(frame, textvariable=value_var, width=5)
        # entry.pack(side=tk.LEFT, padx=5)

    def send_command(self, cmd_type, axis, value):
        """Отправляет команду трансформации в очередь OpenGL."""
        if self.command_queue:
            command = {"type": cmd_type, "axis": axis, "value": value}
            print(f"[Tkinter Controls] Sending command: {command}")
            self.command_queue.put(command)
        else:
            print("Error: Command queue is not set.")

    def reset_all(self):
        """Сбрасывает все ползунки и отправляет команды сброса."""
        # Reset Translation
        self.sliders[("translate", "x")].set(0.0)
        self.sliders[("translate", "y")].set(0.0)
        self.sliders[("translate", "z")].set(0.0)
        # Reset Rotation
        self.sliders[("rotate", "x")].set(0)
        self.sliders[("rotate", "y")].set(0)
        self.sliders[("rotate", "z")].set(0)
        # Reset Scale
        self.sliders[("scale", "x")].set(1.0)
        self.sliders[("scale", "y")].set(1.0)
        self.sliders[("scale", "z")].set(1.0)
        # Explicitly send reset commands via set method trigger or manually
        self.send_command("translate", "x", 0.0)
        self.send_command("translate", "y", 0.0)
        self.send_command("translate", "z", 0.0)
        self.send_command("rotate", "x", 0)
        self.send_command("rotate", "y", 0)
        self.send_command("rotate", "z", 0)
        self.send_command("scale", "x", 1.0)
        self.send_command("scale", "y", 1.0)
        self.send_command("scale", "z", 1.0)

    def on_close(self):
        """Обработчик закрытия окна управления."""
        print("[Tkinter Controls] Control window closing.")
        # Send a quit command to the OpenGL process
        if self.command_queue:
            self.command_queue.put({"type": "quit"})

        # Optionally notify the main editor if needed
        if hasattr(self.parent, 'on_3d_controls_close'):
            self.parent.on_3d_controls_close()

        self.destroy() # Close this Toplevel window

# Example usage (for testing this module directly)
# if __name__ == '__main__':
#     root = tk.Tk()
#     root.withdraw() # Hide main root window if only testing controls
#     q = multiprocessing.Queue()
#     controls = TransformControls(root, q)
#     # In a real scenario, another process would consume from q
#     root.mainloop() 
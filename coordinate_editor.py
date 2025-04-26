# v1.0.0
# Uploaded 25.4.2025.
# by 6769742e646576
import tkinter as tk
from tkinter import filedialog
import numpy as np
import re
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import webbrowser

# Vars
original_coords = []
shifted_coords = []
file_content = ""
current_file_type = None
mirror_hor = False
mirror_ver = False

# Functions
def parse_coordinates(content):
    return [list(map(float, pair.split(','))) for pair in re.findall(r"-?\d*\.\d+,-?\d*\.\d+", content)]

def parse_coordinates_blk(content):
    coords = []
    line_matches = re.findall(r"line\s*:\s*p4\s*=\s*(-?\d+\.\d+),(-?\d+\.\d+),(-?\d+\.\d+),(-?\d+\.\d+)", content)
    for x1, y1, x2, y2 in line_matches:
        coords.append([float(x1), float(y1)])
        coords.append([float(x2), float(y2)])
    quad_matches = re.findall(r"(tl|tr|br|bl)\s*:\s*p2\s*=\s*(-?\d+\.\d+),(-?\d+\.\d+)", content)
    for _, x, y in quad_matches:
        coords.append([float(x), float(y)])
    return coords

def load_txt_file():
    global original_coords, file_content, shifted_coords, current_file_type
    file_path = filedialog.askopenfilename(filetypes=[("TXT files", "*.txt")])
    if not file_path:
        return
    with open(file_path, "r") as f:
        file_content = f.read()
    original_coords = parse_coordinates(file_content)
    shifted_coords = original_coords[:]
    current_file_type = ".txt"
    redraw_plot()
    disable_save_button()

def load_blk_file():
    global original_coords, file_content, shifted_coords, current_file_type
    file_path = filedialog.askopenfilename(filetypes=[("BLK files", "*.blk")])
    if not file_path:
        return
    with open(file_path, "r") as f:
        file_content = f.read()
    original_coords = parse_coordinates_blk(file_content)
    shifted_coords = original_coords[:]
    current_file_type = ".blk"
    redraw_plot()
    disable_save_button()

def shift_coords_data(coordinates, x_offset, y_offset):
    shifted_coordinates = []

    for x, y in coordinates:
        new_x = x + x_offset
        new_y = y + y_offset
        shifted_coordinates.append([new_x, new_y])

    return shifted_coordinates

def scale_coords_data(coordinates, x_scale_factor, y_scale_factor):
    scaled_coordinates = []

    for x, y in coordinates:
        scaled_x = x * x_scale_factor
        scaled_y = y * y_scale_factor
        scaled_coordinates.append([scaled_x, scaled_y])

    return scaled_coordinates

def mirror_coordinates_horizontally():
    global mirror_hor
    mirror_hor = not mirror_hor
    apply_mirroring()

def mirror_coordinates_vertically():
    global mirror_ver
    mirror_ver = not mirror_ver
    apply_mirroring()

def apply_mirroring():
    global shifted_coords

    try:
        x_shift = float(x_shift_inpt.get())
        y_shift = float(y_shift_inpt.get())
        x_scale = float(x_scale_inpt.get())
        y_scale = float(y_scal_inpt.get())
    except ValueError:
        return

    scaled = scale_coords_data(original_coords, x_scale, y_scale)
    shifted = shift_coords_data(scaled, x_shift, y_shift)

    if not shifted:
        return
    xs, ys = zip(*shifted)
    center_x = sum(xs) / len(xs)
    center_y = sum(ys) / len(ys)

    def mirror_point(x, y):
        if mirror_hor and mirror_ver:
            return 2 * center_x - x, 2 * center_y - y
        elif mirror_hor:
            return x, 2 * center_y - y
        elif mirror_ver:
            return 2 * center_x - x, y
        else:
            return x, y

    shifted_coords = [mirror_point(x, y) for x, y in shifted]
    redraw_plot()
    enable_save_button()


def redraw_plot():
    if not original_coords:
        return
    ax.clear()
    ax.set_title(" - Updated Coordinates - ")

    x_half = 1.2
    y_half = 0.6

    ax.set_xlim(-x_half, x_half)
    ax.set_ylim(y_half, -y_half)
    ax.set_xticks(np.arange(-x_half, x_half + 0.1, 0.1))
    ax.set_yticks(np.arange(-y_half, y_half + 0.1, 0.1))
    ax.grid(True)
    ax.axhline(0, color='black', linewidth=1)
    ax.axvline(0, color='black', linewidth=1)

    if shifted_coords:
        xs, ys = zip(*shifted_coords)
        ax.plot(xs, ys, 'bo-', markersize=1, linewidth=1)

    box_x = [-1.0, -1.0, 1.0, 1.0, -1.0]
    box_y = [0.5, -0.5, -0.5, 0.5, 0.5]
    ax.plot(box_x, box_y, 'k:', linewidth=2)

    canvas.draw()

def save_shifted_file():
    try:
        x_shift = float(x_shift_inpt.get())
        y_shift = float(y_shift_inpt.get())
        x_scale = float(x_scale_inpt.get())
        y_scale = float(y_scal_inpt.get())
    except ValueError:
        return

    if not original_coords:
        return

    scaled = scale_coords_data(original_coords, x_scale, y_scale)
    shifted = shift_coords_data(scaled, x_shift, y_shift)
    xs, ys = zip(*shifted)
    center_x = sum(xs) / len(xs)
    center_y = sum(ys) / len(ys)

    def mirror_point(x, y):
        if mirror_hor and mirror_ver:
            return 2 * center_x - x, 2 * center_y - y
        elif mirror_hor:
            return x, 2 * center_y - y
        elif mirror_ver:
            return 2 * center_x - x, y
        else:
            return x, y

    newly_created_content = file_content

    def transform_p4(match):
        x1, y1, x2, y2 = map(float, match.groups())
        x1, y1 = mirror_point(x1 * x_scale + x_shift, y1 * y_scale + y_shift)
        x2, y2 = mirror_point(x2 * x_scale + x_shift, y2 * y_scale + y_shift)
        return f"line:p4={x1:.17f},{y1:.17f},{x2:.17f},{y2:.17f}"

    def transform_p2(match):
        label, x, y = match.groups()
        x, y = mirror_point(float(x) * x_scale + x_shift, float(y) * y_scale + y_shift)
        return f"{label}:p2 = {x:.17f},{y:.17f}"

    if current_file_type == ".blk":
        newly_created_content = re.sub(r"line:p4=([-\d.]+),([-\d.]+),([-\d.]+),([-\d.]+)",transform_p4,newly_created_content)
        newly_created_content = re.sub(r"(tl|tr|br|bl):p2\s*=\s*([-\d.]+),([-\d.]+)",transform_p2,newly_created_content)

    elif current_file_type == ".txt":
        newly_created_content = re.sub(r"line:p4=([-\d.]+),([-\d.]+),([-\d.]+),([-\d.]+)",transform_p4,newly_created_content)
        newly_created_content = re.sub(r"(tl|tr|br|bl):p2\s*=\s*([-\d.]+),([-\d.]+)",transform_p2,newly_created_content)

    ext = current_file_type if current_file_type else ".txt"
    out_path = filedialog.asksaveasfilename(defaultextension=ext, filetypes=[(f"{ext.upper()} files", f"*{ext}")])
    if out_path:
        with open(out_path, "w") as f:
            f.write(newly_created_content)

# GUI func
def on_spinbox_change(*args):
    apply_mirroring()

def enable_save_button():
    save_button.config(bg="green", fg="white", command=save_shifted_file)

def disable_save_button():
    save_button.config(bg="red", fg="white", command=lambda: None)

def open_github():
    webbrowser.open_new("https://github.com/6769742e646576/Coordinate-Editor")

# GUI
root = tk.Tk()
root.title("Coordinate Editor")
root.geometry("1280x720")
root.resizable(True, True)

x_shift_var = tk.StringVar(value="0.0")
x_shift_var.trace_add("write", on_spinbox_change)

y_shift_var = tk.StringVar(value="0.0")
y_shift_var.trace_add("write", on_spinbox_change)

x_scale_var = tk.StringVar(value="1.0")
x_scale_var.trace_add("write", on_spinbox_change)

y_scale_var = tk.StringVar(value="1.0")
y_scale_var.trace_add("write", on_spinbox_change)

control_frame = tk.Frame(root, padx=10, pady=10, bg="#e8e8e8", bd=1, relief="solid")
control_frame.grid(row=0, column=0, sticky="nsw")

label_costum = {"font": ("Arial", 12), "bg": "#e8e8e8"}

tk.Label(control_frame, text="by @6769742e646576 (_Cuc_)", font=("Arial", 8), bg="#e8e8e8", fg="gray").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

tk.Button(control_frame, text="Load from .TXT File", font=("Arial", 12), command=load_txt_file).grid(row=1, column=0, columnspan=2, pady=(0, 5), sticky="ew")
tk.Button(control_frame, text="Load from .BLK File", font=("Arial", 12), command=load_blk_file).grid(row=2, column=0, columnspan=2, pady=5, sticky="ew")

tk.Label(control_frame, text="Drawing Manipulation", font=("Arial", 12, "bold"), bg="#e8e8e8").grid(row=3, column=0, columnspan=2, pady=(10, 5), sticky="w")

tk.Label(control_frame, text="X Shift:", **label_costum).grid(row=4, column=0, sticky="e", padx=5, pady=2)
x_shift_inpt = tk.Spinbox(control_frame, from_=-100.0, to=100.0, increment=0.1, font=("Arial", 12), width=8, textvariable=x_shift_var)
x_shift_inpt.grid(row=4, column=1, pady=2)

tk.Label(control_frame, text="Y Shift:", **label_costum).grid(row=5, column=0, sticky="e", padx=5, pady=2)
y_shift_inpt = tk.Spinbox(control_frame, from_=-100.0, to=100.0, increment=0.1, font=("Arial", 12), width=8, textvariable=y_shift_var)
y_shift_inpt.grid(row=5, column=1, pady=2)

tk.Label(control_frame, text="X Scale:", **label_costum).grid(row=6, column=0, sticky="e", padx=5, pady=2)
x_scale_inpt = tk.Spinbox(control_frame, from_=-100.0, to=100.0, increment=0.1, font=("Arial", 12), width=8, textvariable=x_scale_var)
x_scale_inpt.grid(row=6, column=1, pady=2)

tk.Label(control_frame, text="Y Scale:", **label_costum).grid(row=7, column=0, sticky="e", padx=5, pady=2)
y_scal_inpt = tk.Spinbox(control_frame, from_=-100.0, to=100.0, increment=0.1, font=("Arial", 12), width=8, textvariable=y_scale_var)
y_scal_inpt.grid(row=7, column=1, pady=2)

tk.Button(control_frame, text="Mirror Vertically", font=("Arial", 12), command=mirror_coordinates_vertically).grid(row=8, column=0, columnspan=2, pady=5, sticky="ew")
tk.Button(control_frame, text="Mirror Horizontally", font=("Arial", 12), command=mirror_coordinates_horizontally).grid(row=9, column=0, columnspan=2, pady=5, sticky="ew")

save_button = tk.Button(control_frame, text="Save updated File", font=("Arial", 12), bg="red", fg="white", command=lambda: None)
save_button.grid(row=15, column=0, columnspan=2, pady=5, sticky="ew")

git_button = tk.Button(control_frame, text="\uD83D\uDD17 View on GitHub", font=("Arial", 12, "bold"), fg="white", bg="#24292e", command=open_github)
git_button.grid(row=16, column=0, columnspan=2, pady=(20, 0), sticky="ew")

# Plot
plot_frame = tk.Frame(root)
plot_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

fig, ax = plt.subplots(figsize=(20, 6))
canvas = FigureCanvasTkAgg(fig, master=plot_frame)
canvas_widget = canvas.get_tk_widget()
canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

class CustomToolbar(NavigationToolbar2Tk):
    toolitems = [
        ('Pan', 'Pan axes with left mouse, zoom with right', 'move', 'pan'),
        ('Zoom', 'Zoom to rectangle', 'zoom_to_rect', 'zoom'),
        ('Save', 'Save the figure', 'filesave', 'save_figure')
    ]

toolbar = CustomToolbar(canvas, plot_frame)
toolbar.update()
toolbar.pack(side=tk.BOTTOM, fill=tk.X)

root.grid_columnconfigure(1, weight=1)
root.grid_rowconfigure(0, weight=1)

# Mouse movement
mouse_drag_data = {"x": 0, "y": 0, "xlim": None, "ylim": None}

def on_button_press(event):
    if event.button == 3:
        mouse_drag_data["x"] = event.x
        mouse_drag_data["y"] = event.y
        mouse_drag_data["xlim"] = ax.get_xlim()
        mouse_drag_data["ylim"] = ax.get_ylim()

def on_motion(event):
    if event.button == 3:
        dx = event.x - mouse_drag_data["x"]
        dy = event.y - mouse_drag_data["y"]
        x0, x1 = mouse_drag_data["xlim"]
        y0, y1 = mouse_drag_data["ylim"]
        ax_width, ax_height = canvas.get_width_height()
        dx_units = dx * (x1 - x0) / ax_width
        dy_units = dy * (y1 - y0) / ax_height
        ax.set_xlim(x0 - dx_units, x1 - dx_units)
        ax.set_ylim(y0 - dy_units, y1 - dy_units)
        canvas.draw()

canvas.mpl_connect("button_press_event", on_button_press)
canvas.mpl_connect("motion_notify_event", on_motion)

def on_scroll(event):
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    zoom_factor = 1.1
    factor = 1 / zoom_factor if event.button == 'up' else zoom_factor
    ax.set_xlim(x0 * factor, x1 * factor)
    ax.set_ylim(y0 * factor, y1 * factor)
    canvas.draw()

canvas.mpl_connect("scroll_event", on_scroll)

root.mainloop()
# What brought you here
import tkinter as tk
from tkinter import filedialog
import cv2
from PIL import Image, ImageTk

# Variables
clicked_points = []
points = []
lines = []
rectangles = []
rect_points = []
rooms = []
room_counter = 1
point_counter = 1
img = None
canvas_img = None

# Function to calculate map size
def calculate_map_size():
    if img is not None:
        height, width, _ = img.shape
        print(f"Map size: {width}x{height}")
        return width, height
    return 0, 0


def upload_image():
    global img, canvas_img
    file_path = filedialog.askopenfilename()
    if not file_path:
        return
    img = cv2.imread(file_path)
    width, height = calculate_map_size()
    print(f"Image dimensions: {width}x{height}")
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(img)
    img = img.resize((600, 400))
    canvas_img = ImageTk.PhotoImage(img)
    canvas.create_image(0, 0, anchor=tk.NW, image=canvas_img)

def draw_grid(image):
    """Draw a grid on the image with specified number of cells."""
    num_cells = 40
    height, width, _ = image.shape
    
    # Calculate the size of each cell
    cell_width = width / num_cells
    cell_height = height / num_cells

    # Draw vertical lines
    for i in range(num_cells + 1):
        x = i * cell_width
        cv2.line(image, (int(x), 0), (int(x), height), (150, 130, 10), 1)  # Vertical lines

    # Draw horizontal lines
    for i in range(num_cells + 1):
        y = i * cell_height
        cv2.line(image, (0, int(y)), (width, int(y)),  (150, 130, 10), 1)  # Horizontal lines

def near(x1,y1,x2,y2):
    dist = 3
    if abs(x1 - x2) < dist and abs (y1-y2) < dist  :
        return True
    return False

def on_click(event):
    global point_counter, room_counter
    x, y = event.x, event.y
    if event.num == 1:
        points.append((x, y))
        if len(points) >= 2:
            canvas.create_line(points[-2], points[-1], fill="purple", width=2)
            lines.append((points[-2], points[-1]))
        canvas.create_oval(x-3, y-3, x+3, y+3, fill="red", outline="red")
        canvas.create_text(x+5, y-5, text=str(point_counter), fill="red")
        point_counter += 1
    elif event.num == 3:
        room_size = 100
        rect_start = (x - room_size//2, y - room_size//2)
        rect_end = (x + room_size//2, y + room_size//2)
        canvas.create_rectangle(rect_start, rect_end, outline="blue", width=2)
        canvas.create_text(x, y, text=str(room_counter), fill="blue")
        rooms.append((rect_start, rect_end))
        room_counter += 1

def undo():
    global points, lines, rooms, point_counter, room_counter
    canvas.delete("all")
    if points:
        points.pop()
        point_counter -= 1
    if lines:
        lines.pop()
    if rooms:
        rooms.pop()
        room_counter -= 1
    redraw_canvas()

def clear_points():
    global points, lines, point_counter
    points.clear()
    lines.clear()
    point_counter = 1
    canvas.delete("all")
    redraw_canvas()

def clear_rooms():
    global rooms, room_counter
    rooms.clear()
    room_counter = 1
    canvas.delete("all")
    redraw_canvas()

def submit():
    print("Points:", points)
    print("Lines:", lines)
    print("Rooms:", rooms)

def redraw_canvas():
    if canvas_img:
        canvas.create_image(0, 0, anchor=tk.NW, image=canvas_img)
    for i, pt in enumerate(points):
        canvas.create_oval(pt[0]-3, pt[1]-3, pt[0]+3, pt[1]+3, fill="red", outline="red")
        canvas.create_text(pt[0]+5, pt[1]-5, text=str(i+1), fill="red")
    for ln in lines:
        canvas.create_line(ln[0], ln[1], fill="purple", width=2)
    for j, rect in enumerate(rooms):
        canvas.create_rectangle(rect[0], rect[1], outline="blue", width=2)
        canvas.create_text(rect[0][0]+10, rect[0][1]+10, text=str(j+1), fill="blue")

root = tk.Tk()
root.title("Map Annotation")

canvas = tk.Canvas(root, width=600, height=400)
canvas.pack()
canvas.bind("<Button-1>", on_click)
canvas.bind("<Button-3>", on_click)

btn_upload = tk.Button(root, text="Upload Image", command=upload_image)
btn_upload.pack(side=tk.LEFT)
btn_undo = tk.Button(root, text="Undo", command=undo)
btn_undo.pack(side=tk.LEFT)
btn_clear_points = tk.Button(root, text="Clear Points", command=clear_points)
btn_clear_points.pack(side=tk.LEFT)
btn_clear_rooms = tk.Button(root, text="Clear Rooms", command=clear_rooms)
btn_clear_rooms.pack(side=tk.LEFT)
btn_submit = tk.Button(root, text="Submit", command=submit)
btn_submit.pack(side=tk.LEFT)

root.mainloop()

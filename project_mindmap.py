import customtkinter as ctk
import tkinter as tk
from tkinter import simpledialog, colorchooser, Menu, filedialog, messagebox
import json
import os
from tkinter import font

# Function to check if a color is light or dark
def is_light_color(color):
    r, g, b = [int(color[i:i+2], 16) for i in (1, 3, 5)]
    brightness = (0.299*r + 0.587*g + 0.114*b) / 255
    return brightness > 0.5

# Function to lighten a color by a factor
def lighten_color(color, factor=0.5):
    r, g, b = [int(color[i:i+2], 16) for i in (1, 3, 5)]
    r = int(r + (255 - r) * factor)
    g = int(g + (255 - g) * factor)
    b = int(b + (255 - b) * factor)
    return f"#{r:02x}{g:02x}{b:02x}"

# Function to get a contrasting color for text
def contrast_color(color):
    if is_light_color(color):
        return '#000000'
    else:
        return '#ffffff'

class Node:
    MIN_WIDTH = 120
    MAX_WIDTH = 400  # Adjusted max width for demonstration
    PADDING = 20
    SPACING = 10

    def __init__(self, canvas, x, y, parent=None, width=MIN_WIDTH, height=60, radius=10, color="white", text="Node", notes=""):
        self.canvas = canvas
        self.x, self.y = x, y
        self.parent = parent
        self.width = max(width, self.MIN_WIDTH)
        self.height = height
        self.radius = radius
        self.color = color
        self.text = text
        self.notes = notes
        self.font_color = "black" if is_light_color(color) else "white"
        self.notes_visible = False
        self.subnodes = []
        self.connections = []
        self.updating = False
        self.drag_data = {"x": 0, "y": 0}
        self.file_paths = []
        self.create_context_menu()
        self.notes_id = None
        self.draw()
        self.bind_drag_events()

    def draw(self):
        title_font = ("Helvetica", 18, "bold")  # Increased font size
        notes_font = ("Helvetica", 16)  # Increased font size
        title_width, title_height = self.measure_text_size(self.text, title_font)
        notes_width, notes_height = self.measure_text_size(self.notes, notes_font, self.width - self.PADDING * 2) if self.notes else (0, 0)
        title_display_width = min(title_width, self.MAX_WIDTH)
        self.width = max(self.MIN_WIDTH, title_display_width) + self.PADDING * 2
        title_lines = (title_width - 1) // self.MAX_WIDTH + 1
        title_display_height = title_height * title_lines
        notes_lines = (notes_width - 1) // self.MAX_WIDTH + 1
        notes_display_height = notes_height * notes_lines
        self.height = title_display_height + self.PADDING * 2 + (notes_display_height + self.SPACING if self.notes else 0)
        if hasattr(self, 'body_id'):
            self.canvas.delete(self.body_id)
        if hasattr(self, 'title_id'):
            self.canvas.delete(self.title_id)
        if hasattr(self, 'notes_id'):
            self.canvas.delete(self.notes_id)
        if hasattr(self, 'notes_bg_id'):
            self.canvas.delete(self.notes_bg_id)
        self.body_id = self.canvas.create_rounded_rectangle(
            self.x - self.width // 2, self.y - self.height // 2,
            self.x + self.width // 2, self.y + self.height // 2,
            self.radius, fill=self.color, outline='black', width=2
        )
        self.title_id = self.canvas.create_text(
            self.x, self.y - self.height // 2 + self.PADDING,
            text=self.text, width=self.width - self.PADDING * 2,
            fill=self.font_color, font=title_font, anchor='n'
        )
        if self.notes:
            self.notes_id = self.canvas.create_text(
                self.x, self.y + self.PADDING + self.SPACING,
                text=self.notes, width=self.width - self.PADDING * 2,
                fill=self.font_color, font=notes_font, anchor='n'
            )
            x1, y1, x2, y2 = self.canvas.bbox(self.notes_id)
            self.notes_bg_id = self.canvas.create_rectangle(
                x1 - self.PADDING / 2, y1 - self.PADDING / 2,
                x2 + self.PADDING / 2, y2 + self.PADDING / 2,
                fill=lighten_color(self.color), outline=''
            )
            self.canvas.tag_raise(self.notes_id, self.notes_bg_id)
        self.bind_drag_events()
        self.update_scroll_region()

    def measure_text_size(self, text, font, max_width=None):
        words = text.split()
        if not words:
            return 0, 0

        temp_canvas = tk.Canvas(self.canvas)
        temp_canvas.update_idletasks()
        total_width = 0
        total_height = 0
        line_width = 0
        line_height = 0

        space_width = temp_canvas.bbox(temp_canvas.create_text(0, 0, text=" ", font=font))[2]

        for word in words:
            word_id = temp_canvas.create_text(0, 0, text=word, font=font, anchor="nw")
            temp_canvas.update_idletasks()
            word_width = temp_canvas.bbox(word_id)[2] - temp_canvas.bbox(word_id)[0]
            word_height = temp_canvas.bbox(word_id)[3] - temp_canvas.bbox(word_id)[1]
            temp_canvas.delete(word_id)

            if line_width + word_width + space_width <= (max_width if max_width is not None else self.width - Node.PADDING * 2):
                line_width += word_width + space_width
                line_height = max(line_height, word_height)
            else:
                total_width = max(total_width, line_width)
                total_height += line_height
                line_width = word_width
                line_height = word_height

        total_width = max(total_width, line_width)
        total_height += line_height
        temp_canvas.update_idletasks()
        temp_canvas.destroy()
        return total_width, total_height

    def drag(self, event):
        delta_x = event.x - self.drag_data["x"]
        delta_y = event.y - self.drag_data["y"]
        self.canvas.move(self.body_id, delta_x, delta_y)
        self.canvas.move(self.title_id, delta_x, delta_y)
        if self.notes_id:
            self.canvas.move(self.notes_id, delta_x, delta_y)
        if hasattr(self, 'notes_bg_id') and self.notes_bg_id:
            self.canvas.move(self.notes_bg_id, delta_x, delta_y)
        self.x += delta_x
        self.y += delta_y
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y
        self.update_connections()
        if self.parent:
            self.parent.update_connections()
        self.update_scroll_region()

    def bind_drag_events(self):
        self.canvas.tag_bind(self.body_id, '<ButtonPress-1>', self.start_drag)
        self.canvas.tag_bind(self.body_id, '<ButtonRelease-1>', self.stop_drag)
        self.canvas.tag_bind(self.body_id, '<B1-Motion>', self.drag)
        self.canvas.tag_bind(self.title_id, '<ButtonPress-1>', self.start_drag)
        self.canvas.tag_bind(self.title_id, '<ButtonRelease-1>', self.stop_drag)
        self.canvas.tag_bind(self.title_id, '<B1-Motion>', self.drag)
        self.canvas.tag_bind(self.body_id, '<Double-Button-1>', self.add_subnode)
        self.canvas.tag_bind(self.title_id, '<Double-Button-1>', self.add_subnode)
        self.canvas.tag_bind(self.body_id, '<Button-3>', self.show_context_menu)
        self.canvas.tag_bind(self.title_id, '<Button-3>', self.show_context_menu)
        if self.notes_id:
            self.canvas.tag_bind(self.notes_id, '<ButtonPress-1>', self.start_drag)
            self.canvas.tag_bind(self.notes_id, '<ButtonRelease-1>', self.stop_drag)
            self.canvas.tag_bind(self.notes_id, '<B1-Motion>', self.drag)
        if hasattr(self, 'notes_bg_id') and self.notes_bg_id:
            self.canvas.tag_bind(self.notes_bg_id, '<ButtonPress-1>', self.start_drag)
            self.canvas.tag_bind(self.notes_bg_id, '<ButtonRelease-1>', self.stop_drag)
            self.canvas.tag_bind(self.notes_bg_id, '<B1-Motion>', self.drag)

    def show_context_menu(self, event):
        # Rebuild file submenu dynamically for file operations
        self.context_menu.entryconfigure("Open Attached Files", menu=self.build_file_menu())
        self.context_menu.entryconfigure("Unattach Files", menu=self.build_unattach_menu())  # Update the unattach submenu
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
        # Prevent the event from propagating to the canvas
        return "break"

    def start_drag(self, event):
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y

    def stop_drag(self, event):
        self.drag_data["x"] = 0
        self.drag_data["y"] = 0

    def add_subnode(self, event):
        dialog = CustomInputDialog(self.canvas, "Subnode", "Enter subnode text:")
        text = dialog.result

        if text:
            color = colorchooser.askcolor(title="Choose subnode color")[1]
            new_x = self.x + self.width
            new_y = self.y + (len(self.subnodes) + 1) * (self.height + 20)
            subnode = Node(self.canvas, new_x, new_y, parent=self, text=text, color=color)
            self.subnodes.append(subnode)
            self.update_connections()  # Ensure the connection is drawn immediately
            subnode.update_connections()  # Update connections for the new subnode
            self.update_scroll_region()

    def update_connections(self):
        for conn_id in self.connections:
            self.canvas.delete(conn_id)
        self.connections.clear()
        if self.parent:
            conn_id = self.draw_connection(self.parent)
            self.connections.append(conn_id)
            self.parent.connections.append(conn_id)
        for subnode in self.subnodes:
            conn_id = self.draw_connection(subnode)
            self.connections.append(conn_id)
            subnode.connections.append(conn_id)
        self.update_scroll_region()

    def draw_connection(self, target_node):
        start_x, start_y = self.x, self.y
        end_x, end_y = target_node.x, target_node.y
        direction_x = end_x - start_x
        direction_y = end_y - start_y
        length = (direction_x ** 2 + direction_y ** 2) ** 0.5
        if length == 0:
            return
        direction_x /= length
        direction_y /= length
        adjusted_start_x = start_x + direction_x * (self.width / 2)
        adjusted_start_y = start_y + direction_y * (self.height / 2)
        adjusted_end_x = end_x - direction_x * (target_node.width / 2)
        adjusted_end_y = end_y - direction_y * (target_node.height / 2)
        control_x1 = (adjusted_start_x + adjusted_end_x) / 2
        control_y1 = adjusted_start_y
        control_x2 = (adjusted_start_x + adjusted_end_x) / 2
        control_y2 = adjusted_end_y
        connection = self.canvas.create_line(
            adjusted_start_x, adjusted_start_y,
            control_x1, control_y1,
            control_x2, control_y2,
            adjusted_end_x, adjusted_end_y,
            smooth=True, fill='#CCCCCC', arrow=tk.BOTH, arrowshape=(16, 20, 6)
        )
        return connection

    def propagate_update(self):
        if self.updating:
            return
        self.updating = True
        self.update_connections()
        for subnode in self.subnodes:
            subnode.propagate_update()
        self.updating = False

    def create_context_menu(self):
        self.context_menu = Menu(self.canvas, tearoff=0, font=("Helvetica", 18))  # Increased font size
        self.context_menu.add_command(label="Delete", command=self.delete_node)
        self.context_menu.add_command(label="Rename", command=self.rename_node)
        self.context_menu.add_command(label="Edit Color", command=self.edit_color)
        self.context_menu.add_command(label="Add/Edit Notes", command=self.edit_notes)
        self.context_menu.add_command(label="Attach Files", command=self.attach_files)
        file_menu = Menu(self.context_menu, tearoff=0, font=("Helvetica", 18))  # Increased font size
        self.context_menu.add_cascade(label="Open Attached Files", menu=file_menu)
        unattach_menu = Menu(self.context_menu, tearoff=0, font=("Helvetica", 18))  # Increased font size
        self.context_menu.add_cascade(label="Unattach Files", menu=unattach_menu)

    def build_file_menu(self):
        file_menu = Menu(self.context_menu, tearoff=0, font=("Helvetica", 18))  # Increased font size
        for file_path in self.file_paths:
            file_menu.add_command(
                label=os.path.basename(file_path),
                command=lambda f=file_path: self.open_file(f)  # Correctly captures file_path
            )
        return file_menu

    def build_unattach_menu(self):
        unattach_menu = Menu(self.context_menu, tearoff=0, font=("Helvetica", 18))  # Increased font size
        for file_path in self.file_paths:
            unattach_menu.add_command(
                label=os.path.basename(file_path),
                command=lambda f=file_path: self.unattach_file(f)  # Correctly captures file_path
            )
        return unattach_menu

    def attach_files(self):
        """Attach files to the node without immediately copying them to the node directory."""
        file_paths = filedialog.askopenfilenames(title="Select files")
        if file_paths:
            self.file_paths.extend(file_paths)  # Just store file paths

    def unattach_file(self, file_path):
        """Queue a file for unattachment without immediately moving it to the 'Legacy Files' directory."""
        if file_path in self.file_paths:
            self.file_paths.remove(file_path)
        else:
            messagebox.showerror("Error", "The file could not be found in the attached files list.")

    def open_file(self, file_path):
        if os.path.exists(file_path):
            os.startfile(file_path)

    def edit_color(self):
        new_color = colorchooser.askcolor(title="Choose Node Color")[1]
        if new_color:
            self.color = new_color
            self.font_color = "black" if is_light_color(new_color) else "white"
            self.draw()

    def edit_notes(self):
        """Edit notes without updating directory immediately."""
        dialog = CustomInputDialog(self.canvas, "Add/Edit Notes", "Enter notes:", initialvalue=self.notes)
        new_notes = dialog.result

        if new_notes is not None:
            self.notes = new_notes
            self.draw()

    def delete_node(self):
        while self.subnodes:
            self.subnodes[-1].delete_node()
        for connection in self.connections:
            self.canvas.delete(connection)
        self.connections.clear()
        if self.parent:
            self.parent.subnodes.remove(self)
            self.parent.update_connections()
        self.canvas.delete(self.body_id)
        self.canvas.delete(self.title_id)
        if hasattr(self, 'notes_id') and self.notes_id:
            self.canvas.delete(self.notes_id)
        if hasattr(self, 'notes_bg_id') and self.notes_bg_id:
            self.canvas.delete(self.notes_bg_id)
        for subnode in self.subnodes:
            subnode.parent = None
        self.subnodes = []

    def rename_node(self):
        dialog = CustomInputDialog(self.canvas, "Rename Node", "Enter new text:")
        new_text = dialog.result

        if new_text:
            self.text = new_text
            self.draw()
            self.update_connections()

    def to_dict(self):
        node_dict = {
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'radius': self.radius,
            'color': self.color,
            'text': self.text,
            'notes': self.notes,
            'file_paths': self.file_paths,
            'subnodes': [subnode.to_dict() for subnode in self.subnodes]
        }
        return node_dict

    @classmethod
    def from_dict(cls, canvas, data, parent=None):
        node = cls(canvas, data['x'], data['y'], parent=parent,
                width=data['width'], height=data['height'], radius=data['radius'],
                color=data['color'], text=data['text'], notes=data.get('notes', ''))
        node.file_paths = data.get('file_paths', [])
        node.notes_visible = bool(data.get('notes'))
        for subnode_data in data.get('subnodes', []):
            subnode = cls.from_dict(canvas, subnode_data, parent=node)
            node.subnodes.append(subnode)
        node.update_connections()  # Ensure connections are drawn when loading from dict
        return node

    def update_scroll_region(self):
        self.canvas.update_idletasks()
        bbox = self.canvas.bbox("all")
        buffer = 500  # Add a buffer of 500 pixels in all directions
        if bbox:
            self.canvas.configure(scrollregion=(bbox[0] - buffer, bbox[1] - buffer, bbox[2] + buffer, bbox[3] + buffer))


class CustomCanvas(ctk.CTkCanvas):
    def create_rounded_rectangle(self, x1, y1, x2, y2, radius, **kwargs):
        points = [x1+radius, y1, x1+radius, y1, x2-radius, y1, x2-radius, y1, x2, y1, x2, y1+radius, x2, y1+radius, x2, y2-radius, x2, y2-radius, x2, y2, x2-radius, y2, x2-radius, y2, x1+radius, y2, x1+radius, y2, x1, y2, x1, y2-radius, x1, y1+radius, x1, y1+radius, x1, y1]
        return self.create_polygon(points, smooth=True, **kwargs)

class CustomInputDialog(simpledialog.Dialog):
    def __init__(self, parent, title, prompt, initialvalue=""):
        self.prompt = prompt
        self.initialvalue = initialvalue
        super().__init__(parent, title)

    def body(self, master):
        tk.Label(master, text=self.prompt, font=("Helvetica", 18)).pack(padx=10, pady=10)  # Increased font size
        self.entry = tk.Entry(master, font=("Helvetica", 18))  # Increased font size
        self.entry.pack(padx=10, pady=10)
        self.entry.insert(0, self.initialvalue)
        return self.entry

    def apply(self):
        self.result = self.entry.get()

class MindMapApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title('Project MindMap')
        self.configure(bg_color='#1E1E1E')
        self.geometry('900x600')  # Set initial window size
        self.canvas_bg = '#0d172b'
        
        self.canvas_frame = tk.Frame(self)
        self.canvas_frame.pack(fill="both", expand=True)
        self.canvas = CustomCanvas(self.canvas_frame, background=self.canvas_bg, width=1200, height=800)
        self.scroll_x = tk.Scrollbar(self.canvas_frame, orient="horizontal", command=self.canvas.xview)
        self.scroll_y = tk.Scrollbar(self.canvas_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=self.scroll_x.set, yscrollcommand=self.scroll_y.set)
        
        self.scroll_x.pack(side="bottom", fill="x")
        self.scroll_y.pack(side="right", fill="y")
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind('<Configure>', self.adjust_canvas_title)
        self.canvas.bind_all("<MouseWheel>", self.on_mouse_wheel)
        self.canvas.bind_all("<Shift-MouseWheel>", self.on_shift_mouse_wheel)

        self.root_nodes = []
        self.canvas_title_text = ''
        self.canvas_title_id = None
        self.create_menu()

    def adjust_canvas_title(self, event=None):
        if self.canvas_title_id:
            self.canvas.delete(self.canvas_title_id)
        if self.canvas_title_text:
            self.canvas_title_id = self.canvas.create_text(
                self.canvas.winfo_width() / 2, 20,
                text=self.canvas_title_text, fill=contrast_color(self.canvas_bg),
                font=('Helvetica', 24, 'bold'), anchor='n'
            )

    def on_mouse_wheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def on_shift_mouse_wheel(self, event):
        self.canvas.xview_scroll(int(-1*(event.delta/120)), "units")

    def set_canvas_title(self):
        dialog = CustomInputDialog(self.canvas, "Canvas Title", "Enter canvas title:")
        title = dialog.result

        if title is not None:
            self.canvas_title_text = title
            self.adjust_canvas_title()

    def change_canvas_background(self):
        color = colorchooser.askcolor(title="Choose Background Color", initialcolor=self.canvas_bg)[1]
        if color:
            self.canvas_bg = color
            self.canvas.configure(bg=color)
            self.adjust_canvas_title()

    def create_menu(self):
        menubar = tk.Menu(self, font=("Helvetica", 18))  # Increased font size
        file_menu = tk.Menu(menubar, tearoff=0, font=("Helvetica", 18))  # Increased font size
        file_menu.add_command(label="Save", command=self.save_mind_map)
        file_menu.add_command(label="Load", command=self.load_mind_map)
        menubar.add_cascade(label="File", menu=file_menu)
        canvas_options_menu = tk.Menu(menubar, tearoff=0, font=("Helvetica", 18))  # Increased font size
        canvas_options_menu.add_command(label="Set Canvas Title", command=self.set_canvas_title)
        canvas_options_menu.add_command(label="Change Background Color", command=self.change_canvas_background)
        menubar.add_cascade(label="Canvas Options", menu=canvas_options_menu)

        menubar.add_command(label="Create New Parent Node", command=self.create_root_node)  # Add new button
        self.config(menu=menubar)

    def save_mind_map(self):
        mind_map_data = {
            'title': self.canvas_title_text,
            'nodes': [node.to_dict() for node in self.root_nodes]
        }
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, 'w') as file:
                json.dump(mind_map_data, file, indent=4)

    def load_mind_map(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, 'r') as file:
                mind_map_data = json.load(file)
            self.canvas.delete("all")
            self.root_nodes = []
            self.canvas_title_text = mind_map_data.get('title', '')
            self.adjust_canvas_title()
            for node_data in mind_map_data.get('nodes', []):
                node = Node.from_dict(self.canvas, node_data)
                self.root_nodes.append(node)
            self.update_all_connections()

    def create_root_node(self):
        dialog = CustomInputDialog(self.canvas, "Root Node", "Enter root node text:")
        text = dialog.result
        if text:
            color = colorchooser.askcolor(title="Choose root node color")[1]
            if color:
                node = Node(self.canvas, self.canvas.winfo_width() // 2, self.canvas.winfo_height() // 2, text=text, color=color)
                self.root_nodes.append(node)
                self.update_scroll_region()

    def update_all_connections(self):
        for node in self.root_nodes:
            node.propagate_update()
        self.update_scroll_region()

    def update_scroll_region(self):
        self.canvas.update_idletasks()
        bbox = self.canvas.bbox("all")
        buffer = 500  # Add a buffer of 500 pixels in all directions
        if bbox:
            self.canvas.configure(scrollregion=(bbox[0] - buffer, bbox[1] - buffer, bbox[2] + buffer, bbox[3] + buffer))

if __name__ == '__main__':
    app = MindMapApp()
    app.mainloop()

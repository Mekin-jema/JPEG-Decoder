# jpeg_decoder_ui.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import numpy as np
from io import BytesIO
import threading
from pathlib import Path
from jpeg_decoder import jpeg_decoder  # Assuming the decoder code is in jpeg_decoder.py

class JpegDecoderUI:
    def __init__(self, root):
        self.root = root
        self.root.title("JPEG Decoder")
        
        # Initialize variables
        self.image_path = None
        self.original_image = None
        self.decoded_image = None
        self.loading = False
        
        # Create UI elements
        self.create_widgets()
        
    def create_widgets(self):
        # Main container
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Top panel - File selection
        self.file_frame = ttk.LabelFrame(self.main_frame, text="File Selection", padding="10")
        self.file_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.path_label = ttk.Label(self.file_frame, text="No file selected")
        self.path_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.browse_button = ttk.Button(self.file_frame, text="Browse", command=self.browse_file)
        self.browse_button.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Middle panel - Image display
        self.image_frame = ttk.LabelFrame(self.main_frame, text="Image Preview", padding="10")
        self.image_frame.pack(fill=tk.BOTH, expand=True)
        
        # Canvas for image display
        self.canvas = tk.Canvas(self.image_frame, bg='white')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Bottom panel - Controls
        self.control_frame = ttk.Frame(self.main_frame)
        self.control_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.decode_button = ttk.Button(
            self.control_frame, 
            text="Decode JPEG", 
            command=self.start_decoding_thread,
            state=tk.DISABLED
        )
        self.decode_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.save_button = ttk.Button(
            self.control_frame, 
            text="Save Decoded Image", 
            command=self.save_image,
            state=tk.DISABLED
        )
        self.save_button.pack(side=tk.LEFT)
        
        # Progress bar
        self.progress = ttk.Progressbar(
            self.main_frame, 
            orient=tk.HORIZONTAL, 
            mode='determinate'
        )
        self.progress.pack(fill=tk.X, pady=(10, 0))
        
        # Status label
        self.status_label = ttk.Label(self.main_frame, text="Ready")
        self.status_label.pack(fill=tk.X)
        
        # Configure grid weights
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(1, weight=1)
        
    def browse_file(self):
        filetypes = (
            ("JPEG files", "*.jpg *.jpeg *.jpe *.jfif *.jfi"),
            ("All files", "*.*")
        )
        
        file_path = filedialog.askopenfilename(
            title="Select a JPEG file",
            filetypes=filetypes
        )
        
        if file_path:
            self.image_path = Path(file_path)
            self.path_label.config(text=str(self.image_path))
            self.load_preview_image()
            self.decode_button.config(state=tk.NORMAL)
            self.save_button.config(state=tk.DISABLED)
    
    def load_preview_image(self):
        try:
            # Load and display a preview of the original image
            img = Image.open(self.image_path)
            img.thumbnail((400, 400))  # Resize for preview
            
            self.original_image = ImageTk.PhotoImage(img)
            self.display_image(self.original_image)
            self.status_label.config(text="Preview loaded. Ready to decode.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {str(e)}")
            self.status_label.config(text="Error loading image.")
    
    def display_image(self, photo_image):
        self.canvas.delete("all")
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        # Center the image on the canvas
        x = (canvas_width - photo_image.width()) // 2
        y = (canvas_height - photo_image.height()) // 2
        
        self.canvas.create_image(x, y, anchor=tk.NW, image=photo_image)
    
    def start_decoding_thread(self):
        if self.loading:
            return
            
        self.loading = True
        self.decode_button.config(state=tk.DISABLED)
        self.save_button.config(state=tk.DISABLED)
        self.progress["value"] = 0
        self.status_label.config(text="Decoding...")
        
        # Start decoding in a separate thread to keep UI responsive
        decode_thread = threading.Thread(
            target=self.decode_image,
            daemon=True
        )
        decode_thread.start()
        
        # Check progress periodically
        self.root.after(100, self.check_progress)
    
    def decode_image(self):
        try:
            # Create a decoder instance and decode the image
            decoder = JpegDecoder(self.image_path)
            
            # Get the decoded image array
            decoded_array = decoder.image_array
            
            # Convert to PIL Image
            if decoded_array.ndim == 3:  # Color image
                decoded_array = np.swapaxes(decoded_array, 0, 1)
                self.decoded_image = Image.fromarray(decoded_array)
            else:  # Grayscale image
                self.decoded_image = Image.fromarray(decoded_array)
            
            # Update UI in main thread
            self.root.after(0, self.decoding_complete)
            
        except Exception as e:
            self.root.after(0, self.decoding_failed, str(e))
    
    def check_progress(self):
        # This would be updated to check actual progress from the decoder
        if self.loading:
            current = self.progress["value"]
            if current < 90:  # Simulate progress
                self.progress["value"] = current + 5
            self.root.after(100, self.check_progress)
    
    def decoding_complete(self):
        self.loading = False
        self.progress["value"] = 100
        
        # Display decoded image
        img = self.decoded_image.copy()
        img.thumbnail((400, 400))  # Resize for display
        photo_img = ImageTk.PhotoImage(img)
        
        self.display_image(photo_img)
        self.decoded_image_tk = photo_img  # Keep reference
        
        self.decode_button.config(state=tk.NORMAL)
        self.save_button.config(state=tk.NORMAL)
        self.status_label.config(text="Decoding complete!")
    
    def decoding_failed(self, error_msg):
        self.loading = False
        self.progress["value"] = 0
        self.decode_button.config(state=tk.NORMAL)
        self.status_label.config(text=f"Decoding failed: {error_msg}")
        messagebox.showerror("Decoding Error", error_msg)
    
    def save_image(self):
        if not self.decoded_image:
            return
            
        filetypes = (
            ("PNG files", "*.png"),
            ("JPEG files", "*.jpg"),
            ("All files", "*.*")
        )
        
        default_name = self.image_path.stem + "_decoded.png"
        
        save_path = filedialog.asksaveasfilename(
            title="Save decoded image",
            initialfile=default_name,
            filetypes=filetypes,
            defaultextension=".png"
        )
        
        if save_path:
            try:
                self.decoded_image.save(save_path)
                self.status_label.config(text=f"Image saved to {save_path}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save image: {str(e)}")
                self.status_label.config(text="Save failed")

def main():
    root = tk.Tk()
    root.geometry("800x600")
    
    # Set window icon if available
    try:
        root.iconbitmap(default='icon.ico')  # Provide path to your icon file
    except:
        pass
    
    app = JpegDecoderUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
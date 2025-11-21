# Copyright Artem Khrapov, 2025
# For usage terms, see LICENSE

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
import numpy as np
from PIL import Image, ImageTk
import os
from threading import Thread
import time
import math

class VideoCropperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Enhanced Video Cropper")
        self.root.geometry("1000x750")
        
        # Video properties
        self.video_path = None
        self.video = None
        self.total_frames = 0
        self.current_frame = 0
        self.fps = 30
        self.width = 0
        self.height = 0
        
        # Display properties
        self.display_width = 800
        self.display_height = 450
        self.display_x_offset = 0
        self.display_y_offset = 0
        self.display_scale = 1.0
        
        # Cropping properties
        self.crop_x1 = None
        self.crop_y1 = None
        self.crop_x2 = None
        self.crop_y2 = None
        self.is_selecting = False
        self.selection_rect = None
        self.show_crop_area = False
        self.aspect_ratio = None
        self.maintain_aspect = tk.BooleanVar(value=False)
        self.drag_handle = None
        
        # Temporal cropping
        self.start_frame = 0
        self.end_frame = 0
        
        # Playback state
        self.is_playing = False
        self.playback_thread = None
        
        # New features
        self.manual_frame_var = tk.IntVar(value=0)
        self.manual_frame_entry = None
        self.manual_frame_checkbox = tk.BooleanVar(value=False)
        
        # Processing options
        self.rescale_var = tk.BooleanVar(value=False)
        self.target_width = tk.IntVar(value=512)
        self.target_height = tk.IntVar(value=512)
        
        self.drop_frames_var = tk.BooleanVar(value=False)
        self.target_frames = tk.IntVar(value=100)
        
        self.pad_last_frame_var = tk.BooleanVar(value=False)
        
        self.output_fps = tk.DoubleVar(value=30.0)
        
        # Progress window
        self.progress_window = None
        self.progress_bar = None
        self.progress_label = None
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Left panel (video display)
        left_panel = ttk.Frame(main_frame)
        left_panel.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Video display area
        self.canvas = tk.Canvas(left_panel, width=self.display_width, height=self.display_height, bg='black')
        self.canvas.grid(row=0, column=0, pady=10)
        
        # Bind mouse events
        self.canvas.bind("<Button-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        
        # Timeline with manual frame entry
        timeline_frame = ttk.Frame(left_panel)
        timeline_frame.grid(row=1, column=0, pady=10, sticky=(tk.W, tk.E))
        
        ttk.Label(timeline_frame, text="Timeline:").pack(side=tk.LEFT, padx=5)
        self.timeline = ttk.Scale(timeline_frame, from_=0, to=100, orient=tk.HORIZONTAL,
                                  command=self.on_timeline_change, length=600)
        self.timeline.pack(side=tk.LEFT, padx=5)
        
        self.frame_label = ttk.Label(timeline_frame, text="Frame: 0/0")
        self.frame_label.pack(side=tk.LEFT, padx=10)
        
        # Manual frame entry
        self.manual_frame_checkbox_check = ttk.Checkbutton(
            timeline_frame, 
            text="Manual Frame",
            variable=self.manual_frame_checkbox,
            command=self.toggle_manual_frame_entry
        )
        self.manual_frame_checkbox_check.pack(side=tk.LEFT, padx=5)
        
        self.manual_frame_entry = ttk.Entry(
            timeline_frame, 
            textvariable=self.manual_frame_var,
            width=5,
            state='disabled'
        )
        self.manual_frame_entry.pack(side=tk.LEFT, padx=2)
        self.manual_frame_entry.bind("<Return>", self.on_manual_frame_enter)
        
        # Control buttons
        button_frame = ttk.Frame(left_panel)
        button_frame.grid(row=2, column=0, pady=10)
        
        self.load_btn = ttk.Button(button_frame, text="Load Video", command=self.load_video)
        self.load_btn.pack(side=tk.LEFT, padx=5)
        
        self.play_btn = ttk.Button(button_frame, text="Play", command=self.toggle_playback, state='disabled')
        self.play_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(button_frame, text="Stop", command=self.stop_playback, state='disabled')
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.reset_btn = ttk.Button(button_frame, text="Reset", command=self.reset_selection)
        self.reset_btn.pack(side=tk.LEFT, padx=5)
        
        self.crop_btn = ttk.Button(button_frame, text="Crop Video", command=self.crop_video, state='disabled')
        self.crop_btn.pack(side=tk.LEFT, padx=5)
        
        # Temporal cropping
        temporal_frame = ttk.LabelFrame(left_panel, text="Temporal Cropping", padding="10")
        temporal_frame.grid(row=3, column=0, pady=10, sticky=(tk.W, tk.E))
        
        ttk.Label(temporal_frame, text="Start Frame:").grid(row=0, column=0, sticky=tk.W)
        self.start_frame_var = tk.IntVar(value=0)
        self.start_frame_entry = ttk.Entry(temporal_frame, textvariable=self.start_frame_var, width=10)
        self.start_frame_entry.grid(row=0, column=1, padx=5)
        
        ttk.Label(temporal_frame, text="End Frame:").grid(row=0, column=2, sticky=tk.W, padx=(20, 0))
        self.end_frame_var = tk.IntVar(value=0)
        self.end_frame_entry = ttk.Entry(temporal_frame, textvariable=self.end_frame_var, width=10)
        self.end_frame_entry.grid(row=0, column=3, padx=5)
        
        # Status
        self.status_label = ttk.Label(left_panel, text="No video loaded", relief=tk.SUNKEN)
        self.status_label.grid(row=4, column=0, pady=10, sticky=(tk.W, tk.E))
        
        # Right panel (controls)
        right_panel = ttk.Frame(main_frame)
        right_panel.grid(row=0, column=1, padx=10, sticky=(tk.N, tk.S))
        
        # Aspect ratio control
        self.aspect_check = ttk.Checkbutton(right_panel, text="Maintain Aspect Ratio",
                                           variable=self.maintain_aspect,
                                           command=self.on_aspect_change)
        self.aspect_check.pack(pady=10)
        
        # Manual crop controls
        crop_frame = ttk.LabelFrame(right_panel, text="Crop Coordinates", padding="10")
        crop_frame.pack(pady=10, fill=tk.BOTH, expand=True)
        
        self.coord_entries = {}
        for i, (label, var) in enumerate([("X1:", "x1"), ("Y1:", "y1"), ("X2:", "x2"), ("Y2:", "y2")]):
            ttk.Label(crop_frame, text=label).grid(row=i, column=0, sticky=tk.W, pady=2)
            entry = ttk.Entry(crop_frame, width=8)
            entry.grid(row=i, column=1, padx=5, pady=2)
            entry.bind("<KeyRelease>", lambda e, lbl=label: self.on_coord_change(e, lbl))
            self.coord_entries[label] = entry
        
        # Aspect ratio display
        self.aspect_label = ttk.Label(right_panel, text="Aspect Ratio: N/A")
        self.aspect_label.pack(pady=5)
        
        # Processing options
        process_frame = ttk.LabelFrame(right_panel, text="Processing Options", padding="10")
        process_frame.pack(pady=10, fill=tk.BOTH, expand=True)
        
        # Rescale option
        rescale_check = ttk.Checkbutton(process_frame, text="Rescale Output", variable=self.rescale_var)
        rescale_check.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        ttk.Label(process_frame, text="Target Width:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Entry(process_frame, textvariable=self.target_width, width=8).grid(row=1, column=1, padx=5, pady=2)
        
        ttk.Label(process_frame, text="Target Height:").grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Entry(process_frame, textvariable=self.target_height, width=8).grid(row=2, column=1, padx=5, pady=2)
        
        # Drop frames option
        drop_check = ttk.Checkbutton(process_frame, text="Drop Frames", variable=self.drop_frames_var)
        drop_check.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        ttk.Label(process_frame, text="Target Frame Count:").grid(row=4, column=0, sticky=tk.W, pady=2)
        ttk.Entry(process_frame, textvariable=self.target_frames, width=8).grid(row=4, column=1, padx=5, pady=2)
        
        # Pad last frame option
        pad_check = ttk.Checkbutton(process_frame, text="Pad Last Frame", variable=self.pad_last_frame_var)
        pad_check.grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Output FPS
        ttk.Label(process_frame, text="Output FPS:").grid(row=6, column=0, sticky=tk.W, pady=2)
        ttk.Entry(process_frame, textvariable=self.output_fps, width=8).grid(row=6, column=1, padx=5, pady=2)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=3)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        left_panel.columnconfigure(0, weight=1)
        left_panel.rowconfigure(0, weight=1)
    
    def toggle_manual_frame_entry(self):
        if self.manual_frame_checkbox.get():
            self.manual_frame_entry.config(state='normal')
        else:
            self.manual_frame_entry.config(state='disabled')
    
    def on_manual_frame_enter(self, event):
        if self.manual_frame_checkbox.get() and self.video is not None:
            try:
                frame_num = self.manual_frame_var.get()
                frame_num = max(0, min(self.total_frames - 1, frame_num))
                self.load_frame(frame_num)
                self.timeline.set(frame_num)
            except:
                pass
    
    def on_aspect_change(self):
        if self.maintain_aspect.get():
            if self.crop_x1 is not None and self.crop_x2 is not None:
                width = self.crop_x2 - self.crop_x1
                height = self.crop_y2 - self.crop_y1
                if height > 0:
                    self.aspect_ratio = width / height
                    self.aspect_label.config(text=f"Aspect Ratio: {self.aspect_ratio:.2f}")
            else:
                messagebox.showinfo("Info", "Please make a selection first")
                self.maintain_aspect.set(False)
                self.aspect_ratio = None
                self.aspect_label.config(text="Aspect Ratio: N/A")
        else:
            self.aspect_ratio = None
            self.aspect_label.config(text="Aspect Ratio: N/A")
    
    def on_coord_change(self, event, label):
        try:
            # Get values from all entries
            x1 = float(self.coord_entries["X1:"].get())
            y1 = float(self.coord_entries["Y1:"].get())
            x2 = float(self.coord_entries["X2:"].get())
            y2 = float(self.coord_entries["Y2:"].get())
            
            # Clamp to video dimensions
            x1 = max(0, min(self.width-1, x1))
            y1 = max(0, min(self.height-1, y1))
            x2 = max(0, min(self.width-1, x2))
            y2 = max(0, min(self.height-1, y2))
            
            # Ensure ordering
            if x2 < x1:
                x1, x2 = x2, x1
            if y2 < y1:
                y1, y2 = y2, y1
            
            # Update crop coordinates
            self.crop_x1 = x1
            self.crop_y1 = y1
            self.crop_x2 = x2
            self.crop_y2 = y2
            
            # Redraw the frame and the crop rectangle
            self.load_frame(self.current_frame)
            
            # Update status
            self.status_label.config(text=f"Crop area: {int(x1)}-{int(x2)}, {int(y1)}-{int(y2)}")
            
            # Update aspect ratio if maintaining aspect
            if self.maintain_aspect.get() and self.aspect_ratio is not None:
                self.on_aspect_change()
                
        except ValueError:
            # Ignore invalid input
            pass
    
    def load_video(self):
        file_path = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv")]
        )
        
        if file_path:
            self.video_path = file_path
            self.video = cv2.VideoCapture(file_path)
            
            # Get video properties
            self.total_frames = int(self.video.get(cv2.CAP_PROP_FRAME_COUNT))
            self.fps = self.video.get(cv2.CAP_PROP_FPS)
            self.width = int(self.video.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.height = int(self.video.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Update UI
            self.timeline.config(to=self.total_frames - 1)
            self.start_frame_var.set(0)
            self.end_frame_var.set(self.total_frames - 1)
            self.frame_label.config(text=f"Frame: 0/{self.total_frames}")
            
            # Enable controls
            self.play_btn.config(state='normal')
            self.stop_btn.config(state='normal')
            self.crop_btn.config(state='normal')
            
            # Load first frame
            self.current_frame = 0
            self.load_frame(0)
            
            self.status_label.config(text=f"Loaded: {os.path.basename(file_path)}")
    
    def load_frame(self, frame_num):
        if self.video is None:
            return
            
        self.video.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        ret, frame = self.video.read()
        
        if ret:
            self.current_frame = frame_num
            
            # Convert to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Calculate aspect ratio and scaling factors
            video_aspect = self.width / self.height
            display_aspect = self.display_width / self.display_height
            
            if video_aspect > display_aspect:
                # Video is wider than display
                scale = self.display_width / self.width
                new_width = self.display_width
                new_height = int(self.height * scale)
            else:
                # Video is taller than display
                scale = self.display_height / self.height
                new_width = int(self.width * scale)
                new_height = self.display_height
            
            # Calculate offsets for centering
            self.display_x_offset = (self.display_width - new_width) // 2
            self.display_y_offset = (self.display_height - new_height) // 2
            self.display_scale = scale
            
            # Resize for display while maintaining aspect ratio
            frame_resized = cv2.resize(frame_rgb, (new_width, new_height))
            
            # Create a black background and place the resized frame in the center
            frame_display = np.zeros((self.display_height, self.display_width, 3), dtype=np.uint8)
            frame_display[self.display_y_offset:self.display_y_offset+new_height, 
                         self.display_x_offset:self.display_x_offset+new_width] = frame_resized
            
            # Convert to PIL Image
            self.photo = ImageTk.PhotoImage(image=Image.fromarray(frame_display))
            
            # Clear canvas
            self.canvas.delete("all")
            
            # Draw frame
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
            
            # Draw crop rectangle if exists
            if self.crop_x1 is not None and self.crop_y1 is not None and self.crop_x2 is not None and self.crop_y2 is not None:
                self.draw_crop_rectangle()
            
            # Update label
            self.frame_label.config(text=f"Frame: {frame_num}/{self.total_frames}")
    
    def draw_crop_rectangle(self):
        if self.crop_x1 is None:
            return
            
        # Calculate display coordinates using the scale and offset
        x1 = self.display_x_offset + self.crop_x1 * self.display_scale
        y1 = self.display_y_offset + self.crop_y1 * self.display_scale
        x2 = self.display_x_offset + self.crop_x2 * self.display_scale
        y2 = self.display_y_offset + self.crop_y2 * self.display_scale
        
        # Draw rectangle
        self.canvas.create_rectangle(x1, y1, x2, y2, outline='red', width=2, tags='crop_rect')
        
        # Draw handles
        handle_size = 8
        # Top-left handle
        self.canvas.create_rectangle(x1-handle_size, y1-handle_size, x1+handle_size, y1+handle_size, 
                                    fill='red', outline='white', tags='top_left_handle')
        # Bottom-right handle
        self.canvas.create_rectangle(x2-handle_size, y2-handle_size, x2+handle_size, y2+handle_size, 
                                    fill='red', outline='white', tags='bottom_right_handle')
    
    def on_mouse_down(self, event):
        # Check if click is within the video area (not in the black borders)
        if (event.x < self.display_x_offset or event.x >= self.display_x_offset + self.width * self.display_scale or
            event.y < self.display_y_offset or event.y >= self.display_y_offset + self.height * self.display_scale):
            return
            
        self.is_selecting = True
        
        # Convert display coordinates to video coordinates
        video_x = (event.x - self.display_x_offset) / self.display_scale
        video_y = (event.y - self.display_y_offset) / self.display_scale
        
        # Check if clicking on a handle
        handle = self.canvas.find_closest(event.x, event.y)
        tags = self.canvas.gettags(handle)
        
        if "top_left_handle" in tags:
            self.drag_handle = "top_left"
            # Record initial positions
            self.initial_x1 = self.crop_x1
            self.initial_y1 = self.crop_y1
            self.initial_x2 = self.crop_x2
            self.initial_y2 = self.crop_y2
        elif "bottom_right_handle" in tags:
            self.drag_handle = "bottom_right"
            # Record initial positions
            self.initial_x1 = self.crop_x1
            self.initial_y1 = self.crop_y1
            self.initial_x2 = self.crop_x2
            self.initial_y2 = self.crop_y2
            if self.maintain_aspect.get() and self.aspect_ratio is not None:
                # Record initial aspect ratio
                self.initial_aspect_ratio = self.aspect_ratio
        else:
            # Regular selection
            self.drag_handle = None
            self.crop_x1 = video_x
            self.crop_y1 = video_y
            self.crop_x2 = self.crop_x1
            self.crop_y2 = self.crop_y1
            
            # Set aspect ratio if maintaining aspect
            if self.maintain_aspect.get():
                self.aspect_ratio = 1.0  # Default to 1:1
                self.on_aspect_change()
        
        self.show_crop_area = True
    
    def on_mouse_drag(self, event):
        if not self.is_selecting:
            return
            
        # Convert display coordinates to video coordinates
        video_x = (event.x - self.display_x_offset) / self.display_scale
        video_y = (event.y - self.display_y_offset) / self.display_scale
        
        # Clamp coordinates to video bounds
        video_x = max(0, min(self.width, video_x))
        video_y = max(0, min(self.height, video_y))
        
        if self.drag_handle == "top_left":
            # Move entire crop area
            dx = video_x - self.initial_x1
            dy = video_y - self.initial_y1
            
            self.crop_x1 = self.initial_x2 + dx
            self.crop_y1 = self.initial_y2 + dy
            self.crop_x2 = self.initial_x1 + dx
            self.crop_y2 = self.initial_y1 + dy
            
            # Ensure proper ordering
            if self.crop_x1 > self.crop_x2:
                self.crop_x1, self.crop_x2 = self.crop_x2, self.crop_x1
            if self.crop_y1 > self.crop_y2:
                self.crop_y1, self.crop_y2 = self.crop_y2, self.crop_y1
                
        elif self.drag_handle == "bottom_right":
            # Adjust size
            if self.maintain_aspect.get() and self.aspect_ratio is not None:
                # Maintain aspect ratio
                dx = video_x - self.initial_x2
                dy = video_y - self.initial_y2
                
                # Use the constraint that gives the closest point
                new_x2 = self.initial_x2 + dx
                new_y2 = self.initial_y2 + dy
                
                # Calculate desired points with aspect ratio constraint
                # Horizontal constraint: (new_x2, self.initial_y1 + (new_x2 - self.initial_x1) / self.initial_aspect_ratio)
                x2_h = new_x2
                y2_h = self.initial_y1 + (new_x2 - self.initial_x1) / self.initial_aspect_ratio
                
                # Vertical constraint: (self.initial_x1 + (new_y2 - self.initial_y1) * self.initial_aspect_ratio, new_y2)
                x2_v = self.initial_x1 + (new_y2 - self.initial_y1) * self.initial_aspect_ratio
                y2_v = new_y2
                
                # Calculate distances to original point
                d_h = ((x2_h - new_x2)**2 + (y2_h - new_y2)**2)
                d_v = ((x2_v - new_x2)**2 + (y2_v - new_y2)**2)
                
                # Choose the closer constraint
                if d_h < d_v:
                    self.crop_x2 = x2_h
                    self.crop_y2 = y2_h
                else:
                    self.crop_x2 = x2_v
                    self.crop_y2 = y2_v
            else:
                # Free adjustment
                self.crop_x2 = video_x
                self.crop_y2 = video_y
                
            # Ensure proper ordering
            if self.crop_x2 < self.crop_x1:
                self.crop_x2 = self.crop_x1
            if self.crop_y2 < self.crop_y1:
                self.crop_y2 = self.crop_y1
        else:
            # Regular selection
            self.crop_x2 = video_x
            self.crop_y2 = video_y
            
            # Ensure proper ordering
            if self.crop_x2 < self.crop_x1:
                self.crop_x1, self.crop_x2 = self.crop_x2, self.crop_x1
            if self.crop_y2 < self.crop_y1:
                self.crop_y1, self.crop_y2 = self.crop_y2, self.crop_y1
        
        # Redraw
        self.canvas.delete('crop_rect')
        self.canvas.delete('top_left_handle')
        self.canvas.delete('bottom_right_handle')
        self.draw_crop_rectangle()
        
        # Update coordinate entries
        self.update_coord_entries()
    
    def on_mouse_up(self, event):
        self.is_selecting = False
        self.drag_handle = None
        
        # Update coordinate entries
        self.update_coord_entries()
        
        # Update status
        if self.crop_x1 is not None:
            self.status_label.config(text=f"Crop area: {int(self.crop_x1)}-{int(self.crop_x2)}, {int(self.crop_y1)}-{int(self.crop_y2)}")
        
        # Update aspect ratio if maintaining aspect
        if self.maintain_aspect.get():
            self.on_aspect_change()
    
    def update_coord_entries(self):
        if self.crop_x1 is not None:
            self.coord_entries["X1:"].delete(0, tk.END)
            self.coord_entries["X1:"].insert(0, str(int(self.crop_x1)))
            
            self.coord_entries["Y1:"].delete(0, tk.END)
            self.coord_entries["Y1:"].insert(0, str(int(self.crop_y1)))
            
            self.coord_entries["X2:"].delete(0, tk.END)
            self.coord_entries["X2:"].insert(0, str(int(self.crop_x2)))
            
            self.coord_entries["Y2:"].delete(0, tk.END)
            self.coord_entries["Y2:"].insert(0, str(int(self.crop_y2)))
    
    def toggle_playback(self):
        if self.is_playing:
            self.is_playing = False
            self.play_btn.config(text="Play")
        else:
            self.is_playing = True
            self.play_btn.config(text="Pause")
            self.playback_thread = Thread(target=self.play_video)
            self.playback_thread.start()
    
    def play_video(self):
        while self.is_playing and self.current_frame < self.total_frames - 1:
            self.load_frame(self.current_frame + 1)
            self.timeline.set(self.current_frame)
            self.root.update()
            time.sleep(1.0 / self.fps)
        
        self.is_playing = False
        self.play_btn.config(text="Play")
    
    def stop_playback(self):
        self.is_playing = False
        self.current_frame = 0
        self.load_frame(0)
        self.timeline.set(0)
        self.play_btn.config(text="Play")
    
    def on_timeline_change(self, value):
        frame_num = int(float(value))
        self.load_frame(frame_num)
    
    def reset_selection(self):
        self.crop_x1 = None
        self.crop_y1 = None
        self.crop_x2 = None
        self.crop_y2 = None
        self.canvas.delete('crop_rect')
        self.canvas.delete('top_left_handle')
        self.canvas.delete('bottom_right_handle')
        self.status_label.config(text="No crop area selected")
        self.update_coord_entries()
    
    def create_progress_window(self):
        # Create a new top-level window for progress
        self.progress_window = tk.Toplevel(self.root)
        self.progress_window.title("Processing Video")
        self.progress_window.geometry("400x150")
        
        # Center the progress window
        self.progress_window.transient(self.root)
        self.progress_window.grab_set()
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(self.progress_window, length=300, mode='determinate')
        self.progress_bar.pack(pady=15)
        
        # Status label
        self.progress_label = ttk.Label(self.progress_window, text="Initializing...")
        self.progress_label.pack()
        
        # Make window non-resizable
        self.progress_window.resizable(False, False)
        
        # Position in center of parent window
        self.progress_window.update()
        x = (self.progress_window.winfo_screenwidth() // 2) - (self.progress_window.winfo_width() // 2)
        y = (self.progress_window.winfo_screenheight() // 2) - (self.progress_window.winfo_height() // 2)
        self.progress_window.geometry(f"+{x}+{y}")
        
    def update_progress(self, value, message):
        if self.progress_bar:
            self.progress_bar['value'] = value
        if self.progress_label:
            self.progress_label['text'] = message
        self.progress_window.update()
    
    def close_progress_window(self):
        if self.progress_window:
            self.progress_window.destroy()
            self.progress_window = None
    
    def crop_video(self):
        if self.crop_x1 is None:
            messagebox.showwarning("No Selection", "Please select a crop area first!")
            return
        
        # Get temporal crop values
        start_frame = self.start_frame_var.get()
        end_frame = self.end_frame_var.get()
        
        if end_frame >= self.total_frames:
            end_frame = self.total_frames - 1
        
        if start_frame < 0 or end_frame >= self.total_frames or start_frame > end_frame:
            messagebox.showerror("Invalid Frame Range", "Invalid start/end frame values!")
            return
        
        # Get output file path
        output_path = filedialog.asksaveasfilename(
            title="Save Cropped Video",
            defaultextension=".mp4",
            filetypes=[("MP4 files", "*.mp4")]
        )
        
        if not output_path:
            return
        
        # Create progress window
        self.create_progress_window()
        
        # Disable controls during processing
        self.crop_btn.config(state='disabled')
        
        # Process video in background thread
        Thread(target=self.process_video, args=(output_path, start_frame, end_frame)).start()
    
    def process_video(self, output_path, start_frame, end_frame):
        try:
            cap = cv2.VideoCapture(self.video_path)
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            
            # Get original crop dimensions
            orig_width = int(self.crop_x2 - self.crop_x1)
            orig_height = int(self.crop_y2 - self.crop_y1)
            
            # Determine target dimensions
            if self.rescale_var.get():
                target_w = self.target_width.get()
                target_h = self.target_height.get()
            else:
                target_w = orig_width
                target_h = orig_height
            
            # Calculate frame indices to process
            total_input_frames = end_frame - start_frame + 1
            if self.drop_frames_var.get():
                # Calculate step size for uniform sampling
                target_count = self.target_frames.get()
                step = max(1, total_input_frames / target_count)
                frame_indices = [start_frame + int(i * step) for i in range(target_count)]
                frame_indices[-1] = min(frame_indices[-1], end_frame)  # Ensure last frame doesn't exceed
            else:
                # Process all frames
                frame_indices = list(range(start_frame, end_frame + 1))
            
            # Open output video writer
            output_fps = self.output_fps.get()
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, output_fps, (target_w, target_h))
            
            processed_count = 0
            total_to_process = len(frame_indices)
            
            self.update_progress(0, f"Processing {total_to_process} frames...")
            
            for frame_idx in frame_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Crop frame
                cropped_frame = frame[int(self.crop_y1):int(self.crop_y2),
                                    int(self.crop_x1):int(self.crop_x2)]
                
                # Rescale if needed
                if self.rescale_var.get():
                    cropped_frame = cv2.resize(
                        cropped_frame,
                        (target_w, target_h),
                        interpolation=cv2.INTER_LANCZOS4
                    )
                
                # Write to output
                out.write(cropped_frame)
                processed_count += 1
                
                # Update progress periodically
                if processed_count % 10 == 0 or processed_count == 1:
                    progress = (processed_count / total_to_process) * 100
                    self.update_progress(progress, f"Processing frame {processed_count}/{total_to_process}")
            
            # Handle padding if needed
            if self.pad_last_frame_var.get() and len(frame_indices) > 0:
                # Write the last frame one more time
                out.write(cropped_frame)
                self.update_progress(100, "Padding last frame...")
            
            # Cleanup
            cap.release()
            out.release()
            
            # Update progress to 100% and show success
            self.update_progress(100, "Processing complete!")
            time.sleep(1)
            
            # Close progress window and show success
            self.close_progress_window()
            self.status_label.config(text=f"Video processed successfully! Saved to {os.path.basename(output_path)}")
            messagebox.showinfo("Success", "Video cropped and processed successfully!")
            
        except Exception as e:
            self.close_progress_window()
            self.status_label.config(text=f"Error: {str(e)}")
            messagebox.showerror("Error", f"Failed to process video: {str(e)}")
        finally:
            # Re-enable controls after processing
            self.crop_btn.config(state='normal')

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoCropperApp(root)
    root.mainloop()

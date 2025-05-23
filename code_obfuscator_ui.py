import tkinter as tk
from tkinter import scrolledtext, ttk, Menu, messagebox
import traceback # For detailed error reporting

# Import transformation functions from code_transformer.py
try:
    from code_transformer import simplify_variables_in_code, disrupt_formatting, add_redundant_code
    TRANSFORMER_AVAILABLE = True
except ImportError as e:
    TRANSFORMER_AVAILABLE = False
    TRANSFORMER_IMPORT_ERROR = e

class App:
    # Define Color Palettes
    COLOR_PALETTES = {
        "Default Light": {
            "bg": "#F0F0F0", # Standard Tkinter frame background
            "fg": "#000000", # Standard text color
            "text_bg": "#FFFFFF",
            "text_fg": "#000000",
            "button_bg": "#E1E1E1", # Standard button color (ttk might override)
            "button_fg": "#000000",
            "accent_bg": "#D9D9D9", # For selected items or borders
            "label_frame_bg": "#F0F0F0", # Specific for LabelFrame background
        },
        "Dark Mode": {
            "bg": "#2E2E2E",
            "fg": "#FFFFFF",
            "text_bg": "#3C3C3C",
            "text_fg": "#E0E0E0",
            "button_bg": "#505050",
            "button_fg": "#FFFFFF",
            "accent_bg": "#606060",
            "label_frame_bg": "#2E2E2E",
        },
        "Ocean Blue": {
            "bg": "#E0F7FA", # Light cyan background
            "fg": "#004D40", # Dark teal text
            "text_bg": "#FFFFFF",
            "text_fg": "#003366", # Dark blue text in text areas
            "button_bg": "#B2EBF2", # Light cyan buttons
            "button_fg": "#004D40",
            "accent_bg": "#80DEEA", # Medium cyan for accents
            "label_frame_bg": "#E0F7FA",
        }
    }

    def __init__(self, root):
        self.root = root
        root.title("Code Obfuscator")

        # Configure root window to expand
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        # --- TTK Styling ---
        self.style = ttk.Style() # Initialize style object

        # --- UI Elements (store as instance variables for styling) ---
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.main_frame.columnconfigure(0, weight=1) 
        self.main_frame.columnconfigure(1, weight=0) 
        self.main_frame.columnconfigure(2, weight=1) 
        self.main_frame.rowconfigure(0, weight=1)    
        self.main_frame.rowconfigure(1, weight=0)    

        # Left text area for original code
        self.original_code_text = scrolledtext.ScrolledText(self.main_frame, width=50, height=25, wrap=tk.WORD)
        self.original_code_text.grid(row=0, column=0, padx=(0, 5), sticky=(tk.W, tk.E, tk.N, tk.S))

        # Options frame
        self.options_frame = ttk.LabelFrame(self.main_frame, text="Options", padding="10")
        self.options_frame.grid(row=0, column=1, padx=5, sticky=(tk.N, tk.S, tk.W, tk.E)) 

        # Variable Simplification
        self.var_simplification_label = ttk.Label(self.options_frame, text="Variable Simplification:")
        self.var_simplification_label.grid(row=0, column=0, sticky=tk.W, pady=(0,5))

        self.var_simplification_var = tk.StringVar(value="None")
        self.short_names_radio = ttk.Radiobutton(self.options_frame, text="Short Names (<=5 chars)", variable=self.var_simplification_var, value="Short")
        self.short_names_radio.grid(row=1, column=0, sticky=tk.W)

        self.pinyin_initials_radio = ttk.Radiobutton(self.options_frame, text="Pinyin Initials", variable=self.var_simplification_var, value="Pinyin")
        self.pinyin_initials_radio.grid(row=2, column=0, sticky=tk.W)

        self.none_radio = ttk.Radiobutton(self.options_frame, text="None", variable=self.var_simplification_var, value="None")
        self.none_radio.grid(row=3, column=0, sticky=tk.W, pady=(0,10))

        # Disrupt Code Format
        self.disrupt_format_var = tk.BooleanVar()
        self.disrupt_format_check = ttk.Checkbutton(self.options_frame, text="Disrupt Code Format", variable=self.disrupt_format_var)
        self.disrupt_format_check.grid(row=4, column=0, sticky=tk.W, pady=5)

        # Add Redundant Code
        self.add_redundant_code_var = tk.BooleanVar()
        self.add_redundant_code_check = ttk.Checkbutton(self.options_frame, text="Add Redundant Code", variable=self.add_redundant_code_var)
        self.add_redundant_code_check.grid(row=5, column=0, sticky=tk.W, pady=5)
        
        # Right text area for modified code
        self.modified_code_text = scrolledtext.ScrolledText(self.main_frame, width=50, height=25, wrap=tk.WORD)
        self.modified_code_text.grid(row=0, column=2, padx=(5, 0), sticky=(tk.W, tk.E, tk.N, tk.S))

        # Transform Code button
        self.transform_button = ttk.Button(self.main_frame, text="Transform Code", command=self.transform_code)
        self.transform_button.grid(row=1, column=0, columnspan=3, pady=10)
        
        # --- Menu for Color Schemes ---
        menubar = Menu(root)
        root.config(menu=menubar)
        
        self.color_menu = Menu(menubar, tearoff=0) # Store as instance variable
        menubar.add_cascade(label="Color Schemes", menu=self.color_menu)
        
        for scheme_name in self.COLOR_PALETTES:
            self.color_menu.add_command(label=scheme_name, command=lambda s=scheme_name: self.apply_color_scheme(s))
        
        # Apply default color scheme
        self.apply_color_scheme("Default Light")


    def apply_color_scheme(self, scheme_name):
        palette = self.COLOR_PALETTES.get(scheme_name)
        if not palette:
            print(f"Color scheme '{scheme_name}' not found.")
            return

        # Apply colors to root and main frame
        self.root.configure(bg=palette["bg"])
        self.main_frame.configure(style="App.TFrame") # Apply style to main_frame

        # Define styles for ttk widgets
        self.style.configure("App.TFrame", background=palette["bg"])
        self.style.configure("App.TLabel", background=palette["bg"], foreground=palette["fg"])
        self.style.configure("App.TButton", background=palette["button_bg"], foreground=palette["button_fg"])
        self.style.map("App.TButton", background=[('active', palette["accent_bg"])])
        self.style.configure("App.TRadiobutton", background=palette["bg"], foreground=palette["fg"])
        self.style.map("App.TRadiobutton",
                       background=[('active', palette["accent_bg"])],
                       indicatorcolor=[('selected', palette["accent_bg"])]) # May not work on all platforms for indicator
        self.style.configure("App.TCheckbutton", background=palette["bg"], foreground=palette["fg"])
        self.style.map("App.TCheckbutton",
                       background=[('active', palette["accent_bg"])],
                       indicatorcolor=[('selected', palette["accent_bg"])]) # May not work for indicator

        # Style for LabelFrame (background of the frame itself)
        self.style.configure("App.TLabelframe", background=palette["label_frame_bg"], bordercolor=palette["accent_bg"])
        self.style.configure("App.TLabelframe.Label", background=palette["label_frame_bg"], foreground=palette["fg"])


        # Apply styles to specific widgets
        self.main_frame.configure(style="App.TFrame")
        self.options_frame.configure(style="App.TLabelframe")
        
        # Labels
        self.var_simplification_label.configure(style="App.TLabel")
        
        # Radiobuttons & Checkbuttons (apply style, direct config for fg if needed)
        # TTK Radiobutton/Checkbutton text color is often part of the overall style
        self.short_names_radio.configure(style="App.TRadiobutton")
        self.pinyin_initials_radio.configure(style="App.TRadiobutton")
        self.none_radio.configure(style="App.TRadiobutton")
        self.disrupt_format_check.configure(style="App.TCheckbutton")
        self.add_redundant_code_check.configure(style="App.TCheckbutton")

        # Button
        self.transform_button.configure(style="App.TButton")

        # Text Areas (ScrolledText contains a standard Text widget)
        self.original_code_text.configure(bg=palette["text_bg"], fg=palette["text_fg"])
        self.modified_code_text.configure(bg=palette["text_bg"], fg=palette["text_fg"])
        
        # For ScrolledText, the border/frame might need separate styling if it's not a ttk.Frame
        # Typically, ScrolledText is a tk.Frame containing a tk.Text and tk.Scrollbar.
        # If ScrolledText itself is a tk.Frame:
        try:
            self.original_code_text.frame.configure(background=palette["bg"]) # If ScrolledText has a 'frame' attribute
            self.modified_code_text.frame.configure(background=palette["bg"])
        except AttributeError:
            pass # No 'frame' attribute, or not a tk.Frame

        # Special handling for Text widget's insert background (cursor color)
        # and select background/foreground
        for text_widget in [self.original_code_text, self.modified_code_text]:
            text_widget.configure(
                insertbackground=palette["text_fg"], # Cursor color
                selectbackground=palette["accent_bg"],
                selectforeground=palette["text_fg"]
            )

    def transform_code(self):
        """Performs code transformations based on selected UI options."""
        if not TRANSFORMER_AVAILABLE:
            self.modified_code_text.delete(1.0, tk.END)
            self.modified_code_text.insert(tk.INSERT, f"Error: Transformation functions could not be imported.\n{TRANSFORMER_IMPORT_ERROR}")
            messagebox.showerror("Import Error", f"Could not import transformation functions from code_transformer.py:\n{TRANSFORMER_IMPORT_ERROR}")
            return

        input_code = self.original_code_text.get(1.0, tk.END).strip()
        if not input_code:
            self.modified_code_text.delete(1.0, tk.END)
            self.modified_code_text.insert(tk.INSERT, "Please enter some code in the original code text area.")
            return

        # Get options
        var_simplify_mode = self.var_simplification_var.get()
        do_disrupt_format = self.disrupt_format_var.get()
        do_add_redundant = self.add_redundant_code_var.get()

        # UI Feedback (Start)
        self.transform_button.config(state=tk.DISABLED, text="Processing...")
        self.modified_code_text.delete(1.0, tk.END)
        self.root.update_idletasks() # Ensure UI updates are shown

        processed_code = input_code
        try:
            # Apply Transformations Sequentially
            if var_simplify_mode != "None":
                self.modified_code_text.insert(tk.END, f"Applying variable simplification (Mode: {var_simplify_mode})...\n")
                self.root.update_idletasks()
                processed_code = simplify_variables_in_code(processed_code, var_simplify_mode)

            if do_disrupt_format:
                self.modified_code_text.insert(tk.END, "Applying format disruption (Level: 0.3)...\n")
                self.root.update_idletasks()
                processed_code = disrupt_formatting(processed_code, disrupt_level=0.3)

            if do_add_redundant:
                self.modified_code_text.insert(tk.END, "Adding redundant code (Level: 0.2)...\n")
                self.root.update_idletasks()
                processed_code = add_redundant_code(processed_code, redundancy_level=0.2)
            
            self.modified_code_text.insert(tk.END, "\n--- Transformed Code ---\n")
            self.modified_code_text.insert(tk.END, processed_code)

        except Exception as e:
            tb_str = traceback.format_exc()
            error_message = f"An error occurred during transformation:\n{type(e).__name__}: {e}\n\nTraceback:\n{tb_str}"
            self.modified_code_text.insert(tk.END, f"\n--- ERROR ---\n{error_message}")
            # Also consider showing a messagebox for errors if they are not directly code-output related
            # messagebox.showerror("Transformation Error", f"An error occurred: {e}")
        finally:
            # UI Feedback (End)
            self.transform_button.config(state=tk.NORMAL, text="Transform Code")

    def placeholder_color_scheme(self):
        """Placeholder command for color scheme selection."""
        print("Color scheme selection clicked (placeholder action).")
        # Actual color scheme changing logic will be implemented later.
        # For now, we can show a message in the modified_code_text or a dialog.
        self.modified_code_text.insert(tk.END, "\nColor scheme selection placeholder activated.\n")


def main():
    try:
        root = tk.Tk()
        app = App(root)
        root.mainloop()
    except tk.TclError as e:
        # This error often occurs if DISPLAY is not set, e.g., in a headless environment
        print(f"Tkinter TclError: {e}")
        print("This might be due to a missing DISPLAY environment variable or other Tkinter initialization issues.")
        print("The UI script 'code_obfuscator_ui.py' has been created/updated, but could not be displayed.")
    except ModuleNotFoundError:
        print("ModuleNotFoundError: tkinter is not available in this environment.")
        print("The UI script 'code_obfuscator_ui.py' has been created/updated, but cannot be run without tkinter.")
    except Exception as e:
        print(f"An unexpected error occurred during UI initialization: {e}")
        print("The UI script 'code_obfuscator_ui.py' has been created/updated.")

if __name__ == "__main__":
    main()

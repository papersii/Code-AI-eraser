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
    APP_TEXT = {
        'en': {
            'window_title': "Code Obfuscator",
            'options_frame_title': "Options",
            'var_simplify_label': "Variable Simplification:",
            'var_simplify_short_radio': "Short Names (<=5 chars)",
            'var_simplify_pinyin_radio': "Pinyin Initials",
            'var_simplify_none_radio': "None",
            'disrupt_format_check': "Disrupt Code Format",
            'add_redundant_check': "Add Redundant Code",
            'transform_button_text': "Transform Code",
            'transform_button_processing_text': "Processing...",
            'menu_color_schemes': "Color Schemes",
            'menu_language': "Language", # For future use
            'lang_english': "English",   # For future use
            'lang_chinese': "Chinese",   # For future use
            'color_scheme_default': "Default Light",
            'color_scheme_dark': "Dark Mode",
            'color_scheme_blue': "Ocean Blue",
            'msg_enter_code': "Please enter some code in the original code text area.",
            'msg_applying_simplification': "Applying variable simplification (Mode: {mode})...",
            'msg_applying_formatting': "Applying format disruption (Level: {level})...",
            'msg_adding_redundant': "Adding redundant code (Level: {level})...",
            'msg_transformed_code_header': "--- Transformed Code ---",
            'msg_error_header': "--- ERROR ---",
            'msg_transformer_unavailable': "Error: Transformation functions could not be imported.\n{error}",
            'msg_transformation_error': "An error occurred during transformation:",
        },
        'zh': {
            'window_title': "[中文] Code Obfuscator",
            'options_frame_title': "[中文] Options",
            'var_simplify_label': "[中文] Variable Simplification:",
            'var_simplify_short_radio': "[中文] Short Names (<=5 chars)",
            'var_simplify_pinyin_radio': "[中文] Pinyin Initials",
            'var_simplify_none_radio': "[中文] None",
            'disrupt_format_check': "[中文] Disrupt Code Format",
            'add_redundant_check': "[中文] Add Redundant Code",
            'transform_button_text': "[中文] Transform Code",
            'transform_button_processing_text': "[中文] Processing...",
            'menu_color_schemes': "[中文] Color Schemes",
            'menu_language': "[中文] Language",
            'lang_english': "[中文] English",
            'lang_chinese': "[中文] Chinese",
            'color_scheme_default': "[中文] Default Light",
            'color_scheme_dark': "[中文] Dark Mode",
            'color_scheme_blue': "[中文] Ocean Blue",
            'msg_enter_code': "[中文] Please enter some code in the original code text area.",
            'msg_applying_simplification': "[中文] Applying variable simplification (Mode: {mode})...",
            'msg_applying_formatting': "[中文] Applying format disruption (Level: {level})...",
            'msg_adding_redundant': "[中文] Adding redundant code (Level: {level})...",
            'msg_transformed_code_header': "[中文] --- Transformed Code ---",
            'msg_error_header': "[中文] --- ERROR ---",
            'msg_transformer_unavailable': "[中文] Error: Transformation functions could not be imported.\n{error}",
            'msg_transformation_error': "[中文] An error occurred during transformation:",
        }
    }
    # Define Color Palettes
    COLOR_PALETTES = {
        "Default Light": { # Key matches APP_TEXT['en']['color_scheme_default'] for consistency
            "bg": "#F0F0F0", 
            "fg": "#000000", 
            "text_bg": "#FFFFFF",
            "text_fg": "#000000",
            "button_bg": "#E1E1E1", 
            "button_fg": "#000000",
            "accent_bg": "#D9D9D9", 
            "label_frame_bg": "#F0F0F0", 
        },
        "Dark Mode": { # Key matches APP_TEXT['en']['color_scheme_dark']
            "bg": "#2E2E2E",
            "fg": "#FFFFFF",
            "text_bg": "#3C3C3C",
            "text_fg": "#E0E0E0",
            "button_bg": "#505050",
            "button_fg": "#FFFFFF",
            "accent_bg": "#606060",
            "label_frame_bg": "#2E2E2E",
        },
        "Ocean Blue": { # Key matches APP_TEXT['en']['color_scheme_blue']
            "bg": "#E0F7FA", 
            "fg": "#004D40", 
            "text_bg": "#FFFFFF",
            "text_fg": "#003366", 
            "button_bg": "#B2EBF2", 
            "button_fg": "#004D40",
            "accent_bg": "#80DEEA", 
            "label_frame_bg": "#E0F7FA",
        }
    }

    def __init__(self, root):
        self.root = root
        self.current_language = 'en' # Default language
        self.ui_text = self.APP_TEXT[self.current_language]

        root.title(self.ui_text['window_title'])

        # Configure root window to expand
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        # --- TTK Styling ---
        self.style = ttk.Style() 

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
        self.options_frame = ttk.LabelFrame(self.main_frame, text=self.ui_text['options_frame_title'], padding="10")
        self.options_frame.grid(row=0, column=1, padx=5, sticky=(tk.N, tk.S, tk.W, tk.E)) 

        # Variable Simplification
        self.var_simplification_label = ttk.Label(self.options_frame, text=self.ui_text['var_simplify_label'])
        self.var_simplification_label.grid(row=0, column=0, sticky=tk.W, pady=(0,5))

        self.var_simplification_var = tk.StringVar(value="None") # Default value for the variable itself
        self.short_names_radio = ttk.Radiobutton(self.options_frame, text=self.ui_text['var_simplify_short_radio'], variable=self.var_simplification_var, value="Short")
        self.short_names_radio.grid(row=1, column=0, sticky=tk.W)

        self.pinyin_initials_radio = ttk.Radiobutton(self.options_frame, text=self.ui_text['var_simplify_pinyin_radio'], variable=self.var_simplification_var, value="Pinyin")
        self.pinyin_initials_radio.grid(row=2, column=0, sticky=tk.W)

        self.none_radio = ttk.Radiobutton(self.options_frame, text=self.ui_text['var_simplify_none_radio'], variable=self.var_simplification_var, value="None")
        self.none_radio.grid(row=3, column=0, sticky=tk.W, pady=(0,10))

        # Disrupt Code Format
        self.disrupt_format_var = tk.BooleanVar()
        self.disrupt_format_check = ttk.Checkbutton(self.options_frame, text=self.ui_text['disrupt_format_check'], variable=self.disrupt_format_var)
        self.disrupt_format_check.grid(row=4, column=0, sticky=tk.W, pady=5)

        # Add Redundant Code
        self.add_redundant_code_var = tk.BooleanVar()
        self.add_redundant_code_check = ttk.Checkbutton(self.options_frame, text=self.ui_text['add_redundant_check'], variable=self.add_redundant_code_var)
        self.add_redundant_code_check.grid(row=5, column=0, sticky=tk.W, pady=5)
        
        # Right text area for modified code
        self.modified_code_text = scrolledtext.ScrolledText(self.main_frame, width=50, height=25, wrap=tk.WORD)
        self.modified_code_text.grid(row=0, column=2, padx=(5, 0), sticky=(tk.W, tk.E, tk.N, tk.S))

        # Transform Code button
        self.transform_button = ttk.Button(self.main_frame, text=self.ui_text['transform_button_text'], command=self.transform_code)
        self.transform_button.grid(row=1, column=0, columnspan=3, pady=10)
        
        # --- Menu for Color Schemes ---
        self.menubar = Menu(root) # Store menubar as instance variable
        root.config(menu=self.menubar)
        
        self.color_menu = Menu(self.menubar, tearoff=0) 
        self.menubar.add_cascade(label=self.ui_text['menu_color_schemes'], menu=self.color_menu) # Index 0 for Color Schemes
        
        # Use text from APP_TEXT for color scheme menu items
        self.color_menu.add_command(label=self.ui_text['color_scheme_default'], command=lambda s=self.ui_text['color_scheme_default']: self.apply_color_scheme(s))
        self.color_menu.add_command(label=self.ui_text['color_scheme_dark'], command=lambda s=self.ui_text['color_scheme_dark']: self.apply_color_scheme(s))
        self.color_menu.add_command(label=self.ui_text['color_scheme_blue'], command=lambda s=self.ui_text['color_scheme_blue']: self.apply_color_scheme(s))

        # --- Language Menu ---
        self.language_menu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label=self.ui_text['menu_language'], menu=self.language_menu) # Index 1 for Language
        self.language_menu.add_command(label=self.ui_text['lang_english'], command=lambda: self.switch_language('en'))
        self.language_menu.add_command(label=self.ui_text['lang_chinese'], command=lambda: self.switch_language('zh'))
        
        # Apply default color scheme (using the English key for COLOR_PALETTES for now)
        self.apply_color_scheme(self.APP_TEXT['en']['color_scheme_default'])


    def apply_color_scheme(self, scheme_display_name):
        # Find the internal key for COLOR_PALETTES that matches the display name
        # This assumes display names in the current language map back to the English keys used in COLOR_PALETTES
        # or that COLOR_PALETTES keys are updated to be language-independent if necessary.
        # For now, we assume scheme_display_name is one of the English keys from APP_TEXT['en'] for color schemes
        internal_scheme_key = None
        for lang_key in self.APP_TEXT: # Check all languages just in case
            for text_key, text_value in self.APP_TEXT[lang_key].items():
                if text_value == scheme_display_name:
                    # Map back to the English key used in COLOR_PALETTES if needed
                    if text_key == 'color_scheme_default': internal_scheme_key = self.APP_TEXT['en']['color_scheme_default']
                    elif text_key == 'color_scheme_dark': internal_scheme_key = self.APP_TEXT['en']['color_scheme_dark']
                    elif text_key == 'color_scheme_blue': internal_scheme_key = self.APP_TEXT['en']['color_scheme_blue']
                    break
            if internal_scheme_key: break
        
        if not internal_scheme_key: # Fallback if mapping failed
            internal_scheme_key = scheme_display_name 

        palette = self.COLOR_PALETTES.get(internal_scheme_key)
        if not palette:
            # Fallback to English key if mapping failed and scheme_display_name was a direct key
            palette = self.COLOR_PALETTES.get(scheme_display_name) 
            if not palette:
                print(f"Color scheme '{scheme_display_name}' (resolved to '{internal_scheme_key}') not found.")
                return

        # Apply colors to root and main frame
        self.root.configure(bg=palette["bg"])
        self.main_frame.configure(style="App.TFrame") 

        # Define styles for ttk widgets
        self.style.configure("App.TFrame", background=palette["bg"])
        self.style.configure("App.TLabel", background=palette["bg"], foreground=palette["fg"])
        self.style.configure("App.TButton", background=palette["button_bg"], foreground=palette["button_fg"])
        self.style.map("App.TButton", background=[('active', palette["accent_bg"])])
        self.style.configure("App.TRadiobutton", background=palette["bg"], foreground=palette["fg"])
        self.style.map("App.TRadiobutton",
                       background=[('active', palette["accent_bg"])],
                       indicatorcolor=[('selected', palette["accent_bg"])]) 
        self.style.configure("App.TCheckbutton", background=palette["bg"], foreground=palette["fg"])
        self.style.map("App.TCheckbutton",
                       background=[('active', palette["accent_bg"])],
                       indicatorcolor=[('selected', palette["accent_bg"])]) 

        self.style.configure("App.TLabelframe", background=palette["label_frame_bg"], bordercolor=palette["accent_bg"])
        self.style.configure("App.TLabelframe.Label", background=palette["label_frame_bg"], foreground=palette["fg"])

        # Apply styles to specific widgets
        self.main_frame.configure(style="App.TFrame")
        self.options_frame.configure(style="App.TLabelframe")
        
        self.var_simplification_label.configure(style="App.TLabel")
        
        self.short_names_radio.configure(style="App.TRadiobutton")
        self.pinyin_initials_radio.configure(style="App.TRadiobutton")
        self.none_radio.configure(style="App.TRadiobutton")
        self.disrupt_format_check.configure(style="App.TCheckbutton")
        self.add_redundant_code_check.configure(style="App.TCheckbutton")

        self.transform_button.configure(style="App.TButton")

        self.original_code_text.configure(bg=palette["text_bg"], fg=palette["text_fg"])
        self.modified_code_text.configure(bg=palette["text_bg"], fg=palette["text_fg"])
        
        try:
            self.original_code_text.frame.configure(background=palette["bg"]) 
            self.modified_code_text.frame.configure(background=palette["bg"])
        except AttributeError:
            pass 

        for text_widget in [self.original_code_text, self.modified_code_text]:
            text_widget.configure(
                insertbackground=palette["text_fg"], 
                selectbackground=palette["accent_bg"],
                selectforeground=palette["text_fg"]
            )

    def transform_code(self):
        """Performs code transformations based on selected UI options."""
        current_texts = self.APP_TEXT[self.current_language] # Use current language texts

        if not TRANSFORMER_AVAILABLE:
            error_msg = current_texts['msg_transformer_unavailable'].format(error=TRANSFORMER_IMPORT_ERROR)
            self.modified_code_text.delete(1.0, tk.END)
            self.modified_code_text.insert(tk.INSERT, error_msg)
            messagebox.showerror("Import Error", error_msg) # Consider using a general title from APP_TEXT
            return

        input_code = self.original_code_text.get(1.0, tk.END).strip()
        if not input_code:
            self.modified_code_text.delete(1.0, tk.END)
            self.modified_code_text.insert(tk.INSERT, current_texts['msg_enter_code'])
            return

        var_simplify_mode = self.var_simplification_var.get()
        do_disrupt_format = self.disrupt_format_var.get()
        do_add_redundant = self.add_redundant_code_var.get()

        self.transform_button.config(state=tk.DISABLED, text=current_texts['transform_button_processing_text'])
        self.modified_code_text.delete(1.0, tk.END)
        self.root.update_idletasks() 

        processed_code = input_code
        try:
            if var_simplify_mode != "None":
                self.modified_code_text.insert(tk.END, current_texts['msg_applying_simplification'].format(mode=var_simplify_mode) + "\n")
                self.root.update_idletasks()
                processed_code = simplify_variables_in_code(processed_code, var_simplify_mode)

            if do_disrupt_format:
                self.modified_code_text.insert(tk.END, current_texts['msg_applying_formatting'].format(level=0.3) + "\n")
                self.root.update_idletasks()
                processed_code = disrupt_formatting(processed_code, disrupt_level=0.3)

            if do_add_redundant:
                self.modified_code_text.insert(tk.END, current_texts['msg_adding_redundant'].format(level=0.2) + "\n")
                self.root.update_idletasks()
                processed_code = add_redundant_code(processed_code, redundancy_level=0.2)
            
            self.modified_code_text.insert(tk.END, f"\n{current_texts['msg_transformed_code_header']}\n")
            self.modified_code_text.insert(tk.END, processed_code)

        except Exception as e:
            tb_str = traceback.format_exc()
            error_message = f"{current_texts['msg_transformation_error']}\n{type(e).__name__}: {e}\n\nTraceback:\n{tb_str}"
            self.modified_code_text.insert(tk.END, f"\n{current_texts['msg_error_header']}\n{error_message}")
        finally:
            self.transform_button.config(state=tk.NORMAL, text=current_texts['transform_button_text'])

    def switch_language(self, lang_code):
        # print(f"Switching language to: {lang_code}") # Keep for debugging if needed
        self.current_language = lang_code
        self.ui_text = self.APP_TEXT[self.current_language]
        
        # Update all UI element texts
        self.root.title(self.ui_text['window_title'])
        
        self.options_frame.config(text=self.ui_text['options_frame_title'])
        self.var_simplification_label.config(text=self.ui_text['var_simplify_label'])
        self.short_names_radio.config(text=self.ui_text['var_simplify_short_radio'])
        self.pinyin_initials_radio.config(text=self.ui_text['var_simplify_pinyin_radio'])
        self.none_radio.config(text=self.ui_text['var_simplify_none_radio'])
        self.disrupt_format_check.config(text=self.ui_text['disrupt_format_check'])
        self.add_redundant_code_check.config(text=self.ui_text['add_redundant_check'])
        
        # Reset transform button text to non-processing state
        # Only change if it's not currently "Processing..." (though unlikely mid-language switch)
        if self.transform_button['text'] != self.APP_TEXT['en']['transform_button_processing_text'] and \
           self.transform_button['text'] != self.APP_TEXT['zh']['transform_button_processing_text']:
            self.transform_button.config(text=self.ui_text['transform_button_text'])

        # Update Menubar labels
        # Assuming Color Schemes is at index 0 and Language is at index 1 of the menubar cascades.
        # This might need adjustment if system menus (like on macOS) affect indexing.
        try:
            self.menubar.entryconfigure(0, label=self.ui_text['menu_color_schemes'])
            self.menubar.entryconfigure(1, label=self.ui_text['menu_language'])
        except tk.TclError as e:
            print(f"Error updating menubar cascade labels (check indices): {e}")


        # Update individual color scheme names in the color menu
        try:
            self.color_menu.entryconfigure(0, label=self.ui_text['color_scheme_default'])
            self.color_menu.entryconfigure(1, label=self.ui_text['color_scheme_dark'])
            self.color_menu.entryconfigure(2, label=self.ui_text['color_scheme_blue'])
        except tk.TclError as e:
            print(f"Error updating color_menu item labels: {e}")

        # Update individual language names in the language menu
        try:
            self.language_menu.entryconfigure(0, label=self.ui_text['lang_english'])
            self.language_menu.entryconfigure(1, label=self.ui_text['lang_chinese'])
        except tk.TclError as e:
            print(f"Error updating language_menu item labels: {e}")
            
        # print(f"UI updated for language: {lang_code}") # Keep for debugging if needed

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

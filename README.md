# Python Code Obfuscator Tool

## 1. Purpose

This tool is a Python application designed to transform AI-generated Python code into a style that appears more like it was written by a college student. It applies various modifications to the code's structure and appearance without altering its core functionality (though aggressive transformations might inadvertently affect complex code).

## 2. Features

*   **Variable Name Simplification:**
    *   Option to change variable, function, and class names to short random strings (1-5 characters).
    *   Option to change names to Pinyin initials (e.g., `user_data` becomes `yd`).
    *   Option to keep original names.
*   **Code Formatting Disruption:**
    *   Randomly inserts or removes blank lines.
    *   Randomly adds extra spaces to indentation (conservatively, to avoid breaking code).
    *   Randomly adds/alters spaces around operators and parentheses.
*   **Redundant Code Addition:**
    *   Injects syntactically valid but non-functional code statements (e.g., unused variable assignments, `if True: pass` blocks) to complicate the program flow.
*   **Customizable UI:**
    *   A Tkinter-based graphical user interface for easy interaction.
    *   Selectable UI color schemes: "Default Light", "Dark Mode", and "Ocean Blue".
*   **Modular Design:**
    *   UI logic (`code_obfuscator_ui.py`) is separated from transformation logic (`code_transformer.py`).

## 3. Running the Script

### Dependencies:

*   **Python 3.x:** The script is written for Python 3.
*   **Tkinter:** This is usually bundled with Python standard distributions. If not present (e.g., on some minimal Linux installs), you may need to install it separately (e.g., `sudo apt-get install python3-tk`).
*   **`astor` library:** Used for converting the Abstract Syntax Tree (AST) back into Python code. Install it via pip:
    ```bash
    pip install astor
    ```

### Instructions:

1.  Ensure all dependencies are installed.
2.  Save both `code_obfuscator_ui.py` and `code_transformer.py` in the same directory.
3.  Open a terminal or command prompt, navigate to that directory.
4.  Run the UI script:
    ```bash
    python code_obfuscator_ui.py
    ```
5.  The application window will open.
    *   Paste your original Python code into the left text area ("Original Code").
    *   Select your desired transformation options from the "Options" panel in the middle.
    *   Choose a UI theme from the "Color Schemes" menu (optional).
    *   Click the "Transform Code" button.
    *   The modified code will appear in the right text area ("Modified Code").

## 4. Packaging as an .exe (for Windows)

To create a standalone `.exe` file that can be run on Windows without needing a Python installation (it bundles a Python interpreter), you can use PyInstaller.

### Dependencies for Packaging:

*   **PyInstaller:** Install it via pip:
    ```bash
    pip install pyinstaller
    ```
    (If you haven't already installed `astor` from the previous step, do so: `pip install astor`)

### Instructions:

1.  Ensure `pyinstaller` and `astor` are installed in your Python environment.
2.  Place `code_obfuscator_ui.py` and `code_transformer.py` in the same directory.
3.  Open a terminal or command prompt and navigate to this directory.
4.  Run the following PyInstaller command:
    ```bash
    pyinstaller --onefile --windowed code_obfuscator_ui.py
    ```
    *   `--onefile`: Bundles everything into a single executable file.
    *   `--windowed`: Prevents a console window from appearing when you run the GUI application.
    *   PyInstaller will automatically detect `code_transformer.py` as it's imported by `code_obfuscator_ui.py`. It will also bundle the `astor` library if it's installed in the environment PyInstaller uses.

5.  After PyInstaller finishes, you will find a `dist` subfolder in your current directory. Inside `dist`, you will find `code_obfuscator_ui.exe`. This is your standalone application.

## 5. Modules

*   **`code_obfuscator_ui.py`**: Handles the graphical user interface, user inputs, option selection, and orchestrates the transformation process by calling functions from `code_transformer.py`.
*   **`code_transformer.py`**: Contains the core logic for all code transformations:
    *   Variable simplification (using AST manipulation).
    *   Formatting disruption (using line-based string manipulation).
    *   Redundant code injection (using AST manipulation).
    This module also includes its own set of self-tests.

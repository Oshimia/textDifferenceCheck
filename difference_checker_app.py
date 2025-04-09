import tkinter as tk
from tkinter import scrolledtext, ttk # Import ttk for Combobox
import difflib
import sys

# --- Pygments Imports (for Syntax Highlighting) ---
try:
    from pygments import lex
    from pygments.lexers import get_lexer_by_name, TextLexer
    # Choose a style (e.g., 'monokai', 'default', 'native', 'vs')
    from pygments.styles import get_style_by_name
    from pygments.token import Token, STANDARD_TYPES
    PYGMENTS_AVAILABLE = True
except ImportError:
    PYGMENTS_AVAILABLE = False
    print("Pygments library not found. Syntax highlighting disabled.")
    print("Install it with: pip install Pygments")

# --- Dark Theme Colors ---
BG_COLOR = "#2b2b2b"
FG_COLOR = "#cccccc"
TEXT_BG_COLOR = "#333333"
CURSOR_COLOR = "#ffffff"
BUTTON_BG_COLOR = "#444444"
BUTTON_FG_COLOR = "#cccccc"
BUTTON_ACTIVE_BG = "#555555"
SELECT_BG_COLOR = "#555555" # Lighter grey selection
DEL_BG_COLOR = "#6e3b3b"
ADD_BG_COLOR = "#3b6e3b"
CHANGE_BG_COLOR = "#3b3b6e"
MISSING_FG_COLOR = "#ff6347" # Tomato red

# --- Syntax Highlighting Style ---
# Choose a Pygments style compatible with dark background
SYNTAX_STYLE_NAME = 'monokai'


class DiffCheckerApp:
    def __init__(self, master):
        self.master = master
        master.title("Text Difference Checker")
        master.geometry("1250x750") # Wider for new buttons
        master.config(bg=BG_COLOR)

        self.diffs = []
        self.current_diff_index = -1 # Index in self.diffs of the currently selected diff
        self.selected_diff_details = None
        self.identical_visible = True # State for identical line visibility

        # --- Configure Tags ---
        self.tag_add = "addition"
        self.tag_del = "deletion"
        self.tag_change = "change"
        self.tag_selected = "selected_diff"
        self.tag_missing = "missing_line"
        self.tag_identical = "identical_line" # New tag for identical lines
        # Syntax tags will be configured dynamically
        self.syntax_tags = {} # Map Pygments Token -> Tkinter Tag Name

        # --- Main PanedWindow ---
        self.paned_window = tk.PanedWindow(
            master, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, bg=BG_COLOR, bd=2
        )
        self.paned_window.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        # --- Left Pane ---
        self.left_frame = tk.Frame(self.paned_window, bg=BG_COLOR)
        self.text1_scroll = tk.Scrollbar(self.left_frame, troughcolor=BG_COLOR)
        self.text1 = scrolledtext.ScrolledText(
            self.left_frame, wrap=tk.WORD, yscrollcommand=self.text1_scroll.set,
            undo=True, font=("Courier New", 10), bg=TEXT_BG_COLOR, fg=FG_COLOR,
            insertbackground=CURSOR_COLOR, selectbackground=SELECT_BG_COLOR, # Text selection uses it too
            selectforeground=FG_COLOR, bd=0, highlightthickness=0
        )
        self.text1_scroll.config(command=self.text1.yview)
        self.text1_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.text1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._apply_base_tag_configs(self.text1) # Apply diff/missing/identical tags
        self.paned_window.add(self.left_frame, stretch="always")

        # --- Right Pane ---
        self.right_frame = tk.Frame(self.paned_window, bg=BG_COLOR)
        self.text2_scroll = tk.Scrollbar(self.right_frame, troughcolor=BG_COLOR)
        self.text2 = scrolledtext.ScrolledText(
            self.right_frame, wrap=tk.WORD, yscrollcommand=self.text2_scroll.set,
            undo=True, font=("Courier New", 10), bg=TEXT_BG_COLOR, fg=FG_COLOR,
            insertbackground=CURSOR_COLOR, selectbackground=SELECT_BG_COLOR, # Text selection uses it too
            selectforeground=FG_COLOR, bd=0, highlightthickness=0
        )
        self.text2_scroll.config(command=self.text2.yview)
        self.text2_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.text2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._apply_base_tag_configs(self.text2) # Apply diff/missing/identical tags
        self.paned_window.add(self.right_frame, stretch="always")

        # --- Configure Syntax Highlighting (if available) ---
        if PYGMENTS_AVAILABLE:
            self._configure_syntax_tags(SYNTAX_STYLE_NAME)
        # ------------------------------------------------------------------

        # --- Control Frame (Top) ---
        self.control_frame = tk.Frame(master, bg=BG_COLOR)
        self.control_frame.pack(fill=tk.X, pady=5, padx=5)

        self.compare_button = tk.Button(
            self.control_frame, text="Compare Texts", command=self.compare_text,
            bg=BUTTON_BG_COLOR, fg=BUTTON_FG_COLOR, activebackground=BUTTON_ACTIVE_BG, activeforeground=BUTTON_FG_COLOR, relief=tk.FLAT, bd=1
        )
        self.compare_button.pack(side=tk.LEFT, padx=5)

        self.next_diff_button = tk.Button(
            self.control_frame, text="Find Next Diff", command=self.find_next_diff_from_cursor, state=tk.DISABLED,
            bg=BUTTON_BG_COLOR, fg=BUTTON_FG_COLOR, activebackground=BUTTON_ACTIVE_BG, activeforeground=BUTTON_FG_COLOR, relief=tk.FLAT, bd=1
        )
        self.next_diff_button.pack(side=tk.LEFT, padx=5)

        self.diff_status_label = tk.Label(self.control_frame, text="", bg=BG_COLOR, fg=FG_COLOR)
        self.diff_status_label.pack(side=tk.LEFT, padx=10)

        # --- Hide/Show Identical Buttons ---
        self.hide_identical_button = tk.Button(
            self.control_frame, text="Hide Identical", command=self.hide_identical_lines, state=tk.DISABLED,
            bg=BUTTON_BG_COLOR, fg=BUTTON_FG_COLOR, activebackground=BUTTON_ACTIVE_BG, activeforeground=BUTTON_FG_COLOR, relief=tk.FLAT, bd=1
        )
        self.hide_identical_button.pack(side=tk.LEFT, padx=(20, 5))

        self.show_identical_button = tk.Button(
            self.control_frame, text="Show Identical", command=self.show_identical_lines, state=tk.DISABLED,
            bg=BUTTON_BG_COLOR, fg=BUTTON_FG_COLOR, activebackground=BUTTON_ACTIVE_BG, activeforeground=BUTTON_FG_COLOR, relief=tk.FLAT, bd=1
        )
        self.show_identical_button.pack(side=tk.LEFT, padx=5)


        # --- Syntax Highlighting Dropdown ---
        tk.Label(self.control_frame, text="Syntax:", bg=BG_COLOR, fg=FG_COLOR).pack(side=tk.LEFT, padx=(20, 2))
        self.language_var = tk.StringVar()
        languages = ["Plain Text", "Python", "JavaScript", "HTML", "CSS", "JSON", "XML", "SQL", "C", "C++", "Java", "PHP", "Ruby"]
        self.language_dropdown = ttk.Combobox(
            self.control_frame, textvariable=self.language_var, values=languages,
            state="readonly" if PYGMENTS_AVAILABLE else "disabled", width=15
        )
        self.language_dropdown.set("Plain Text")
        if PYGMENTS_AVAILABLE:
            self.language_dropdown.bind("<<ComboboxSelected>>", self.on_language_change)
        self.language_dropdown.pack(side=tk.LEFT, padx=5)


                # --- Merge/Copy Buttons Frame (Bottom) ---
                # --- Merge/Copy Buttons Frame (Bottom) ---
        self.merge_copy_frame = tk.Frame(master, bg=BG_COLOR)
        self.merge_copy_frame.pack(fill=tk.X, pady=5, padx=10) # Add some horizontal padding

        # Create a single frame to hold all buttons, centered
        self.center_button_frame = tk.Frame(self.merge_copy_frame, bg=BG_COLOR)
        # Packing without side or fill/expand tends to center it horizontally
        self.center_button_frame.pack()

        # --- Place Buttons into the central frame, packed left-to-right ---

        # Copy Left Button
        self.copy_left_button = tk.Button(
            self.center_button_frame, # Parent is the center frame
            text="Copy Left", command=self.copy_left_text,
            bg=BUTTON_BG_COLOR, fg=BUTTON_FG_COLOR, activebackground=BUTTON_ACTIVE_BG, activeforeground=BUTTON_FG_COLOR, relief=tk.FLAT, bd=1
        )
        self.copy_left_button.pack(side=tk.LEFT, padx=5, pady=2)

        # Merge -> Right Button
        self.merge_to_right_button = tk.Button(
            self.center_button_frame, # Parent is the center frame
            text="Merge Sel ->", command=self.merge_to_right, state=tk.DISABLED,
            bg=BUTTON_BG_COLOR, fg=BUTTON_FG_COLOR, activebackground=BUTTON_ACTIVE_BG, activeforeground=BUTTON_FG_COLOR, relief=tk.FLAT, bd=1
        )
        self.merge_to_right_button.pack(side=tk.LEFT, padx=5, pady=2)

        # Merge <- Left Button
        self.merge_to_left_button = tk.Button(
            self.center_button_frame, # Parent is the center frame
            text="<- Merge Sel", command=self.merge_to_left, state=tk.DISABLED,
            bg=BUTTON_BG_COLOR, fg=BUTTON_FG_COLOR, activebackground=BUTTON_ACTIVE_BG, activeforeground=BUTTON_FG_COLOR, relief=tk.FLAT, bd=1
        )
        self.merge_to_left_button.pack(side=tk.LEFT, padx=5, pady=2)

        # Copy Right Button
        self.copy_right_button = tk.Button(
            self.center_button_frame, # Parent is the center frame
            text="Copy Right", command=self.copy_right_text,
            bg=BUTTON_BG_COLOR, fg=BUTTON_FG_COLOR, activebackground=BUTTON_ACTIVE_BG, activeforeground=BUTTON_FG_COLOR, relief=tk.FLAT, bd=1
        )
        self.copy_right_button.pack(side=tk.LEFT, padx=5, pady=2)

        # --- Synchronized Scrolling ---
        self._bind_scroll()

    # --- Tag Configuration ---
    def _apply_base_tag_configs(self, text_widget):
        """Applies non-syntax tag configurations."""
        text_widget.tag_config(self.tag_del, background=DEL_BG_COLOR)
        text_widget.tag_config(self.tag_add, background=ADD_BG_COLOR)
        text_widget.tag_config(self.tag_change, background=CHANGE_BG_COLOR)
        text_widget.tag_config(self.tag_selected, background=SELECT_BG_COLOR, borderwidth=1, relief=tk.SOLID)
        text_widget.tag_config(self.tag_missing, foreground=MISSING_FG_COLOR, font=("Courier New", 10, "italic"))
        # Configure identical tag - initially not elided
        text_widget.tag_config(self.tag_identical, elide=False) # Add config for identical tag

    def _configure_syntax_tags(self, style_name):
        """Configures Tkinter tags based on a Pygments style."""
        if not PYGMENTS_AVAILABLE: return
        try:
            style = get_style_by_name(style_name)
        except Exception as e:
            print(f"Error getting Pygments style '{style_name}': {e}")
            style = get_style_by_name('default') # Fallback

        self.syntax_tags = {}
        try:
            base_style_info = style.style_for_token(Token)
            default_fg_hex = base_style_info.get('color')
            default_fg = f"#{default_fg_hex}" if default_fg_hex else FG_COLOR
        except Exception as e:
            print(f"Warning: Could not determine default style color: {e}")
            default_fg = FG_COLOR

        for token_type, style_info in style:
            tag_name = f"syntax_{str(token_type).replace('.', '_')}"
            self.syntax_tags[token_type] = tag_name
            fg_color_hex = style_info.get('color')
            is_bold = style_info.get('bold', False)
            is_italic = style_info.get('italic', False)
            final_fg = f"#{fg_color_hex}" if fg_color_hex else default_fg
            font_parts = ["Courier New", 10]
            if is_bold: font_parts.append('bold')
            if is_italic: font_parts.append('italic')
            font_tuple = tuple(font_parts)
            config_opts = {}
            if final_fg: config_opts['foreground'] = final_fg
            if len(font_tuple) > 2: config_opts['font'] = font_tuple
            if config_opts:
                if hasattr(self, 'text1') and hasattr(self, 'text2'):
                     self.text1.tag_config(tag_name, **config_opts)
                     self.text2.tag_config(tag_name, **config_opts)

    # --- Syntax Highlighting Application ---
    def on_language_change(self, event=None):
        """Called when the language dropdown changes."""
        self.apply_syntax_highlighting()
        self.compare_text()

    def apply_syntax_highlighting(self):
        """Applies syntax highlighting based on selected language."""
        if not PYGMENTS_AVAILABLE: return
        lang = self.language_var.get()
        lexer = TextLexer() # Default
        if lang and lang != "Plain Text":
            try: lexer = get_lexer_by_name(lang.lower(), stripall=True)
            except Exception: print(f"Lexer for '{lang}' not found.")
        self._clear_syntax_tags(self.text1)
        self._clear_syntax_tags(self.text2)
        text1_content = self.text1.get("1.0", "end-1c")
        self._highlight_widget(self.text1, lexer, text1_content)
        text2_content = self.text2.get("1.0", "end-1c")
        self._highlight_widget(self.text2, lexer, text2_content)

    def _clear_syntax_tags(self, text_widget):
        """Removes only syntax-related tags from a widget."""
        if not PYGMENTS_AVAILABLE: return
        for tag_name in self.syntax_tags.values():
            text_widget.tag_remove(tag_name, "1.0", tk.END)

    def _highlight_widget(self, text_widget, lexer, content):
        """Applies Pygments highlighting to a single text widget."""
        if not PYGMENTS_AVAILABLE: return
        text_widget.mark_set("range_start", "1.0")
        for index, token_type, token_text in lexer.get_tokens_unprocessed(content):
            start_index = text_widget.index(f"1.0 + {index} chars")
            end_index = text_widget.index(f"{start_index} + {len(token_text)} chars")
            current_type = token_type
            tag_to_apply = None
            while current_type != Token and current_type is not None:
                if current_type in self.syntax_tags:
                    tag_to_apply = self.syntax_tags[current_type]
                    break
                if not hasattr(current_type, 'parent'): break
                current_type = current_type.parent
            if tag_to_apply:
                text_widget.tag_add(tag_to_apply, start_index, end_index)

    # --- Copy Methods (Filter Placeholders) ---
    def copy_left_text(self):
        """Copies the content of the left text area to the clipboard,
           excluding placeholder lines."""
        try:
            full_text = self.text1.get("1.0", "end-1c")
            lines = full_text.splitlines()
            filtered_lines = [line for line in lines if ">>> Missing Line(s) <<<" not in line]
            text_to_copy = "\n".join(filtered_lines)
            self.master.clipboard_clear()
            self.master.clipboard_append(text_to_copy)
        except tk.TclError: print("Error copying left text")

    def copy_right_text(self):
        """Copies the content of the right text area to the clipboard,
           excluding placeholder lines."""
        try:
            full_text = self.text2.get("1.0", "end-1c")
            lines = full_text.splitlines()
            filtered_lines = [line for line in lines if ">>> Missing Line(s) <<<" not in line]
            text_to_copy = "\n".join(filtered_lines)
            self.master.clipboard_clear()
            self.master.clipboard_append(text_to_copy)
        except tk.TclError: print("Error copying right text")

    # --- Scrolling Logic (Unchanged) ---
    def _bind_scroll(self, *args):
        if sys.platform == "win32" or sys.platform == "darwin":
             self.text1.bind("<MouseWheel>", self._scroll_both)
             self.text2.bind("<MouseWheel>", self._scroll_both)
        elif sys.platform == "linux":
            self.text1.bind("<Button-4>", self._scroll_both)
            self.text1.bind("<Button-5>", self._scroll_both)
            self.text2.bind("<Button-4>", self._scroll_both)
            self.text2.bind("<Button-5>", self._scroll_both)
        self.text1_scroll.config(command=self._scroll_text2_and_bar1)
        self.text2_scroll.config(command=self._scroll_text1_and_bar2)
        self.text1.config(yscrollcommand=self._scroll_bar1_and_text2)
        self.text2.config(yscrollcommand=self._scroll_bar2_and_text1)

    def _scroll_both(self, event):
        delta = 0
        if sys.platform == "linux":
            if event.num == 4: delta = -1
            elif event.num == 5: delta = 1
        elif sys.platform == "win32":
            delta = -1 * int(event.delta / 120)
        elif sys.platform == "darwin":
             delta = -1 * event.delta
        if delta:
            view1_start, view1_end = self.text1.yview()
            view2_start, view2_end = self.text2.yview()
            can_scroll_up = delta < 0 and (view1_start > 0 or view2_start > 0)
            can_scroll_down = delta > 0 and (view1_end < 1.0 or view2_end < 1.0)
            if (delta < 0 and can_scroll_up) or (delta > 0 and can_scroll_down):
                self.text1.yview_scroll(delta, "units")
                self.text2.yview_scroll(delta, "units")
                self._update_scrollbars()
        return "break"

    def _scroll_text1_and_bar2(self, *args):
        if self.text2.yview() != self.text1.yview(): self.text2.yview_moveto(args[0])
        self.text2_scroll.set(*args)

    def _scroll_text2_and_bar1(self, *args):
        if self.text1.yview() != self.text2.yview(): self.text1.yview_moveto(args[0])
        self.text1_scroll.set(*args)

    def _scroll_bar1_and_text2(self, *args):
        self.text1_scroll.set(*args)
        if self.text2.yview() != (float(args[0]), float(args[1])): self.text2.yview_moveto(args[0])

    def _scroll_bar2_and_text1(self, *args):
        self.text2_scroll.set(*args)
        if self.text1.yview() != (float(args[0]), float(args[1])): self.text1.yview_moveto(args[0])

    def _update_scrollbars(self):
        try:
            view1 = self.text1.yview()
            view2 = self.text2.yview()
            if self.text1_scroll.get() != view1: self.text1_scroll.set(*view1)
            if self.text2_scroll.get() != view2: self.text2_scroll.set(*view2)
        except tk.TclError: pass

    # --- Diff and Merge Logic ---
    def _remove_tagged_lines(self, text_widget, tag_name):
        """Removes all lines that contain the given tag."""
        try:
            current_text = text_widget.get("1.0", tk.END)
            lines = current_text.splitlines()
            cleaned_lines = [line for line in lines if ">>> Missing Line(s) <<<" not in line]
            new_text = "\n".join(cleaned_lines)
            if new_text != current_text.rstrip('\n'):
                 view = text_widget.yview()
                 was_undo = text_widget.cget('undo')
                 text_widget.config(undo=False)
                 text_widget.delete("1.0", tk.END)
                 text_widget.insert("1.0", new_text)
                 text_widget.config(undo=was_undo)
                 text_widget.yview_moveto(view[0])
        except Exception as e: print(f"Error removing tagged lines: {e}")


    def compare_text(self):
        """Performs comparison, syntax highlighting, adds placeholders, and highlights diffs."""
        # --- 1. Preparation ---
        view1_start, view1_end = self.text1.yview()
        view2_start, view2_end = self.text2.yview()
        undo1_state = self.text1.cget('undo')
        undo2_state = self.text2.cget('undo')
        self.text1.config(undo=False)
        self.text2.config(undo=False)

        # --- 2. Apply Syntax Highlighting FIRST ---
        self.apply_syntax_highlighting()

        # --- 3. Clear Diff Tags and Placeholders ---
        # Include identical tag in clearing
        diff_tags = [self.tag_add, self.tag_del, self.tag_change, self.tag_selected, self.tag_missing, self.tag_identical]
        for tag in diff_tags:
            self.text1.tag_remove(tag, "1.0", tk.END)
            self.text2.tag_remove(tag, "1.0", tk.END)
        self._remove_tagged_lines(self.text1, self.tag_missing)
        self._remove_tagged_lines(self.text2, self.tag_missing)

        # Reset diff state
        self.diffs = []
        self.current_diff_index = -1
        self.selected_diff_details = None
        self.diff_status_label.config(text="")
        self.next_diff_button.config(state=tk.DISABLED)
        self.merge_to_left_button.config(state=tk.DISABLED)
        self.merge_to_right_button.config(state=tk.DISABLED)
        # Reset hide/show button state initially
        self.hide_identical_button.config(state=tk.DISABLED)
        self.show_identical_button.config(state=tk.DISABLED)


        # Get content AFTER clearing placeholders
        text1_content = self.text1.get("1.0", "end-1c").splitlines()
        text2_content = self.text2.get("1.0", "end-1c").splitlines()

        # --- 4. Calculate Differences ---
        matcher = difflib.SequenceMatcher(None, text1_content, text2_content, autojunk=False)
        opcodes = matcher.get_opcodes()

        # --- 5. Process Opcodes for Placeholders and Diff/Identical Highlighting ---
        placeholders_to_add = []
        identical_ranges1 = [] # Store (start, end) for identical lines in text1
        identical_ranges2 = [] # Store (start, end) for identical lines in text2
        diff_count = 0
        has_identical = False # Flag to enable hide/show buttons
        current_line1 = 1
        current_line2 = 1

        for tag, i1, i2, j1, j2 in opcodes:
            len1 = i2 - i1
            len2 = j2 - j1
            diff_detail = {'tag': tag, 'i1': i1, 'i2': i2, 'j1': j1, 'j2': j2,
                           'line1': current_line1, 'line2': current_line2}
            if tag == 'equal':
                # Store ranges for identical lines
                start1 = f"{current_line1}.0"
                end1 = f"{current_line1 + len1}.0"
                start2 = f"{current_line2}.0"
                end2 = f"{current_line2 + len2}.0"
                identical_ranges1.append((start1, end1))
                identical_ranges2.append((start2, end2)) # Store for text2
                has_identical = True
                current_line1 += len1
                current_line2 += len2
            elif tag == 'delete':
                placeholder_text = ">>> Missing Line(s) <<<\n" * len1
                placeholders_to_add.append((self.text2, current_line2, placeholder_text, self.tag_missing))
                self.diffs.append(diff_detail)
                diff_count += 1
                current_line1 += len1
            elif tag == 'insert':
                placeholder_text = ">>> Missing Line(s) <<<\n" * len2
                placeholders_to_add.append((self.text1, current_line1, placeholder_text, self.tag_missing))
                self.diffs.append(diff_detail)
                diff_count += 1
                current_line2 += len2
            elif tag == 'replace':
                if len1 < len2:
                    placeholder_text = ">>> Missing Line(s) <<<\n" * (len2 - len1)
                    placeholders_to_add.append((self.text1, current_line1 + len1, placeholder_text, self.tag_missing))
                elif len2 < len1:
                    placeholder_text = ">>> Missing Line(s) <<<\n" * (len1 - len2)
                    placeholders_to_add.append((self.text2, current_line2 + len2, placeholder_text, self.tag_missing))
                self.diffs.append(diff_detail)
                diff_count += 1
                current_line1 += len1
                current_line2 += len2

        # --- 6. Insert Placeholders ---
        placeholders_to_add.sort(key=lambda x: x[1], reverse=True)
        for widget, line_index, text, tag_name in placeholders_to_add:
            widget.insert(f"{line_index}.0", text, (tag_name,))

        # --- 7. Apply Diff and Identical Highlighting ---
        # Diffs first
        for diff in self.diffs:
            tag = diff['tag']
            widget_line1, widget_line2 = diff['line1'], diff['line2']
            len1, len2 = diff['i2'] - diff['i1'], diff['j2'] - diff['j1']
            start1, end1 = f"{widget_line1}.0", f"{widget_line1 + len1}.0"
            start2, end2 = f"{widget_line2}.0", f"{widget_line2 + len2}.0"
            if tag == 'delete': self.text1.tag_add(self.tag_del, start1, end1)
            elif tag == 'insert': self.text2.tag_add(self.tag_add, start2, end2)
            elif tag == 'replace':
                self.text1.tag_add(self.tag_change, start1, end1)
                self.text2.tag_add(self.tag_change, start2, end2)
        # Identical lines next
        for start, end in identical_ranges1:
            self.text1.tag_add(self.tag_identical, start, end)
        for start, end in identical_ranges2:
            self.text2.tag_add(self.tag_identical, start, end)

        # --- 8. Configure Eliding based on state ---
        self.text1.tag_config(self.tag_identical, elide=(not self.identical_visible))
        self.text2.tag_config(self.tag_identical, elide=(not self.identical_visible))

        # --- 9. Finalize ---
        self.text1.config(undo=undo1_state)
        self.text2.config(undo=undo2_state)
        try:
            self.text1.yview_moveto(view1_start)
            self.text2.yview_moveto(view2_start)
            self._update_scrollbars()
        except tk.TclError: pass

        # Update button states
        if self.diffs: self.next_diff_button.config(state=tk.NORMAL)
        if has_identical:
            if self.identical_visible:
                self.hide_identical_button.config(state=tk.NORMAL)
                self.show_identical_button.config(state=tk.DISABLED)
            else:
                self.hide_identical_button.config(state=tk.DISABLED)
                self.show_identical_button.config(state=tk.NORMAL)

        # Update status label
        if self.diffs: self.diff_status_label.config(text=f"{len(self.diffs)} differences found.")
        else: self.diff_status_label.config(text="No differences found.")


    # --- Hide/Show Identical Line Methods ---
    def hide_identical_lines(self):
        """Hides lines tagged as identical."""
        if not self.identical_visible: return # Already hidden
        self.identical_visible = False
        # Configure elide=True for BOTH text widgets
        self.text1.tag_config(self.tag_identical, elide=True)
        self.text2.tag_config(self.tag_identical, elide=True) # <<< ESSENTIAL LINE FOR TEXT2
        # Update button states
        self.hide_identical_button.config(state=tk.DISABLED)
        if self.text1.tag_ranges(self.tag_identical) or self.text2.tag_ranges(self.tag_identical):
             self.show_identical_button.config(state=tk.NORMAL)


    def show_identical_lines(self):
        """Shows lines tagged as identical."""
        if self.identical_visible: return # Already visible
        self.identical_visible = True
        # Configure elide=False for BOTH text widgets
        self.text1.tag_config(self.tag_identical, elide=False)
        self.text2.tag_config(self.tag_identical, elide=False) # <<< ESSENTIAL LINE FOR TEXT2
        # Update button states
        self.show_identical_button.config(state=tk.DISABLED)
        if self.text1.tag_ranges(self.tag_identical) or self.text2.tag_ranges(self.tag_identical):
             self.hide_identical_button.config(state=tk.NORMAL)


    # --- Find Next / Select Diff ---
    def find_next_diff_from_cursor(self, reset=False):
        """Finds the next difference starting AFTER the cursor position,
           wrapping around if necessary, and selects it."""
        if not self.diffs: return
        try:
            cursor_pos = self.text1.index(tk.INSERT)
            cursor_line = int(cursor_pos.split('.')[0])
        except Exception: cursor_line = 0

        next_diff_idx = -1
        start_search_idx = 0
        if not reset and self.current_diff_index != -1:
             start_search_idx = (self.current_diff_index + 1) % len(self.diffs)
        search_order = list(range(start_search_idx, len(self.diffs))) + list(range(0, start_search_idx))

        found_after_cursor = False
        for idx in search_order:
            diff = self.diffs[idx]
            if reset: # Find first diff >= cursor line
                 if diff['line1'] >= cursor_line:
                      next_diff_idx = idx; found_after_cursor = True; break
            else: # Find first diff > cursor line (in search order)
                 if diff['line1'] > cursor_line:
                      next_diff_idx = idx; found_after_cursor = True; break

        # Wrap around if not found after cursor
        if not found_after_cursor and self.diffs:
             next_diff_idx = search_order[0] # First element in the search order

        # Handle reset case wrap-around
        if reset and next_diff_idx == -1 and self.diffs:
             next_diff_idx = 0

        if not self.diffs or next_diff_idx == -1:
            self._select_and_scroll_to_diff(-1) # Clear selection
            return

        # Prevent getting stuck if only one diff or if next found is current
        if not reset and len(self.diffs) > 1 and next_diff_idx == self.current_diff_index:
             next_diff_idx = (self.current_diff_index + 1) % len(self.diffs)

        self._select_and_scroll_to_diff(next_diff_idx)


    def _select_and_scroll_to_diff(self, index):
        """Highlights and scrolls to the difference at the given index."""
        if not self.diffs or index < 0 or index >= len(self.diffs):
            self.current_diff_index = -1
            self.selected_diff_details = None
            self.text1.tag_remove(self.tag_selected, "1.0", tk.END)
            self.text2.tag_remove(self.tag_selected, "1.0", tk.END)
            self.merge_to_left_button.config(state=tk.DISABLED)
            self.merge_to_right_button.config(state=tk.DISABLED)
            return

        self.current_diff_index = index
        diff = self.diffs[self.current_diff_index]
        self.selected_diff_details = diff
        self.text1.tag_remove(self.tag_selected, "1.0", tk.END)
        self.text2.tag_remove(self.tag_selected, "1.0", tk.END)
        widget_line1, widget_line2 = diff['line1'], diff['line2']
        tag = diff['tag']
        len1, len2 = diff['i2'] - diff['i1'], diff['j2'] - diff['j1']
        start1, start2 = f"{widget_line1}.0", f"{widget_line2}.0"
        max_len = max(len1, len2)
        # Ensure at least one line height for selection highlight
        end1_line = widget_line1 + max(max_len, 1)
        end2_line = widget_line2 + max(max_len, 1)
        end1, end2 = f"{end1_line}.0", f"{end2_line}.0"

        scroll_target_line = widget_line1
        primary_widget = self.text1
        if tag == 'delete':
            self.text1.tag_add(self.tag_selected, start1, end1)
            self.text2.tag_add(self.tag_selected, start2, end2)
            scroll_target_line = widget_line1; primary_widget = self.text1
        elif tag == 'insert':
            self.text1.tag_add(self.tag_selected, start1, end1)
            self.text2.tag_add(self.tag_selected, start2, end2)
            scroll_target_line = widget_line2; primary_widget = self.text2
        elif tag == 'replace':
            self.text1.tag_add(self.tag_selected, start1, end1)
            self.text2.tag_add(self.tag_selected, start2, end2)
            scroll_target_line = widget_line1; primary_widget = self.text1

        self.diff_status_label.config(text=f"Difference {self.current_diff_index + 1} of {len(self.diffs)}")
        self.merge_to_left_button.config(state=tk.NORMAL)
        self.merge_to_right_button.config(state=tk.NORMAL)
        primary_widget.see(f"{scroll_target_line}.0")
        self.master.after(10, self._sync_scroll_after_find)


    def _sync_scroll_after_find(self):
        """Sync scroll positions after find_next_diff has scrolled one widget."""
        if not self.selected_diff_details: return
        try:
            if self.current_diff_index < 0 or self.current_diff_index >= len(self.diffs): return
            diff_tag = self.diffs[self.current_diff_index]['tag']
            if diff_tag == 'insert':
                 fraction = self.text2.yview()[0]
                 if self.text1.yview()[0] != fraction: self.text1.yview_moveto(fraction)
            else:
                 fraction = self.text1.yview()[0]
                 if self.text2.yview()[0] != fraction: self.text2.yview_moveto(fraction)
            self._update_scrollbars()
        except (tk.TclError, IndexError): pass


        # --- Merge Logic (Auto-find next) ---
    def merge_to_right(self):
        """Merges the selected difference from the left text box to the right."""
        if not self.selected_diff_details: return
        diff = self.selected_diff_details
        tag, i1, i2, j1, j2 = diff['tag'], diff['i1'], diff['i2'], diff['j1'], diff['j2']

        # --- Temporarily ensure all lines are visible for accurate indexing ---
        originally_hidden = not self.identical_visible
        if originally_hidden:
            self.text1.tag_config(self.tag_identical, elide=False)
            self.text2.tag_config(self.tag_identical, elide=False)
            # Allow Tkinter to process the un-hiding before getting text
            self.master.update_idletasks()
        # --------------------------------------------------------------------

        try: # Use try...finally to ensure compare_text runs
            text1_current = self.text1.get("1.0", "end-1c")
            text2_current = self.text2.get("1.0", "end-1c")
            # Clean placeholders (now operating on fully visible text)
            text1_lines_cleaned = [line for line in text1_current.splitlines() if ">>> Missing Line(s) <<<" not in line]
            text2_lines_cleaned = [line for line in text2_current.splitlines() if ">>> Missing Line(s) <<<" not in line]

            # Extract source content using original indices (should now be correct)
            content_lines_to_merge = text1_lines_cleaned[i1:i2]

            # Modify target lines
            new_text2_lines = []
            if tag == 'delete' or tag == 'replace':
                new_text2_lines = text2_lines_cleaned[:j1] + content_lines_to_merge + text2_lines_cleaned[j2:]
            elif tag == 'insert':
                new_text2_lines = text2_lines_cleaned[:j1] + text2_lines_cleaned[j2:]

            # Store view, disable undo, modify, restore undo, restore view
            view1, view2 = self.text1.yview(), self.text2.yview()
            undo1, undo2 = self.text1.cget('undo'), self.text2.cget('undo')
            self.text1.config(undo=False); self.text2.config(undo=False)
            # Set the *modified cleaned* text back
            self.text1.delete("1.0", tk.END); self.text1.insert("1.0", "\n".join(text1_lines_cleaned))
            # Set the *unmodified cleaned* text back to the other side for consistency before compare
            self.text2.delete("1.0", tk.END); self.text2.insert("1.0", "\n".join(new_text2_lines))
            self.text1.config(undo=undo1); self.text2.config(undo=undo2)
            # Attempt to restore view, might be slightly off after text change
            try:
                self.text1.yview_moveto(view1[0]); self.text2.yview_moveto(view2[0])
            except tk.TclError: pass # Ignore if view is invalid

        finally:
            # --- No need to manually re-hide here ---
            # compare_text will handle re-applying elide based on self.identical_visible
            pass

        # Re-compare (will re-apply hiding if originally_hidden was True)
        self.compare_text()

        # Auto-find next diff
        if self.diffs:
            next_idx_to_select = -1
            for idx, d in enumerate(self.diffs):
                 if d['j1'] >= j1: # Compare original indices
                      next_idx_to_select = idx
                      break
            if next_idx_to_select == -1: next_idx_to_select = 0 # Wrap
            if len(self.diffs) > 1 and next_idx_to_select == self.current_diff_index:
                 next_idx_to_select = (next_idx_to_select + 1) % len(self.diffs)
            self._select_and_scroll_to_diff(next_idx_to_select)
        else:
            self._select_and_scroll_to_diff(-1)


    def merge_to_left(self):
        """Merges the selected difference from the right text box to the left."""
        if not self.selected_diff_details: return
        diff = self.selected_diff_details
        tag, i1, i2, j1, j2 = diff['tag'], diff['i1'], diff['i2'], diff['j1'], diff['j2']

        # --- Temporarily ensure all lines are visible for accurate indexing ---
        originally_hidden = not self.identical_visible
        if originally_hidden:
            self.text1.tag_config(self.tag_identical, elide=False)
            self.text2.tag_config(self.tag_identical, elide=False)
            # Allow Tkinter to process the un-hiding before getting text
            self.master.update_idletasks()
        # --------------------------------------------------------------------

        try: # Use try...finally to ensure compare_text runs
            text1_current = self.text1.get("1.0", "end-1c")
            text2_current = self.text2.get("1.0", "end-1c")
            # Clean placeholders (now operating on fully visible text)
            text1_lines_cleaned = [line for line in text1_current.splitlines() if ">>> Missing Line(s) <<<" not in line]
            text2_lines_cleaned = [line for line in text2_current.splitlines() if ">>> Missing Line(s) <<<" not in line]

            # Extract source content using original indices (should now be correct)
            content_lines_to_merge = text2_lines_cleaned[j1:j2]

            # Modify target lines
            new_text1_lines = []
            if tag == 'insert' or tag == 'replace':
                new_text1_lines = text1_lines_cleaned[:i1] + content_lines_to_merge + text1_lines_cleaned[i2:]
            elif tag == 'delete':
                new_text1_lines = text1_lines_cleaned[:i1] + text1_lines_cleaned[i2:]

            # Store view, disable undo, modify, restore undo, restore view
            view1, view2 = self.text1.yview(), self.text2.yview()
            undo1, undo2 = self.text1.cget('undo'), self.text2.cget('undo')
            self.text1.config(undo=False); self.text2.config(undo=False)
            # Set the *modified cleaned* text back
            self.text1.delete("1.0", tk.END); self.text1.insert("1.0", "\n".join(new_text1_lines))
            # Set the *unmodified cleaned* text back to the other side for consistency before compare
            self.text2.delete("1.0", tk.END); self.text2.insert("1.0", "\n".join(text2_lines_cleaned))
            self.text1.config(undo=undo1); self.text2.config(undo=undo2)
            # Attempt to restore view
            try:
                self.text1.yview_moveto(view1[0]); self.text2.yview_moveto(view2[0])
            except tk.TclError: pass

        finally:
            # --- No need to manually re-hide here ---
            pass

        # Re-compare (will re-apply hiding if originally_hidden was True)
        self.compare_text()

        # Auto-find next diff
        if self.diffs:
            next_idx_to_select = -1
            for idx, d in enumerate(self.diffs):
                 if d['i1'] >= i1: # Compare original indices
                      next_idx_to_select = idx
                      break
            if next_idx_to_select == -1: next_idx_to_select = 0 # Wrap
            if len(self.diffs) > 1 and next_idx_to_select == self.current_diff_index:
                 next_idx_to_select = (next_idx_to_select + 1) % len(self.diffs)
            self._select_and_scroll_to_diff(next_idx_to_select)
        else:
            self._select_and_scroll_to_diff(-1)




# --- Main Execution ---
if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style(root)
    style.theme_use('clam')
    style.configure("TCombobox", fieldbackground=TEXT_BG_COLOR, background=BUTTON_BG_COLOR, foreground=FG_COLOR, arrowcolor=FG_COLOR, selectbackground=TEXT_BG_COLOR, selectforeground=FG_COLOR)
    style.map('TCombobox', fieldbackground=[('readonly', TEXT_BG_COLOR)])
    style.map('TCombobox', selectbackground=[('readonly', TEXT_BG_COLOR)])
    style.map('TCombobox', selectforeground=[('readonly', FG_COLOR)])
    root.option_add("*Background", BG_COLOR)
    root.option_add("*Foreground", FG_COLOR)
    root.option_add("*Button.Background", BUTTON_BG_COLOR)
    root.option_add("*Button.Foreground", BUTTON_FG_COLOR)
    root.option_add("*Button.activeBackground", BUTTON_ACTIVE_BG)
    root.option_add("*Button.activeForeground", BUTTON_FG_COLOR)
    root.option_add("*Label.Background", BG_COLOR)
    root.option_add("*Label.Foreground", FG_COLOR)
    root.option_add("*Frame.Background", BG_COLOR)
    root.option_add("*Text.Background", TEXT_BG_COLOR)
    root.option_add("*Text.Foreground", FG_COLOR)
    root.option_add("*Text.insertBackground", CURSOR_COLOR)
    root.option_add("*Text.selectBackground", SELECT_BG_COLOR) # Text selection uses it too
    root.option_add("*Text.selectForeground", FG_COLOR)
    root.option_add("*Scrollbar.background", BUTTON_BG_COLOR)
    root.option_add("*Scrollbar.troughColor", BG_COLOR)
    root.option_add("*Scrollbar.activeBackground", BUTTON_ACTIVE_BG)

    app = DiffCheckerApp(root)
    root.mainloop()
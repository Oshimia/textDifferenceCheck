# Python Diff Checker GUI

A graphical diff tool built with Python and Tkinter

## Features

*   **Side-by-Side Comparison:** Two resizable text panes for pasting and comparing text content.
*   **Difference Highlighting:**
    *   <span style="background-color:#DDFFDD; color:black;">Additions</span> (lines present in the right pane but not the left) highlighted in light green.
    *   <span style="background-color:#FFDDDD; color:black;">Deletions</span> (lines present in the left pane but not the right) highlighted in light red.
    *   <span style="background-color:#DDDDFF; color:black;">Changes</span> (lines modified between the two panes) highlighted in light blue.
    *   Selected difference block highlighted with a distinct background (e.g., light grey/yellow).
*   **Missing Line Indicators:** When lines are added or deleted, placeholder lines (`>>> Missing Line(s) <<<`) are inserted in the opposite pane to maintain visual alignment.
*   **Difference Navigation:** "Find Next Diff" button jumps to the next difference block starting *after* the current cursor position (wraps around).
*   **Selective Merging:** Merge the *currently selected* difference block from one pane to the other using the central "Merge Sel ->" and "<- Merge Sel" buttons. Merging automatically finds the next logical difference.
*   **Hide/Show Identical Lines:** Buttons to toggle the visibility of lines that are identical between the two panes, helping to focus only on the changes.
*   **Syntax Highlighting:** Optional syntax highlighting for various common languages (powered by Pygments) selectable via a dropdown menu.
*   **Copy Functionality:** "Copy Left" and "Copy Right" buttons copy the *actual* content (excluding placeholder lines) of the respective panes to the clipboard.
*   **Dark Theme:** A visually comfortable dark theme is applied to the interface.

## Requirements

To run the python script without the exe you will need:
*   **Python:** Version 3.7 or higher recommended (uses f-strings and includes modern Tkinter).
*   **Tkinter:** Usually included with standard Python installations. If not, you may need to install it separately (e.g., `sudo apt-get install python3-tk` on Debian/Ubuntu).
*   **Pygments:** Required for syntax highlighting.

## Usage

1.  **Run the script:**
    ```bash
    python diff_checker_app.py
    ```
or
1. **run diff_checker_app.exe**

2.  **Paste Text:** Paste the text you want to compare into the left and right input panes. You can edit the text directly in the panes before or after comparing.

3.  **Compare:** Click the "Compare Texts" button. Differences will be highlighted according to the color scheme described above. Placeholder lines (`>>> Missing Line(s) <<<`) may appear to indicate insertions/deletions.

4.  **Syntax Highlighting:** Select a language from the "Syntax:" dropdown menu. The text will be highlighted accordingly. Comparing again will re-apply syntax highlighting first.

5.  **Navigate Differences:** Click the "Find Next Diff" button. The application will find the next difference block starting *after* your current cursor position in the left pane and highlight it. Clicking again continues the search.

6.  **Focus on Changes:**
    *   Click "Hide Identical" to collapse sections of text that are the same in both panes.
    *   Click "Show Identical" to reveal the hidden sections again.

7.  **Merge Differences:**
    *   Navigate to the difference you want to merge using "Find Next Diff". The selected difference block will be highlighted.
    *   Click "Merge Sel ->" to replace the corresponding block in the right pane with the content from the selected block in the left pane.
    *   Click "<- Merge Sel" to replace the corresponding block in the left pane with the content from the selected block in the right pane.
    *   After merging, the comparison is automatically updated, and the next logical difference is selected.

8.  **Copy Text:**
    *   Click "Copy Left" to copy the entire content of the left pane (excluding any `>>> Missing Line(s) <<<` placeholders) to your clipboard.
    *   Click "Copy Right" to copy the content of the right pane (excluding placeholders).
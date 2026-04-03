#!/usr/bin/env python3
"""
FileCounter - A desktop application to count files in directories
and display them in a tree structure with aggregated counts and sizes.
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import threading


class DirectoryNode:
    """Represents a directory in the file tree with aggregated statistics."""

    def __init__(self, path):
        self.path = path
        self.name = os.path.basename(path) or path
        self.file_count = 0
        self.total_size = 0
        self.children = []
        self.is_directory = True

    def add_child(self, child):
        """Add a child node and update aggregated statistics."""
        self.children.append(child)
        self.file_count += child.file_count
        self.total_size += child.total_size

    def add_file(self, size):
        """Add a file to this directory's statistics."""
        self.file_count += 1
        self.total_size += size


class DirectoryScanner:
    """Scans directories and builds a tree structure with file statistics."""

    def __init__(self, progress_callback=None):
        self.progress_callback = progress_callback
        self.cancelled = False

    def cancel(self):
        """Cancel the current scan operation."""
        self.cancelled = True

    def scan(self, root_path):
        """
        Scan a directory tree and return a DirectoryNode with statistics.

        Args:
            root_path: The root directory to scan

        Returns:
            DirectoryNode representing the scanned tree
        """
        self.cancelled = False
        return self._scan_directory(root_path)

    def _scan_directory(self, dir_path):
        """Recursively scan a directory and build the tree structure."""
        if self.cancelled:
            return None

        node = DirectoryNode(dir_path)

        if self.progress_callback:
            self.progress_callback(dir_path)

        try:
            # Get all entries in the directory
            entries = os.listdir(dir_path)
        except (PermissionError, OSError) as e:
            # If we can't read the directory, return the node with zero stats
            return node

        for entry in entries:
            if self.cancelled:
                return None

            entry_path = os.path.join(dir_path, entry)

            # Skip symbolic links
            if os.path.islink(entry_path):
                continue

            try:
                if os.path.isdir(entry_path):
                    # Recursively scan subdirectory
                    child_node = self._scan_directory(entry_path)
                    if child_node:
                        node.add_child(child_node)
                else:
                    # It's a file, add its size
                    try:
                        file_size = os.path.getsize(entry_path)
                        node.add_file(file_size)
                    except (OSError, PermissionError):
                        # If we can't get the size, skip this file
                        pass
            except (OSError, PermissionError):
                # Skip entries we can't access
                continue

        return node


class FileCounterApp:
    """Main application window for the FileCounter."""

    def __init__(self, root):
        self.root = root
        self.root.title("FileCounter")
        self.root.geometry("900x600")

        self.scanner = None
        self.scan_thread = None
        self.current_root_node = None

        self._create_ui()

    def _create_ui(self):
        """Create the user interface."""
        # Top frame with controls
        top_frame = ttk.Frame(self.root, padding="10")
        top_frame.pack(fill=tk.X)

        # Select directory button
        self.select_btn = ttk.Button(
            top_frame,
            text="Select Directory",
            command=self.select_directory
        )
        self.select_btn.pack(side=tk.LEFT, padx=5)

        # Selected path label
        self.path_label = ttk.Label(top_frame, text="No directory selected")
        self.path_label.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # Cancel button (initially disabled)
        self.cancel_btn = ttk.Button(
            top_frame,
            text="Cancel",
            command=self.cancel_scan,
            state=tk.DISABLED
        )
        self.cancel_btn.pack(side=tk.RIGHT, padx=5)

        # Progress frame
        progress_frame = ttk.Frame(self.root, padding="10")
        progress_frame.pack(fill=tk.X)

        self.progress_label = ttk.Label(progress_frame, text="")
        self.progress_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.progress_bar = ttk.Progressbar(
            progress_frame,
            mode='indeterminate',
            length=200
        )
        # Progress bar is hidden initially

        # Tree view frame
        tree_frame = ttk.Frame(self.root, padding="10")
        tree_frame.pack(fill=tk.BOTH, expand=True)

        # Create scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")

        # Create tree view
        self.tree = ttk.Treeview(
            tree_frame,
            columns=("files", "size"),
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )

        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)

        # Configure columns
        self.tree.heading("#0", text="Directory", anchor=tk.W)
        self.tree.heading("files", text="File Count", anchor=tk.E)
        self.tree.heading("size", text="Total Size", anchor=tk.E)

        self.tree.column("#0", width=400, minwidth=200)
        self.tree.column("files", width=150, anchor=tk.E)
        self.tree.column("size", width=150, anchor=tk.E)

        # Grid layout for tree and scrollbars
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

    def select_directory(self):
        """Open a dialog to select a directory to scan."""
        directory = filedialog.askdirectory(title="Select Directory to Scan")

        if directory:
            self.path_label.config(text=directory)
            self.start_scan(directory)

    def start_scan(self, directory):
        """Start scanning a directory in a background thread."""
        # Clear existing tree
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Update UI state
        self.select_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)
        self.progress_label.config(text="Scanning...")
        self.progress_bar.pack(side=tk.RIGHT, padx=5)
        self.progress_bar.start(10)

        # Create scanner and start scan thread
        self.scanner = DirectoryScanner(progress_callback=self.update_progress)
        self.scan_thread = threading.Thread(
            target=self._scan_worker,
            args=(directory,),
            daemon=True
        )
        self.scan_thread.start()

    def _scan_worker(self, directory):
        """Worker thread function to perform the scan."""
        try:
            root_node = self.scanner.scan(directory)

            if root_node and not self.scanner.cancelled:
                self.current_root_node = root_node
                # Schedule UI update on main thread
                self.root.after(0, self.populate_tree)
            else:
                # Scan was cancelled
                self.root.after(0, self.scan_cancelled)
        except Exception as e:
            # Handle unexpected errors
            self.root.after(0, lambda: self.scan_error(str(e)))

    def update_progress(self, current_path):
        """Update progress indicator with current path being scanned."""
        # Truncate path if too long
        display_path = current_path
        if len(display_path) > 60:
            display_path = "..." + display_path[-57:]

        self.root.after(0, lambda: self.progress_label.config(
            text=f"Scanning: {display_path}"
        ))

    def populate_tree(self):
        """Populate the tree view with scan results."""
        if self.current_root_node:
            self._add_node_to_tree("", self.current_root_node)

        self.scan_complete()

    def _add_node_to_tree(self, parent, node):
        """Recursively add nodes to the tree view."""
        # Format the values
        file_count_str = f"{node.file_count:,}"
        size_str = self._format_size(node.total_size)

        # Insert the node
        item_id = self.tree.insert(
            parent,
            "end",
            text=node.name,
            values=(file_count_str, size_str)
        )

        # Add children (sort by file count descending for easier identification of large dirs)
        sorted_children = sorted(
            node.children,
            key=lambda x: x.file_count,
            reverse=True
        )

        for child in sorted_children:
            self._add_node_to_tree(item_id, child)

    def _format_size(self, size_bytes):
        """Format size in bytes to human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                if unit == 'B':
                    return f"{size_bytes:.0f} {unit}"
                else:
                    return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

    def scan_complete(self):
        """Handle scan completion."""
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.progress_label.config(text="Scan complete")
        self.select_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)

    def scan_cancelled(self):
        """Handle scan cancellation."""
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.progress_label.config(text="Scan cancelled")
        self.select_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)

    def scan_error(self, error_msg):
        """Handle scan error."""
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.progress_label.config(text="Scan failed")
        self.select_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)
        messagebox.showerror("Scan Error", f"An error occurred during scanning:\n{error_msg}")

    def cancel_scan(self):
        """Cancel the current scan operation."""
        if self.scanner:
            self.scanner.cancel()


def main():
    """Main entry point for the application."""
    root = tk.Tk()
    app = FileCounterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

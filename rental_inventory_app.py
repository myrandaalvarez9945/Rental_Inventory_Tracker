import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import csv
import os

class RentalManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Myranda's Rental Tracker 3000")
        self.columns = ["ID", "Item", "Serial", "Renter", "Date Rented", "Due Date", "Status", "Notes"]
        self.inventory = []
        self.entries = {}

        print("Working directory is:", os.getcwd())
        print("CSV path is:", os.path.abspath('rental_inventory.csv'))

        self.create_widgets()
        self.load_inventory()
        self.check_due_reminders()

    def create_widgets(self):
        # Search bar
        search_frame = tk.Frame(self.root)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(search_frame, text="🔍 Search:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.apply_filter)
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, width=50)
        search_entry.pack(side=tk.LEFT, padx=5)

        # Treeview
        self.tree = ttk.Treeview(self.root, columns=self.columns, show="headings")
        for col in self.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Form fields
        form_frame = tk.Frame(self.root)
        form_frame.pack(fill=tk.X)

        for i, col in enumerate(self.columns):
            tk.Label(form_frame, text=col).grid(row=i, column=0, sticky='e')
            if col == "Status":
                status_var = tk.StringVar()
                status_menu = ttk.Combobox(form_frame, textvariable=status_var)
                status_menu['values'] = ("New", "Rented", "Returned")
                status_menu.set("New")
                status_menu.grid(row=i, column=1)
                self.entries[col] = status_menu
            else:
                entry = tk.Entry(form_frame)
                entry.grid(row=i, column=1)
                self.entries[col] = entry

        # Buttons
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)
        buttons = [
            ("Add Rental", self.add_rental),
            ("Edit Rental", self.edit_rental),
            ("Update Rental", self.update_rental),
            ("Delete Rental", self.delete_rental),
            ("Mark as Returned", self.mark_as_returned),
            ("Export to CSV", self.export_csv),
            ("Show Due Soon", self.show_due_soon),
            ("Start New Semester", self.start_new_semester),
        ]
        for txt, cmd in buttons:
            tk.Button(btn_frame, text=txt, command=cmd).pack(side=tk.LEFT)

    def get_entry_data(self):
        return [self.entries[col].get().strip() for col in self.columns]

    def clear_entries(self):
        for col in self.columns:
            if isinstance(self.entries[col], ttk.Combobox):
                self.entries[col].set("New")
            else:
                self.entries[col].delete(0, tk.END)

    def add_rental(self):
        rental_id = self.entries["ID"].get().strip()
        if not rental_id:
            messagebox.showerror("Missing ID", "Rental ID cannot be empty.")
            return
        if any(str(row[0]).strip() == rental_id for row in self.inventory):
            messagebox.showerror("Duplicate ID", f"Rental ID {rental_id} already exists.")
            return
        data = self.get_entry_data()
        self.tree.insert('', 'end', values=data)
        self.inventory.append(data)
        self.save_inventory()
        self.clear_entries()
        messagebox.showinfo("Added", "Rental successfully added.")

    def edit_rental(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No selection", "Please select a rental to edit.")
            return
        values = self.tree.item(selected[0])['values']
        for col, val in zip(self.columns, values):
            if isinstance(self.entries[col], ttk.Combobox):
                self.entries[col].set(val)
            else:
                self.entries[col].delete(0, tk.END)
                self.entries[col].insert(0, val)

    def update_rental(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No selection", "Please select a rental to update.")
            return
        selected_id = str(self.tree.item(selected[0])['values'][0]).strip()
        new_data = self.get_entry_data()
        original_values = self.tree.item(selected[0])['values']
        updated_data = [
            new if new.strip() != '' else str(original)
            for new, original in zip(new_data, original_values)
        ]
        self.tree.item(selected[0], values=updated_data)
        updated = False
        for i, row in enumerate(self.inventory):
            if str(row[0]).strip() == selected_id:
                self.inventory[i] = updated_data
                updated = True
                break
        if updated:
            self.save_inventory()
            self.clear_entries()
            messagebox.showinfo("Updated", f"Rental ID {selected_id} updated.")
        else:
            messagebox.showerror("Update Failed", f"No matching rental with ID {selected_id} found.")

    def delete_rental(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No selection", "Please select a rental to delete.")
            return
        confirm = messagebox.askyesno("Confirm Deletion", "Are you sure you want to delete this rental?")
        if not confirm:
            return
        selected_id = str(self.tree.item(selected[0])['values'][0]).strip()
        self.tree.delete(selected[0])
        self.inventory = [row for row in self.inventory if str(row[0]).strip() != selected_id]
        self.save_inventory()
        messagebox.showinfo("Deleted", f"Rental ID {selected_id} deleted.")

    def mark_as_returned(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No selection", "Please select a rental to mark as returned.")
            return
        item = self.tree.item(selected[0])
        updated = list(item['values'])
        updated[6] = "Returned"
        self.tree.item(selected[0], values=updated)
        for i, row in enumerate(self.inventory):
            if str(row[0]).strip() == str(updated[0]).strip():
                self.inventory[i] = updated
                break
        self.save_inventory()

    def export_csv(self):
        default_name = f"rental_export_{datetime.now().strftime('%Y-%m-%d')}.csv"
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=default_name,
            filetypes=[("CSV Files", "*.csv")],
            title="Save CSV Export As"
        )
        if not file_path:
            return
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(self.columns)
                writer.writerows(self.inventory)
                f.flush()
                os.fsync(f.fileno())
            messagebox.showinfo("Exported", f"CSV exported as:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Could not export file:\n{e}")

    def start_new_semester(self):
        self.export_csv()
        self.tree.delete(*self.tree.get_children())
        self.inventory = []
        self.save_inventory()
        messagebox.showinfo("Reset", "Semester started fresh.")

    def show_due_soon(self):
        today = datetime.now().date()
        due_window = tk.Toplevel(self.root)
        due_window.title("Due Soon Rentals")
        tree = ttk.Treeview(due_window, columns=self.columns, show="headings")
        for col in self.columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        tree.pack(fill=tk.BOTH, expand=True)
        found = False
        for row in self.inventory:
            try:
                due_date = datetime.strptime(row[5], "%m/%d/%Y").date()
                days_left = (due_date - today).days
                if days_left in [5, 3, 0] and row[6] != "Returned":
                    tree.insert('', 'end', values=row)
                    found = True
            except:
                continue
        if not found:
            tk.Label(due_window, text="No rentals due soon today.").pack()

    def save_inventory(self):
        clean_inventory = [row for row in self.inventory if any(str(cell).strip() for cell in row)]
        try:
            with open('rental_inventory.csv', 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(self.columns)
                writer.writerows(clean_inventory)
                f.flush()
                os.fsync(f.fileno())
        except Exception as e:
            messagebox.showerror("File Save Error", f"Could not save CSV:\n{e}")

    def load_inventory(self):
        if os.path.exists('rental_inventory.csv'):
            with open('rental_inventory.csv', 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader, None)
                for row in reader:
                    if any(str(cell).strip() for cell in row):
                        self.inventory.append(row)
                        self.tree.insert('', 'end', values=row)

    def check_due_reminders(self):
        today = datetime.now().date()
        for row in self.inventory:
            try:
                due_date = datetime.strptime(row[5], "%m/%d/%Y").date()
                days_left = (due_date - today).days
                if days_left in [5, 3, 0] and row[6] != "Returned":
                    msg = f"Reminder: Rental ID {row[0]} is due in {days_left} days." if days_left > 0 else f"FINAL NOTICE: Rental ID {row[0]} is due TODAY!"
                    messagebox.showinfo("Laptop Rental Reminder", msg)
            except:
                continue

    def apply_filter(self, *args):
        query = self.search_var.get().lower()
        self.tree.delete(*self.tree.get_children())
        for row in self.inventory:
            if any(query in str(cell).lower() for cell in row):
                self.tree.insert('', 'end', values=row)

if __name__ == "__main__":
    root = tk.Tk()
    app = RentalManager(root)
    root.mainloop()
"""
Library Management System — GUI
---------------------------------
A minimal Tkinter GUI built on top of the existing library_system.py logic.
Reuses the Database and Library classes so business logic isn't duplicated.

Author: Anirudh Thakur
"""

import tkinter as tk
from tkinter import ttk, messagebox

from library_system import Database, Library


class LibraryGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Library Management System")
        self.root.geometry("800x520")
        self.root.minsize(700, 450)

        self.db = Database()
        self.library = Library(self.db)

        # Notebook (tabs)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.books_tab = ttk.Frame(self.notebook)
        self.members_tab = ttk.Frame(self.notebook)
        self.loans_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.books_tab, text="Books")
        self.notebook.add(self.members_tab, text="Members")
        self.notebook.add(self.loans_tab, text="Loans")

        self._build_books_tab()
        self._build_members_tab()
        self._build_loans_tab()

        self.refresh_all()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # ---------------- BOOKS TAB ----------------

    def _build_books_tab(self):
        form = ttk.LabelFrame(self.books_tab, text="Add Book")
        form.pack(fill="x", padx=10, pady=10)

        ttk.Label(form, text="Title").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.title_entry = ttk.Entry(form, width=25)
        self.title_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form, text="Author").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.author_entry = ttk.Entry(form, width=20)
        self.author_entry.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(form, text="ISBN").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.isbn_entry = ttk.Entry(form, width=25)
        self.isbn_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(form, text="Copies").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.copies_entry = ttk.Entry(form, width=10)
        self.copies_entry.grid(row=1, column=3, padx=5, pady=5, sticky="w")

        ttk.Button(form, text="Add Book", command=self.add_book).grid(
            row=0, column=4, rowspan=2, padx=10, pady=5
        )

        search_frame = ttk.Frame(self.books_tab)
        search_frame.pack(fill="x", padx=10)
        ttk.Label(search_frame, text="Search:").pack(side="left")
        self.book_search_entry = ttk.Entry(search_frame, width=30)
        self.book_search_entry.pack(side="left", padx=5)
        ttk.Button(search_frame, text="Search", command=self.search_books).pack(side="left")
        ttk.Button(search_frame, text="Clear", command=self.refresh_books).pack(side="left", padx=5)
        ttk.Button(search_frame, text="Delete Selected", command=self.delete_book).pack(side="right")

        columns = ("id", "title", "author", "isbn", "available", "total")
        self.books_tree = ttk.Treeview(self.books_tab, columns=columns, show="headings", height=10)
        for col, label, width in [
            ("id", "ID", 40), ("title", "Title", 220), ("author", "Author", 160),
            ("isbn", "ISBN", 130), ("available", "Available", 80), ("total", "Total", 60),
        ]:
            self.books_tree.heading(col, text=label)
            self.books_tree.column(col, width=width, anchor="w")
        self.books_tree.pack(fill="both", expand=True, padx=10, pady=10)

    def add_book(self):
        title = self.title_entry.get().strip()
        author = self.author_entry.get().strip()
        isbn = self.isbn_entry.get().strip() or None
        copies_str = self.copies_entry.get().strip()

        if not title or not author or not copies_str:
            messagebox.showerror("Missing info", "Title, Author, and Copies are required.")
            return
        try:
            copies = int(copies_str)
            if copies <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid input", "Copies must be a positive whole number.")
            return

        try:
            self.library.cursor.execute(
                "INSERT INTO books (title, author, isbn, total_copies, available_copies) "
                "VALUES (?, ?, ?, ?, ?)",
                (title, author, isbn, copies, copies),
            )
            self.library.conn.commit()
        except Exception:
            messagebox.showerror("Duplicate ISBN", "A book with this ISBN already exists.")
            return

        for e in (self.title_entry, self.author_entry, self.isbn_entry, self.copies_entry):
            e.delete(0, tk.END)
        self.refresh_books()
        self.refresh_book_dropdowns()

    def refresh_books(self, rows=None):
        for row in self.books_tree.get_children():
            self.books_tree.delete(row)
        if rows is None:
            self.library.cursor.execute(
                "SELECT book_id, title, author, isbn, available_copies, total_copies FROM books"
            )
            rows = self.library.cursor.fetchall()
        for r in rows:
            self.books_tree.insert("", "end", values=(r[0], r[1], r[2], r[3] or "-", r[4], r[5]))

    def search_books(self):
        keyword = self.book_search_entry.get().strip().lower()
        if not keyword:
            self.refresh_books()
            return
        q = f"%{keyword}%"
        self.library.cursor.execute(
            "SELECT book_id, title, author, isbn, available_copies, total_copies FROM books "
            "WHERE LOWER(title) LIKE ? OR LOWER(author) LIKE ?",
            (q, q),
        )
        self.refresh_books(self.library.cursor.fetchall())

    def delete_book(self):
        selected = self.books_tree.selection()
        if not selected:
            messagebox.showinfo("No selection", "Select a book in the table first.")
            return
        book_id = self.books_tree.item(selected[0])["values"][0]
        if messagebox.askyesno("Confirm", f"Delete book ID {book_id}? This cannot be undone."):
            self.library.cursor.execute("DELETE FROM books WHERE book_id = ?", (book_id,))
            self.library.conn.commit()
            self.refresh_books()
            self.refresh_book_dropdowns()

    # ---------------- MEMBERS TAB ----------------

    def _build_members_tab(self):
        form = ttk.LabelFrame(self.members_tab, text="Register Member")
        form.pack(fill="x", padx=10, pady=10)

        ttk.Label(form, text="Name").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.member_name_entry = ttk.Entry(form, width=25)
        self.member_name_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form, text="Email").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.member_email_entry = ttk.Entry(form, width=25)
        self.member_email_entry.grid(row=0, column=3, padx=5, pady=5)

        ttk.Button(form, text="Register", command=self.add_member).grid(
            row=0, column=4, padx=10, pady=5
        )

        columns = ("id", "name", "email")
        self.members_tree = ttk.Treeview(self.members_tab, columns=columns, show="headings", height=12)
        for col, label, width in [("id", "ID", 50), ("name", "Name", 220), ("email", "Email", 280)]:
            self.members_tree.heading(col, text=label)
            self.members_tree.column(col, width=width, anchor="w")
        self.members_tree.pack(fill="both", expand=True, padx=10, pady=10)

    def add_member(self):
        name = self.member_name_entry.get().strip()
        email = self.member_email_entry.get().strip()
        if not name or not email:
            messagebox.showerror("Missing info", "Name and Email are required.")
            return
        try:
            self.library.cursor.execute(
                "INSERT INTO members (name, email) VALUES (?, ?)", (name, email)
            )
            self.library.conn.commit()
        except Exception:
            messagebox.showerror("Duplicate email", "A member with this email already exists.")
            return

        self.member_name_entry.delete(0, tk.END)
        self.member_email_entry.delete(0, tk.END)
        self.refresh_members()
        self.refresh_book_dropdowns()

    def refresh_members(self):
        for row in self.members_tree.get_children():
            self.members_tree.delete(row)
        self.library.cursor.execute("SELECT member_id, name, email FROM members")
        for r in self.library.cursor.fetchall():
            self.members_tree.insert("", "end", values=r)

    # ---------------- LOANS TAB ----------------

    def _build_loans_tab(self):
        form = ttk.LabelFrame(self.loans_tab, text="Issue Book")
        form.pack(fill="x", padx=10, pady=10)

        ttk.Label(form, text="Book").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.issue_book_combo = ttk.Combobox(form, width=30, state="readonly")
        self.issue_book_combo.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form, text="Member").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.issue_member_combo = ttk.Combobox(form, width=25, state="readonly")
        self.issue_member_combo.grid(row=0, column=3, padx=5, pady=5)

        ttk.Button(form, text="Issue", command=self.issue_book).grid(row=0, column=4, padx=10)

        action_frame = ttk.Frame(self.loans_tab)
        action_frame.pack(fill="x", padx=10)
        ttk.Button(action_frame, text="Return Selected Loan", command=self.return_book).pack(
            side="left", pady=5
        )
        ttk.Button(action_frame, text="Refresh", command=self.refresh_loans).pack(
            side="left", padx=5
        )

        columns = ("loan_id", "book", "member", "issued", "due", "status")
        self.loans_tree = ttk.Treeview(self.loans_tab, columns=columns, show="headings", height=10)
        for col, label, width in [
            ("loan_id", "Loan ID", 60), ("book", "Book", 200), ("member", "Member", 150),
            ("issued", "Issued", 90), ("due", "Due", 90), ("status", "Status", 100),
        ]:
            self.loans_tree.heading(col, text=label)
            self.loans_tree.column(col, width=width, anchor="w")
        self.loans_tree.pack(fill="both", expand=True, padx=10, pady=10)

    def refresh_book_dropdowns(self):
        self.library.cursor.execute(
            "SELECT book_id, title, available_copies FROM books WHERE available_copies > 0"
        )
        books = self.library.cursor.fetchall()
        self.book_choices = {f"{b[0]} - {b[1]} ({b[2]} left)": b[0] for b in books}
        self.issue_book_combo["values"] = list(self.book_choices.keys())

        self.library.cursor.execute("SELECT member_id, name FROM members")
        members = self.library.cursor.fetchall()
        self.member_choices = {f"{m[0]} - {m[1]}": m[0] for m in members}
        self.issue_member_combo["values"] = list(self.member_choices.keys())

    def issue_book(self):
        book_label = self.issue_book_combo.get()
        member_label = self.issue_member_combo.get()
        if not book_label or not member_label:
            messagebox.showerror("Missing selection", "Select both a book and a member.")
            return

        book_id = self.book_choices[book_label]
        member_id = self.member_choices[member_label]

        from datetime import datetime, timedelta
        issue_date = datetime.now()
        due_date = issue_date + timedelta(days=14)

        self.library.cursor.execute(
            "INSERT INTO loans (book_id, member_id, issue_date, due_date) VALUES (?, ?, ?, ?)",
            (book_id, member_id, issue_date.strftime("%Y-%m-%d"), due_date.strftime("%Y-%m-%d")),
        )
        self.library.cursor.execute(
            "UPDATE books SET available_copies = available_copies - 1 WHERE book_id = ?",
            (book_id,),
        )
        self.library.conn.commit()

        messagebox.showinfo("Issued", f"Book issued. Due back: {due_date.strftime('%Y-%m-%d')}")
        self.refresh_all()

    def return_book(self):
        selected = self.loans_tree.selection()
        if not selected:
            messagebox.showinfo("No selection", "Select a loan in the table first.")
            return
        loan_id = self.loans_tree.item(selected[0])["values"][0]

        self.library.cursor.execute(
            "SELECT book_id, due_date, return_date FROM loans WHERE loan_id = ?", (loan_id,)
        )
        loan = self.library.cursor.fetchone()
        if not loan or loan[2] is not None:
            messagebox.showinfo("Already returned", "This loan has already been closed.")
            return

        from datetime import datetime
        book_id, due_date_str, _ = loan
        return_date = datetime.now()
        due_date = datetime.strptime(due_date_str, "%Y-%m-%d")
        fine = max(0, (return_date - due_date).days) * 5 if return_date > due_date else 0

        self.library.cursor.execute(
            "UPDATE loans SET return_date = ? WHERE loan_id = ?",
            (return_date.strftime("%Y-%m-%d"), loan_id),
        )
        self.library.cursor.execute(
            "UPDATE books SET available_copies = available_copies + 1 WHERE book_id = ?",
            (book_id,),
        )
        self.library.conn.commit()

        if fine > 0:
            messagebox.showwarning("Returned late", f"Fine due: ₹{fine}")
        else:
            messagebox.showinfo("Returned", "Returned on time, no fine.")
        self.refresh_all()

    def refresh_loans(self):
        for row in self.loans_tree.get_children():
            self.loans_tree.delete(row)
        self.library.cursor.execute("""
            SELECT loans.loan_id, books.title, members.name, loans.issue_date,
                   loans.due_date, loans.return_date
            FROM loans
            JOIN books ON loans.book_id = books.book_id
            JOIN members ON loans.member_id = members.member_id
            ORDER BY loans.loan_id DESC
        """)
        from datetime import datetime
        today = datetime.now()
        for r in self.library.cursor.fetchall():
            loan_id, title, member, issued, due, returned = r
            if returned:
                status = "Returned"
            elif datetime.strptime(due, "%Y-%m-%d") < today:
                status = "OVERDUE"
            else:
                status = "Active"
            self.loans_tree.insert("", "end", values=(loan_id, title, member, issued, due, status))

    # ---------------- SHARED ----------------

    def refresh_all(self):
        self.refresh_books()
        self.refresh_members()
        self.refresh_book_dropdowns()
        self.refresh_loans()

    def on_close(self):
        self.db.close()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = LibraryGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

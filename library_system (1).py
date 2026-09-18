"""
Library Management System
--------------------------
A command-line library management system built with Python and SQLite.

Features:
- Add, search, list, and delete books
- Register members
- Issue and return books, with due dates
- Automatic fine calculation for overdue returns
- Persistent storage using SQLite (data survives after you close the program)

Author: Anirudh Thakur
"""

import sqlite3
from datetime import datetime, timedelta

DB_NAME = "library.db"
LOAN_PERIOD_DAYS = 14
FINE_PER_DAY = 5  # in rupees


class Database:
    """Handles all database connections and table setup."""

    def __init__(self, db_name=DB_NAME):
        self.conn = sqlite3.connect(db_name)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS books (
                book_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                isbn TEXT UNIQUE,
                total_copies INTEGER NOT NULL DEFAULT 1,
                available_copies INTEGER NOT NULL DEFAULT 1
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS members (
                member_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS loans (
                loan_id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER NOT NULL,
                member_id INTEGER NOT NULL,
                issue_date TEXT NOT NULL,
                due_date TEXT NOT NULL,
                return_date TEXT,
                FOREIGN KEY (book_id) REFERENCES books (book_id),
                FOREIGN KEY (member_id) REFERENCES members (member_id)
            )
        """)
        self.conn.commit()

    def close(self):
        self.conn.close()


class Library:
    """Core business logic for the library system."""

    def __init__(self, db: Database):
        self.db = db
        self.cursor = db.cursor
        self.conn = db.conn

    # ---------------- BOOK OPERATIONS ----------------

    def add_book(self, title, author, isbn, copies):
        try:
            self.cursor.execute(
                "INSERT INTO books (title, author, isbn, total_copies, available_copies) "
                "VALUES (?, ?, ?, ?, ?)",
                (title, author, isbn, copies, copies),
            )
            self.conn.commit()
            print(f"\n✅ Book '{title}' added successfully with {copies} copies.\n")
        except sqlite3.IntegrityError:
            print("\n❌ A book with this ISBN already exists.\n")

    def list_books(self):
        self.cursor.execute("SELECT book_id, title, author, isbn, available_copies, total_copies FROM books")
        rows = self.cursor.fetchall()
        if not rows:
            print("\nNo books in the library yet.\n")
            return
        print("\n{:<5}{:<30}{:<20}{:<15}{:<10}".format("ID", "Title", "Author", "ISBN", "Available"))
        print("-" * 80)
        for r in rows:
            print("{:<5}{:<30}{:<20}{:<15}{}/{}".format(r[0], r[1], r[2], r[3] or "-", r[4], r[5]))
        print()

    def search_books(self, keyword):
        query = f"%{keyword.lower()}%"
        self.cursor.execute(
            "SELECT book_id, title, author, isbn, available_copies, total_copies FROM books "
            "WHERE LOWER(title) LIKE ? OR LOWER(author) LIKE ?",
            (query, query),
        )
        rows = self.cursor.fetchall()
        if not rows:
            print("\nNo matching books found.\n")
            return
        print("\n{:<5}{:<30}{:<20}{:<15}{:<10}".format("ID", "Title", "Author", "ISBN", "Available"))
        print("-" * 80)
        for r in rows:
            print("{:<5}{:<30}{:<20}{:<15}{}/{}".format(r[0], r[1], r[2], r[3] or "-", r[4], r[5]))
        print()

    def delete_book(self, book_id):
        self.cursor.execute("SELECT title FROM books WHERE book_id = ?", (book_id,))
        row = self.cursor.fetchone()
        if not row:
            print("\n❌ No such book ID.\n")
            return
        self.cursor.execute("DELETE FROM books WHERE book_id = ?", (book_id,))
        self.conn.commit()
        print(f"\n✅ Book '{row[0]}' deleted.\n")

    # ---------------- MEMBER OPERATIONS ----------------

    def add_member(self, name, email):
        try:
            self.cursor.execute(
                "INSERT INTO members (name, email) VALUES (?, ?)", (name, email)
            )
            self.conn.commit()
            print(f"\n✅ Member '{name}' registered successfully.\n")
        except sqlite3.IntegrityError:
            print("\n❌ A member with this email already exists.\n")

    def list_members(self):
        self.cursor.execute("SELECT member_id, name, email FROM members")
        rows = self.cursor.fetchall()
        if not rows:
            print("\nNo members registered yet.\n")
            return
        print("\n{:<5}{:<25}{:<30}".format("ID", "Name", "Email"))
        print("-" * 60)
        for r in rows:
            print("{:<5}{:<25}{:<30}".format(r[0], r[1], r[2]))
        print()

    # ---------------- LOAN OPERATIONS ----------------

    def issue_book(self, book_id, member_id):
        self.cursor.execute("SELECT available_copies, title FROM books WHERE book_id = ?", (book_id,))
        book = self.cursor.fetchone()
        if not book:
            print("\n❌ No such book ID.\n")
            return
        if book[0] <= 0:
            print(f"\n❌ No available copies of '{book[1]}' right now.\n")
            return

        self.cursor.execute("SELECT member_id FROM members WHERE member_id = ?", (member_id,))
        if not self.cursor.fetchone():
            print("\n❌ No such member ID.\n")
            return

        issue_date = datetime.now()
        due_date = issue_date + timedelta(days=LOAN_PERIOD_DAYS)

        self.cursor.execute(
            "INSERT INTO loans (book_id, member_id, issue_date, due_date) VALUES (?, ?, ?, ?)",
            (book_id, member_id, issue_date.strftime("%Y-%m-%d"), due_date.strftime("%Y-%m-%d")),
        )
        self.cursor.execute(
            "UPDATE books SET available_copies = available_copies - 1 WHERE book_id = ?",
            (book_id,),
        )
        self.conn.commit()
        print(f"\n✅ '{book[1]}' issued. Due date: {due_date.strftime('%Y-%m-%d')}\n")

    def return_book(self, loan_id):
        self.cursor.execute(
            "SELECT book_id, due_date, return_date FROM loans WHERE loan_id = ?", (loan_id,)
        )
        loan = self.cursor.fetchone()
        if not loan:
            print("\n❌ No such loan ID.\n")
            return
        if loan[2] is not None:
            print("\n❌ This book has already been returned.\n")
            return

        book_id, due_date_str, _ = loan
        return_date = datetime.now()
        due_date = datetime.strptime(due_date_str, "%Y-%m-%d")

        fine = 0
        if return_date > due_date:
            days_late = (return_date - due_date).days
            fine = days_late * FINE_PER_DAY

        self.cursor.execute(
            "UPDATE loans SET return_date = ? WHERE loan_id = ?",
            (return_date.strftime("%Y-%m-%d"), loan_id),
        )
        self.cursor.execute(
            "UPDATE books SET available_copies = available_copies + 1 WHERE book_id = ?",
            (book_id,),
        )
        self.conn.commit()

        if fine > 0:
            print(f"\n⚠️  Book returned late. Fine: ₹{fine}\n")
        else:
            print("\n✅ Book returned on time. No fine.\n")

    def view_active_loans(self):
        self.cursor.execute("""
            SELECT loans.loan_id, books.title, members.name, loans.issue_date, loans.due_date
            FROM loans
            JOIN books ON loans.book_id = books.book_id
            JOIN members ON loans.member_id = members.member_id
            WHERE loans.return_date IS NULL
        """)
        rows = self.cursor.fetchall()
        if not rows:
            print("\nNo active loans.\n")
            return
        print("\n{:<8}{:<25}{:<20}{:<15}{:<15}".format("LoanID", "Book", "Member", "Issued", "Due"))
        print("-" * 85)
        today = datetime.now()
        for r in rows:
            overdue_flag = " (OVERDUE)" if datetime.strptime(r[4], "%Y-%m-%d") < today else ""
            print("{:<8}{:<25}{:<20}{:<15}{:<15}".format(r[0], r[1], r[2], r[3], r[4] + overdue_flag))
        print()


def print_menu():
    print("""
========== LIBRARY MANAGEMENT SYSTEM ==========
 1. Add Book
 2. List All Books
 3. Search Books
 4. Delete Book
 5. Register Member
 6. List Members
 7. Issue Book
 8. Return Book
 9. View Active Loans
 0. Exit
=================================================
""")


def main():
    db = Database()
    library = Library(db)

    while True:
        print_menu()
        choice = input("Enter your choice: ").strip()

        if choice == "1":
            title = input("Title: ").strip()
            author = input("Author: ").strip()
            isbn = input("ISBN (optional, press Enter to skip): ").strip() or None
            try:
                copies = int(input("Number of copies: ").strip())
            except ValueError:
                print("\n❌ Invalid number.\n")
                continue
            library.add_book(title, author, isbn, copies)

        elif choice == "2":
            library.list_books()

        elif choice == "3":
            keyword = input("Search by title or author: ").strip()
            library.search_books(keyword)

        elif choice == "4":
            try:
                book_id = int(input("Book ID to delete: ").strip())
            except ValueError:
                print("\n❌ Invalid ID.\n")
                continue
            library.delete_book(book_id)

        elif choice == "5":
            name = input("Member name: ").strip()
            email = input("Member email: ").strip()
            library.add_member(name, email)

        elif choice == "6":
            library.list_members()

        elif choice == "7":
            try:
                book_id = int(input("Book ID: ").strip())
                member_id = int(input("Member ID: ").strip())
            except ValueError:
                print("\n❌ Invalid ID.\n")
                continue
            library.issue_book(book_id, member_id)

        elif choice == "8":
            try:
                loan_id = int(input("Loan ID: ").strip())
            except ValueError:
                print("\n❌ Invalid ID.\n")
                continue
            library.return_book(loan_id)

        elif choice == "9":
            library.view_active_loans()

        elif choice == "0":
            print("\nGoodbye!\n")
            db.close()
            break

        else:
            print("\n❌ Invalid choice, try again.\n")


if __name__ == "__main__":
    main()

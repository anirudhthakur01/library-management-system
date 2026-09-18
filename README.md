# Library Management System

A command-line Library Management System built with **Python** and **SQLite**, simulating how a real library tracks books, members, and loans.

## Features
- Add, search, list, and delete books (tracks total vs. available copies)
- Register and list members
- Issue books to members with automatic due-date calculation (14-day loan period)
- Return books with automatic fine calculation for overdue returns (₹5/day)
- View all currently active (unreturned) loans, flagged if overdue
- Persistent storage using SQLite — data is saved in `library.db` and survives across runs
- Input validation and error handling (duplicate ISBNs/emails, invalid IDs, no available copies, etc.)

## Tech Stack
- **Language:** Python 3
- **Database:** SQLite3 (via Python's built-in `sqlite3` module)
- **Interface:** Command-line (menu-driven)

## How to Run
```bash
python3 library_system.py
```

No external dependencies required — uses only Python's standard library.

## Project Structure
```
library-management-system/
├── library_system.py   # Main application (Database, Library classes + CLI)
└── README.md
```

## Design Notes
- `Database` class handles the SQLite connection and schema creation.
- `Library` class contains all business logic (adding books, issuing/returning, fine calculation).
- Three tables: `books`, `members`, `loans` — `loans` uses foreign keys to link books and members.
- Fine calculation is based on the difference between due date and actual return date.

## Possible Future Improvements
- Add a web interface using Flask
- Add user authentication (admin vs. member login)
- Export loan/fine reports to CSV
- Add book categories/genres and filtering

---
Built by Anirudh Thakur

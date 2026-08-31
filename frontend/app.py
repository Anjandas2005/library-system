"""
Gradio front-end for the Library Management API.

This file never touches the database directly — every action here calls the
FastAPI backend over HTTP, exactly like any other client (Postman, a mobile
app, etc.) would. Run the backend first, then run this.
"""

import httpx
import gradio as gr

API_BASE = "http://127.0.0.1:8000"


# ---------------- Helpers ----------------

def _fmt_error(resp: httpx.Response) -> str:
    try:
        detail = resp.json().get("detail", resp.text)
    except Exception:
        detail = resp.text
    return f"Error ({resp.status_code}): {detail}"


# ---------------- Books tab ----------------

def create_book(isbn, title, author, publisher, year, genre):
    payload = {
        "isbn": isbn,
        "title": title,
        "author": author,
        "publisher": publisher or None,
        "publication_year": int(year) if year else None,
        "genre": genre or None,
    }
    resp = httpx.post(f"{API_BASE}/books", json=payload)
    if resp.status_code >= 400:
        return _fmt_error(resp), list_books()
    book = resp.json()
    return f"Book created: #{book['book_id']} — {book['title']}", list_books()


def list_books(title="", author="", genre=""):
    params = {}
    if title:
        params["title"] = title
    if author:
        params["author"] = author
    if genre:
        params["genre"] = genre
    resp = httpx.get(f"{API_BASE}/books", params=params)
    if resp.status_code >= 400:
        return [[_fmt_error(resp), "", "", ""]]
    books = resp.json()
    return [[b["book_id"], b["title"], b["author"], b["isbn"]] for b in books]


def add_copy(book_id, barcode, shelf):
    if not book_id:
        return "Please enter a Book ID.", list_copies(book_id)
    payload = {"barcode": barcode, "shelf_location": shelf or None}
    resp = httpx.post(f"{API_BASE}/books/{int(book_id)}/copies", json=payload)
    if resp.status_code >= 400:
        return _fmt_error(resp), list_copies(book_id)
    copy = resp.json()
    return f"Copy created: #{copy['copy_id']} (barcode {copy['barcode']})", list_copies(book_id)


def list_copies(book_id):
    if not book_id:
        return []
    resp = httpx.get(f"{API_BASE}/books/{int(book_id)}/copies")
    if resp.status_code >= 400:
        return [[_fmt_error(resp), "", "", ""]]
    copies = resp.json()
    return [[c["copy_id"], c["barcode"], c["status"], c["shelf_location"]] for c in copies]


# ---------------- Members tab ----------------

def create_member(first_name, last_name, email, phone, membership_type):
    payload = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "phone": phone or None,
        "membership_type": membership_type,
    }
    resp = httpx.post(f"{API_BASE}/members", json=payload)
    if resp.status_code >= 400:
        return _fmt_error(resp), list_members()
    member = resp.json()
    return f"Member registered: #{member['member_id']} — {member['first_name']} {member['last_name']}", list_members()


def list_members():
    resp = httpx.get(f"{API_BASE}/members")
    if resp.status_code >= 400:
        return [[_fmt_error(resp), "", "", ""]]
    members = resp.json()
    return [[m["member_id"], f"{m['first_name']} {m['last_name']}", m["email"], m["status"]] for m in members]


# ---------------- Issue / Return tab ----------------

def issue_book(copy_id, member_id, due_date):
    payload = {"copy_id": int(copy_id), "member_id": int(member_id), "due_date": due_date}
    resp = httpx.post(f"{API_BASE}/transactions", json=payload)
    if resp.status_code >= 400:
        return _fmt_error(resp), list_transactions()
    txn = resp.json()
    return f"Issued: Transaction #{txn['transaction_id']} — copy {txn['copy_id']} to member {txn['member_id']}, due {txn['due_date']}", list_transactions()


def check_fine(transaction_id):
    if not transaction_id:
        return "Enter a Transaction ID."
    resp = httpx.get(f"{API_BASE}/transactions/{int(transaction_id)}/current-fine")
    if resp.status_code >= 400:
        return _fmt_error(resp)
    data = resp.json()
    label = "Final fine charged" if data["final"] else "Estimated fine if returned today"
    return f"{label}: ₹{data['fine_amount']}"


def return_book(transaction_id):
    resp = httpx.patch(f"{API_BASE}/transactions/{int(transaction_id)}/return", json={})
    if resp.status_code >= 400:
        return _fmt_error(resp), list_transactions()
    txn = resp.json()
    return f"Returned: Transaction #{txn['transaction_id']} — fine charged: ₹{txn['fine_amount']}", list_transactions()


def list_transactions():
    resp = httpx.get(f"{API_BASE}/transactions")
    if resp.status_code >= 400:
        return [[_fmt_error(resp), "", "", "", "", ""]]
    txns = resp.json()
    return [
        [t["transaction_id"], t["copy_id"], t["member_id"], t["due_date"], t["status"], f"₹{t['fine_amount']}"]
        for t in txns
    ]


# ---------------- UI layout ----------------

custom_css = """
footer {display: none !important}
"""

with gr.Blocks(title="Library Management System", css=custom_css) as demo:
    gr.Markdown("# 📚 Library Management System")

    with gr.Tab("Books & Copies"):
        gr.Markdown("### Add a new book title")
        with gr.Row():
            isbn_in = gr.Textbox(label="ISBN")
            title_in = gr.Textbox(label="Title")
            author_in = gr.Textbox(label="Author")
        with gr.Row():
            publisher_in = gr.Textbox(label="Publisher")
            year_in = gr.Textbox(label="Publication Year")
            genre_in = gr.Textbox(label="Genre")
        create_book_btn = gr.Button("Create Book", variant="primary")
        book_status = gr.Textbox(label="Status", interactive=False)

        gr.Markdown("### Search / filter books")
        with gr.Row():
            search_title_in = gr.Textbox(label="Title contains")
            search_author_in = gr.Textbox(label="Author contains")
            search_genre_in = gr.Textbox(label="Genre contains")
        search_books_btn = gr.Button("Search")

        gr.Markdown("### All books")
        books_table = gr.Dataframe(headers=["Book ID", "Title", "Author", "ISBN"], interactive=False)
        refresh_books_btn = gr.Button("Refresh list (clears search)")

        gr.Markdown("### Add a physical copy to a book")
        with gr.Row():
            copy_book_id_in = gr.Textbox(label="Book ID")
            barcode_in = gr.Textbox(label="Barcode")
            shelf_in = gr.Textbox(label="Shelf Location")
        add_copy_btn = gr.Button("Add Copy", variant="primary")
        copy_status = gr.Textbox(label="Status", interactive=False)

        gr.Markdown("### Copies for a book")
        copies_table = gr.Dataframe(headers=["Copy ID", "Barcode", "Status", "Shelf"], interactive=False)
        view_copies_btn = gr.Button("View Copies for Book ID above")

        create_book_btn.click(
            create_book,
            inputs=[isbn_in, title_in, author_in, publisher_in, year_in, genre_in],
            outputs=[book_status, books_table],
        )
        search_books_btn.click(
            list_books,
            inputs=[search_title_in, search_author_in, search_genre_in],
            outputs=books_table,
        )
        refresh_books_btn.click(list_books, outputs=books_table)
        add_copy_btn.click(
            add_copy, inputs=[copy_book_id_in, barcode_in, shelf_in], outputs=[copy_status, copies_table]
        )
        view_copies_btn.click(list_copies, inputs=copy_book_id_in, outputs=copies_table)

    with gr.Tab("Members"):
        gr.Markdown("### Register a new member")
        with gr.Row():
            fname_in = gr.Textbox(label="First Name")
            lname_in = gr.Textbox(label="Last Name")
        with gr.Row():
            email_in = gr.Textbox(label="Email")
            phone_in = gr.Textbox(label="Phone")
            type_in = gr.Dropdown(["student", "faculty", "public"], label="Membership Type", value="student")
        create_member_btn = gr.Button("Register Member", variant="primary")
        member_status = gr.Textbox(label="Status", interactive=False)

        gr.Markdown("### All members")
        members_table = gr.Dataframe(headers=["Member ID", "Name", "Email", "Status"], interactive=False)
        refresh_members_btn = gr.Button("Refresh list")

        create_member_btn.click(
            create_member,
            inputs=[fname_in, lname_in, email_in, phone_in, type_in],
            outputs=[member_status, members_table],
        )
        refresh_members_btn.click(list_members, outputs=members_table)

    with gr.Tab("Issue / Return"):
        gr.Markdown("### Issue a book")
        with gr.Row():
            issue_copy_id_in = gr.Textbox(label="Copy ID")
            issue_member_id_in = gr.Textbox(label="Member ID")
            due_date_in = gr.Textbox(label="Due Date (YYYY-MM-DD)")
        issue_btn = gr.Button("Issue Book", variant="primary")
        issue_status = gr.Textbox(label="Status", interactive=False)

        gr.Markdown("### Check fine / Return a book")
        with gr.Row():
            txn_id_in = gr.Textbox(label="Transaction ID")
        with gr.Row():
            check_fine_btn = gr.Button("Check Current Fine")
            return_btn = gr.Button("Return Book", variant="stop")
        return_status = gr.Textbox(label="Status", interactive=False)

        gr.Markdown("### All transactions")
        txns_table = gr.Dataframe(
            headers=["Transaction ID", "Copy ID", "Member ID", "Due Date", "Status", "Fine"],
            interactive=False,
        )
        refresh_txns_btn = gr.Button("Refresh list")

        issue_btn.click(
            issue_book,
            inputs=[issue_copy_id_in, issue_member_id_in, due_date_in],
            outputs=[issue_status, txns_table],
        )
        check_fine_btn.click(check_fine, inputs=txn_id_in, outputs=return_status)
        return_btn.click(return_book, inputs=txn_id_in, outputs=[return_status, txns_table])
        refresh_txns_btn.click(list_transactions, outputs=txns_table)


if __name__ == "__main__":
    demo.launch(css=custom_css)
def add_contact(cur, holdid, holdnavn):
    cur.execute("INSERT INTO public.teams(holdid, holdnavn) VALUES (%s, %s)",
                (holdid, holdnavn))
    cur.execute("INSERT INTO public.sumo(holdid, holdnavn, tid) VALUES (%s, %s, NULL)",
                (holdid, holdnavn))
    cur.execute("INSERT INTO public.wallfollow(holdid, holdnavn, tid) VALUES (%s, %s, NULL)",
                (holdid, holdnavn))

def add_timesumo(cur, holdid, tid):
    cur.execute("UPDATE public.sumo SET tid = %s WHERE holdid = %s", (tid, holdid))

def add_timewall(cur, holdid, tid):
    cur.execute("UPDATE public.wallfollow SET tid = %s WHERE holdid = %s", (tid, holdid))

# Replace Contact
def replace_contact(cur, holdid, holdnavn):
    cur.execute("INSERT INTO public.teams(holdid, holdnavn) VALUES (%s, %s) "
                "ON CONFLICT (holdid) DO UPDATE SET holdnavn = EXCLUDED.holdnavn",
                (holdid, holdnavn))

# Print List of Contacts
def print_contacts(cur):
    teams = []
    cur.execute("SELECT holdid, holdnavn FROM public.teams")
    for holdid, holdnavn in cur.fetchall():
        teams.append(f"{holdid} {holdnavn}")
    print("\n".join(teams))

# Delete Contact
def delete_contact(cur, holdid):
    cur.execute("DELETE FROM public.teams WHERE holdid = %s", (holdid,))
    cur.execute("DELETE FROM public.wallfollow WHERE holdid = %s", (holdid,))
    cur.execute("DELETE FROM public.sumo WHERE holdid = %s", (holdid,))

def generate_html_table(rows):
    html_rows = '<tr><th>holdid</th><th>holdnavn</th><th>tid</th><th>lab1</th><th>lab2</th><th>lab3</th></tr>'
    for holdid, holdnavn, tid, lab1, lab2, lab3 in rows:
        html_rows += f'<tr><td>{holdid}</td><td>{holdnavn}</td><td>{tid}</td><td>{lab1}</td><td>{lab2}</td><td>{lab3}</td></tr>'
    return html_rows

def generate_html_tablesumo(rows):
    html_rows = '<tr><th>holdid</th><th>holdnavn</th><th>tid</th></tr>'
    for holdid, holdnavn, tid in rows:  # Note: only 3 values now
        html_rows += f'<tr><td>{holdid}</td><td>{holdnavn}</td><td>{tid}</td></tr>'
    return html_rows
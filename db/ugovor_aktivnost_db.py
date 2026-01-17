from db.db import *

def fetch_narucitelji():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT naziv FROM narucitelji ORDER BY naziv")
    data = [r[0] for r in cur.fetchall()]
    cur.close()
    conn.close()
    return data


def fetch_stanja():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT naziv FROM stanja_aktivnosti ORDER BY stanje_id")
    data = [r[0] for r in cur.fetchall()]
    cur.close()
    conn.close()
    return data


def fetch_ugovori():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT u.ugovor_id, u.naziv, n.naziv,
               TO_CHAR(u.datum_pocetka,'YYYY-MM-DD'),
               COALESCE(TO_CHAR(u.datum_zavrsetka,'YYYY-MM-DD'), '')
        FROM ugovori u
        JOIN narucitelji n ON u.narucitelj_id = n.narucitelj_id
        ORDER BY u.datum_pocetka DESC
    """)
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data


def fetch_aktivnosti(ugovor_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT a.aktivnost_id, a.naziv, a.planirani_sati, s.naziv
        FROM aktivnosti a
        JOIN stanja_aktivnosti s ON a.stanje_id = s.stanje_id
        WHERE a.ugovor_id = %s
        ORDER BY a.naziv
    """, (ugovor_id,))
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data


def dodaj_ugovor(narucitelj, naziv, od, do):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT narucitelj_id FROM narucitelji WHERE naziv=%s", (narucitelj,))
        nid = cur.fetchone()[0]

        cur.execute("""
            INSERT INTO ugovori(narucitelj_id, naziv, datum_pocetka, datum_zavrsetka)
            VALUES (%s,%s,%s,%s)
        """, (nid, naziv, od, do or None))
        conn.commit()
        return True
    except Exception as e:
        print(e)
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()


def dodaj_aktivnost(ugovor_id, naziv, sati, stanje):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT stanje_id FROM stanja_aktivnosti WHERE naziv=%s",
            (stanje,)
        )
        sid = cur.fetchone()[0]

        cur.execute("""
            INSERT INTO aktivnosti(ugovor_id, naziv, planirani_sati, stanje_id)
            VALUES (%s, %s, %s, %s)
        """, (ugovor_id, naziv, sati, sid))

        conn.commit()
        return True

    except Exception as e:
        conn.rollback()
        print("Greška pri dodavanju aktivnosti")
        return False

    finally:
        cur.close()
        conn.close()


def promijeni_stanje(aktivnost_id, novo_stanje):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT stanje_id FROM stanja_aktivnosti WHERE naziv=%s",
            (novo_stanje,)
        )
        sid = cur.fetchone()[0]

        cur.execute(
            "UPDATE aktivnosti SET stanje_id=%s WHERE aktivnost_id=%s",
            (sid, aktivnost_id)
        )

        conn.commit()
        return True

    except Exception as e:
        conn.rollback()
        print("Greška pri promjeni stanja")
        return False

    finally:
        cur.close()
        conn.close()


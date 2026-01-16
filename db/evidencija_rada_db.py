from db.db import *

def fetch_radnici():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT radnik_id, ime || ' ' || prezime
        FROM radnici
        WHERE aktivan = TRUE
        ORDER BY prezime
    """)
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data


def fetch_aktivnosti():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT a.aktivnost_id,
               a.naziv || ' (' || u.naziv || ')'
        FROM aktivnosti a
        JOIN ugovori u ON a.ugovor_id = u.ugovor_id
        ORDER BY a.naziv
    """)
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data


def fetch_dnevnik():
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT dr.unos_id,
                   r.ime || ' ' || r.prezime,
                   a.naziv,
                   dr.datum_rada,
                   dr.sati,
                   COALESCE(dr.opis, '')
            FROM dnevnik_rada dr
            JOIN radnici r ON dr.radnik_id = r.radnik_id
            JOIN aktivnosti a ON dr.aktivnost_id = a.aktivnost_id
            ORDER BY dr.datum_rada DESC
        """)
        data = cur.fetchall()
        return data

    except Exception as e:
        print("Greška u fetch_dnevnik:", e)
        return []

    finally:
        cur.close()
        conn.close()


def dodaj_unos(radnik_id, aktivnost_id, datum, sati, opis):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO dnevnik_rada
                (radnik_id, aktivnost_id, datum_rada, sati, opis)
            VALUES (%s, %s, %s, %s, %s)
        """, (radnik_id, aktivnost_id, datum, sati, opis))
        conn.commit()
        return True

    except Exception as e:
        conn.rollback()
        print("Greška pri unosu rada:", e)
        return str(e)

    finally:
        cur.close()
        conn.close()

from db.db import *

def fetch_isplate(radnik_id=None):
    conn = get_connection()
    cur = conn.cursor()
    try:
        query = """
            SELECT i.isplata_id,
                   r.ime || ' ' || r.prezime,
                   i.datum_isplate,
                   i.ukupno_sati,
                   i.ukupni_trosak
            FROM isplate i
            JOIN radnici r ON i.radnik_id = r.radnik_id
        """
        params = ()
        if radnik_id:
            query += " WHERE i.radnik_id = %s"
            params = (radnik_id,)
        query += " ORDER BY i.datum_isplate DESC"
        cur.execute(query, params)
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()


def fetch_radnici_aktivni():
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT radnik_id, ime || ' ' || prezime
            FROM radnici
            WHERE aktivan = TRUE
            ORDER BY prezime
        """)
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()

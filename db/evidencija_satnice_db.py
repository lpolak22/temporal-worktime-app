from db.db import *

def fetch_satnice(radnik_id=None):
    conn = get_connection()
    cur = conn.cursor()
    try:
        query = """
            SELECT sr.satnica_id,
                   r.ime || ' ' || r.prezime,
                   sr.vrijedi_od,
                   sr.vrijedi_do,
                   sr.iznos_eur_po_satu
            FROM satnice_radnika sr
            JOIN radnici r ON sr.radnik_id = r.radnik_id
        """
        params = ()
        if radnik_id:
            query += " WHERE sr.radnik_id = %s"
            params = (radnik_id,)
        query += " ORDER BY sr.radnik_id, sr.vrijedi_od"
        cur.execute(query, params)
        data = cur.fetchall()
        return data
    finally:
        cur.close()
        conn.close()


def dodaj_satnicu(radnik_id, vrijedi_od, iznos):
    conn = get_connection()
    cur = conn.cursor()
    try:
        if isinstance(vrijedi_od, str):
            vrijedi_od = vrijedi_od.strip()

        cur.execute("""
            SELECT satnica_id, vrijedi_od, vrijedi_do
            FROM satnice_radnika
            WHERE radnik_id = %s
            ORDER BY vrijedi_od DESC
            LIMIT 1
        """, (radnik_id,))
        zadnja = cur.fetchone()

        if zadnja:
            cur.execute("""
                UPDATE satnice_radnika
                SET vrijedi_do = %s
                WHERE satnica_id = %s
            """, (vrijedi_od, zadnja[0]))

        cur.execute("""
            INSERT INTO satnice_radnika (radnik_id, vrijedi_od, iznos_eur_po_satu)
            VALUES (%s, %s, %s)
        """, (radnik_id, vrijedi_od, iznos))

        conn.commit()
        return True

    except Exception as e:
        conn.rollback()
        print("Greška kod satnice")
        return str(e)
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

from db.db import *

def fetch_pozicije():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT naziv FROM pozicije ORDER BY naziv")
    data = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return data

def fetch_radnici():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT r.radnik_id, r.ime || ' ' || r.prezime, p.naziv,
               TO_CHAR(r.datum_zaposlenja, 'YYYY-MM-DD')
        FROM radnici r
        JOIN radnik_pozicija rp ON r.radnik_id = rp.radnik_id
        JOIN pozicije p ON rp.pozicija_id = p.pozicija_id
        WHERE r.aktivan = TRUE
        ORDER BY r.prezime, r.ime
    """)
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data

def dodaj_radnika(ime, prezime, datum, pozicija):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO radnici(ime, prezime, datum_zaposlenja) VALUES (%s, %s, %s) RETURNING radnik_id",
                    (ime, prezime, datum))
        radnik_id = cur.fetchone()[0]
        cur.execute("SELECT pozicija_id FROM pozicije WHERE naziv = %s", (pozicija,))
        poz_id = cur.fetchone()[0]
        cur.execute("INSERT INTO radnik_pozicija(radnik_id, pozicija_id) VALUES (%s, %s)", (radnik_id, poz_id))
        cur.execute("INSERT INTO satnice_radnika(radnik_id, vrijedi_od, vrijedi_do, iznos_eur_po_satu) VALUES (%s, CURRENT_DATE, 'infinity', 7.5)", (radnik_id,))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Greška: {e}")
        return False
    finally:
        cur.close()
        conn.close()

def obrisi_radnika(radnik_id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE radnici SET aktivan = FALSE, datum_odlaska = CURRENT_DATE WHERE radnik_id = %s", (radnik_id,))
        conn.commit()
        return True
    except:
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()

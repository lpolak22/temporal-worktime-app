CREATE EXTENSION IF NOT EXISTS btree_gist;

CREATE TABLE narucitelji (
  narucitelj_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  naziv VARCHAR(80) NOT NULL,
  email VARCHAR(120) NOT NULL UNIQUE,
  telefon VARCHAR(30)
);

CREATE TABLE stanja_aktivnosti (
  stanje_id SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  naziv VARCHAR(20) NOT NULL UNIQUE
);

CREATE TABLE pozicije (
  pozicija_id SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  naziv VARCHAR(40) NOT NULL UNIQUE
);

CREATE TABLE radnici (
  radnik_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  ime VARCHAR(40) NOT NULL,
  prezime VARCHAR(60) NOT NULL,
  datum_zaposlenja DATE NOT NULL,
  datum_odlaska DATE,
  aktivan BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE radnik_pozicija (
  radnik_id BIGINT NOT NULL REFERENCES radnici(radnik_id) ON DELETE CASCADE,
  pozicija_id SMALLINT NOT NULL REFERENCES pozicije(pozicija_id),
  PRIMARY KEY (radnik_id, pozicija_id)
);

CREATE TABLE ugovori (
  ugovor_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  narucitelj_id BIGINT NOT NULL REFERENCES narucitelji(narucitelj_id),
  naziv VARCHAR(120) NOT NULL,
  datum_pocetka DATE NOT NULL,
  datum_zavrsetka DATE
);

CREATE TABLE aktivnosti (
  aktivnost_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  ugovor_id BIGINT NOT NULL REFERENCES ugovori(ugovor_id) ON DELETE CASCADE,
  naziv VARCHAR(120) NOT NULL,
  planirani_sati NUMERIC(10,2) NOT NULL CHECK (planirani_sati >= 0),
  stanje_id SMALLINT NOT NULL REFERENCES stanja_aktivnosti(stanje_id),
  UNIQUE (ugovor_id, naziv)
);

CREATE TABLE satnice_radnika (
  satnica_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  radnik_id BIGINT NOT NULL REFERENCES radnici(radnik_id) ON DELETE CASCADE,
  vrijedi_od DATE NOT NULL,
  vrijedi_do DATE NOT NULL DEFAULT 'infinity'::date,
  iznos_eur_po_satu NUMERIC(10,2) NOT NULL CHECK (iznos_eur_po_satu > 0),
  CHECK (vrijedi_od < vrijedi_do)
);

ALTER TABLE satnice_radnika
ADD CONSTRAINT satnice_bez_preklapanja
EXCLUDE USING gist (
  radnik_id WITH =,
  daterange(vrijedi_od, vrijedi_do, '[)') WITH &&
);

CREATE TABLE dnevnik_rada (
  unos_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  radnik_id BIGINT NOT NULL REFERENCES radnici(radnik_id),
  aktivnost_id BIGINT NOT NULL REFERENCES aktivnosti(aktivnost_id),
  datum_rada DATE NOT NULL,
  sati NUMERIC(10,2) NOT NULL CHECK (sati > 0 AND sati <= 24),
  opis TEXT,
  CONSTRAINT uq_radnik_aktivnost_datum UNIQUE(radnik_id, aktivnost_id, datum_rada)
);

CREATE TABLE isplate (
  isplata_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  radnik_id BIGINT NOT NULL REFERENCES radnici(radnik_id),
  ugovor_id BIGINT NOT NULL REFERENCES ugovori(ugovor_id),
  datum_isplate DATE NOT NULL DEFAULT CURRENT_DATE,
  broj_unosa INTEGER NOT NULL CHECK (broj_unosa > 0),
  ukupno_sati NUMERIC(10,2) NOT NULL CHECK (ukupno_sati >= 0),
  ukupni_trosak NUMERIC(12,2) NOT NULL CHECK (ukupni_trosak >= 0),
  CONSTRAINT uq_isplata_radnik_datum UNIQUE(radnik_id, datum_isplate)
);

CREATE INDEX idx_dnevnik_rada_radnik_datum
ON dnevnik_rada(radnik_id, datum_rada);

CREATE INDEX idx_aktivnosti_ugovor
ON aktivnosti(ugovor_id);

CREATE OR REPLACE FUNCTION trg_zabrani_dupli_unos()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    postoji INT;
BEGIN
    SELECT COUNT(*)
      INTO postoji
      FROM dnevnik_rada
     WHERE radnik_id = NEW.radnik_id
       AND aktivnost_id = NEW.aktivnost_id
       AND datum_rada = NEW.datum_rada;

    IF postoji > 0 THEN
        RAISE EXCEPTION 'Radnik % već ima unos za aktivnost % na datum %', 
            NEW.radnik_id, NEW.aktivnost_id, NEW.datum_rada;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER t_dupli_unos
BEFORE INSERT OR UPDATE ON dnevnik_rada
FOR EACH ROW
EXECUTE FUNCTION trg_zabrani_dupli_unos();

CREATE OR REPLACE FUNCTION trg_limit_40_sati_7_dana()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
  start_tjedna DATE;
  suma_tjedna NUMERIC(10,2);

BEGIN
  start_tjedna := date_trunc('week', NEW.datum_rada + INTERVAL '1 day')::DATE;

  SELECT COALESCE(SUM(sati), 0)
  INTO suma_tjedna
  FROM dnevnik_rada
  WHERE radnik_id = NEW.radnik_id
    AND datum_rada >= start_tjedna
    AND datum_rada < start_tjedna + INTERVAL '7 days'
    AND (TG_OP = 'INSERT' OR unos_id <> NEW.unos_id);

  IF suma_tjedna + NEW.sati > 40 THEN
    RAISE EXCEPTION
      'Zbroj sati u tjednu % ne smije preći 40 (trenutno % + novi unos %)',
      start_tjedna::text, round(suma_tjedna, 2), round(NEW.sati, 2);
  END IF;

  RETURN NEW;
END;
$$;

CREATE TRIGGER t_limit_40_sati_7_dana
BEFORE INSERT OR UPDATE
ON dnevnik_rada
FOR EACH ROW
EXECUTE FUNCTION trg_limit_40_sati_7_dana();

CREATE OR REPLACE FUNCTION trg_kreiraj_isplatu_tjedno()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
  start_tjedna DATE;
  end_tjedna DATE;
  ukupno_sati NUMERIC(10,2);
  ukupni_trosak NUMERIC(12,2);
  v_ugovor_id BIGINT;
  vec_isplata INT;

BEGIN
  start_tjedna := date_trunc('week', NEW.datum_rada + INTERVAL '1 day')::DATE;
  end_tjedna := start_tjedna + INTERVAL '7 days';

  SELECT COUNT(*)
  INTO vec_isplata
  FROM isplate
  WHERE radnik_id = NEW.radnik_id
    AND datum_isplate >= start_tjedna
    AND datum_isplate < end_tjedna;

  IF vec_isplata = 0 THEN
    SELECT a.ugovor_id
    INTO v_ugovor_id
    FROM aktivnosti a
    JOIN dnevnik_rada dr ON a.aktivnost_id = dr.aktivnost_id
    WHERE dr.radnik_id = NEW.radnik_id
      AND dr.datum_rada >= start_tjedna
      AND dr.datum_rada < end_tjedna
    LIMIT 1;

    IF v_ugovor_id IS NOT NULL THEN
      SELECT COALESCE(SUM(sati), 0)
      INTO ukupno_sati
      FROM dnevnik_rada
      WHERE radnik_id = NEW.radnik_id
        AND datum_rada >= start_tjedna
        AND datum_rada < end_tjedna;

      SELECT COALESCE(SUM(dr.sati * sr.iznos_eur_po_satu), 0)
      INTO ukupni_trosak
      FROM dnevnik_rada dr
      JOIN satnice_radnika sr
        ON sr.radnik_id = dr.radnik_id
       AND dr.datum_rada >= sr.vrijedi_od
       AND dr.datum_rada < sr.vrijedi_do
      WHERE dr.radnik_id = NEW.radnik_id
        AND dr.datum_rada >= start_tjedna
        AND dr.datum_rada < end_tjedna;

      INSERT INTO isplate(
        radnik_id, ugovor_id, datum_isplate, broj_unosa, ukupno_sati, ukupni_trosak
      )
      SELECT
        NEW.radnik_id,
        v_ugovor_id,
        end_tjedna::DATE - 1,
        COUNT(*),
        ukupno_sati,
        ukupni_trosak
      FROM dnevnik_rada
      WHERE radnik_id = NEW.radnik_id
        AND datum_rada >= start_tjedna
        AND datum_rada < end_tjedna;
    END IF;
  END IF;

  RETURN NEW;
END;
$$;

CREATE TRIGGER t_isplata_tjedno
AFTER INSERT
ON dnevnik_rada
FOR EACH ROW
EXECUTE FUNCTION trg_kreiraj_isplatu_tjedno();

CREATE OR REPLACE FUNCTION trg_provjera_unosa_rada()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
  v_stanje TEXT;
  v_pocetak DATE;
  v_zavrsetak DATE;

BEGIN
  SELECT s.naziv
  INTO v_stanje
  FROM aktivnosti a
  JOIN stanja_aktivnosti s ON a.stanje_id = s.stanje_id
  WHERE a.aktivnost_id = NEW.aktivnost_id;

  IF v_stanje <> 'U tijeku' THEN
    RAISE EXCEPTION
      'Rad se može evidentirati samo za aktivnosti u tijeku (trenutno: %)',
      v_stanje;
  END IF;

  SELECT u.datum_pocetka, u.datum_zavrsetka
  INTO v_pocetak, v_zavrsetak
  FROM ugovori u
  JOIN aktivnosti a ON a.ugovor_id = u.ugovor_id
  WHERE a.aktivnost_id = NEW.aktivnost_id;

  IF NEW.datum_rada < v_pocetak THEN
    RAISE EXCEPTION 'Datum rada je prije početka ugovora (%).', v_pocetak;
  END IF;

  IF v_zavrsetak IS NOT NULL AND NEW.datum_rada > v_zavrsetak THEN
    RAISE EXCEPTION 'Ugovor je završen % – nije moguće evidentirati rad.', v_zavrsetak;
  END IF;

  RETURN NEW;
END;
$$;

CREATE TRIGGER t_provjera_unosa_rada
BEFORE INSERT OR UPDATE
ON dnevnik_rada
FOR EACH ROW
EXECUTE FUNCTION trg_provjera_unosa_rada();

CREATE OR REPLACE FUNCTION azuriraj_isplatu_tjedno_f(radnik BIGINT, datum DATE)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    start_tjedna DATE;
    end_tjedna DATE;
    ukupno_sati NUMERIC(10,2);
    ukupni_trosak NUMERIC(12,2);
    v_ugovor_id BIGINT;
BEGIN
    start_tjedna := date_trunc('week', datum + INTERVAL '1 day')::DATE;
    end_tjedna := start_tjedna + INTERVAL '7 days';

    SELECT a.ugovor_id
    INTO v_ugovor_id
    FROM aktivnosti a
    JOIN dnevnik_rada dr ON a.aktivnost_id = dr.aktivnost_id
    WHERE dr.radnik_id = radnik
      AND dr.datum_rada >= start_tjedna
      AND dr.datum_rada < end_tjedna
    LIMIT 1;

    IF v_ugovor_id IS NOT NULL THEN
        SELECT COALESCE(SUM(sati),0)
        INTO ukupno_sati
        FROM dnevnik_rada
        WHERE radnik_id = radnik
          AND datum_rada >= start_tjedna
          AND datum_rada < end_tjedna;

        SELECT COALESCE(SUM(dr.sati * sr.iznos_eur_po_satu),0)
        INTO ukupni_trosak
        FROM dnevnik_rada dr
        JOIN satnice_radnika sr
          ON sr.radnik_id = dr.radnik_id
         AND dr.datum_rada >= sr.vrijedi_od
         AND dr.datum_rada < sr.vrijedi_do
        WHERE dr.radnik_id = radnik
          AND dr.datum_rada >= start_tjedna
          AND dr.datum_rada < end_tjedna;

        INSERT INTO isplate(radnik_id, ugovor_id, datum_isplate, broj_unosa, ukupno_sati, ukupni_trosak)
        SELECT
            radnik,
            v_ugovor_id,
            end_tjedna::DATE - 1,
            COUNT(*),
            ukupno_sati,
            ukupni_trosak
        FROM dnevnik_rada
        WHERE radnik_id = radnik
          AND datum_rada >= start_tjedna
          AND datum_rada < end_tjedna
        ON CONFLICT (radnik_id, datum_isplate)
        DO UPDATE SET
            broj_unosa = EXCLUDED.broj_unosa,
            ukupno_sati = EXCLUDED.ukupno_sati,
            ukupni_trosak = EXCLUDED.ukupni_trosak;
    END IF;
END;
$$;


CREATE OR REPLACE FUNCTION trg_azuriraj_isplatu_po_satnici()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    dr RECORD;
BEGIN
    FOR dr IN
        SELECT unos_id, radnik_id, datum_rada
        FROM dnevnik_rada
        WHERE radnik_id = NEW.radnik_id
          AND datum_rada >= NEW.vrijedi_od
          AND datum_rada < NEW.vrijedi_do
    LOOP
        PERFORM azuriraj_isplatu_tjedno_f(dr.radnik_id, dr.datum_rada);
    END LOOP;

    RETURN NEW;
END;
$$;

CREATE TRIGGER t_azuriraj_isplatu_po_satnici
AFTER INSERT OR UPDATE ON satnice_radnika
FOR EACH ROW
EXECUTE FUNCTION trg_azuriraj_isplatu_po_satnici();


INSERT INTO stanja_aktivnosti(naziv)
VALUES
('Nije započeto'),
  ('U tijeku'),
  ('Dovršeno');

INSERT INTO pozicije(naziv)
VALUES
('Programer'),
  ('Voditelj projekta'),
  ('Računovodstvo');

INSERT INTO narucitelji(naziv, email, telefon)
VALUES
('Orion d.o.o.', 'kontakt@orion.hr', '012111222'),
  ('Beta d.o.o.', 'info@beta.hr', '012333444'),
  ('Gamma d.o.o.', 'kontakt@gamma.hr', '098555666');

INSERT INTO radnici(ime, prezime, datum_zaposlenja)
VALUES
('Ivana', 'Klarić', '2024-10-01'),
  ('Marko', 'Horvat', '2025-02-15'),
  ('Ana', 'Kovač', '2025-03-01'),
  ('Petar', 'Babić', '2025-01-20');

INSERT INTO radnik_pozicija
VALUES
(1, 1),
  (2, 1),
  (3, 2),
  (4, 3);

INSERT INTO satnice_radnika(radnik_id, vrijedi_od, iznos_eur_po_satu)
VALUES
(1, '2025-01-01', 7.50),
  (2, '2025-01-01', 8.00),
  (3, '2025-01-01', 12.00),
  (4, '2025-01-01', 10.00);

INSERT INTO ugovori(narucitelj_id, naziv, datum_pocetka, datum_zavrsetka)
VALUES
(1, 'Razvoj sustava evidencije rada', '2025-11-01', '2026-01-16'),
  (2, 'Razvoj web aplikacije', '2025-12-01', '2026-03-31'),
  (3, 'Implementacija ERP sustava', '2025-11-15', '2026-03-31');

INSERT INTO aktivnosti(ugovor_id, naziv, planirani_sati, stanje_id)
VALUES
(1, 'Analiza zahtjeva', 40, 2),
  (1, 'Implementacija sustava', 80, 2);

INSERT INTO aktivnosti(ugovor_id, naziv, planirani_sati, stanje_id)
VALUES
(2, 'Frontend development', 120, 1),
  (2, 'Backend development', 150, 1);

INSERT INTO aktivnosti(ugovor_id, naziv, planirani_sati, stanje_id)
VALUES
(3, 'Analiza procesa', 60, 2),
  (3, 'Migracija podataka', 40, 1);

UPDATE aktivnosti
SET stanje_id = (
  SELECT stanje_id
  FROM stanja_aktivnosti
  WHERE naziv = 'U tijeku'
)
WHERE ugovor_id = 2
  AND naziv = 'Frontend development';

INSERT INTO dnevnik_rada(radnik_id, aktivnost_id, datum_rada, sati, opis)
VALUES
(1, 1, '2025-11-03', 6, 'Analiza zahtjeva s klijentom'),
  (1, 2, '2025-11-04', 7, 'Postavljanje baze podataka'),
  (2, 3, '2025-12-02', 8, 'Implementacija login forme'),
  (2, 3, '2025-12-03', 8, 'CSS i responsive layout'),
  (3, 5, '2025-11-18', 6, 'Radionica s korisnicima');

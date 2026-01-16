CREATE EXTENSION IF NOT EXISTS btree_gist;

CREATE TABLE narucitelji (
    narucitelj_id      BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    naziv              VARCHAR(80) NOT NULL,
    email              VARCHAR(120) NOT NULL UNIQUE,
    telefon            VARCHAR(30)
);

CREATE TABLE stanja_aktivnosti (
    stanje_id          SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    naziv              VARCHAR(20) NOT NULL UNIQUE
);

CREATE TABLE pozicije (
    pozicija_id        SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    naziv              VARCHAR(40) NOT NULL UNIQUE
);

CREATE TABLE radnici (
    radnik_id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ime                VARCHAR(40) NOT NULL,
    prezime            VARCHAR(60) NOT NULL,
    datum_zaposlenja   DATE NOT NULL,
    datum_odlaska      DATE,
    aktivan            BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE radnik_pozicija (
    radnik_id          BIGINT NOT NULL REFERENCES radnici(radnik_id) ON DELETE CASCADE,
    pozicija_id        SMALLINT NOT NULL REFERENCES pozicije(pozicija_id),
    PRIMARY KEY (radnik_id, pozicija_id)
);

CREATE TABLE ugovori (
    ugovor_id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    narucitelj_id      BIGINT NOT NULL REFERENCES narucitelji(narucitelj_id),
    naziv              VARCHAR(120) NOT NULL,
    datum_pocetka      DATE NOT NULL,
    datum_zavrsetka    DATE
);

CREATE TABLE aktivnosti (
    aktivnost_id       BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ugovor_id          BIGINT NOT NULL REFERENCES ugovori(ugovor_id) ON DELETE CASCADE,
    naziv              VARCHAR(120) NOT NULL,
    planirani_sati     NUMERIC(10,2) NOT NULL CHECK (planirani_sati >= 0),
    stanje_id          SMALLINT NOT NULL REFERENCES stanja_aktivnosti(stanje_id),
    UNIQUE (ugovor_id, naziv)
);

CREATE TABLE satnice_radnika (
    satnica_id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    radnik_id          BIGINT NOT NULL REFERENCES radnici(radnik_id) ON DELETE CASCADE,
    vrijedi_od         DATE NOT NULL,
    vrijedi_do         DATE NOT NULL DEFAULT 'infinity'::date,
    iznos_eur_po_satu  NUMERIC(10,2) NOT NULL CHECK (iznos_eur_po_satu > 0),
    CHECK (vrijedi_od < vrijedi_do)
);

ALTER TABLE satnice_radnika
ADD CONSTRAINT satnice_bez_preklapanja
EXCLUDE USING gist (
    radnik_id WITH =,
    daterange(vrijedi_od, vrijedi_do, '[)') WITH &&
);

CREATE TABLE dnevnik_rada (
    unos_id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    radnik_id          BIGINT NOT NULL REFERENCES radnici(radnik_id),
    aktivnost_id       BIGINT NOT NULL REFERENCES aktivnosti(aktivnost_id),
    datum_rada         DATE NOT NULL,
    sati               NUMERIC(10,2) NOT NULL CHECK (sati > 0 AND sati <= 24),
    opis               TEXT,

    CONSTRAINT uq_radnik_datum UNIQUE (radnik_id, datum_rada)
);

CREATE TABLE isplate (
    isplata_id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    radnik_id          BIGINT NOT NULL REFERENCES radnici(radnik_id),
    ugovor_id          BIGINT NOT NULL REFERENCES ugovori(ugovor_id),
    datum_isplate      DATE NOT NULL DEFAULT CURRENT_DATE,
    broj_unosa         INTEGER NOT NULL CHECK (broj_unosa > 0),
    ukupno_sati        NUMERIC(10,2) NOT NULL CHECK (ukupno_sati >= 0),
    ukupni_trosak      NUMERIC(12,2) NOT NULL CHECK (ukupni_trosak >= 0)
);

CREATE INDEX idx_dnevnik_rada_radnik_datum ON dnevnik_rada(radnik_id, datum_rada);
CREATE INDEX idx_aktivnosti_ugovor ON aktivnosti(ugovor_id);

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
       AND datum_rada = NEW.datum_rada;

    IF postoji > 0 THEN
        RAISE EXCEPTION 'Radnik % već ima unos za datum %', NEW.radnik_id, NEW.datum_rada;
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
BEFORE INSERT OR UPDATE ON dnevnik_rada
FOR EACH ROW
EXECUTE FUNCTION trg_limit_40_sati_7_dana();

INSERT INTO stanja_aktivnosti(naziv) VALUES ('Nije započeto'), ('U tijeku'), ('Dovršeno');
INSERT INTO pozicije(naziv) VALUES ('Programer'), ('Voditelj projekta'), ('Računovodstvo');

INSERT INTO radnici(ime, prezime, datum_zaposlenja) VALUES ('Ivana', 'Klarić', '2024-10-01');
INSERT INTO radnik_pozicija(radnik_id, pozicija_id) VALUES (1, 1);

INSERT INTO satnice_radnika(radnik_id, vrijedi_od, vrijedi_do, iznos_eur_po_satu)
VALUES (1, '2025-01-01', 'infinity', 7.5);

INSERT INTO narucitelji(naziv, email) VALUES ('Orion d.o.o.', 'kontakt@orion.hr');
INSERT INTO ugovori(narucitelj_id, naziv, datum_pocetka) VALUES (1, 'Razvoj sustava evidencije rada', '2025-11-01');

INSERT INTO aktivnosti(ugovor_id, naziv, planirani_sati, stanje_id)
VALUES (1, 'Implementacija evidencije', 80, 2);

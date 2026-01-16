import PySimpleGUI as sg
from db.ugovor_aktivnost_db import *

def ugovori_aktivnosti_window(narucitelji, ugovori, aktivnosti, stanja):
    heading_ug = ["ID", "Naziv", "Naručitelj", "Početak", "Završetak"]
    heading_act = ["ID", "Naziv", "Planirani sati", "Stanje"]

    layout = [
        [sg.Text("Ugovori i aktivnosti", font=("Arial", 14))],

        [sg.Frame("Unos novog ugovora", [
            [sg.Text("Naručitelj"), sg.Combo(narucitelji, key="NARUCITELJ", readonly=True)],
            [sg.Text("Naziv ugovora"), sg.Input(key="UG_NAZIV")],
            [sg.Text("Datum početka"), sg.Input(key="UG_OD"),
             sg.CalendarButton("KALENDAR", target="UG_OD", format="%Y-%m-%d")],
            [sg.Text("Datum završetka"), sg.Input(key="UG_DO"),
             sg.CalendarButton("KALENDAR", target="UG_DO", format="%Y-%m-%d")],
            [sg.Button("Dodaj ugovor")]
        ])],

        [sg.HorizontalSeparator()],

        [sg.Frame("Ugovori", [
            [sg.Table(
                values=ugovori,
                headings=heading_ug,
                auto_size_columns=True,
                num_rows=6,
                key="UGOVOR_TBL",
                select_mode="browse",
                enable_events=True
            )]
        ])],

        [sg.HorizontalSeparator()],

        [sg.Frame("Aktivnosti po ugovoru", [
            [sg.Text("Naziv aktivnosti"), sg.Input(key="AKT_NAZIV")],
            [sg.Text("Planirani sati"), sg.Input(key="AKT_SATI")],
            [sg.Text("Stanje"), sg.Combo(stanja, key="AKT_STANJE", readonly=True)],
            [sg.Button("Dodaj aktivnost")],

            [sg.Table(
                values=aktivnosti,
                headings=heading_act,
                auto_size_columns=True,
                num_rows=6,
                key="AKT_TBL",
                select_mode="browse"
            )],

            [sg.Text("Promjena stanja"),
             sg.Combo(stanja, key="NOVO_STANJE", readonly=True),
             sg.Button("Promijeni stanje")]
        ])],

        [sg.Button("Nazad")],
        [sg.Text("", key="STATUS", size=(50,1), font=("Arial", 10), text_color="white")]
    ]

    return sg.Window("Ugovori i aktivnosti", layout, finalize=True)


def run_ugovori_aktivnosti_window():
    narucitelji = fetch_narucitelji()
    stanja = fetch_stanja()
    ugovori = fetch_ugovori()
    aktivnosti = []

    win = ugovori_aktivnosti_window(narucitelji, ugovori, aktivnosti, stanja)

    trenutno_odabrani_ugovor = None

    while True:
        event, values = win.read()

        if event in (sg.WIN_CLOSED, "Nazad"):
            win.close()
            return

        if event == "Dodaj ugovor":
            if values["NARUCITELJ"] and values["UG_NAZIV"] and values["UG_OD"]:
                if dodaj_ugovor(
                    values["NARUCITELJ"],
                    values["UG_NAZIV"],
                    values["UG_OD"],
                    values["UG_DO"]
                ):
                    win["STATUS"].update("Ugovor uspješno dodan", text_color="white")
                    win["UGOVOR_TBL"].update(values=fetch_ugovori())

                    for key in ["UG_NAZIV", "UG_OD", "UG_DO", "NARUCITELJ"]:
                        win[key].update("")
                else:
                    win["STATUS"].update("Greška pri dodavanju ugovora", text_color="orange")
            else:
                win["STATUS"].update("Popuni sva obavezna polja ugovora", text_color="orange")

        elif event == "UGOVOR_TBL":
            selected = values["UGOVOR_TBL"]
            if selected:
                ugovor_id = fetch_ugovori()[selected[0]][0]
                trenutno_odabrani_ugovor = ugovor_id
                win["AKT_TBL"].update(values=fetch_aktivnosti(ugovor_id))
                win["STATUS"].update(f"Odabran ugovor ID {ugovor_id}", text_color="white")


        elif event == "Dodaj aktivnost":
            if trenutno_odabrani_ugovor is None:
                win["STATUS"].update("Najprije odaberi ugovor", text_color="orange")
                continue

            if values["AKT_NAZIV"] and values["AKT_SATI"] and values["AKT_STANJE"]:
                if not values["AKT_SATI"].replace('.', '', 1).isdigit():
                    win["STATUS"].update("Planirani sati moraju biti broj", text_color="orange")
                    continue

                if dodaj_aktivnost(
                    trenutno_odabrani_ugovor,
                    values["AKT_NAZIV"],
                    values["AKT_SATI"],
                    values["AKT_STANJE"]
                ):
                    win["STATUS"].update("Aktivnost dodana", text_color="white")
                    win["AKT_TBL"].update(values=fetch_aktivnosti(trenutno_odabrani_ugovor))

                    for key in ["AKT_NAZIV", "AKT_SATI", "AKT_STANJE"]:
                        win[key].update("")
                else:
                    win["STATUS"].update("Greška pri dodavanju aktivnosti", text_color="orange")
            else:
                win["STATUS"].update("Popuni sva polja aktivnosti", text_color="orange")

        elif event == "Promijeni stanje":
            akt_sel = values["AKT_TBL"]

            if trenutno_odabrani_ugovor is None:
                win["STATUS"].update("Nije odabran ugovor", text_color="orange")
                continue

            if not akt_sel:
                win["STATUS"].update("Odaberi aktivnost", text_color="orange")
                continue

            if not values["NOVO_STANJE"]:
                win["STATUS"].update("Odaberi novo stanje", text_color="orange")
                continue

            akt_id = fetch_aktivnosti(trenutno_odabrani_ugovor)[akt_sel[0]][0]

            if promijeni_stanje(akt_id, values["NOVO_STANJE"]):
                win["STATUS"].update("Stanje aktivnosti promijenjeno", text_color="white")
                win["AKT_TBL"].update(values=fetch_aktivnosti(trenutno_odabrani_ugovor))
            else:
                win["STATUS"].update("Greška pri promjeni stanja", text_color="orange")

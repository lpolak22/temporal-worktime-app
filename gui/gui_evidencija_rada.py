import PySimpleGUI as sg
from db.evidencija_rada_db import *

def evidencija_rada_window(radnici, aktivnosti, dnevnik):
    headings = ["ID", "Radnik", "Aktivnost", "Datum", "Sati", "Opis"]

    layout = [
        [sg.Text("Evidencija rada", font=("Arial", 14))],

        [sg.Frame("Novi unos rada", [
            [sg.Text("Radnik"), sg.Combo(
                [r[1] for r in radnici], key="RADNIK", readonly=True)],

            [sg.Text("Aktivnost"), sg.Combo(
                [a[1] for a in aktivnosti], key="AKTIVNOST", readonly=True)],

            [sg.Text("Datum rada"),
             sg.Input(key="DATUM"),
             sg.CalendarButton("KALENDAR", target="DATUM", format="%Y-%m-%d")],

            [sg.Text("Broj sati"), sg.Input(key="SATI")],

            [sg.Text("Opis"), sg.Multiline(key="OPIS", size=(40, 3))],

            [sg.Button("Spremi unos")]
        ])],

        [sg.HorizontalSeparator()],

        [sg.Table(
            values=dnevnik,
            headings=headings,
            auto_size_columns=False,
            num_rows=8,
            key="TBL_RAD",
            col_widths=[6, 18, 25, 10, 6, 40],
            enable_events=True
        )],
        
        [sg.Button("Nazad")],
        [sg.Text("", key="STATUS", size=(70,1), text_color="white")]
    ]

    return sg.Window("Evidencija rada", layout, finalize=True)


def run_evidencija_rada_window():
    radnici = fetch_radnici()
    aktivnosti = fetch_aktivnosti()
    dnevnik = fetch_dnevnik()
    if dnevnik is None:
        dnevnik = []


    win = evidencija_rada_window(radnici, aktivnosti, dnevnik)

    while True:
        event, values = win.read()

        if event in (sg.WIN_CLOSED, "Nazad"):
            win.close()
            return

        elif event == "TBL_RAD":
            selected = values["TBL_RAD"]
            if selected:
                unos = dnevnik[selected[0]]
                layout_popup = [
                    [sg.Text(f"Radnik: {unos[1]}")],
                    [sg.Text(f"Aktivnost: {unos[2]}")],
                    [sg.Text(f"Datum: {unos[3]}")],
                    [sg.Text(f"Sati: {unos[4]}")],
                    [sg.Text("Opis:")],
                    [sg.Multiline(unos[5], size=(60, 15), disabled=True, autoscroll=True)],
                    [sg.Button("Zatvori")]
                ]
                win_popup = sg.Window("Detalji unosa", layout_popup, modal=True)
                while True:
                    e, v = win_popup.read()
                    if e in (sg.WIN_CLOSED, "Zatvori"):
                        break
                win_popup.close()


        if event == "Spremi unos":

            if not all([values["RADNIK"], values["AKTIVNOST"],
                        values["DATUM"], values["SATI"]]):
                win["STATUS"].update("Popuni sva obavezna polja", text_color="orange")
                continue

            if not values["SATI"].replace('.', '', 1).isdigit():
                win["STATUS"].update("Sati moraju biti broj", text_color="orange")
                continue

            radnik_id = next(r[0] for r in radnici if r[1] == values["RADNIK"])
            aktivnost_id = next(a[0] for a in aktivnosti if a[1] == values["AKTIVNOST"])

            result = dodaj_unos(
                radnik_id,
                aktivnost_id,
                values["DATUM"],
                values["SATI"],
                values["OPIS"]
            )

            if result is True:
                win["STATUS"].update("Unos rada spremljen", text_color="white")
                win["TBL_RAD"].update(values=fetch_dnevnik())

                for k in ["RADNIK", "AKTIVNOST", "DATUM", "SATI", "OPIS"]:
                    win[k].update("")
            else:
                win["STATUS"].update(result, text_color="orange")

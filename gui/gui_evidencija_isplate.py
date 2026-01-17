import PySimpleGUI as sg
from db.evidencija_isplate_db import fetch_isplate, fetch_radnici_aktivni

import datetime
from db.evidencija_isplate_db import fetch_detalji_isplate

def isplate_window(radnici, isplate):
    headings = ["Radnik", "Datum isplate", "Ukupni sati", "Ukupni trošak (€)"]
    
    isplate_table = [
        [i[2], i[3], i[4], i[5]] for i in isplate
    ]

    layout = [
        [sg.Text("Pregled isplata", font=("Arial", 14))],

        [sg.Frame("Filter po radniku", [
            [sg.Text("Radnik"), sg.Combo([r[1] for r in radnici], key="RADNIK", readonly=True)],
            [sg.Button("Primjeni filter"), sg.Button("Očisti filter")]
        ])],

        [sg.HorizontalSeparator()],

        [sg.Table(
            values=isplate_table,
            headings=headings,
            auto_size_columns=False,
            num_rows=15,
            key="TBL_ISPLATE",
            col_widths=[6, 20, 12, 10, 12],
            enable_events=True
        )],

        [sg.Button("Nazad")],
        [sg.Text("", key="STATUS", size=(50,1), text_color="white")]
    ]

    return sg.Window("Isplate i obračun", layout, finalize=True)


def run_isplate_window():
    radnici = fetch_radnici_aktivni()
    isplate = fetch_isplate()
    win = isplate_window(radnici, isplate)

    while True:
        event, values = win.read()
        if event in (sg.WIN_CLOSED, "Nazad"):
            win.close()
            return

        elif event == "Primjeni filter":
            if not values["RADNIK"]:
                win["STATUS"].update("Odaberi radnika za filter", text_color="orange")
                continue
            radnik_id = next(r[0] for r in radnici if r[1] == values["RADNIK"])
            filtrirane_isplate = fetch_isplate(radnik_id)
            filtrirani_table = [[i[2], i[3], i[4], i[5]] for i in filtrirane_isplate]
            win["TBL_ISPLATE"].update(values=filtrirani_table)
            win["STATUS"].update(f"Prikaz isplata za {values['RADNIK']}", text_color="white")

        elif event == "Očisti filter":
            isplate = fetch_isplate()
            isplate_table = [[i[2], i[3], i[4], i[5]] for i in isplate]
            win["TBL_ISPLATE"].update(values=isplate_table)
            win["RADNIK"].update("")
            win["STATUS"].update("Filter uklonjen", text_color="white")

        elif event == "TBL_ISPLATE":
            selected = values["TBL_ISPLATE"]
            if not selected:
                continue

            isplata = fetch_isplate()[selected[0]]

            radnik_id = isplata[1]
            radnik_ime = isplata[2]
            datum_isplate = isplata[3]

            od = datum_isplate - datetime.timedelta(days=6)
            do = datum_isplate

            detalji = fetch_detalji_isplate(radnik_id, od, do)

            popup_layout = [
                [sg.Text(f"Radnik: {radnik_ime}", font=("Arial", 12, "bold"))],
                [sg.Text(f"Razdoblje: {od} - {do}")],

                [sg.Table(
                    values=detalji,
                    headings=["Datum", "Aktivnost", "Sati", "Satnica (€)", "Iznos (€)"],
                    auto_size_columns=False,
                    col_widths=[12, 25, 8, 10, 12],
                    num_rows=10
                )],

                [sg.Button("Zatvori")]
            ]

            win_popup = sg.Window(
                "Detalji isplate",
                popup_layout,
                modal=True,
                finalize=True
            )

            while True:
                e, _ = win_popup.read()
                if e in (sg.WIN_CLOSED, "Zatvori"):
                    break

            win_popup.close()


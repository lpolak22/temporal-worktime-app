import PySimpleGUI as sg
from db.evidencija_satnice_db import *

def satnice_window(radnici, satnice):
    headings = ["ID", "Radnik", "Vrijedi od", "Vrijedi do", "Iznos €/sat"]

    layout = [
        [sg.Text("Satnice radnika", font=("Arial", 14))],

        [sg.Frame("Nova satnica", [
            [sg.Text("Radnik"), sg.Combo([r[1] for r in radnici], key="RADNIK", readonly=True)],
            [sg.Text("Vrijedi od"), sg.Input(key="VRIJEDI_OD"),
             sg.CalendarButton("Kalendar", target="VRIJEDI_OD", format="%Y-%m-%d")],
            [sg.Text("Iznos €/sat"), sg.Input(key="IZNOS")],
            [sg.Button("Spremi satnicu")]
        ])],

        [sg.HorizontalSeparator()],

        [sg.Table(
            values=satnice,
            headings=headings,
            auto_size_columns=False,
            num_rows=10,
            key="TBL_SATNICE",
            col_widths=[6, 20, 12, 12, 10],
            enable_events=True
        )],

        [sg.Button("Nazad")],
        [sg.Text("", key="STATUS", size=(50,1), text_color="white")]
    ]

    return sg.Window("Satnice radnika", layout, finalize=True)


def run_satnice_window():
    radnici = fetch_radnici_aktivni()
    satnice = fetch_satnice()
    win = satnice_window(radnici, satnice)

    while True:
        event, values = win.read()
        if event in (sg.WIN_CLOSED, "Nazad"):
            win.close()
            return

        elif event == "Spremi satnicu":
            if not all([values["RADNIK"], values["VRIJEDI_OD"], values["IZNOS"]]):
                win["STATUS"].update("Popuni sva polja", text_color="orange")
                continue

            try:
                iznos = float(values["IZNOS"])
            except ValueError:
                win["STATUS"].update("Iznos mora biti broj", text_color="orange")
                continue

            radnik_id = next(r[0] for r in radnici if r[1] == values["RADNIK"])
            result = dodaj_satnicu(radnik_id, values["VRIJEDI_OD"], iznos)

            if result is True:
                win["STATUS"].update("Satnica spremljena", text_color="white")
                win["TBL_SATNICE"].update(values=fetch_satnice())
                for k in ["RADNIK", "VRIJEDI_OD", "IZNOS"]:
                    win[k].update("")
            else:
                win["STATUS"].update(result, text_color="orange")

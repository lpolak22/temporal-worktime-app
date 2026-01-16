import PySimpleGUI as sg

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
                select_mode="browse"
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
        [sg.Text("", key="STATUS", size=(60,1))]
    ]

    return sg.Window("Ugovori i aktivnosti", layout, finalize=True)


def run_ugovori_aktivnosti_window():
    narucitelji = ["Varaždin"]
    stanja = ["Planirano"]
    ugovori =  [1, "Održavanje", "Varaždin", "2025-10-01", "2026-03-37"],
    aktivnosti = [
        [1, "1", 20, "U tijeku"],
        [2, "2", 12, "Planirano"],
        [3, "3", 8, "Završeno"]
    ]

    win = ugovori_aktivnosti_window(narucitelji, ugovori, aktivnosti, stanja)

    while True:
        event, values = win.read()
        if event in (sg.WIN_CLOSED, "Nazad"):
            win.close()
            return

        
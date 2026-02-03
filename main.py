import os
import csv
from datetime import datetime

from kivy.app import App
from kivy.metrics import dp, sp
from kivy.utils import platform

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup

from openpyxl import Workbook

# Opcional: compartir archivo (Android)
try:
    from plyer import share
except Exception:
    share = None


def show_popup(title: str, msg: str):
    root = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(10))

    lbl = Label(text=msg, halign="left", valign="top")
    lbl.bind(size=lambda *_: setattr(lbl, "text_size", (lbl.width, None)))
    root.add_widget(lbl)

    btn = Button(text="OK", size_hint=(1, None), height=dp(48))
    root.add_widget(btn)

    pop = Popup(title=title, content=root, size_hint=(0.92, 0.55), auto_dismiss=False)
    btn.bind(on_release=pop.dismiss)
    pop.open()


class RowItem(BoxLayout):
    """Fila con 2 columnas: codigo | nombre/marca"""
    def __init__(self, codigo: str, nombre: str, **kwargs):
        super().__init__(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(36),
            padding=(dp(8), dp(4)),
            spacing=dp(10),
            **kwargs
        )

        self.lbl_codigo = Label(
            text=codigo,
            size_hint_x=0.38,
            halign="left",
            valign="middle",
            font_size=sp(14)
        )
        self.lbl_codigo.bind(size=self.lbl_codigo.setter("text_size"))

        self.lbl_nombre = Label(
            text=nombre,
            size_hint_x=0.62,
            halign="left",
            valign="middle",
            font_size=sp(14)
        )
        self.lbl_nombre.bind(size=self.lbl_nombre.setter("text_size"))

        self.add_widget(self.lbl_codigo)
        self.add_widget(self.lbl_nombre)


class PLUAppUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=dp(12), spacing=dp(10), **kwargs)

        self.data = []
        self.filtered = []

        # Título
        title = Label(text="PLU APP", font_size=sp(20), size_hint=(1, None), height=dp(40))
        self.add_widget(title)

        # Barra de búsqueda
        bar = BoxLayout(orientation="horizontal", size_hint=(1, None), height=dp(46), spacing=dp(8))
        self.query = TextInput(
            hint_text="Buscar por código o nombre...",
            multiline=False,
            font_size=sp(14),
            padding=(dp(10), dp(10))
        )
        btn_search = Button(text="Buscar", size_hint=(None, 1), width=dp(110), font_size=sp(14))
        btn_clear = Button(text="Limpiar", size_hint=(None, 1), width=dp(110), font_size=sp(14))

        btn_search.bind(on_release=lambda *_: self.apply_filter())
        btn_clear.bind(on_release=lambda *_: self.clear_filter())

        bar.add_widget(self.query)
        bar.add_widget(btn_search)
        bar.add_widget(btn_clear)
        self.add_widget(bar)

        # Acciones
        actions = BoxLayout(orientation="horizontal", size_hint=(1, None), height=dp(46), spacing=dp(8))
        btn_reload = Button(text="Recargar CSV", font_size=sp(14))
        btn_export = Button(text="Exportar a Excel", font_size=sp(14))

        btn_reload.bind(on_release=lambda *_: self.load_csv())
        btn_export.bind(on_release=lambda *_: self.export_excel())

        actions.add_widget(btn_reload)
        actions.add_widget(btn_export)
        self.add_widget(actions)

        # Estado
        self.status = Label(text="Cargando...", size_hint=(1, None), height=dp(26), font_size=sp(13))
        self.add_widget(self.status)

        # Header de tabla
        header = BoxLayout(orientation="horizontal", size_hint=(1, None), height=dp(30), padding=(dp(8), 0), spacing=dp(10))
        h1 = Label(text="[b]CODIGO[/b]", markup=True, size_hint_x=0.38, halign="left", valign="middle", font_size=sp(13))
        h2 = Label(text="[b]MARCA/NOMBRE[/b]", markup=True, size_hint_x=0.62, halign="left", valign="middle", font_size=sp(13))
        h1.bind(size=h1.setter("text_size"))
        h2.bind(size=h2.setter("text_size"))
        header.add_widget(h1)
        header.add_widget(h2)
        self.add_widget(header)

        # Lista scroll
        self.scroll = ScrollView(do_scroll_x=False)
        self.list_layout = GridLayout(cols=1, spacing=dp(6), size_hint_y=None, padding=(0, dp(4), 0, dp(10)))
        self.list_layout.bind(minimum_height=self.list_layout.setter("height"))
        self.scroll.add_widget(self.list_layout)
        self.add_widget(self.scroll)

        self.query.bind(on_text_validate=lambda *_: self.apply_filter())

        self.load_csv()

    def csv_path(self):
        return os.path.join(os.path.dirname(__file__), "plu_catalogo.csv")

    def load_csv(self):
        path = self.csv_path()

        if not os.path.exists(path):
            self.data = []
            self.filtered = []
            self.render_results([])
            self.status.text = "⚠️ No se encontró plu_catalogo.csv"
            show_popup(
                "Falta CSV",
                "No se encontró 'plu_catalogo.csv' junto a main.py.\n\n"
                "Solución:\n"
                "1) Sube plu_catalogo.csv al repo (misma carpeta de main.py)\n"
                "2) Recompila el APK."
            )
            return

        try:
            with open(path, "r", encoding="utf-8", newline="") as f:
                rows = list(csv.reader(f))

            items = []
            start_idx = 0
            if rows and len(rows[0]) >= 2:
                h0 = (rows[0][0] or "").strip().lower()
                h1 = (rows[0][1] or "").strip().lower()
                if "codigo" in h0 and ("nombre" in h1 or "marca" in h1):
                    start_idx = 1

            for r in rows[start_idx:]:
                if not r or len(r) < 2:
                    continue
                codigo = (r[0] or "").strip()
                nombre = (r[1] or "").strip()
                if codigo and nombre:
                    items.append({"codigo": codigo, "nombre": nombre})

            self.data = items
            self.filtered = items
            self.render_results(self.filtered)
            self.status.text = f"✅ Cargados: {len(self.data)} registros"

        except Exception as e:
            self.data = []
            self.filtered = []
            self.render_results([])
            self.status.text = "❌ Error cargando CSV"
            show_popup("Error CSV", f"Error leyendo CSV:\n{e}")

    def apply_filter(self):
        q = (self.query.text or "").strip().lower()
        if not q:
            self.filtered = self.data
        else:
            self.filtered = [
                x for x in self.data
                if q in x["codigo"].lower() or q in x["nombre"].lower()
            ]

        self.render_results(self.filtered)
        self.status.text = f"Resultados: {len(self.filtered)}"

    def clear_filter(self):
        self.query.text = ""
        self.filtered = self.data
        self.render_results(self.filtered)
        self.status.text = f"✅ Cargados: {len(self.data)} registros"

    def render_results(self, items):
        self.list_layout.clear_widgets()

        if not items:
            self.list_layout.add_widget(Label(text="(Sin resultados)", size_hint_y=None, height=dp(30), font_size=sp(14)))
            return

        max_show = 200
        for it in items[:max_show]:
            self.list_layout.add_widget(RowItem(it["codigo"], it["nombre"]))

        if len(items) > max_show:
            self.list_layout.add_widget(Label(
                text=f"... mostrando {max_show} de {len(items)} (refina la búsqueda)",
                size_hint_y=None,
                height=dp(30),
                font_size=sp(13)
            ))

    def export_excel(self):
        if not self.filtered:
            show_popup("Nada para exportar", "No hay resultados para exportar.")
            return

        try:
            app = App.get_running_app()
            out_dir = app.user_data_dir
            os.makedirs(out_dir, exist_ok=True)

            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            out_path = os.path.join(out_dir, f"plu_export_{stamp}.xlsx")

            wb = Workbook()
            ws = wb.active
            ws.title = "PLU"
            ws.append(["codigo", "nombre"])

            for it in self.filtered:
                ws.append([it["codigo"], it["nombre"]])

            wb.save(out_path)

            # Compartir en Android
            if platform == "android" and share is not None:
                try:
                    share.share(
                        title="Export PLU",
                        text="Archivo Excel generado por PLU APP",
                        filepath=out_path
                    )
                    self.status.text = "✅ Excel creado y listo para compartir"
                    return
                except Exception:
                    pass

            show_popup("Listo", f"Excel creado en:\n{out_path}\n\n(Es carpeta interna de la app)")
            self.status.text = "✅ Excel creado"

        except Exception as e:
            show_popup("Error exportando", f"No se pudo crear el Excel:\n{e}")


class PLUApp(App):
    def build(self):
        return PLUAppUI()


if __name__ == "__main__":
    PLUApp().run()






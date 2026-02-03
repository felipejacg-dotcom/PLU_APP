import os
import csv
from datetime import datetime

from kivy.app import App
from kivy.utils import platform
from kivy.metrics import dp, sp
from kivy.core.window import Window

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup

from openpyxl import Workbook

# Opcional: compartir archivo en Android
try:
    from plyer import share
except Exception:
    share = None


def show_popup(title: str, msg: str):
    content = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(10))
    lbl = Label(text=msg, halign="left", valign="middle")
    lbl.bind(size=lambda *_: setattr(lbl, "text_size", (lbl.width, None)))
    btn = Button(text="OK", size_hint=(1, None), height=dp(48))
    content.add_widget(lbl)
    content.add_widget(btn)

    pop = Popup(title=title, content=content, size_hint=(0.9, 0.5), auto_dismiss=False)
    btn.bind(on_release=pop.dismiss)
    pop.open()


class RowItem(BoxLayout):
    """Fila bonita: codigo arriba, nombre abajo, con wrap."""
    def __init__(self, codigo, nombre, **kwargs):
        super().__init__(orientation="vertical", padding=(dp(10), dp(8)), spacing=dp(4),
                         size_hint_y=None, **kwargs)
        self.codigo_lbl = Label(
            text=f"[b]{codigo}[/b]",
            markup=True,
            font_size=sp(16),
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(22),
        )
        self.codigo_lbl.bind(size=lambda *_: setattr(self.codigo_lbl, "text_size", (self.codigo_lbl.width, None)))

        self.nombre_lbl = Label(
            text=nombre,
            font_size=sp(14),
            halign="left",
            valign="top",
            size_hint_y=None,
        )
        # wrap del texto
        self.nombre_lbl.bind(
            width=lambda *_: setattr(self.nombre_lbl, "text_size", (self.nombre_lbl.width, None))
        )
        # altura dinámica para que no se pise
        self.nombre_lbl.bind(texture_size=self._update_height)

        self.add_widget(self.codigo_lbl)
        self.add_widget(self.nombre_lbl)

    def _update_height(self, *_):
        # altura = alto del texto + paddings aproximados
        self.nombre_lbl.height = max(dp(20), self.nombre_lbl.texture_size[1] + dp(4))
        self.height = self.codigo_lbl.height + self.nombre_lbl.height + dp(16)


class PLUAppUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=dp(12), spacing=dp(10), **kwargs)

        self.data = []
        self.filtered = []

        title = Label(text="PLU APP", font_size=sp(22), size_hint=(1, None), height=dp(42))
        self.add_widget(title)

        # Barra búsqueda
        bar = BoxLayout(orientation="horizontal", size_hint=(1, None), height=dp(48), spacing=dp(8))
        self.query = TextInput(
            hint_text="Buscar por código o nombre...",
            multiline=False,
            font_size=sp(16),
        )
        btn_search = Button(text="Buscar", size_hint=(None, 1), width=dp(110))
        btn_clear = Button(text="Limpiar", size_hint=(None, 1), width=dp(110))

        btn_search.bind(on_release=lambda *_: self.apply_filter())
        btn_clear.bind(on_release=lambda *_: self.clear_filter())

        bar.add_widget(self.query)
        bar.add_widget(btn_search)
        bar.add_widget(btn_clear)
        self.add_widget(bar)

        # Botones acciones
        actions = BoxLayout(orientation="horizontal", size_hint=(1, None), height=dp(48), spacing=dp(8))
        btn_reload = Button(text="Recargar CSV")
        btn_export = Button(text="Exportar a Excel")

        btn_reload.bind(on_release=lambda *_: self.load_csv())
        btn_export.bind(on_release=lambda *_: self.export_excel())

        actions.add_widget(btn_reload)
        actions.add_widget(btn_export)
        self.add_widget(actions)

        # Estado
        self.status = Label(text="Cargando...", size_hint=(1, None), height=dp(28), font_size=sp(14))
        self.add_widget(self.status)

        # Lista resultados
        self.scroll = ScrollView()
        self.list_layout = GridLayout(cols=1, spacing=dp(8), size_hint_y=None, padding=(0, dp(6), 0, dp(6)))
        self.list_layout.bind(minimum_height=self.list_layout.setter("height"))
        self.scroll.add_widget(self.list_layout)
        self.add_widget(self.scroll)

        # Cargar al iniciar
        self.load_csv()

        self.query.bind(on_text_validate=lambda *_: self.apply_filter())

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
                "Falta archivo",
                "No se encontró 'plu_catalogo.csv' junto a main.py.\n"
                "Debe estar en la raíz del repo para que el APK lo incluya."
            )
            return

        try:
            with open(path, "r", encoding="utf-8", newline="") as f:
                reader = csv.reader(f)
                rows = list(reader)

            start_idx = 0
            if rows and len(rows[0]) >= 2:
                h0 = (rows[0][0] or "").strip().lower()
                h1 = (rows[0][1] or "").strip().lower()
                if "codigo" in h0 and "nombre" in h1:
                    start_idx = 1

            items = []
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
            self.filtered = [x for x in self.data if q in x["codigo"].lower() or q in x["nombre"].lower()]

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
            self.list_layout.add_widget(Label(text="(Sin resultados)", size_hint_y=None, height=dp(30)))
            return

        max_show = 200
        to_show = items[:max_show]

        for it in to_show:
            self.list_layout.add_widget(RowItem(it["codigo"], it["nombre"]))

        if len(items) > max_show:
            more = Label(
                text=f"... mostrando {max_show} de {len(items)} (refina la búsqueda)",
                size_hint_y=None,
                height=dp(30),
                font_size=sp(14),
            )
            self.list_layout.add_widget(more)

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

            if platform == "android" and share is not None:
                try:
                    share.share(title="Export PLU", text="Excel generado por PLU APP", filepath=out_path)
                    self.status.text = "✅ Excel creado y listo para compartir"
                    return
                except Exception:
                    pass

            self.status.text = "✅ Excel creado"
            show_popup("Listo", f"Excel creado en:\n{out_path}\n\n(Es carpeta interna de la app)")

        except Exception as e:
            show_popup("Error exportando", f"No se pudo crear el Excel:\n{e}")


class PLUApp(App):
    def build(self):
        return PLUAppUI()


if __name__ == "__main__":
    PLUApp().run()

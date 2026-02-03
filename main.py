import os
import csv
from datetime import datetime

from kivy.app import App
from kivy.utils import platform
from kivy.resources import resource_find
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.recycleview.views import RecycleDataViewBehavior

from openpyxl import Workbook


def show_popup(title: str, msg: str):
    content = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(10))
    lbl = Label(text=msg, halign="left", valign="middle")
    lbl.bind(size=lambda *_: setattr(lbl, "text_size", (lbl.width, None)))
    btn = Button(text="OK", size_hint=(1, None), height=dp(48))
    content.add_widget(lbl)
    content.add_widget(btn)
    pop = Popup(title=title, content=content, size_hint=(0.92, 0.55), auto_dismiss=False)
    btn.bind(on_release=pop.dismiss)
    pop.open()


class RowItem(RecycleDataViewBehavior, Label):
    pass


class ResultsRV(RecycleView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.viewclass = "RowItem"
        layout = RecycleBoxLayout(
            default_size=(None, dp(34)),
            default_size_hint=(1, None),
            size_hint=(1, None),
            orientation="vertical",
            spacing=dp(6),
            padding=[dp(8), dp(8), dp(8), dp(8)],
        )
        layout.bind(minimum_height=layout.setter("height"))
        self.layout_manager = layout
        self.add_widget(layout)


class PLUAppUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=dp(12), spacing=dp(10), **kwargs)

        self.data = []
        self.filtered = []

        # Título
        title = Label(text="PLU APP", font_size=dp(22), size_hint=(1, None), height=dp(40))
        self.add_widget(title)

        # Barra búsqueda (más alta y cómoda)
        bar = BoxLayout(orientation="horizontal", size_hint=(1, None), height=dp(52), spacing=dp(8))
        self.query = TextInput(
            hint_text="Buscar por código o nombre...",
            multiline=False,
            font_size=dp(18),
            padding=[dp(10), dp(14), dp(10), dp(10)]
        )
        btn_search = Button(text="Buscar", size_hint=(None, 1), width=dp(130), font_size=dp(16))
        btn_clear = Button(text="Limpiar", size_hint=(None, 1), width=dp(130), font_size=dp(16))

        btn_search.bind(on_release=lambda *_: self.apply_filter())
        btn_clear.bind(on_release=lambda *_: self.clear_filter())

        bar.add_widget(self.query)
        bar.add_widget(btn_search)
        bar.add_widget(btn_clear)
        self.add_widget(bar)

        # Botones acciones
        actions = BoxLayout(orientation="horizontal", size_hint=(1, None), height=dp(52), spacing=dp(8))
        btn_reload = Button(text="Recargar CSV", font_size=dp(16))
        btn_export = Button(text="Exportar a Excel", font_size=dp(16))
        btn_reload.bind(on_release=lambda *_: self.load_csv())
        btn_export.bind(on_release=lambda *_: self.export_excel())
        actions.add_widget(btn_reload)
        actions.add_widget(btn_export)
        self.add_widget(actions)

        # Estado
        self.status = Label(text="Cargando...", size_hint=(1, None), height=dp(28), font_size=dp(14))
        self.add_widget(self.status)

        # Resultados con RecycleView
        self.rv = ResultsRV(size_hint=(1, 1))
        self.add_widget(self.rv)

        # Cargar
        self.load_csv()
        self.query.bind(on_text_validate=lambda *_: self.apply_filter())

    def find_csv(self):
        # Busca el CSV en los assets empaquetados por buildozer
        # Asegúrate de que el archivo exista en el repo y se llame EXACTO:
        # plu_catalogo.csv
        p = resource_find("plu_catalogo.csv")
        if p and os.path.exists(p):
            return p

        # fallback: mismo directorio del main.py (útil en PC)
        p2 = os.path.join(os.path.dirname(__file__), "plu_catalogo.csv")
        if os.path.exists(p2):
            return p2

        return None

    def load_csv(self):
        path = self.find_csv()
        if not path:
            self.data = []
            self.filtered = []
            self.rv.data = [{"text": "(No se encontró plu_catalogo.csv)", "font_size": dp(16)}]
            self.status.text = "⚠️ Falta plu_catalogo.csv"
            show_popup(
                "Falta archivo",
                "No se encontró 'plu_catalogo.csv'.\n\n"
                "Solución:\n"
                "1) Sube plu_catalogo.csv a la raíz del repo\n"
                "2) Confirma que buildozer.spec tiene source.include_exts = py,csv,...\n"
                "3) Recompila"
            )
            return

        try:
            items = []
            with open(path, "r", encoding="utf-8", newline="") as f:
                reader = csv.reader(f)
                rows = list(reader)

            start_idx = 0
            if rows and len(rows[0]) >= 2:
                h0 = (rows[0][0] or "").strip().lower()
                h1 = (rows[0][1] or "").strip().lower()
                if "codigo" in h0 and "nombre" in h1:
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
            self.rv.data = [{"text": "(Error leyendo CSV)", "font_size": dp(16)}]
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
        if not items:
            self.rv.data = [{"text": "(Sin resultados)", "font_size": dp(16)}]
            return

        # Mostramos máximo 300 para fluidez
        max_show = 300
        to_show = items[:max_show]

        self.rv.data = [
            {
                "text": f"{it['codigo']}  -  {it['nombre']}",
                "font_size": dp(16),
                "size_hint_y": None,
                "height": dp(34),
                "halign": "left",
                "valign": "middle",
            }
            for it in to_show
        ]

        if len(items) > max_show:
            self.rv.data.append({
                "text": f"... mostrando {max_show} de {len(items)} (refina la búsqueda)",
                "font_size": dp(14),
                "height": dp(34),
            })

    def export_excel(self):
        if not self.filtered:
            show_popup("Nada para exportar", "No hay resultados para exportar.")
            return

        try:
            app = App.get_running_app()
            out_dir = app.user_data_dir  # seguro en Android
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

            self.status.text = "✅ Excel creado"
            show_popup("Listo", f"Excel creado en:\n{out_path}\n\n(Es carpeta interna de la app)")

        except Exception as e:
            show_popup("Error exportando", f"No se pudo crear el Excel:\n{e}")


class PLUApp(App):
    def build(self):
        return PLUAppUI()


if __name__ == "__main__":
    PLUApp().run()




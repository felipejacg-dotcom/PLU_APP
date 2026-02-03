# main.py
import os
import csv
from datetime import datetime

from kivy.app import App
from kivy.lang import Builder
from kivy.resources import resource_find
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.properties import ListProperty, NumericProperty, StringProperty
from kivy.core.clipboard import Clipboard

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment


KV = r"""
#:import dp kivy.metrics.dp

<PluRow@Button>:
    size_hint_y: None
    height: dp(44)
    halign: "left"
    valign: "middle"
    text_size: self.size
    on_release: app.select_index(self.index)

BoxLayout:
    orientation: "vertical"
    padding: dp(12)
    spacing: dp(10)

    Label:
        text: "PLU_APP"
        font_size: "24sp"
        size_hint_y: None
        height: dp(34)
        bold: True

    BoxLayout:
        size_hint_y: None
        height: dp(44)
        spacing: dp(8)

        TextInput:
            id: search_in
            hint_text: "Buscar por código o nombre (ej: 3035 o nectarín)"
            multiline: False
            on_text: app.apply_filter(self.text)

        Button:
            text: "Limpiar"
            size_hint_x: None
            width: dp(95)
            on_release:
                search_in.text = ""
                app.apply_filter("")

    BoxLayout:
        size_hint_y: None
        height: dp(44)
        spacing: dp(8)

        Button:
            text: "Copiar código"
            on_release: app.copy_selected()

        Button:
            text: "Exportar Excel"
            on_release: app.export_excel()

    Label:
        id: status_lbl
        text: app.status_text
        size_hint_y: None
        height: dp(26)

    RecycleView:
        id: rv
        viewclass: "PluRow"
        scroll_type: ["bars", "content"]
        bar_width: dp(8)
        RecycleBoxLayout:
            default_size: None, dp(44)
            default_size_hint: 1, None
            size_hint_y: None
            height: self.minimum_height
            orientation: "vertical"
            spacing: dp(6)
"""


def asset_path(filename: str) -> str:
    """
    Devuelve ruta del asset tanto en PC como dentro del APK.
    Primero intenta resource_find(), si no, cae al mismo directorio del script.
    """
    p = resource_find(filename)
    if p:
        return p
    return os.path.join(os.path.dirname(__file__), filename)


def read_catalog(csv_path: str):
    """
    Lee csv tipo: codigo,nombre
    Intenta detectar delimitador (coma/punto y coma).
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"No se encontró el archivo: {csv_path}")

    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        sample = f.read(4096)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=";,")
        except Exception:
            dialect = csv.excel
            dialect.delimiter = ","

        reader = csv.DictReader(f, dialect=dialect)
        rows = []
        for r in reader:
            # Soporta headers "codigo" / "nombre" (y variantes)
            codigo = (r.get("codigo") or r.get("Código") or r.get("CODIGO") or "").strip()
            nombre = (r.get("nombre") or r.get("Nombre") or r.get("NOMBRE") or "").strip()
            if codigo or nombre:
                rows.append({"codigo": codigo, "nombre": nombre})
        return rows


class PluApp(App):
    catalog = ListProperty([])
    filtered = ListProperty([])
    selected_index = NumericProperty(-1)
    status_text = StringProperty("")

    def build(self):
        self.title = "PLU_APP"
        root = Builder.load_string(KV)

        # Cargar CSV
        try:
            csv_file = asset_path("plu_catalogo.csv")
            self.catalog = read_catalog(csv_file)
            self.filtered = list(self.catalog)
            self._refresh_rv()
            self.status_text = f"Catálogo cargado: {len(self.catalog)} items"
        except Exception as e:
            self.catalog = []
            self.filtered = []
            self._refresh_rv()
            self.status_text = "No se pudo cargar el catálogo."
            self._popup("Error cargando CSV", str(e))

        return root

    def _refresh_rv(self):
        rv = self.root.ids.rv
        data = []
        # Limita un poco para que no se ponga pesado si el csv es enorme
        max_items = 400
        for i, item in enumerate(self.filtered[:max_items]):
            texto = f"{item['codigo']} — {item['nombre']}"
            data.append({"text": texto, "index": i})
        rv.data = data

        if len(self.filtered) > max_items:
            self.status_text = f"Mostrando {max_items} de {len(self.filtered)} resultados (filtra más)."
        elif self.catalog:
            self.status_text = f"Resultados: {len(self.filtered)} / {len(self.catalog)}"
        else:
            self.status_text = "Sin datos."

    def apply_filter(self, text: str):
        t = (text or "").strip().lower()
        if not t:
            self.filtered = list(self.catalog)
        else:
            self.filtered = [
                x for x in self.catalog
                if t in (x["codigo"] or "").lower() or t in (x["nombre"] or "").lower()
            ]
        self.selected_index = -1
        self._refresh_rv()

    def select_index(self, idx: int):
        self.selected_index = idx
        try:
            item = self.filtered[idx]
            self.status_text = f"Seleccionado: {item['codigo']} — {item['nombre']}"
        except Exception:
            self.status_text = "Selección inválida."

    def copy_selected(self):
        if self.selected_index < 0 or self.selected_index >= len(self.filtered):
            self._popup("Copiar", "Primero selecciona un item de la lista.")
            return
        item = self.filtered[self.selected_index]
        Clipboard.copy(item["codigo"])
        self._popup("Copiado", f"Copiado al portapapeles: {item['codigo']}")

    def export_excel(self):
        if not self.catalog:
            self._popup("Exportar", "No hay datos para exportar.")
            return

        try:
            wb = Workbook()
            ws = wb.active
            ws.title = "PLU"

            # Encabezados
            ws["A1"] = "codigo"
            ws["B1"] = "nombre"
            bold = Font(bold=True)
            ws["A1"].font = bold
            ws["B1"].font = bold
            ws["A1"].alignment = Alignment(horizontal="center")
            ws["B1"].alignment = Alignment(horizontal="center")

            # Datos
            for r, item in enumerate(self.catalog, start=2):
                ws.cell(row=r, column=1, value=item["codigo"])
                ws.cell(row=r, column=2, value=item["nombre"])

            # Ajuste simple de ancho
            ws.column_dimensions["A"].width = 16
            ws.column_dimensions["B"].width = 60

            # Guardar (Android: user_data_dir funciona seguro)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            out_name = f"plu_catalogo_{ts}.xlsx"
            out_path = os.path.join(self.user_data_dir, out_name)
            wb.save(out_path)

            self._popup("Exportado", f"Excel guardado en:\n{out_path}")
        except Exception as e:
            self._popup("Error exportando", str(e))

    def _popup(self, title: str, msg: str):
        Popup(
            title=title,
            content=Label(text=msg),
            size_hint=(0.88, 0.45),
        ).open()


if __name__ == "__main__":
    PluApp().run()


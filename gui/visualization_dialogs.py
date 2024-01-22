from PyQt5.QtWidgets import QVBoxLayout, QLineEdit, QDialog, QComboBox, QPushButton, \
    QFormLayout, QHBoxLayout, QFileDialog, QProgressBar, QMessageBox, QLabel

from osm_data.import_osm_data_geojson import build_query, download_data, save_to_file
from gui.threads import GeocodingThread
from geocoding.geocodingETRS89 import get_coordinates, process_data
   
class LayerGenerationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        # Formularlayout für Eingaben
        formLayout = QFormLayout()

        # Eingabefelder für Dateipfade und Koordinaten
        self.streetLayerInput, self.streetLayerButton = self.createFileInput("net_generation_QGIS/Straßen Zittau.geojson")
        self.dataCsvInput, self.dataCsvButton = self.createFileInput("geocoding/data_output_zi_ETRS89.csv")

        # Auswahlmodus für Erzeugerstandort
        self.locationModeComboBox = QComboBox(self)
        self.locationModeComboBox.addItems(["Koordinaten direkt eingeben", "Adresse eingeben", "Koordinaten aus CSV laden"])
        self.locationModeComboBox.currentIndexChanged.connect(self.toggleLocationInputMode)

        self.xCoordInput = QLineEdit("486267.306999999971595", self)
        self.yCoordInput = QLineEdit("5637294.910000000149012", self)
        self.countryInput = QLineEdit(self)
        self.countryInput.setPlaceholderText("Land")
        self.countryInput.setEnabled(False)
        self.stateInput = QLineEdit(self)
        self.stateInput.setPlaceholderText("Bundesland")
        self.stateInput.setEnabled(False)
        self.cityInput = QLineEdit(self)
        self.cityInput.setPlaceholderText("Stadt")
        self.cityInput.setEnabled(False)
        self.streetInput = QLineEdit(self)
        self.streetInput.setPlaceholderText("Straße und Hausnummer")
        self.streetInput.setEnabled(False)
        self.coordsCsvInput, self.coordsCsvButton = self.createFileInput("Pfad/zu/Koordinaten.csv")
        self.coordsCsvInput.setEnabled(False)
        self.coordsCsvButton.setEnabled(False)

        # Buttons
        self.geocodeButton = QPushButton("Adresse geocodieren", self)
        self.geocodeButton.clicked.connect(self.geocodeAddress)
        self.geocodeButton.setEnabled(False)
        self.loadCoordsButton = QPushButton("Koordinaten aus csv laden", self)
        self.loadCoordsButton.clicked.connect(self.loadCoordsFromCSV)
        self.loadCoordsButton.setEnabled(False)

        # Hinzufügen von Widgets zum Formularlayout
        formLayout.addRow("GeoJSON-Straßen-Layer:", self.createFileInputLayout(self.streetLayerInput, self.streetLayerButton))
        formLayout.addRow("CSV mit Gebäudestandorten:", self.createFileInputLayout(self.dataCsvInput, self.dataCsvButton))
        formLayout.addRow("Modus für Erzeugerstandort:", self.locationModeComboBox)
        formLayout.addRow("X-Koordinate Erzeugerstandort:", self.xCoordInput)
        formLayout.addRow("Y-Koordinate Erzeugerstandort:", self.yCoordInput)
        formLayout.addRow("Land:", self.countryInput)
        formLayout.addRow("Bundesland:", self.stateInput)
        formLayout.addRow("Stadt:", self.cityInput)
        formLayout.addRow("Straße:", self.streetInput)
        formLayout.addRow(self.geocodeButton)
        formLayout.addRow("CSV mit Koordinaten:", self.createFileInputLayout(self.coordsCsvInput, self.coordsCsvButton))
        formLayout.addRow(self.loadCoordsButton)

        layout.addLayout(formLayout)

        # OK und Abbrechen Buttons
        self.okButton = QPushButton("OK", self)
        self.okButton.clicked.connect(self.accept)
        self.cancelButton = QPushButton("Abbrechen", self)
        self.cancelButton.clicked.connect(self.reject)

        layout.addWidget(self.okButton)
        layout.addWidget(self.cancelButton)

        self.setLayout(layout)

    def toggleLocationInputMode(self, index):
        self.xCoordInput.setEnabled(index == 0)
        self.yCoordInput.setEnabled(index == 0)
        self.countryInput.setEnabled(index == 1)
        self.stateInput.setEnabled(index == 1)
        self.cityInput.setEnabled(index == 1)
        self.streetInput.setEnabled(index == 1)
        self.coordsCsvInput.setEnabled(index == 2)
        self.coordsCsvButton.setEnabled(index == 2)
        self.geocodeButton.setEnabled(index == 1)
        self.loadCoordsButton.setEnabled(index == 2)

    def geocodeAddress(self):
        # Zusammensetzen der vollständigen Adresse aus den einzelnen Feldern
        address = f"{self.streetInput.text()}, {self.cityInput.text()}, {self.stateInput.text()}, {self.countryInput.text()}"
        if address.strip(", ").replace(" ", ""):
            utm_x, utm_y = get_coordinates(address)
            if utm_x and utm_y:
                self.xCoordInput.setText(str(utm_x))
                self.yCoordInput.setText(str(utm_y))
            else:
                QMessageBox.warning(self, "Warnung", "Adresse konnte nicht geocodiert werden.")
        else:
            QMessageBox.warning(self, "Warnung", "Bitte geben Sie eine vollständige Adresse ein.")

    def loadCoordsFromCSV(self):
        csv_file_path = self.coordsCsvInput.text()
        if csv_file_path:
            try:
                process_data(csv_file_path, "temporary_output.csv")
                QMessageBox.information(self, "Info", "Koordinaten wurden geladen und in 'temporary_output.csv' gespeichert.")
            except Exception as e:
                QMessageBox.critical(self, "Fehler", f"Ein Fehler ist aufgetreten: {e}")
        else:
            QMessageBox.warning(self, "Warnung", "Bitte wählen Sie eine CSV-Datei aus.")

    def createFileInput(self, default_path):
        lineEdit = QLineEdit(default_path)
        button = QPushButton("Durchsuchen")
        button.clicked.connect(lambda: self.openFileDialog(lineEdit))
        return lineEdit, button

    def openFileDialog(self, lineEdit):
        filename, _ = QFileDialog.getOpenFileName(self, "Datei auswählen", "", "All Files (*)")
        if filename:
            lineEdit.setText(filename)

    def createFileInputLayout(self, lineEdit, button):
        layout = QHBoxLayout()
        layout.addWidget(lineEdit)
        layout.addWidget(button)
        return layout

    def getInputs(self):
        return {
            "streetLayer": self.streetLayerInput.text(),
            "dataCsv": self.dataCsvInput.text(),
            "xCoord": self.xCoordInput.text(),
            "yCoord": self.yCoordInput.text()
        }


class DownloadOSMDataDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tags_to_download = []
        self.standard_tags = [
            {"highway": "primary"},
            {"highway": "secondary"},
            {"highway": "tertiary"},
            {"highway": "residential"}
        ]
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Download OSM-Data")
        layout = QVBoxLayout(self)

        # Postleitzahl Eingabefeld
        #self.postalCodeLineEdit = QLineEdit(self)
        #self.postalCodeLineEdit.setPlaceholderText("Postleitzahl")
        #layout.addWidget(QLabel("Postleitzahl:"))
        #layout.addWidget(self.postalCodeLineEdit)

        # Stadtname Eingabefeld
        self.cityLineEdit = QLineEdit("Zittau")
        layout.addWidget(self.cityLineEdit)
        
        # Dateiname Eingabefeld
        self.filenameLineEdit, fileButton = self.createFileInput("osm_data/osm_data.geojson")
        layout.addLayout(self.createFileInputLayout(self.filenameLineEdit, fileButton))

        # Dropdown-Menü für einzelne Standard-Tags
        self.standardTagsComboBox = QComboBox(self)
        for tag in self.standard_tags:
            key = next(iter(tag))
            value = tag[key]
            self.standardTagsComboBox.addItem(f"{key}: {value}")

        # Button zum Laden eines ausgewählten Standard-Tags
        self.loadStandardTagButton = QPushButton("Standard-Tag hinzufügen", self)
        self.loadStandardTagButton.clicked.connect(self.loadSelectedStandardTag)
        layout.addWidget(self.standardTagsComboBox)
        layout.addWidget(self.loadStandardTagButton)

        # Tags-Auswahl
        self.tagsLayout = QFormLayout()
        layout.addLayout(self.tagsLayout)
        
        # Buttons zum Hinzufügen/Entfernen von Tags
        self.addTagButton = QPushButton("Tag hinzufügen", self)
        self.addTagButton.clicked.connect(self.addTagField)
        layout.addWidget(self.addTagButton)

        self.removeTagButton = QPushButton("Tag entfernen", self)
        self.removeTagButton.clicked.connect(self.removeTagField)
        layout.addWidget(self.removeTagButton)

        # Abfrage-Button
        self.queryButton = QPushButton("Abfrage starten", self)
        self.queryButton.clicked.connect(self.startQuery)
        layout.addWidget(self.queryButton)
        
        # Buttons für OK und Abbrechen
        self.okButton = QPushButton("OK", self)
        self.okButton.clicked.connect(self.accept)
        layout.addWidget(self.okButton)

        self.cancelButton = QPushButton("Abbrechen", self)
        layout.addWidget(self.cancelButton)

    def createFileInput(self, default_path):
        lineEdit = QLineEdit(default_path)
        button = QPushButton("Durchsuchen")
        button.clicked.connect(lambda: self.selectFile(lineEdit))
        return lineEdit, button

    def createFileInputLayout(self, lineEdit, button):
        layout = QHBoxLayout()
        layout.addWidget(lineEdit)
        layout.addWidget(button)
        return layout

    def selectFile(self, lineEdit):
        filename, _ = QFileDialog.getOpenFileName(self, "Datei auswählen", "", "All Files (*)")
        if filename:
            lineEdit.setText(filename)

    def addTagField(self, key="", value=""):
        # Sicherstellen, dass key und value immer Strings sind
        key = str(key) if key is not None else ""
        value = str(value) if value is not None else ""

        keyLineEdit = QLineEdit(key)
        valueLineEdit = QLineEdit(value)
        self.tagsLayout.addRow(keyLineEdit, valueLineEdit)
        self.tags_to_download.append((keyLineEdit, valueLineEdit))

    def removeTagField(self):
        if self.tags_to_download:
            keyLineEdit, valueLineEdit = self.tags_to_download.pop()
            self.tagsLayout.removeRow(keyLineEdit)

    def loadAllStandardTags(self):
        for tag in self.standard_tags:
            key = next(iter(tag))
            value = tag[key]
            self.addTagField(key, value)

    def loadSelectedStandardTag(self):
        selected_tag_index = self.standardTagsComboBox.currentIndex()
        tag = self.standard_tags[selected_tag_index]
        key = next(iter(tag))
        value = tag[key]
        self.addTagField(key, value)
    
    def startQuery(self):
        # Daten sammeln
        #postal_code = self.postalCodeLineEdit.text()
        self.filename = self.filenameLineEdit.text()
        tags = {key.text(): value.text() for key, value in self.tags_to_download if key.text()}
        
        city_name =self.cityLineEdit.text()

        # Erstelle die Overpass-Abfrage
        query = build_query(city_name, tags, element_type="way")
        # Lade die Daten herunter
        geojson_data = download_data(query, element_type="way")
        # Speichere die Daten als GeoJSON
        save_to_file(geojson_data, self.filename)

        QMessageBox.information(self, "Erfolg", f"Abfrageergebnisse gespeichert in {self.filename}")
            
        # Rufen Sie die loadNetData-Methode des Haupt-Tabs auf
        self.parent().loadNetData(self.filename)

class OSMBuildingQueryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        self.setWindowTitle("OSM Gebäudeabfrage")

        # Postleitzahl Eingabefeld
        #self.postalCodeLineEdit = QLineEdit(self)
        #self.postalCodeLineEdit.setPlaceholderText("Postleitzahl")
        #layout.addWidget(QLabel("Postleitzahl:"))
        #layout.addWidget(self.postalCodeLineEdit)

        # Stadtname Eingabefeld
        self.cityLineEdit = QLineEdit(self)
        layout.addWidget(QLabel("Stadtname:"))
        layout.addWidget(self.cityLineEdit)

        # Dateiname Eingabefeld
        self.filenameLineEdit = QLineEdit("osm_data/output_buildings.geojson", self)
        layout.addWidget(QLabel("Ausgabedatei:"))
        layout.addWidget(self.filenameLineEdit)

        # Koordinaten Eingabefelder
        self.minLatLineEdit = QLineEdit(self)
        self.minLatLineEdit.setPlaceholderText("Optional: Minimale Breite")
        layout.addWidget(QLabel("Minimale Breite:"))
        layout.addWidget(self.minLatLineEdit)

        self.minLonLineEdit = QLineEdit(self)
        self.minLonLineEdit.setPlaceholderText("Optional: Minimale Länge")
        layout.addWidget(QLabel("Minimale Länge:"))
        layout.addWidget(self.minLonLineEdit)

        self.maxLatLineEdit = QLineEdit(self)
        self.maxLatLineEdit.setPlaceholderText("Optional: Maximale Breite")
        layout.addWidget(QLabel("Maximale Breite:"))
        layout.addWidget(self.maxLatLineEdit)

        self.maxLonLineEdit = QLineEdit(self)
        self.maxLonLineEdit.setPlaceholderText("Optional: Maximale Länge")
        layout.addWidget(QLabel("Maximale Länge:"))
        layout.addWidget(self.maxLonLineEdit)

        # Abfrage-Button
        self.queryButton = QPushButton("Abfrage starten", self)
        self.queryButton.clicked.connect(self.startQuery)
        layout.addWidget(self.queryButton)

        # OK und Abbrechen Buttons
        self.okButton = QPushButton("OK", self)
        self.okButton.clicked.connect(self.accept)
        layout.addWidget(self.okButton)
        self.cancelButton = QPushButton("Abbrechen", self)
        self.cancelButton.clicked.connect(self.reject)
        layout.addWidget(self.cancelButton)

    def startQuery(self):
        #postal_code = self.postalCodeLineEdit.text()
        city_name = self.cityLineEdit.text()
        filename = self.filenameLineEdit.text()
        if city_name and filename:
            # Führen Sie hier Ihre Abfrage-Logik durch
            tags = {"building": "yes"}  # oder andere Tags
            query = build_query(city_name, tags, element_type="building")
            geojson_data = download_data(query, element_type="building")

            min_lat = self.minLatLineEdit.text() #51.054091
            min_lon = self.minLonLineEdit.text() #14.549694
            max_lat = self.maxLatLineEdit.text() #51.070836
            max_lon = self.maxLonLineEdit.text() #14.589713

            if min_lat and min_lon and max_lat and max_lon:
                geojson_data = self.filter_geojson_data(geojson_data, min_lat, min_lon, max_lat, max_lon)

            save_to_file(geojson_data, filename)
            QMessageBox.information(self, "Erfolg", f"Abfrageergebnisse gespeichert in {filename}")
            
            # Rufen Sie die loadNetData-Methode des Haupt-Tabs auf
            self.parent().loadNetData(filename)
        else:
            QMessageBox.warning(self, "Warnung", "Bitte geben Sie Postleitzahl, Stadtname und Ausgabedatei an.")

    def filter_geojson_data(self, geojson_data, min_lat, min_lon, max_lat, max_lon):
        min_lat, min_lon, max_lat, max_lon = map(float, [min_lat, min_lon, max_lat, max_lon])

        def is_within_bounds(lat, lon):
            return min_lon <= lon <= max_lon and min_lat <= lat <= max_lat

        def is_polygon_within_bounds(polygon):
            # Überprüfen, ob irgendein Punkt des Polygons innerhalb der Grenzen liegt
            for ring in polygon:
                if any(is_within_bounds(lat, lon) for lon, lat in ring):
                    return True
            return False

        filtered_features = []
        for feature in geojson_data['features']:
            geometry = feature['geometry']
            if geometry['type'] == 'Polygon':
                if is_polygon_within_bounds(geometry['coordinates']):
                    filtered_features.append(feature)
            elif geometry['type'] == 'MultiPolygon':
                if any(is_polygon_within_bounds(polygon) for polygon in geometry['coordinates']):
                    filtered_features.append(feature)

        # Erstelle ein neues GeoJSON-Objekt mit den gefilterten Features
        filtered_geojson = {
            "type": "FeatureCollection",
            "features": filtered_features
        }
        return filtered_geojson

class GeocodeAdressesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Adressdaten geocodieren")

        layout = QVBoxLayout(self)

        # Stadtname Eingabefeld
        self.inputfilenameLineEdit, fileButton = self.createFileInput("geocoding/data_input_zi.csv")
        layout.addLayout(self.createFileInputLayout(self.inputfilenameLineEdit, fileButton))
        
        # Dateiname Eingabefeld
        self.outputfilenameLineEdit, fileButton = self.createFileInput("geocoding/data_output_zi_ETRS89.csv")
        layout.addLayout(self.createFileInputLayout(self.outputfilenameLineEdit, fileButton))
        
        # Buttons für OK und Abbrechen
        self.okButton = QPushButton("OK", self)
        self.okButton.clicked.connect(self.onAccept)
        self.cancelButton = QPushButton("Abbrechen", self)
        self.cancelButton.clicked.connect(self.reject)
        
        layout.addWidget(self.okButton)
        layout.addWidget(self.cancelButton)

        self.progressBar = QProgressBar(self)
        layout.addWidget(self.progressBar)

    def createFileInput(self, default_path):
        lineEdit = QLineEdit(default_path)
        button = QPushButton("Durchsuchen")
        button.clicked.connect(lambda: self.selectFile(lineEdit))
        return lineEdit, button

    def createFileInputLayout(self, lineEdit, button):
        layout = QHBoxLayout()
        layout.addWidget(lineEdit)
        layout.addWidget(button)
        return layout

    def selectFile(self, lineEdit):
        filename, _ = QFileDialog.getOpenFileName(self, "Datei auswählen", "", "All Files (*)")
        if filename:
            lineEdit.setText(filename)

    def onAccept(self):
        # Daten sammeln
        self.inputfilename = self.inputfilenameLineEdit.text()
        self.outputfilename = self.outputfilenameLineEdit.text()
        
        # Abfrage erstellen und Daten herunterladen
        self.geocodeAdresses(self.inputfilename, self.outputfilename)

    # Die Methode des Dialogs, die die anderen Funktionen aufruft
    def geocodeAdresses(self, inputfilename, outputfilename):
        # Stellen Sie sicher, dass der vorherige Thread beendet wird
        if hasattr(self, 'geocodingThread') and self.geocodingThread.isRunning():
            self.geocodingThread.terminate()
            self.geocodingThread.wait()
        self.geocodingThread = GeocodingThread(inputfilename, outputfilename)
        self.geocodingThread.calculation_done.connect(self.on_generation_done)
        self.geocodingThread.calculation_error.connect(self.on_generation_error)
        self.geocodingThread.start()
        self.progressBar.setRange(0, 0)  # Aktiviert den indeterministischen Modus

    def on_generation_done(self, results):
        self.accept()

    def on_generation_error(self, error_message):
        QMessageBox.critical(self, "Fehler beim Geocoding", error_message)
        self.progressBar.setRange(0, 1)  # Deaktiviert den indeterministischen Modus
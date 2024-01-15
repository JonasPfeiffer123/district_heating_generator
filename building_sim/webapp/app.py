from flask import Flask, render_template, request, jsonify
import heat_requirement_BDEW
import numpy as np

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        data = request.json
        JEB_Wärme_ges_kWh = float(data['JEB_Wärme_ges_kWh'])
        building_type = data['building_type']

        # Hier würden Sie die gleiche Logik wie in Ihrer PyQt5-App verwenden
        # Beispiel:
        time_steps, waerme_ges_kW, hourly_temperatures = heat_requirement_BDEW.calculate(JEB_Wärme_ges_kWh, building_type, subtyp="03")

        # Konvertieren Sie die Daten in ein Format, das an das Frontend gesendet werden kann
        result = {
            "time_steps": time_steps.tolist(),
            "waerme_ges_kW": waerme_ges_kW.tolist(),
            "hourly_temperatures": hourly_temperatures.tolist()
        }

        return jsonify(result)
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@app.route('/calculate_cop', methods=['POST'])
def calculate_cop():
    try:
        data = request.json
        QT = float(data['quelltemperatur'])
        HT = float(data['heiztemperatur'])

        # Verhindern Sie eine Division durch Null, wenn HT und QT gleich sind
        if HT == QT:
            return jsonify({'error': 'Heiztemperatur und Quelltemperatur dürfen nicht gleich sein'}), 400

        COP_id = (HT + 273.15) / (HT - QT)
        COP = COP_id * 0.6  # Anpassen Sie diese Formel nach Bedarf
        return jsonify({'cop': COP})
    
    except (ValueError, ZeroDivisionError) as e:
        return jsonify({'error': str(e)}), 400

# Ihre spezifische Logikfunktionen (können Sie nach Ihren Anforderungen anpassen)
def calculate_cop_and_stromverbrauch(heiztemperatur, waermequelle, erdreich_temperatur):
    # Beispiel-Berechnung (Bitte ersetzen Sie dies durch Ihre eigentliche Berechnung)
    if waermequelle == 'Erdreich':
        cop = heiztemperatur / erdreich_temperatur
    else:
        cop = heiztemperatur / 5  # Angenommener Wert für Luft als Wärmequelle

    stromverbrauch = 10000 / cop  # Angenommener Wert für Stromverbrauch

    # Generieren von beispielhaften Zeitstempeln und weiteren Werten
    time_steps = np.arange('2021-01', '2022-01', dtype='datetime64[M]')
    weitere_werte = np.random.rand(len(time_steps)) * 10  # Zufällige Werte

    return cop, stromverbrauch, time_steps.tolist(), weitere_werte.tolist()

@app.route('/calculate_heatgen', methods=['POST'])
def calculate_heatgen():
    try:
        data = request.json
        heiztemperatur = float(data['heiztemperatur'])
        waermequelle = data['waermequelle']
        erdreich_temperatur = float(data['erdreich_temperatur']) if waermequelle == 'Erdreich' else None
        JEB_Wärme_ges_kWh = float(data['JEB_Wärme_ges_kWh'])
        building_type = data['building_type']
        
        cop, stromverbrauch, time_steps, weitere_werte = calculate_cop_and_stromverbrauch(heiztemperatur, waermequelle, erdreich_temperatur)

        result = {
            "cop": cop,
            "stromverbrauch": stromverbrauch,
            "time_steps": time_steps,
            "weitere_werte": weitere_werte
        }

        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    
if __name__ == '__main__':
    app.run(debug=True, port=8000)

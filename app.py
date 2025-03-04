from flask import Flask, render_template, request, jsonify
from collections import Counter
from decimal import Decimal, ROUND_DOWN, getcontext
import math

app = Flask(__name__)

getcontext().prec = 28
TWO_PLACES = Decimal('0.01')


def round_decimal(value):
    return Decimal(str(value)).quantize(TWO_PLACES, rounding=ROUND_DOWN)


def moda(tabla, r):
    max_fi = max(tabla, key=lambda row: row[2])[2]
    for x in range(len(tabla)):
        if tabla[x][2] == max_fi:
            if x > 0:
                fiMenosUno = tabla[x - 1][2]
            else:
                fiMenosUno = 0
            if x < len(tabla) - 1:
                fiMasUno = tabla[x + 1][2]
            else:
                fiMasUno = 0
            datos = [max_fi, round_decimal(tabla[x][0][0]), fiMenosUno, round_decimal(fiMasUno)]
    operacion1 = datos[1]
    operacion2 = (datos[0] - datos[2]) / ((datos[0] - datos[2]) + (datos[0] - datos[3]))
    operacion2 = round_decimal(operacion2)
    operacionFinal = operacion1 + operacion2 * r
    return operacionFinal


def datosMediana(n, array, r):
    preLimiteInferior = round_decimal(n / Decimal('2'))
    for x in range(len(array)):
        if array[x][4] >= preLimiteInferior:
            return [array[x][0][0], array[x - 1][4], array[x][2], n, r]


def calcularMediana(limInferior, Fj, fi, n, r):
    n = round_decimal(n / Decimal('2'))
    result = limInferior + round_decimal((n - Fj) / fi) * r
    return round_decimal(result)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/calculate', methods=['POST'])
def calculate():
    data = request.json
    lista = data['lista']
    cuenta = Counter(lista)
    n = round_decimal(len(lista))
    xmax = max(lista)
    xmin = min(lista)
    amplitud = xmax - xmin
    amplitud = round_decimal(amplitud)
    k = (1 + 3.322 * math.log(n, 10))
    if int(k) % 2 == 0:
        k = int(k - 1)
    else:
        k = int(k)
    r = math.ceil(amplitud / k)
    base = min(lista)
    Fi = 0
    sumaXifi = 0
    arrayFi = []
    tabla = []

    for i in range(k):
        fila = []
        fi = 0
        rango = [base, base + r]
        fila.append(rango)
        xi = (base + (base + r)) / 2
        xi = round_decimal(xi)
        fila.append(xi)
        for x, y in cuenta.items():
            if x >= base and x < (base + r):
                fi += y
            fi = round_decimal(fi)
        fila.append(fi)
        xifi = xi * fi
        xifi = round_decimal(xifi)
        fila.append(xifi)
        sumaXifi += xifi
        Fi += fi
        arrayFi.append(round_decimal(Fi))
        fila.append(round_decimal(Fi))
        fr = float(fi) / float(n) * 100
        fr = round_decimal(fr)
        fila.append(fr)
        grados = fr * 360 / 100
        grados = round_decimal(grados)
        fila.append(grados)
        tabla.append(fila)
        fi = 0
        base += r

    media = sumaXifi / n
    media = round_decimal(media)
    sumaFinal = 0

    # Create a formatted table for JSON
    table_data = []

    for x in range(k):
        operacion = (tabla[x][1] - media) ** 2
        operacion = round_decimal(operacion)
        tabla[x].append(operacion)
        operacion2 = operacion * tabla[x][2]
        operacion2 = round_decimal(operacion2)
        tabla[x].append(operacion2)
        sumaFinal += operacion2

        # Build table row
        row = {
            "rango": [str(tabla[x][0][0]), str(tabla[x][0][1])],
            "xi": str(tabla[x][1]),
            "fi": str(tabla[x][2]),
            "xi*fi": str(tabla[x][3]),
            "Fi": str(tabla[x][4]),
            "fr%": str(tabla[x][5]),
            "grados": str(tabla[x][6]),
            "(xi-media)^2": str(tabla[x][7]),
            "(xi-media)^2*fi": str(tabla[x][8])
        }
        table_data.append(row)

    poblacion = sumaFinal / n
    poblacion = round_decimal(poblacion)
    poblacion_raiz = round_decimal(Decimal(str(poblacion)).sqrt())
    cv = (poblacion_raiz / media) * 100
    cv = round_decimal(cv)

    try:
        mediana = datosMediana(n, tabla, r)
        mediana = calcularMediana(mediana[0], mediana[1], mediana[2], mediana[3], mediana[4])
    except Exception as e:
        mediana = "Error calculating median: " + str(e)

    try:
        moda_value = moda(tabla, r)
    except Exception as e:
        moda_value = "Error calculating mode: " + str(e)

    return jsonify({
        'basic_stats': {
            'N': str(n),
            'Xmax': str(xmax),
            'Xmin': str(xmin),
            'amplitud': str(amplitud),
            'intervalo': str(k),
            'rango': str(r)
        },
        'calculated_values': {
            'Σ(Xi*fi)': str(sumaXifi),
            'Σ(xi - media)^2 * fi': str(sumaFinal),
            'media': str(media),
            'poblacion': str(poblacion_raiz),
            'coeficiente_variacion': str(cv),
            'mediana': str(mediana),
            'moda': str(moda_value)
        },
        'table': table_data
    })


if __name__ == '__main__':
    app.run(debug=True)
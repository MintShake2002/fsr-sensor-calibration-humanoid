import time
import serial
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# =============================================================================
# CONFIGURACIÓN INICIAL
# =============================================================================
PUERTO_COM = 'COM4'  # Cambia esto al puerto correcto que diga en el IDE de Arduino
BAUD_RATE = 115200  # Coincide con SerialUSB.begin(115200) del Arduino
ARCHIVO_CSV = 'calibracion_fsr_dinamometro.csv'

lista_adc = []
lista_fuerza = []

print("=== SCRIPT DE CALIBRACIÓN CON DINAMÓMETRO Y TEMPLADOR ===")
print(f"Conectando a {PUERTO_COM} a {BAUD_RATE} baudios...")

try:
    arduino = serial.Serial(PUERTO_COM, BAUD_RATE, timeout=0.1)
    time.sleep(2)  # Tiempo para estabilizar la apertura de la conexión
    print("Conexión serial establecida con éxito.\n")
except Exception as e:
    print(f"Error fatal al abrir el puerto serial: {e}")
    exit()

# =============================================================================
# BUCLE DE CAPTURA DE DATOS INTERACTIVO
# =============================================================================
try:
    while True:
        entrada = input(
            "Ingrese la fuerza leída en el dinamómetro en Newtons (o escriba 'salir' para finalizar): ").strip().lower()

        if entrada == 'salir':
            print("\nFinalizando captura de datos...")
            break

        # Validación de entrada numérica
        try:
            fuerza_newtons = float(entrada)
        except ValueError:
            print("❌ Entrada no válida. Por favor, ingrese un número decimal o escriba 'salir'.\n")
            continue

        # Pausa recomendada tras ajustar la tensión con el templador
        print("Estabilizando tensión en el tendón...")
        time.sleep(0.5)

        # Limpiamos el buffer serial para descartar lecturas tomadas mientras se giraba el templador
        arduino.reset_input_buffer()
        print("Capturando lecturas de 'fsr2' durante 2 segundos...")

        lecturas_crudas = []
        tiempo_inicio = time.time()

        while time.time() - tiempo_inicio < 2.0:
            if arduino.in_waiting > 0:
                linea = arduino.readline().decode('utf-8', errors='ignore').strip()
                if linea:
                    datos = linea.split(',')
                    # Validamos que la trama tenga al menos 9 valores
                    if len(datos) >= 9:
                        try:
                            # Extraemos fsr2 (último elemento de la trama)
                            valor_adc = int(datos[-1].strip())

                            # Si en lugar de fsr2 quisieras calibrar fsr1, usas: datos[-2]
                            if valor_adc >= 0:
                                lecturas_crudas.append(valor_adc)
                        except ValueError:
                            # Ignora lecturas incompletas o erróneas
                            continue

        if len(lecturas_crudas) > 0:
            adc_promedio = sum(lecturas_crudas) / len(lecturas_crudas)
            lista_fuerza.append(fuerza_newtons)
            lista_adc.append(adc_promedio)

            print(
                f"✅ Punto registrado -> Fuerza: {fuerza_newtons:.2f} N | ADC Promedio (fsr2): {adc_promedio:.2f} (de {len(lecturas_crudas)} muestras)\n")
        else:
            print("⚠️ No se recibieron tramas válidas del Arduino. Verifica la comunicación serial.\n")

finally:
    arduino.close()
    print("Puerto serial cerrado.")

# =============================================================================
# ANÁLISIS Y REGRESIÓN MATEMÁTICA (ALTA PRECISIÓN POLINOMIAL)
# =============================================================================
# Subimos el requerimiento a 5 puntos mínimos para evitar que el ajuste matemático falle
if len(lista_adc) < 5:
    print("\n❌ Se necesitan al menos 5 puntos de medición para calcular curvas polinomiales avanzadas. Saliendo.")
    exit()

X = np.array(lista_adc)  # Variable independiente: ADC (fsr2)
Y = np.array(lista_fuerza)  # Variable dependiente: Fuerza (N)

# Ajuste Polinomial de 3er Grado (Cúbico): y = ax^3 + bx^2 + cx + d
coef_cubico = np.polyfit(X, Y, 3)
a3, b3, c3, d3 = coef_cubico

# Ajuste Polinomial de 4to Grado (Cuártico): y = ax^4 + bx^3 + cx^2 + dx + e
coef_cuartico = np.polyfit(X, Y, 4)
a4, b4, c4, d4, e4 = coef_cuartico

print("\n" + "=" * 80)
print("ECUACIONES DE CALIBRACIÓN PARA EL FIRMWARE (ESP32 / ROBOT WALTER)")
print("Nota: Se usa multiplicación directa en lugar de pow() para ahorrar ciclos de reloj.")
print("=" * 80)
print("float f_raw = (float)fsr2; // Variable auxiliar para facilitar la lectura\n")

print("// Opción 1: Ajuste Cúbico (3er Grado)")
print(f"float fuerza_N = ({a3:.15f} * f_raw * f_raw * f_raw) + ({b3:.12f} * f_raw * f_raw) + ({c3:.8f} * f_raw) + ({d3:.8f});\n")

print("// Opción 2: Ajuste Cuártico (4to Grado) -> Más apegado a la ruta de los puntos")
print(f"float fuerza_N = ({a4:.18f} * f_raw * f_raw * f_raw * f_raw) + ({b4:.15f} * f_raw * f_raw * f_raw) + ({c4:.12f} * f_raw * f_raw) + ({d4:.8f} * f_raw) + ({e4:.8f});")
print("=" * 80 + "\n")

# =============================================================================
# ALMACENAMIENTO Y VISUALIZACIÓN
# =============================================================================
# Guardar en archivo CSV
df = pd.DataFrame({
    'ADC_fsr2_Promedio': X,
    'Fuerza_Newtons': Y
})
df.to_csv(ARCHIVO_CSV, index=False)
print(f"💾 Datos guardados exitosamente en '{ARCHIVO_CSV}'.")

# Generar puntos de la curva ajustada para la gráfica
x_grafica = np.linspace(min(X) - 50, max(X) + 50, 500)
x_grafica = np.clip(x_grafica, 0, 4095)

y_cubico = np.polyval(coef_cubico, x_grafica)
y_cuartico = np.polyval(coef_cuartico, x_grafica)

# Configuración de Matplotlib
plt.figure(figsize=(10, 6))
plt.scatter(X, Y, color='red', zorder=5, label='Puntos Reales (Dinamómetro)', s=50)

# Dibujamos las nuevas curvas
plt.plot(x_grafica, y_cubico, '--', color='blue', label='Ajuste Cúbico (Grado 3)', linewidth=2)
plt.plot(x_grafica, y_cuartico, '-', color='green', label='Ajuste Cuártico (Grado 4)', linewidth=2)

plt.title('Calibración FSR - Ajuste Polinomial No Lineal', fontsize=14)
plt.xlabel('Lectura Analógica ADC (fsr2)', fontsize=12)
plt.ylabel('Fuerza (Newtons)', fontsize=12)
plt.grid(True, linestyle=':', alpha=0.6)
plt.legend(fontsize=10)

print("Mostrando gráfica interactiva...")
plt.show()

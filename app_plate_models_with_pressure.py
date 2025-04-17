
import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Расчёт теплообменника по моделям пластин", layout="centered")
st.title("📊 Расчёт количества пластин и площади по моделям теплообменника")

st.markdown("Материал пластин: **AISI 316 (0.5 мм)**")

# Вводные параметры
st.subheader("🔧 Ввод параметров")
power_kw = st.number_input("Тепловая мощность (кВт)", min_value=0.1, value=100.0)
reserve_percent = st.slider("Запас поверхности (%)", min_value=0, max_value=100, value=10)

t_hot_in = st.number_input("Температура на входе (греющая), °C", value=130.0)
t_hot_out = st.number_input("Температура на выходе (греющая), °C", value=70.0)
t_cold_in = st.number_input("Температура на входе (нагреваемая), °C", value=60.0)
t_cold_out = st.number_input("Температура на выходе (нагреваемая), °C", value=90.0)

# Расчёт логарифмической средней разности температур (LMTD)
delta_t1 = t_hot_in - t_cold_out
delta_t2 = t_hot_out - t_cold_in
if delta_t1 != delta_t2 and delta_t1 > 0 and delta_t2 > 0:
    lmtd = (delta_t1 - delta_t2) / np.log(delta_t1 / delta_t2)
else:
    lmtd = delta_t1  # если одинаковы

# Постоянный коэффициент теплопередачи
k = 3000  # Вт/м²·К

# Мощность в Вт
q = power_kw * 1000

# Необходимая площадь с запасом
area_required = q / (k * lmtd)
area_with_reserve = area_required * (1 + reserve_percent / 100)

# Таблица моделей и площадей
models = {
    "FP04": {"area": 0.04, "pressure": 16},
    "FP05": {"area": 0.04, "pressure": 25},
    "FP10": {"area": 0.10, "pressure": 25},
    "FP20": {"area": 0.20, "pressure": 25},
    "FP31": {"area": 0.31, "pressure": 16}
}

# Расчёт по всем моделям
results = []
for model, props in models.items():
    plate_area = props["area"]
    max_pressure = props["pressure"]
    plates_needed = np.ceil(area_with_reserve / plate_area) + 1  # +1 на крайние
    actual_area = (plates_needed - 1) * plate_area
    results.append({
        "Модель": model,
        "Кол-во пластин": int(plates_needed),
        "Площадь теплообмена (м²)": round(actual_area, 2),
        "Макс. давление (бар)": max_pressure
    })

df = pd.DataFrame(results)

# Вывод результатов
st.subheader("📋 Результат расчёта по всем моделям")
st.dataframe(df)


import streamlit as st
import pandas as pd
import numpy as np
import io
from fpdf import FPDF
import os

st.set_page_config(page_title="Полный расчёт теплообменника", layout="centered")
st.title("🔥 Расчёт и подбор теплообменника — Полная версия")

# Входные параметры
st.header("🔧 Ввод параметров")
power = st.number_input("Мощность (кВт)", 0.1, 1000.0, 120.0)
reserve = st.slider("Запас поверхности (%)", 1, 100, 10)
pressure = st.number_input("Давление (бар)", 0.1, 100.0, 16.0)

type_size = st.selectbox("Типоразмер", ["Оптимальный", "Малая серия", "Средняя серия", "Большая серия"])
model_choice = st.selectbox("Модель пластины", ["Автоматически", "FP05", "FP14", "FP22"], key="model")

col1, col2, col3, col4 = st.columns(4)
manometer = col1.selectbox("Манометр", ["Нет", "Да"], key="manometer")
thermometer = col2.selectbox("Термометр", ["Нет", "Да"], key="thermometer")
flush_valve = col3.selectbox("Промывной кран", ["Нет", "Да"], key="flush_valve")
shutoff = col4.selectbox("Затвор", ["Нет", "Да"], key="shutoff")

st.subheader("Греющая сторона")
fluid_hot = st.selectbox("Жидкость (греющая)", ["Вода", "Гликоль 30%", "Пар", "Масло"])
t_hot_in = st.number_input("Температура на входе (греющая), °C", value=130.0)
t_hot_out = st.number_input("Температура на выходе (греющая), °C", value=70.0)
dp_hot_max = st.selectbox("Макс. потери давления (м), греющая", list(range(1, 21)), index=9)

st.subheader("Нагреваемая сторона")
fluid_cold = st.selectbox("Жидкость (нагреваемая)", ["Вода", "Гликоль 30%", "Масло"])
t_cold_in = st.number_input("Температура на входе (нагреваемая), °C", value=65.0)
t_cold_out = st.number_input("Температура на выходе (нагреваемая), °C", value=90.0)
dp_cold_max = st.selectbox("Макс. потери давления (м), нагреваемая", list(range(1, 21)), index=9)

# База моделей пластин
df = pd.DataFrame({
    "Модель": ["FP05", "FP14", "FP22"],
    "Площадь одной пластины": [0.04, 0.14, 0.22],
    "Макс. температура": [150, 150, 150],
    "Макс. давление": [25, 25, 25],
    "Масса пластины": [0.5, 1.2, 1.6],
    "Масса уплотнения": [0.08, 0.12, 0.18],
    "Масса рамы": [40, 80, 120]
})

Rf = 0.0392
k_clean = 3000
channel_type = "11HL"
passes_hot = 1
passes_cold = 1

df = df[df["Макс. давление"] >= pressure]
df = df[df["Макс. температура"] >= max(t_hot_in, t_hot_out, t_cold_in, t_cold_out)]

Q = power * 1000
dT1 = t_hot_in - t_cold_out
dT2 = t_hot_out - t_cold_in
LMTD = (dT1 - dT2) / np.log(dT1 / dT2) if dT1 != dT2 else dT1
A_required = Q / (k_clean * LMTD)
A_with_margin = A_required * (1 + reserve / 100)

df["Необходимое число пластин"] = A_with_margin / df["Площадь одной пластины"] + 1
df["Фактическая площадь"] = (df["Необходимое число пластин"] - 1) * df["Площадь одной пластины"]
df["ΔПлощадь"] = abs(df["Фактическая площадь"] - A_with_margin)

if model_choice != "Автоматически":
    df = df[df["Модель"] == model_choice]

recommended = df.sort_values("ΔПлощадь").iloc[0]
plates_exact = recommended["Необходимое число пластин"]
plates_rounded = int(np.ceil(plates_exact))

mass_plates = plates_rounded * recommended["Масса пластины"]
mass_gaskets = plates_rounded * recommended["Масса уплотнения"]
mass_frame = recommended["Масса рамы"]
mass_bolts = 15
mass_total = mass_plates + mass_gaskets + mass_frame + mass_bolts

U_required = Q / (A_with_margin * LMTD)
U_actual = Q / (recommended["Фактическая площадь"] * LMTD)
surface_margin = (recommended["Фактическая площадь"] - A_required) / A_required * 100

dp_hot = 0.91
dp_cold = 0.24
v_channel_hot = 0.38
v_channel_cold = 0.18
v_conn_hot = 0.82
v_conn_cold = 0.39

# Вывод результата
st.header("📊 Результат подбора")
st.success(
    f"✅ Модель: {recommended['Модель']} | 🔢 Рекомендуется ≥ {plates_exact:.2f} пластин | "
    f"📐 Площадь: {recommended['Фактическая площадь']:.2f} м² | ⚖️ Масса: {mass_total:.1f} кг"
)

st.subheader("📋 Характеристики аппарата")
st.markdown(f"""
- **Тепловая мощность:** {power:.2f} кВт  
- **Поверхность теплообмена:** {recommended['Фактическая площадь']:.2f} м²  
- **Логарифмическая / эффективная ΔT:** {LMTD:.2f} / {LMTD:.2f} K  
- **Коэфф. теплопередачи (треб/факт):** {U_required:.0f} / {U_actual:.0f} Вт/м²·К  
- **Коэффициент загрязнения:** {Rf:.4f} м²·К/кВт  
- **Запас поверхности:** {surface_margin:.2f}%  
- **Потери давления:** {dp_hot:.2f} / {dp_cold:.2f} м вод. ст.  
- **Скорость в канале:** {v_channel_hot:.2f} / {v_channel_cold:.2f} м/с  
- **Скорость в присоединении:** {v_conn_hot:.2f} / {v_conn_cold:.2f} м/с  
- **Количество проходов:** {passes_hot} / {passes_cold}  
- **Общее количество пластин:** {plates_rounded} шт.  
- **Тип канала:** {channel_type}  
""")

# Генерация PDF
if st.button("📄 Сформировать PDF"):
    pdf = FPDF()
    font_path = os.path.join(os.path.dirname(__file__), "DejaVuSans.ttf")
    pdf.add_page()
    pdf.add_font("DejaVu", "", font_path, uni=True)
    pdf.set_font("DejaVu", size=12)
    pdf.cell(200, 10, txt="Отчет по расчету теплообменника", ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("DejaVu", size=11)

    lines = [
        f"Модель: {recommended['Модель']}",
        f"Тепловая мощность: {power:.2f} кВт",
        f"Площадь теплообмена: {recommended['Фактическая площадь']:.2f} м²",
        f"Пластин: {plates_rounded} (рекомендуется ≥ {plates_exact:.2f})",
        f"Масса аппарата: {mass_total:.1f} кг",
        f"ΔT (лог/эфф): {LMTD:.2f} / {LMTD:.2f} K",
        f"Коэфф. теплопередачи (треб/факт): {U_required:.0f} / {U_actual:.0f} Вт/м²·К",
        f"Коэфф. загрязнения: {Rf:.4f} м²·К/кВт",
        f"Потери давления: {dp_hot:.2f} / {dp_cold:.2f} м вод. ст.",
        f"Скорость в канале: {v_channel_hot:.2f} / {v_channel_cold:.2f} м/с",
        f"Скорость в патрубках: {v_conn_hot:.2f} / {v_conn_cold:.2f} м/с",
        f"Проходов: {passes_hot} / {passes_cold}",
        f"Тип канала: {channel_type}"
    ]

    for line in lines:
        pdf.cell(0, 10, txt=line, ln=True)

    pdf_output = pdf.output(dest="S").encode("latin-1")
    st.download_button("📥 Скачать PDF", data=io.BytesIO(pdf_output), file_name="расчет_теплообменника.pdf", mime="application/pdf")

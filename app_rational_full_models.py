
import streamlit as st
import numpy as np
import math

st.set_page_config(page_title="Полный расчёт теплообменника", layout="centered")
st.title("🧠 Расчёт теплообменника по всем моделям пластин (как Rational)")

st.markdown("Введите параметры: температура, потери давления, мощность — и получите детальные результаты по каждой модели пластины")

# Ввод данных
power_kw = st.number_input("Тепловая мощность (кВт)", value=123.89, min_value=0.1)
t_hot_in = st.number_input("Температура греющей стороны (вход), °C", value=44.0)
t_hot_out = st.number_input("Температура греющей стороны (выход), °C", value=28.7)
t_cold_in = st.number_input("Температура нагреваемой стороны (вход), °C", value=5.0)
t_cold_out = st.number_input("Температура нагреваемой стороны (выход), °C", value=37.0)
dp_hot = st.number_input("Максимальные потери давления (греющая сторона, м)", value=1.0)
dp_cold = st.number_input("Максимальные потери давления (нагреваемая сторона, м)", value=1.0)
reserve_percent = st.slider("Запас поверхности (%)", 0, 100, 17)

# Проверка температурного графика
if t_hot_in <= t_hot_out:
    st.error("❌ Ошибка: температура на входе греющей стороны должна быть выше, чем на выходе.")
elif t_cold_out <= t_cold_in:
    st.error("❌ Ошибка: температура на выходе нагреваемой стороны должна быть выше, чем на входе.")
else:
    # Таблицы U (данные Rational)
    u_table_hot = {1: 9327, 2: 12240, 3: 14788, 4: 14788, 5: 17616, 6: 19233, 7: 19233, 8: 19233, 9: 21292, 10: 21292}
    u_table_cold = {1: 5936, 2: 7503, 3: 9415, 4: 9415, 5: 11144, 6: 12132, 7: 12132, 8: 12132, 9: 13376, 10: 13376}

    def interpolate_u(dp, u_table):
        keys = sorted(u_table.keys())
        for i in range(len(keys)-1):
            if keys[i] <= dp <= keys[i+1]:
                x0, x1 = keys[i], keys[i+1]
                y0, y1 = u_table[x0], u_table[x1]
                return y0 + (dp - x0) * (y1 - y0) / (x1 - x0)
        return u_table[keys[0]] if dp <= keys[0] else u_table[keys[-1]]

    # Расчёт LMTD
    delta_t1 = t_hot_in - t_cold_out
    delta_t2 = t_hot_out - t_cold_in
    if delta_t1 > 0 and delta_t2 > 0 and delta_t1 != delta_t2:
        lmtd = (delta_t1 - delta_t2) / np.log(delta_t1 / delta_t2)
    else:
        lmtd = (delta_t1 + delta_t2) / 2 if (delta_t1 + delta_t2) > 0 else 0

    if lmtd == 0 or np.isnan(lmtd):
        st.error("❌ Ошибка: LMTD невозможно вычислить. Проверьте корректность температур.")
    else:
        # Расчётные параметры (одинаковые для всех моделей)
        q = power_kw * 1000
        u_hot = interpolate_u(dp_hot, u_table_hot)
        u_cold = interpolate_u(dp_cold, u_table_cold)
        u_avg = (u_hot + u_cold) / 2
        area_required = q / (u_avg * lmtd)
        area_with_reserve = area_required * (1 + reserve_percent / 100)

        # Модели пластин
        plate_models = {
            "FP04": {"area": 0.04, "volume": 0.167},
            "FP05": {"area": 0.04, "volume": 0.167},
            "FP10": {"area": 0.10, "volume": 0.167},
            "FP20": {"area": 0.20, "volume": 0.167},
            "FP31": {"area": 0.31, "volume": 0.167},
        }

        st.subheader("📊 Расчёты по каждой модели пластины:")
        for model, props in plate_models.items():
            area = props["area"]
            volume_per_plate = props["volume"]
            plates = math.ceil(area_with_reserve / area) + 1
            actual_area = (plates - 1) * area
            volume = round(plates * volume_per_plate, 2)

            with st.expander(f"🔹 {model}: {plates} шт (площадь одной = {area} м²)"):
                st.markdown(f"""
                **U греющей стороны:** {int(u_hot)} Вт/м²·К  
                **U нагреваемой стороны:** {int(u_cold)} Вт/м²·К  
                **Средний коэффициент U:** {int(u_avg)} Вт/м²·К  
                **LMTD:** {round(lmtd, 2)} °C  
                **Расчётная площадь без запаса:** {round(area_required, 2)} м²  
                **Площадь с учётом запаса:** {round(area_with_reserve, 2)} м²  
                **Фактическая площадь:** {round(actual_area, 2)} м²  
                **Количество пластин:** {plates}  
                **Объём греющей стороны:** {volume} л  
                **Объём нагреваемой стороны:** {volume} л  
                **Температурный график греющая:** {t_hot_in} / {t_hot_out} °C  
                **Температурный график нагреваемая:** {t_cold_in} / {t_cold_out} °C  
                **Макс. потери давления греющая:** {dp_hot} м  
                **Макс. потери давления нагреваемая:** {dp_cold} м  
                """)

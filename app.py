import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math

# -------------------------------
# Настройка страницы и кастомный CSS
# -------------------------------
st.set_page_config(
    page_title="ArVi Calculator",
    page_icon="🧮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Словарь для сопоставления марок/классов бетона и их плотностей
BETON_MAP = {
    # Классы бетона
    "B7.5": {"mark": "M100", "density": 2300},
    "B10": {"mark": "M150", "density": 2350},
    "B12.5": {"mark": "M150", "density": 2350},
    "B15": {"mark": "M200", "density": 2400},
    "B20": {"mark": "M250", "density": 2400},
    "B22.5": {"mark": "M300", "density": 2400},
    "B25": {"mark": "M350", "density": 2450},
    "B27.5": {"mark": "M350", "density": 2450},
    "B30": {"mark": "M400", "density": 2450},
    "B35": {"mark": "M450", "density": 2450},
    "B40": {"mark": "M500", "density": 2450},
    
    # Марки бетона
    "M100": {"class": "B7.5", "density": 2300},
    "M150": {"class": "B12.5", "density": 2350},
    "M200": {"class": "B15", "density": 2400},
    "M250": {"class": "B20", "density": 2400},
    "M300": {"class": "B22.5", "density": 2400},
    "M350": {"class": "B25", "density": 2450},
    "M400": {"class": "B30", "density": 2450},
    "M450": {"class": "B35", "density": 2450},
    "M500": {"class": "B40", "density": 2450},
}

# Словарь для стяжек
SCREED_MAP = {
    "M75": {"density": 1600},
    "M100": {"density": 1700},
    "M150": {"density": 1800},
    "M200": {"density": 1900},
    "M250": {"density": 2000},
    "M300": {"density": 2100},
}

# Классификация зданий по СП 51.13330.2011
BUILDING_TYPES = {
    "Жилые здания категории А (высококомфортные)": {"Rw": 54, "Lnw": 55},
    "Жилые здания категории Б (комфортные)": {"Rw": 52, "Lnw": 58},
    "Жилые здания категории В (предельно допустимые)": {"Rw": 50, "Lnw": 60},
    "Гостиницы категории А": {"Rw": 52, "Lnw": 57},
    "Гостиницы категории Б": {"Rw": 50, "Lnw": 60},
    "Гостиницы категории В": {"Rw": 48, "Lnw": 62},
    "Перекрытия между комнатами в квартире (двухуровневой)": {"Rw": 48, "Lnw": 63},
    "Перекрытия между рабочими комнатами/офисами": {"Rw": 48, "Lnw": 63},
    "Административные здания (кабинеты)": {"Rw": 48, "Lnw": 66},
    "Больницы, санатории (палаты)": {"Rw": 52, "Lnw": 58},
    "Школы, учебные заведения (классы)": {"Rw": 52, "Lnw": 58},
    "Детские дошкольные учреждения": {"Rw": 52, "Lnw": 55},
}

# Кастомный CSS
st.markdown("""
<style>
    .main {
        background: linear-gradient(145deg, #e6f3ff 0%, #b0d4ff 70%, #4a6fa5 100%);
        padding: 1rem;
        border-radius: 10px;
        position: relative;
        overflow: hidden;
    }
    .main::before {
        content: "";
        position: absolute;
        top: -50px;
        right: -50px;
        width: 200px;
        height: 200px;
        background: radial-gradient(circle, rgba(0,0,0,0.2) 0%, transparent 70%);
        border-radius: 50%;
        pointer-events: none;
    }
    .main::after {
        content: "";
        position: absolute;
        bottom: -50px;
        left: -50px;
        width: 250px;
        height: 250px;
        background: radial-gradient(circle, rgba(0,0,100,0.3) 0%, transparent 70%);
        border-radius: 50%;
        pointer-events: none;
    }
    h1 {
        color: #0a2f44;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        font-size: 3rem;
        text-align: center;
        margin-bottom: 0;
        position: relative;
        z-index: 10;
    }
    h1::before {
        content: "🧮";
        margin-right: 15px;
        font-size: 3rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: rgba(255,255,255,0.3);
        border-radius: 20px;
        padding: 10px;
        backdrop-filter: blur(5px);
        position: relative;
        z-index: 10;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 15px;
        padding: 8px 16px;
        background-color: rgba(255,255,255,0.7);
        color: #0a2f44;
        font-weight: bold;
        transition: all 0.3s;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4a6fa5 !important;
        color: white !important;
        transform: scale(1.05);
    }
    .css-1d391kg {
        background: linear-gradient(135deg, #2c3e50, #1c2833);
        color: white;
    }
    .stButton button {
        background: #4a6fa5;
        color: white;
        font-weight: bold;
        border: none;
        border-radius: 8px;
        transition: all 0.3s;
    }
    .stButton button:hover {
        background: #2c3e50;
        transform: scale(1.02);
    }
    .dataframe {
        background: rgba(255,255,255,0.8);
        border-radius: 10px;
        padding: 5px;
    }
    .stAlert {
        background-color: rgba(255,255,200,0.8);
        color: #856404;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1>🧮 ArVi Calculator</h1>", unsafe_allow_html=True)

# Вкладки
tab_names = [
    "🔊 Звукоизоляция (ударный шум)",
    "🔥 Теплоизоляционный расчет",
    "📉 Теплопотери",
    "💪 Прочностные расчеты",
    "📦 Логистические расчеты",
    "💰 Экономический расчет",
    "🧪 Теплоизоляция труб"
]
tabs = st.tabs(tab_names)

# -------------------------------
# Общие функции
# -------------------------------
def linear_interpolate(x, xp, fp):
    if x <= xp[0]:
        return fp[0]
    if x >= xp[-1]:
        return fp[-1]
    for i in range(len(xp)-1):
        if xp[i] <= x <= xp[i+1]:
            return fp[i] + (fp[i+1]-fp[i]) * (x-xp[i])/(xp[i+1]-xp[i])
    return fp[-1]

def get_Lnw0(m1, slab_type):
    monolith = {150:86,200:84,250:82,300:80,350:78,400:77,450:76,500:75,550:74,600:73}
    hollow   = {150:88,200:86,250:84,300:82,350:80,400:79,450:78,500:77,550:76,600:75}
    table = monolith if slab_type == "Монолитная" else hollow
    masses = sorted(table.keys())
    values = [table[m] for m in masses]
    return int(round(linear_interpolate(m1, masses, values)))

def calculate_for_material(h0, E_dyn, eps, m2, m1, slab_type):
    try:
        h3 = h0 * (1 - eps) / 1000.0
        if h3 <= 0:
            return None, None
        E_Pa = E_dyn * 1e6
        f0 = 0.16 * math.sqrt(E_Pa / (h3 * m2))
        Lnw0 = get_Lnw0(m1, slab_type)
        f_grid = [60, 80, 100, 125, 160, 200]
        Lnw0_grid = [74, 76, 78, 80, 82, 84, 86]
        Lnw_matrix = [
            [48,49,51,54,56,58,61],
            [51,52,53,56,57,59,62],
            [54,55,56,57,59,61,64],
            [56,57,58,59,61,63,66],
            [57,58,60,61,63,65,68],
            [59,60,62,64,66,68,70]
        ]
        if f0 <= f_grid[0]:
            i_low = i_high = 0
        elif f0 >= f_grid[-1]:
            i_low = i_high = len(f_grid)-1
        else:
            for i in range(len(f_grid)-1):
                if f_grid[i] <= f0 <= f_grid[i+1]:
                    i_low, i_high = i, i+1
                    break
        if Lnw0 <= Lnw0_grid[0]:
            j_low = j_high = 0
        elif Lnw0 >= Lnw0_grid[-1]:
            j_low = j_high = len(Lnw0_grid)-1
        else:
            for j in range(len(Lnw0_grid)-1):
                if Lnw0_grid[j] <= Lnw0 <= Lnw0_grid[j+1]:
                    j_low, j_high = j, j+1
                    break
        if i_low == i_high:
            if j_low == j_high:
                Lnw = Lnw_matrix[i_low][j_low]
            else:
                val_low = Lnw_matrix[i_low][j_low]
                val_high = Lnw_matrix[i_low][j_high]
                Lnw = val_low + (Lnw0 - Lnw0_grid[j_low]) / (Lnw0_grid[j_high] - Lnw0_grid[j_low]) * (val_high - val_low)
        else:
            if j_low == j_high:
                L_at_low = Lnw_matrix[i_low][j_low]
                L_at_high = Lnw_matrix[i_high][j_low]
            else:
                val_low_low = Lnw_matrix[i_low][j_low]
                val_low_high = Lnw_matrix[i_low][j_high]
                L_at_low = val_low_low + (Lnw0 - Lnw0_grid[j_low]) / (Lnw0_grid[j_high] - Lnw0_grid[j_low]) * (val_low_high - val_low_low)
                val_high_low = Lnw_matrix[i_high][j_low]
                val_high_high = Lnw_matrix[i_high][j_high]
                L_at_high = val_high_low + (Lnw0 - Lnw0_grid[j_low]) / (Lnw0_grid[j_high] - Lnw0_grid[j_low]) * (val_high_high - val_high_low)
            Lnw = L_at_low + (f0 - f_grid[i_low]) / (f_grid[i_high] - f_grid[i_low]) * (L_at_high - L_at_low)
        Lnw = int(round(Lnw))
        return f0, Lnw
    except Exception:
        return None, None

# -------------------------------
# Звукоизоляция
# -------------------------------
def show_acoustic():
    st.header("🔊 Звукоизоляционный расчет (ударный шум)")

    # Блок выбора типа здания (основная область)
    st.markdown("---")
    st.subheader("Требования к звукоизоляции")
    building_type = st.selectbox("Тип здания/помещения", list(BUILDING_TYPES.keys()), index=0)
    norm_Rw = BUILDING_TYPES[building_type]["Rw"]
    norm_Lnw = BUILDING_TYPES[building_type]["Lnw"]
    st.text(f"Норматив: Lnw ≤ {norm_Lnw} дБ, Rw ≥ {norm_Rw} дБ")

    # Боковая панель с вводом данных
    with st.sidebar:
        st.subheader("Параметры конструкции")

        # Плита
        slab_type = st.selectbox("Тип плиты", ["Монолитная", "Пустотная"])
        beton_options = list(BETON_MAP.keys())
        beton_options_sorted = sorted(beton_options, key=lambda x: (x[0] != 'M', x))
        selected_beton = st.selectbox("Марка/класс бетона", beton_options_sorted,
                                      index=beton_options_sorted.index("M350") if "M350" in beton_options_sorted else 0)
        concrete_density = BETON_MAP[selected_beton]["density"]
        st.text(f"Плотность (авто): {concrete_density} кг/м³")
        slab_thickness = st.number_input("Толщина плиты, мм", min_value=50, max_value=500, value=180, step=1)

        if slab_type == "Монолитная":
            m1 = slab_thickness / 1000.0 * concrete_density
            st.text(f"m₁ = {m1:.1f} кг/м²")
        else:
            m1 = st.number_input("Поверхностная плотность плиты m₁, кг/м²", min_value=100, max_value=1000, value=250, step=1)

        # Стяжка
        screed_type = st.text_input("Тип стяжки", value="Цементно-песчаная")
        screed_options = list(SCREED_MAP.keys())
        selected_screed = st.selectbox("Марка стяжки", screed_options,
                                       index=screed_options.index("M150") if "M150" in screed_options else 0)
        screed_density = SCREED_MAP[selected_screed]["density"]
        st.text(f"Плотность (авто): {screed_density} кг/м³")
        screed_thickness = st.number_input("Толщина стяжки, мм", min_value=20, max_value=150, value=70, step=1)
        m2 = screed_thickness / 1000.0 * screed_density
        st.text(f"m₂ = {m2:.1f} кг/м²")

        # Материалы
        st.markdown("---")
        st.subheader("Звукоизоляционные материалы")
        if "materials" not in st.session_state:
            st.session_state.materials = []

        def add_material():
            st.session_state.materials.append({"name": "", "h0": 5.0, "Eд": 0.1, "eps": 0.05})

        def remove_material(index):
            st.session_state.materials.pop(index)

        st.button("➕ Добавить материал", on_click=add_material)

        for i, mat in enumerate(st.session_state.materials):
            with st.expander(f"Материал {i+1}"):
                mat["name"] = st.text_input("Название", value=mat.get("name", ""), key=f"name_{i}")
                col1, col2 = st.columns(2)
                with col1:
                    mat["h0"] = st.number_input("h₀, мм", min_value=1.0, max_value=50.0, value=float(mat.get("h0", 5)), step=0.1, key=f"h0_{i}")
                    mat["Eд"] = st.number_input("Eд, МПа", min_value=0.01, max_value=10.0, value=float(mat.get("Eд", 0.1)), step=0.01, key=f"Eд_{i}")
                with col2:
                    mat["eps"] = st.number_input("ε", min_value=0.0, max_value=0.5, value=float(mat.get("eps", 0.05)), step=0.001, format="%.3f", key=f"eps_{i}")
                if st.button("🗑️ Удалить", key=f"del_{i}"):
                    remove_material(i)
                    st.rerun()

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            calc_button = st.button("🔍 Рассчитать все")
        with col2:
            reset_button = st.button("🔄 Сбросить")
            if reset_button:
                st.session_state.materials = []
                st.rerun()

    # Основная область – результаты
    if calc_button:
        if len(st.session_state.materials) == 0:
            st.warning("Добавьте хотя бы один материал.")
        else:
            results = []
            for mat in st.session_state.materials:
                if not mat["name"] or mat["h0"] <= 0 or mat["Eд"] <= 0 or mat["eps"] <= 0:
                    continue
                f0, Lnw = calculate_for_material(
                    h0=mat["h0"],
                    E_dyn=mat["Eд"],
                    eps=mat["eps"],
                    m2=m2,
                    m1=m1,
                    slab_type=slab_type
                )
                if f0 is not None:
                    margin = norm_Lnw - Lnw  # запас относительно выбранного норматива
                    status = "Соответствует" if Lnw <= norm_Lnw else "Не соответствует"
                    results.append({
                        "Материал": mat["name"],
                        "h₀ (мм)": mat["h0"],
                        "Eд (МПа)": mat["Eд"],
                        "ε": mat["eps"],
                        "f₀ (Гц)": round(f0, 1),
                        "Lnw (дБ)": Lnw,
                        "Запас (дБ)": margin,
                        "Статус": status
                    })
            if results:
                df = pd.DataFrame(results).sort_values(by="Lnw (дБ)")
                st.subheader("📊 Сравнение материалов")
                def highlight_best(row):
                    if row["Lnw (дБ)"] == df["Lnw (дБ)"].min():
                        return ['background-color: lightgreen'] * len(row)
                    return [''] * len(row)
                st.dataframe(df.style.apply(highlight_best, axis=1), use_container_width=True)

                # Расчёт без подложки (минимальные плотности)
                st.subheader("🧱 Конструкция без звукоизоляции")
                screed_density_min = 1800
                m2_min = screed_thickness / 1000.0 * screed_density_min
                if slab_type == "Монолитная":
                    concrete_density_min = 2200
                    m1_min = slab_thickness / 1000.0 * concrete_density_min
                else:
                    m1_min = m1  # для пустотной оставляем как введено (или можно задать мин)
                m_total = m1_min + m2_min
                Lnw_without = get_Lnw0(m_total, slab_type)
                st.write(f"**Без подложки:** Lnw = {Lnw_without} дБ → {'НЕ СООТВЕТСТВУЕТ' if Lnw_without > norm_Lnw else 'СООТВЕТСТВУЕТ'}")
                best_Lnw = df["Lnw (дБ)"].min()
                best_margin = norm_Lnw - best_Lnw
                st.write(f"**С лучшим материалом:** Lnw = {best_Lnw} дБ → СООТВЕТСТВУЕТ (запас {best_margin} дБ)")

                # График
                st.subheader("📈 Сравнение Lnw")
                fig, ax = plt.subplots()
                materials = df["Материал"].tolist()
                values = df["Lnw (дБ)"].tolist()
                colors = ['green' if v <= norm_Lnw else 'red' for v in values]
                ax.bar(materials, values, color=colors)
                ax.axhline(y=norm_Lnw, color='black', linestyle='--', label=f'Норматив {norm_Lnw} дБ')
                ax.set_ylabel("Lnw, дБ")
                ax.set_title("Индекс ударного шума")
                plt.xticks(rotation=45, ha='right')
                ax.legend()
                st.pyplot(fig)

                # Техническое заключение
                st.markdown("---")
                st.subheader("📄 Техническое заключение")

                best_row = df.iloc[0]
                best_material_name = best_row["Материал"]
                best_Lnw = best_row["Lnw (дБ)"]
                best_margin = best_row["Запас (дБ)"]

                conclusion = f"""
**Анализ результатов расчёта индекса изоляции ударного шума Lnw**

**1. Исходные данные:**
- Плита перекрытия: {slab_type.lower()}, марка бетона {selected_beton}, толщина {slab_thickness} мм.
- Стяжка: {screed_type}, марка {selected_screed}, толщина {screed_thickness} мм.
- Тип здания/помещения: **{building_type}**.
- Нормативное значение согласно СП 51.13330.2011: **Lnw,норм = {norm_Lnw} дБ**.

**2. Расчёт с применением звукоизоляционного материала:**
- Рассмотрено {len(results)} материалов.
- Лучший результат показал материал **«{best_material_name}»**:
  - Расчётный индекс ударного шума: Lnw = {best_Lnw} дБ.
  - Запас относительно норматива: **{best_margin} дБ**.
  - Статус: **{'✅ СООТВЕТСТВУЕТ' if best_margin >= 0 else '❌ НЕ СООТВЕТСТВУЕТ'}** требованиям СП 51.13330.2011 для данного типа помещений.

**3. Расчёт без звукоизоляционного слоя (минимальные плотности):**
- Конструкция без подложки (только плита + стяжка):
  - Расчётный индекс ударного шума: Lnw,без = {Lnw_without} дБ.
  - Статус: **{'❌ НЕ СООТВЕТСТВУЕТ' if Lnw_without > norm_Lnw else '✅ СООТВЕТСТВУЕТ'}** нормативу.

**4. Вывод:**
Применение звукоизоляционного материала **«{best_material_name}»** позволяет снизить уровень ударного шума на **{Lnw_without - best_Lnw} дБ** и обеспечить выполнение нормативных требований СП 51.13330.2011. Конструкция без дополнительной звукоизоляции не удовлетворяет нормативам, что подтверждает эффективность использования подложек GLOBEX.

*Расчёт выполнен в соответствии с методиками СП 23-103-2003 и ГОСТ Р 56770-2015.*
"""
                st.markdown(conclusion)

                if st.button("💾 Сохранить заключение как .txt"):
                    with open("acoustic_conclusion.txt", "w", encoding="utf-8") as f:
                        f.write(conclusion)
                    st.success("Заключение сохранено в файл acoustic_conclusion.txt")
            else:
                st.warning("Нет корректных данных для расчёта.")

# -------------------------------
# Заглушки для остальных вкладок
# -------------------------------
def show_thermal_insulation():
    st.header("🔥 Теплоизоляционный расчет")
    st.info("Раздел в разработке. Здесь будет подбор толщины утеплителя, проверка на конденсат и другие теплотехнические расчёты.")

def show_thermal_loss():
    st.header("📉 Расчет теплопотерь")
    st.info("Раздел в разработке. Здесь будет расчет теплопотерь через ограждающие конструкции.")

def show_strength():
    st.header("💪 Прочностные расчеты")
    st.info("Раздел в разработке. Здесь будет оценка деформации под нагрузкой, точечные нагрузки и т.д.")

def show_logistics():
    st.header("📦 Логистические расчеты")
    st.info("Раздел в разработке. Здесь будет расчет количества рулонов, скотча, жгутов, веса и объема.")

def show_economic():
    st.header("💰 Экономический расчет")
    st.info("Раздел в разработке. Здесь будет расчет срока окупаемости утепления.")

def show_pipe_insulation():
    st.header("🧪 Теплоизоляция труб")
    st.info("Раздел в разработке. Здесь будет подбор толщины скорлуп, проверка на конденсат.")

# -------------------------------
# Привязка вкладок
# -------------------------------
with tabs[0]:
    show_acoustic()
with tabs[1]:
    show_thermal_insulation()
with tabs[2]:
    show_thermal_loss()
with tabs[3]:
    show_strength()
with tabs[4]:
    show_logistics()
with tabs[5]:
    show_economic()
with tabs[6]:
    show_pipe_insulation()
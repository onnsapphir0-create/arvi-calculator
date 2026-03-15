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

# -----------------------------------------------------------------
# Словари данных по материалам (на основе ГОСТ и СП)
# -----------------------------------------------------------------

# Плиты перекрытия железобетонные (по ГОСТ 26434-2015 и др.)
SLAB_TYPES = {
    "Многопустотные": {
        "1ПК (220 мм, ∅159)": {
            "thickness": 220,
            "density_range": (2200, 2500),
            "hollow_factor": 0.4,
            "surface_density_range": (300, 340),
            "description": "Плита с круглыми пустотами 159 мм"
        },
        "2ПК (220 мм, ∅140)": {
            "thickness": 220,
            "density_range": (2400, 2500),
            "hollow_factor": 0.35,
            "surface_density_range": (320, 350),
            "description": "Плита с пустотами 140 мм"
        },
        "ПБ (220 мм, безопалубочная)": {
            "thickness": 220,
            "density_range": (2400, 2500),
            "hollow_factor": 0.35,
            "surface_density_range": (300, 350),
            "description": "Безопалубочного формования"
        },
        "ПНО (160 мм, облегчённая)": {
            "thickness": 160,
            "density_range": (2200, 2400),
            "hollow_factor": 0.3,
            "surface_density_range": (250, 280),
            "description": "Облегчённая плита"
        },
        "3,1ПБ (220 мм, промздания)": {
            "thickness": 220,
            "density_range": (2400, 2500),
            "hollow_factor": 0.35,
            "surface_density_range": (320, 340),
            "description": "Для промышленных зданий"
        },
    },
    "Сплошные (однослойные)": {
        "1П (120 мм)": {
            "thickness": 120,
            "density_range": (2400, 2500),
            "hollow_factor": 0,
            "surface_density_range": (280, 300),
            "description": "Сплошная плита, опирание по контуру"
        },
        "2П (160 мм)": {
            "thickness": 160,
            "density_range": (2400, 2500),
            "hollow_factor": 0,
            "surface_density_range": (380, 400),
            "description": "Сплошная плита"
        },
        "3П (200–250 мм)": {
            "thickness": 220,
            "density_range": (2400, 2500),
            "hollow_factor": 0,
            "surface_density_range": (480, 600),
            "description": "Монолитная или сборная"
        },
    },
    "Ребристые": {
        "ПР (300–400 мм)": {
            "thickness": 350,
            "density_range": (2400, 2500),
            "hollow_factor": 0,
            "surface_density_range": (500, 700),
            "description": "Ребристая плита для промзданий"
        },
    }
}

# Марки бетона и их плотности (мин/макс)
BETON_MAP = {
    "B7.5": {"mark": "M100", "density_min": 2200, "density_max": 2300},
    "B10": {"mark": "M150", "density_min": 2200, "density_max": 2350},
    "B12.5": {"mark": "M150", "density_min": 2200, "density_max": 2350},
    "B15": {"mark": "M200", "density_min": 2300, "density_max": 2400},
    "B20": {"mark": "M250", "density_min": 2300, "density_max": 2400},
    "B22.5": {"mark": "M300", "density_min": 2300, "density_max": 2400},
    "B25": {"mark": "M350", "density_min": 2350, "density_max": 2450},
    "B27.5": {"mark": "M350", "density_min": 2350, "density_max": 2450},
    "B30": {"mark": "M400", "density_min": 2350, "density_max": 2450},
    "B35": {"mark": "M450", "density_min": 2350, "density_max": 2450},
    "B40": {"mark": "M500", "density_min": 2350, "density_max": 2450},
    "M100": {"class": "B7.5", "density_min": 2200, "density_max": 2300},
    "M150": {"class": "B12.5", "density_min": 2200, "density_max": 2350},
    "M200": {"class": "B15", "density_min": 2300, "density_max": 2400},
    "M250": {"class": "B20", "density_min": 2300, "density_max": 2400},
    "M300": {"class": "B22.5", "density_min": 2300, "density_max": 2400},
    "M350": {"class": "B25", "density_min": 2350, "density_max": 2450},
    "M400": {"class": "B30", "density_min": 2350, "density_max": 2450},
    "M450": {"class": "B35", "density_min": 2350, "density_max": 2450},
    "M500": {"class": "B40", "density_min": 2350, "density_max": 2450},
}

# Марки стяжек и их плотности (мин/макс) – используются только для справки, теперь будем использовать расширенный расчет
SCREED_MAP = {
    "M75": {"density_min": 1500, "density_max": 1600},
    "M100": {"density_min": 1600, "density_max": 1700},
    "M150": {"density_min": 1700, "density_max": 1800},
    "M200": {"density_min": 1800, "density_max": 1900},
    "M250": {"density_min": 1900, "density_max": 2000},
    "M300": {"density_min": 2000, "density_max": 2100},
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

# -----------------------------------------------------------------
# Новые словари для перегородок
# -----------------------------------------------------------------

# Данные для определения fB по таблице 8 СП 23-103-2003
FB_TABLE = {
    "density": [1800, 1600, 1400, 1200, 1000, 800, 600],
    "fb_const": [29000, 31000, 33000, 35000, 37000, 39000, 40000]
}

# Оценочная кривая изоляции воздушного шума
REFERENCE_CURVE = {
    100: 33, 125: 36, 160: 39, 200: 42, 250: 45, 315: 48, 400: 51, 500: 52,
    630: 53, 800: 54, 1000: 55, 1250: 56, 1600: 56, 2000: 56, 2500: 56, 3150: 56
}

# Коэффициент K для разных материалов (таблица 10 СП)
K_FACTOR = {
    "кирпич": 1.2,
    "бетон": 1.0,
    "газобетон": 0.8,
    "пенобетон": 0.8,
    "керамзитобетон": 1.1,
    "ПГП гипсовая": 1.0,
    "ПГП силикатная": 1.0,
}

WALL_TYPES = {
    "Кирпичные": {
        "Полнотелый керамический": {
            "density_range": (1700, 1900),
            "default_thickness": 120,
            "K": K_FACTOR["кирпич"],
            "Rw_range": (47, 50),
            "description": "Кирпич полнотелый керамический"
        },
        "Пустотелый керамический": {
            "density_range": (1300, 1600),
            "default_thickness": 120,
            "K": K_FACTOR["кирпич"],
            "Rw_range": (45, 48),
            "description": "Кирпич пустотелый керамический"
        },
        "Силикатный полнотелый": {
            "density_range": (1800, 2000),
            "default_thickness": 120,
            "K": K_FACTOR["кирпич"],
            "Rw_range": (48, 52),
            "description": "Силикатный полнотелый"
        },
        "Силикатный пустотелый": {
            "density_range": (1400, 1650),
            "default_thickness": 120,
            "K": K_FACTOR["кирпич"],
            "Rw_range": (46, 49),
            "description": "Силикатный пустотелый"
        },
        "Клинкерный": {
            "density_range": (2000, 2200),
            "default_thickness": 120,
            "K": K_FACTOR["кирпич"],
            "Rw_range": (52, 55),
            "description": "Клинкерный"
        },
    },
    "Блочные": {
        "Газобетон D400–D600": {
            "density_range": (400, 600),
            "default_thickness": 150,
            "K": K_FACTOR["газобетон"],
            "Rw_range": (37, 44),
            "description": "Газобетон автоклавный"
        },
        "Газобетон D600–D800": {
            "density_range": (600, 800),
            "default_thickness": 200,
            "K": K_FACTOR["газобетон"],
            "Rw_range": (44, 50),
            "description": "Газобетон автоклавный"
        },
        "Пенобетон неавтоклавный D600–D800": {
            "density_range": (600, 800),
            "default_thickness": 150,
            "K": K_FACTOR["пенобетон"],
            "Rw_range": (40, 48),
            "description": "Пенобетон"
        },
        "Пенобетон D900–D1200": {
            "density_range": (900, 1200),
            "default_thickness": 120,
            "K": K_FACTOR["пенобетон"],
            "Rw_range": (48, 53),
            "description": "Пенобетон"
        },
        "Керамзитобетонные блоки D1000–D1500": {
            "density_range": (1000, 1500),
            "default_thickness": 120,
            "K": K_FACTOR["керамзитобетон"],
            "Rw_range": (45, 52),
            "description": "Керамзитобетон"
        },
    },
    "Пазогребневые плиты (ПГП)": {
        "Гипсовые 80 мм": {
            "density_range": (1100, 1250),
            "default_thickness": 80,
            "K": K_FACTOR["ПГП гипсовая"],
            "Rw_range": (40, 43),
            "description": "ПГП гипсовая 80 мм"
        },
        "Гипсовые 100 мм": {
            "density_range": (1100, 1250),
            "default_thickness": 100,
            "K": K_FACTOR["ПГП гипсовая"],
            "Rw_range": (45, 48),
            "description": "ПГП гипсовая 100 мм"
        },
        "Силикатные 80 мм": {
            "density_range": (1500, 1700),
            "default_thickness": 80,
            "K": K_FACTOR["ПГП силикатная"],
            "Rw_range": (45, 48),
            "description": "ПГП силикатная 80 мм"
        },
        "Силикатные 100 мм": {
            "density_range": (1500, 1700),
            "default_thickness": 100,
            "K": K_FACTOR["ПГП силикатная"],
            "Rw_range": (50, 53),
            "description": "ПГП силикатная 100 мм"
        },
    },
    "Гипсокартонные (каркасные)": {
        "ГКЛ одинарный каркас, 1 слой": {
            "sheet_thickness": 12.5,
            "density": 900,
            "layers": 1,
            "frame": "single",
            "insulation": False,
            "Rw_range": (41, 45),
            "description": "ГКЛ 12.5 мм, 1 слой с каждой стороны"
        },
        "ГКЛ одинарный каркас, 2 слоя": {
            "sheet_thickness": 12.5,
            "density": 900,
            "layers": 2,
            "frame": "single",
            "insulation": False,
            "Rw_range": (45, 48),
            "description": "ГКЛ 12.5 мм, 2 слоя"
        },
        "ГКЛ двойной каркас + минвата": {
            "sheet_thickness": 12.5,
            "density": 900,
            "layers": 2,
            "frame": "double",
            "insulation": True,
            "Rw_range": (50, 55),
            "description": "Двойной каркас, минвата 50 мм"
        },
        "ГВЛ 10–12.5 мм, 1 слой": {
            "sheet_thickness": 12.5,
            "density": 1200,
            "layers": 1,
            "frame": "single",
            "insulation": False,
            "Rw_range": (43, 48),
            "description": "ГВЛ"
        },
    },
    "Межквартирные повышенные": {
        "Двойная кирпичная с зазором 50 мм": {
            "layers": [
                {"material": "кирпич", "thickness": 120, "density": 1800},
                {"gap": 50, "insulation": True},
                {"material": "кирпич", "thickness": 120, "density": 1800}
            ],
            "Rw_range": (58, 62),
            "description": "Двойная кирпичная с зазором"
        },
        "Бетонная монолитная 160–200 мм": {
            "density_range": (2400, 2500),
            "default_thickness": 180,
            "K": K_FACTOR["бетон"],
            "Rw_range": (55, 60),
            "description": "Бетонная монолитная"
        },
        "Ж/б панель 140–180 мм": {
            "density_range": (2400, 2500),
            "default_thickness": 160,
            "K": K_FACTOR["бетон"],
            "Rw_range": (52, 57),
            "description": "Железобетонная панель"
        },
        "Трёхслойная ж/б – утеплитель – ж/б": {
            "layers": [
                {"material": "бетон", "thickness": 80, "density": 2500},
                {"material": "утеплитель", "thickness": 100, "density": 50, "is_soft": True},
                {"material": "бетон", "thickness": 80, "density": 2500}
            ],
            "Rw_range": (60, 65),
            "description": "Трёхслойная панель"
        },
    },
}

# -----------------------------------------------------------------
# Кастомный CSS (оформление)
# -----------------------------------------------------------------
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

# -----------------------------------------------------------------
# Вкладки (первая – звукоизоляция, последняя – стяжки)
# -----------------------------------------------------------------
tab_names = [
    "🔊 Звукоизоляция (ударный + воздушный)",
    "🔥 Теплоизоляционный расчёт",
    "📉 Теплопотери",
    "💪 Прочностные расчёты",
    "📦 Логистические расчёты",
    "💰 Экономический расчёт",
    "🧪 Теплоизоляция труб",
    "🧱 Расчёт стяжек"
]
tabs = st.tabs(tab_names)

# -----------------------------------------------------------------
# Общие вспомогательные функции
# -----------------------------------------------------------------
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
    """Определяет Lnw0 по массе плиты и типу (СП 23-103-2003)."""
    monolith = {150:86,200:84,250:82,300:80,350:78,400:77,450:76,500:75,550:74,600:73}
    hollow   = {150:88,200:86,250:84,300:82,350:80,400:79,450:78,500:77,550:76,600:75}
    table = monolith if slab_type == "Монолитная" else hollow
    masses = sorted(table.keys())
    values = [table[m] for m in masses]
    return int(round(linear_interpolate(m1, masses, values)))

def calculate_for_material(h0, E_dyn, eps, m2, m1, slab_type):
    """Расчёт для одного материала (упругий слой) – возвращает (f0, Lnw)."""
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

# -----------------------------------------------------------------
# Функции для расчёта воздушного шума (перегородки)
# -----------------------------------------------------------------
def get_fB_by_density(density, thickness_mm):
    """Возвращает частоту fB (Гц) по плотности и толщине (таблица 8 СП)."""
    xp = FB_TABLE["density"]
    fp = FB_TABLE["fb_const"]
    const = linear_interpolate(density, xp, fp)
    return const / thickness_mm

def build_reference_curve(frequencies):
    """Строит оценочную кривую на заданных частотах (интерполяция)."""
    ref_freqs = sorted(REFERENCE_CURVE.keys())
    ref_vals = [REFERENCE_CURVE[f] for f in ref_freqs]
    return [linear_interpolate(f, ref_freqs, ref_vals) for f in frequencies]

def compute_Rw_from_curve(calc_curve, freqs, ref_curve):
    """
    Вычисляет индекс Rw путём сравнения расчётной кривой с оценочной.
    Возвращает Rw, смещение и сумму неблагоприятных отклонений.
    """
    # Сначала без смещения
    deviations = [calc_curve[i] - ref_curve[i] for i in range(len(freqs))]
    unfav_sum = sum(-d for d in deviations if d < 0)
    if unfav_sum <= 32:
        return int(round(ref_curve[freqs.index(500)] if 500 in freqs else ref_curve[0])), 0, unfav_sum
    # Требуется смещение вниз
    shift = 0
    while unfav_sum > 32:
        shift += 1
        new_ref = [r - shift for r in ref_curve]
        deviations = [calc_curve[i] - new_ref[i] for i in range(len(freqs))]
        unfav_sum = sum(-d for d in deviations if d < 0)
    Rw = (REFERENCE_CURVE[500] if 500 in REFERENCE_CURVE else REFERENCE_CURVE[min(REFERENCE_CURVE.keys())]) - shift
    return int(round(Rw)), -shift, unfav_sum

def calculate_Rw_massive(density, thickness, K=1.0):
    """
    Расчёт Rw для однослойной массивной перегородки по п. 9.3 СП 23-103-2003.
    Возвращает Rw, список частот и значений расчётной кривой.
    """
    thickness_m = thickness / 1000.0
    m = density * thickness_m  # поверхностная плотность
    m_eq = K * m
    # Частота fB
    fB = get_fB_by_density(density, thickness)
    # Ордината точки B
    RB = 20 * math.log10(m_eq) - 12
    # Построение ломаной ABCD: от 100 Гц до fB – горизонталь RB,
    # от fB до fC (где достигается 65 дБ) – наклон 6 дБ/октаву,
    # далее до 3150 Гц – горизонталь 65.
    fC = fB * 2**((65 - RB)/6) if RB < 65 else fB
    # Формируем частоты 1/3-октавного ряда от 100 до 3150 Гц
    freqs_third_octave = [100,125,160,200,250,315,400,500,630,800,1000,1250,1600,2000,2500,3150]
    calc_curve = []
    for f in freqs_third_octave:
        if f <= fB:
            R = RB
        elif f <= fC:
            octaves_above = math.log2(f / fB)
            R = RB + 6 * octaves_above
            if R > 65:
                R = 65
        else:
            R = 65
        calc_curve.append(R)
    ref_curve = build_reference_curve(freqs_third_octave)
    Rw, shift, unfav = compute_Rw_from_curve(calc_curve, freqs_third_octave, ref_curve)
    return Rw, freqs_third_octave, calc_curve, ref_curve, shift, unfav

def calculate_Rw_frame(sheet_thickness, density, layers, frame_type, insulation):
    """
    Упрощённый расчёт для каркасно-обшивных перегородок.
    Возвращает ориентировочный Rw.
    """
    # База: для одного слоя ГКЛ (12.5 мм, плотность 900) Rw ~ 41 дБ.
    base_rw = 41
    # Поправка на плотность: чем выше плотность, тем выше Rw (грубо)
    density_factor = (density / 900) ** 0.5
    # Поправка на количество слоёв (по таблице 21)
    if layers == 2:
        layer_factor = 1.15
    else:
        layer_factor = 1.0
    # Поправка на каркас
    if frame_type == "double":
        frame_factor = 1.1
    else:
        frame_factor = 1.0
    # Поправка на утеплитель
    if insulation:
        insul_factor = 1.1
    else:
        insul_factor = 1.0
    Rw = base_rw * density_factor * layer_factor * frame_factor * insul_factor
    return int(round(Rw))

# -----------------------------------------------------------------
# Основная функция для звукоизоляции (объединённая)
# -----------------------------------------------------------------
def show_acoustic():
    st.header("🔊 Звукоизоляционные расчёты (ударный и воздушный шум)")

    with st.expander("📘 Что такое звукоизоляция и зачем её рассчитывать?"):
        st.markdown("""
        **Ударный шум** – возникает при механическом воздействии на перекрытие (шаги, падение предметов).  
        **Воздушный шум** – передаётся по воздуху (речь, музыка, шум транспорта).  

        Расчёт позволяет:
        - Обеспечить комфортные условия проживания.
        - Правильно подобрать конструкцию пола или перегородки.
        - Соответствовать требованиям СП 51.13330.2011 и СП 23-103-2003.
        """)

    # Боковая панель
    with st.sidebar:
        st.subheader("Требования к звукоизоляции")
        building_type = st.selectbox("Тип здания/помещения", list(BUILDING_TYPES.keys()), index=0)
        norm_Rw = BUILDING_TYPES[building_type]["Rw"]
        norm_Lnw = BUILDING_TYPES[building_type]["Lnw"]
        st.text(f"Норматив: Lnw ≤ {norm_Lnw} дБ, Rw ≥ {norm_Rw} дБ")

        st.markdown("---")
        st.subheader("Тип рассчитываемой конструкции")
        constr_type = st.radio("Выберите тип", ["Перекрытие", "Перегородка"])

        # ---------------------------------------------------------
        # Блок для перекрытий (ударный шум)
        # ---------------------------------------------------------
        if constr_type == "Перекрытие":
            st.markdown("---")
            st.subheader("Параметры перекрытия")

            floor_type = st.selectbox("Тип перекрытия",
                                       ["Междуэтажное", "Чердачное", "Над подвалом", "Цокольное"],
                                       index=0)

            st.markdown("**Параметры плиты перекрытия**")
            slab_category = st.selectbox("Тип плиты", ["Монолитная", "Пустотная"])  # исправлено с "ПУСТОТЕЛАЯ"

            if slab_category == "Монолитная":
                slab_family = "Сплошные (однослойные)"
            else:
                slab_family = "Многопустотные"
            slab_options = list(SLAB_TYPES[slab_family].keys())
            selected_slab = st.selectbox("Марка/тип плиты", slab_options)

            slab_params = SLAB_TYPES[slab_family][selected_slab]
            default_thickness = slab_params["thickness"]
            default_density_min, default_density_max = slab_params["density_range"]
            hollow_factor = slab_params.get("hollow_factor", 0)

            slab_thickness = st.number_input("Толщина плиты, мм", min_value=50, max_value=500,
                                             value=default_thickness, step=1)

            beton_options = list(BETON_MAP.keys())
            beton_options_sorted = sorted(beton_options, key=lambda x: (x[0] != 'M', x))
            selected_beton = st.selectbox("Марка/класс бетона", beton_options_sorted,
                                           index=beton_options_sorted.index("M350") if "M350" in beton_options_sorted else 0)

            density_min = BETON_MAP[selected_beton]["density_min"]
            density_max = BETON_MAP[selected_beton]["density_max"]
            concrete_density_max = density_max
            concrete_density_min = density_min

            st.text(f"Плотность бетона: макс {concrete_density_max} кг/м³, мин {concrete_density_min} кг/м³")

            base_m1_max = slab_thickness / 1000.0 * concrete_density_max
            if slab_category == "Пустотная":
                hollow_factor = st.number_input("Коэффициент пустотности (для пустотных плит)",
                                                min_value=0.1, max_value=0.6, value=hollow_factor, step=0.01)
                m1_max = base_m1_max * (1 - hollow_factor)
            else:
                m1_max = base_m1_max

            st.text(f"Пов. плотность плиты (макс) m₁ = {m1_max:.1f} кг/м²")

            base_m1_min = slab_thickness / 1000.0 * concrete_density_min
            if slab_category == "Пустотная":
                m1_min = base_m1_min * (1 - hollow_factor)
            else:
                m1_min = base_m1_min

            st.markdown("**Параметры стяжки**")
            screed_type = st.text_input("Тип стяжки", value="Цементно-песчаная")
            screed_options = list(SCREED_MAP.keys())
            selected_screed = st.selectbox("Марка стяжки", screed_options,
                                           index=screed_options.index("M150") if "M150" in screed_options else 0)

            screed_density_min = SCREED_MAP[selected_screed]["density_min"]
            screed_density_max = SCREED_MAP[selected_screed]["density_max"]
            st.text(f"Плотность стяжки: макс {screed_density_max} кг/м³, мин {screed_density_min} кг/м³")

            screed_thickness = st.number_input("Толщина стяжки, мм", min_value=20, max_value=150, value=70, step=1)
            m2_max = screed_thickness / 1000.0 * screed_density_max
            m2_min = screed_thickness / 1000.0 * screed_density_min
            st.text(f"Пов. плотность стяжки m₂ = {m2_max:.1f} кг/м² (макс)")

            st.markdown("**Тип пола**")
            floor_construction = st.radio("Выберите тип пола",
                                           ["Плавающая стяжка с упругим слоем",
                                            "Рулонное покрытие (линолеум, ковролин, паркет)"])

            if floor_construction == "Рулонное покрытие (линолеум, ковролин, паркет)":
                st.info("Для рулонных покрытий используется индекс снижения ударного шума ΔL, который берётся из паспорта материала.")
                delta_L = st.number_input("Индекс снижения ударного шума ΔL, дБ",
                                           min_value=0, max_value=50, value=20, step=1)
                show_materials = False
            else:
                delta_L = None
                show_materials = True

            if show_materials:
                st.markdown("---")
                st.subheader("Звукоизоляционные материалы (упругий слой)")
                if "materials" not in st.session_state:
                    st.session_state.materials = []

                def add_material():
                    st.session_state.materials.append({"name": "", "h0": 5.0, "Eд": 0.1, "eps": 0.05})

                def remove_material(index):
                    st.session_state.materials.pop(index)

                st.button("➕ Добавить материал", on_click=add_material)

                for i, mat in enumerate(st.session_state.materials):
                    with st.expander(f"Материал {i+1}"):  # исправлено, если были странные названия
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
                calc_button = st.button("🔍 Рассчитать")  # кнопка должна быть "Рассчитать"
            with col2:
                reset_button = st.button("🔄 Сбросить")
                if reset_button:
                    st.session_state.materials = []
                    st.rerun()

        # ---------------------------------------------------------
        # Блок для перегородок (воздушный шум)
        # ---------------------------------------------------------
        else:
            st.markdown("---")
            st.subheader("Параметры перегородки")

            # Пока не используется, но добавим для будущего
            wall_purpose = st.radio("Тип перегородки", ["Межкомнатная", "Межквартирная"], index=0)

            wall_category = st.selectbox("Категория материала перегородки", list(WALL_TYPES.keys()))
            wall_options = list(WALL_TYPES[wall_category].keys())
            selected_wall = st.selectbox("Тип перегородки (конкретный)", wall_options)

            wall_params = WALL_TYPES[wall_category][selected_wall]

            # Инициализируем переменные, которые будем использовать в расчёте
            if "density_range" in wall_params:
                # Массивная перегородка
                density_min, density_max = wall_params["density_range"]
                default_thickness = wall_params["default_thickness"]
                K = wall_params.get("K", 1.0)

                thickness = st.number_input("Толщина перегородки, мм", min_value=20, max_value=500,
                                             value=default_thickness, step=1)

                # Выбор плотности (исправлено: правильные подписи)
                density_choice = st.radio("Плотность", ["минимальная", "максимальная", "средняя", "ввести вручную"], index=2)
                if density_choice == "минимальная":
                    density = density_min
                elif density_choice == "максимальная":
                    density = density_max
                elif density_choice == "средняя":
                    density = (density_min + density_max) / 2
                else:
                    density = st.number_input("Плотность (кг/м³)", min_value=300, max_value=3000,
                                               value=int((density_min+density_max)/2), step=10)

                st.text(f"Плотность: {density:.0f} кг/м³")
                st.text(f"Коэффициент K = {K}")

            elif "sheet_thickness" in wall_params:
                # Каркасно-обшивная перегородка (гипсокартон)
                sheet_thickness = wall_params["sheet_thickness"]
                density = wall_params["density"]
                layers = wall_params["layers"]
                frame = wall_params["frame"]
                insulation = wall_params["insulation"]
                thickness = sheet_thickness * layers * 2  # грубо
                st.text(f"Тип: {wall_params['description']}")
                st.text(f"Толщина листа: {sheet_thickness} мм, слоёв: {layers}")
                st.text(f"Каркас: {'двойной' if frame=='double' else 'одинарный'}")
                st.text(f"Утеплитель: {'да' if insulation else 'нет'}")
                density = st.number_input("Плотность материала (кг/м³)", min_value=500, max_value=1500,
                                           value=density, step=10)
            else:
                # Сложные межквартирные (пока не реализовано)
                st.info("Расчёт для этого типа перегородок будет добавлен позже.")
                density = None
                thickness = None
                K = 1.0

            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                calc_button = st.button("🔍 Рассчитать")  # исправлено
            with col2:
                reset_button = st.button("🔄 Сбросить", key="reset_wall")
                if reset_button:
                    pass  # пока ничего не сбрасываем

    # -----------------------------------------------------------------
    # Основная область – результаты
    # -----------------------------------------------------------------
    if calc_button:
        if constr_type == "Перекрытие":
            if floor_construction == "Плавающая стяжка с упругим слоем":
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
                            m2=m2_max,
                            m1=m1_max,
                            slab_type=slab_category
                        )
                        if f0 is not None:
                            margin = norm_Lnw - Lnw
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

                        st.subheader("🧱 Конструкция без звукоизоляции")
                        m_total = m1_min + m2_min
                        Lnw_without = get_Lnw0(m_total, slab_category)
                        st.write(f"**Без подложки:** Lnw = {Lnw_without} дБ → {'НЕ СООТВЕТСТВУЕТ' if Lnw_without > norm_Lnw else 'СООТВЕТСТВУЕТ'}")
                        best_Lnw = df["Lnw (дБ)"].min()
                        best_margin = norm_Lnw - best_Lnw
                        st.write(f"**С лучшим материалом:** Lnw = {best_Lnw} дБ → СООТВЕТСТВУЕТ (запас {best_margin} дБ)")

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

                        st.markdown("---")
                        st.subheader("📄 Техническое заключение")
                        best_row = df.iloc[0]
                        best_material_name = best_row["Материал"]
                        best_Lnw = best_row["Lnw (дБ)"]
                        best_margin = best_row["Запас (дБ)"]

                        conclusion = f"""
**Анализ результатов расчёта ударного шума Lnw**

**1. Исходные данные:**  
Плита: {selected_slab}, бетон {selected_beton}, толщина {slab_thickness} мм.  
Стяжка: {screed_type}, марка {selected_screed}, толщина {screed_thickness} мм.  
Тип здания: **{building_type}**.  
Норматив: **Lnw ≤ {norm_Lnw} дБ**.

**2. Расчёт с материалом:**  
Лучший материал **«{best_material_name}»** даёт Lnw = {best_Lnw} дБ, запас {best_margin} дБ – **{'✅ СООТВЕТСТВУЕТ' if best_margin >= 0 else '❌ НЕ СООТВЕТСТВУЕТ'}**.

**3. Без подложки:** Lnw = {Lnw_without} дБ – **НЕ СООТВЕТСТВУЕТ**.

**4. Вывод:** Применение подложки снижает шум на {Lnw_without - best_Lnw} дБ и обеспечивает выполнение норм.
"""
                        st.markdown(conclusion)
                        if st.button("💾 Сохранить заключение"):
                            with open("acoustic_conclusion.txt", "w", encoding="utf-8") as f:
                                f.write(conclusion)
                            st.success("Заключение сохранено")
                    else:
                        st.warning("Нет корректных данных для расчёта.")
            else:  # Рулонное покрытие
                st.subheader("🧱 Конструкция с рулонным покрытием")
                Lnw0_plate = get_Lnw0(m1_min, slab_category)
                Lnw_with_cover = Lnw0_plate - delta_L
                status = "СООТВЕТСТВУЕТ" if Lnw_with_cover <= norm_Lnw else "НЕ СООТВЕТСТВУЕТ"
                st.write(f"**Индекс плиты Lnw0 (мин. плотность):** {Lnw0_plate} дБ")
                st.write(f"**С покрытием (ΔL = {delta_L} дБ):** Lnw = {Lnw_with_cover} дБ → {status}")

        else:  # Перегородка (воздушный шум)
            if wall_category in ["Гипсокартонные (каркасные)"]:
                # Используем упрощённый расчёт
                Rw = calculate_Rw_frame(sheet_thickness, density, layers, frame, insulation)
                st.subheader("📊 Результат расчёта воздушного шума")
                st.write(f"**Индекс изоляции воздушного шума Rw = {Rw} дБ**")
                margin = norm_Rw - Rw
                if margin >= 0:
                    st.success(f"✅ СООТВЕТСТВУЕТ (запас {margin} дБ)")
                else:
                    st.error(f"❌ НЕ СООТВЕТСТВУЕТ (превышение на {-margin} дБ)")
                st.write(f"Норматив для данного типа здания: Rw ≥ {norm_Rw} дБ")
                # График не строим
            elif density is not None and thickness is not None:
                # Массивная перегородка
                try:
                    Rw, freqs, calc_curve, ref_curve, shift, unfav = calculate_Rw_massive(density, thickness, K)
                    st.subheader("📊 Результат расчёта воздушного шума")
                    st.write(f"**Индекс изоляции воздушного шума Rw = {Rw} дБ**")
                    margin = norm_Rw - Rw
                    if margin >= 0:
                        st.success(f"✅ СООТВЕТСТВУЕТ (запас {margin} дБ)")
                    else:
                        st.error(f"❌ НЕ СООТВЕТСТВУЕТ (превышение на {-margin} дБ)")
                    st.write(f"Норматив: Rw ≥ {norm_Rw} дБ")
                    st.write(f"Сумма неблагоприятных отклонений: {unfav:.1f} дБ")
                    if shift != 0:
                        st.write(f"Оценочная кривая смещена на {shift} дБ")

                    # График частотной характеристики
                    fig, ax = plt.subplots(figsize=(10,6))
                    ax.semilogx(freqs, calc_curve, 'b-', linewidth=2, label='Расчётная кривая')
                    shifted_ref = [r - shift for r in ref_curve]
                    ax.semilogx(freqs, shifted_ref, 'r--', linewidth=2, label=f'Оценочная кривая (смещена на {shift} дБ)')
                    ax.axhline(y=Rw, color='gray', linestyle=':', label=f'Rw = {Rw} дБ')
                    ax.set_xlabel('Частота, Гц')
                    ax.set_ylabel('R, дБ')
                    ax.set_title('Частотная характеристика изоляции воздушного шума')
                    ax.grid(True, which='both', linestyle='--', alpha=0.7)
                    ax.legend()
                    st.pyplot(fig)

                    st.markdown("---")
                    st.subheader("📄 Техническое заключение")
                    conclusion = f"""
**Анализ изоляции воздушного шума**

**1. Исходные данные:**  
Перегородка: {selected_wall}  
Плотность: {density:.0f} кг/м³, толщина: {thickness} мм, коэффициент K = {K}

**2. Расчётный индекс Rw = {Rw} дБ.**  
Норматив для данного типа здания: Rw ≥ {norm_Rw} дБ.

**3. Вывод:** конструкция **{'СООТВЕТСТВУЕТ' if margin>=0 else 'НЕ СООТВЕТСТВУЕТ'}** нормативным требованиям.
"""
                    st.markdown(conclusion)
                    if st.button("💾 Сохранить заключение"):
                        with open("wall_conclusion.txt", "w", encoding="utf-8") as f:
                            f.write(conclusion)
                        st.success("Заключение сохранено")
                except Exception as e:
                    st.error(f"Ошибка расчёта: {e}")
            else:
                st.info("Для выбранного типа перегородки расчёт пока не реализован.")

# -----------------------------------------------------------------
# Заглушки для остальных вкладок (без изменений)
# -----------------------------------------------------------------
def show_thermal_insulation():
    st.header("🔥 Теплоизоляционный расчёт")
    st.info("Раздел в разработке. Здесь будет подбор толщины утеплителя, проверка на конденсат и другие теплотехнические расчёты.")

def show_thermal_loss():
    st.header("📉 Расчёт теплопотерь")
    st.info("Раздел в разработке. Здесь будет расчёт теплопотерь через ограждающие конструкции.")

def show_strength():
    st.header("💪 Прочностные расчёты")
    st.info("Раздел в разработке. Здесь будет оценка деформации под нагрузкой, точечные нагрузки и т.д.")

def show_logistics():
    st.header("📦 Логистические расчёты")
    st.info("Раздел в разработке. Здесь будет расчёт количества рулонов, скотча, жгутов, веса и объема.")

def show_economic():
    st.header("💰 Экономический расчёт")
    st.info("Раздел в разработке. Здесь будет расчёт срока окупаемости утепления.")

def show_pipe_insulation():
    st.header("🧪 Теплоизоляция труб")
    st.info("Раздел в разработке. Здесь будет подбор толщины скорлуп, проверка на конденсат.")

# -----------------------------------------------------------------
# Новая вкладка – расчёт стяжек
# -----------------------------------------------------------------
def show_screed():
    st.header("🧱 Расчёт материалов для стяжки пола")
    st.markdown("Калькулятор позволяет определить количество материалов для различных типов стяжек: мокрая, полусухая, сухая, наливная.")

    with st.form("screed_form"):
        col1, col2 = st.columns(2)
        with col1:
            S = st.number_input("Площадь помещения (м²)", min_value=1.0, max_value=1000.0, value=50.0, step=1.0)
            h_min = st.number_input("Минимальная толщина стяжки (мм)", min_value=20, max_value=200, value=40, step=5)
            h_max = st.number_input("Максимальная толщина стяжки (мм)", min_value=20, max_value=200, value=50, step=5)
        with col2:
            screed_type = st.selectbox("Тип стяжки",
                                        ["Мокрая (цементно-песчаная)",
                                         "Полусухая",
                                         "Сухая (сборная)",
                                         "Наливной пол"])
            cement_mark = st.selectbox("Марка цемента", [400, 500], index=0)
            bag_weight = st.selectbox("Масса мешка цемента (кг)", [25, 40, 50], index=2)

        submitted = st.form_submit_button("Рассчитать")  # кнопка с правильным текстом

    if submitted:
        # Вычисляем среднюю толщину
        h_avg_mm = (h_min + h_max) / 2.0
        h_m = h_avg_mm / 1000.0
        V = S * h_m  # объём раствора, м³

        st.subheader("Результаты расчёта")

        if screed_type == "Мокрая (цементно-песчаная)":
            # Расход цемента и песка на 1 м³ (табличные данные)
            if cement_mark == 400:
                cement_per_m3 = 300
                sand_per_m3 = 900
            else:  # 500
                cement_per_m3 = 330
                sand_per_m3 = 990
            cement_kg = cement_per_m3 * V
            sand_kg = sand_per_m3 * V
            water_l = cement_kg * 0.5  # В/Ц примерно 0.5

            st.write(f"**Объём раствора:** {V:.2f} м³")
            st.write(f"**Цемент:** {cement_kg:.1f} кг → {math.ceil(cement_kg / bag_weight)} мешков по {bag_weight} кг")
            st.write(f"**Песок:** {sand_kg:.1f} кг")
            st.write(f"**Вода:** {water_l:.1f} л")

        elif screed_type == "Полусухая":
            k_us = 1.03  # коэффициент усадки
            V_suh = V * k_us
            # Пропорция 1:3, В/Ц = 0.4
            rho_cem = 1300  # кг/м³
            rho_sand = 1600  # кг/м³
            wc = 0.4
            vol_cement_part = 1
            vol_sand_part = 3
            vol_water_part = (wc * rho_cem) / 1000
            total_parts = vol_cement_part + vol_sand_part + vol_water_part
            cement_vol = V_suh * vol_cement_part / total_parts
            sand_vol = V_suh * vol_sand_part / total_parts
            water_vol = V_suh * vol_water_part / total_parts
            cement_kg = cement_vol * rho_cem
            sand_kg = sand_vol * rho_sand
            water_l = water_vol * 1000
            fiber_kg = (cement_kg / 50) * 0.135  # среднее

            st.write(f"**Объём раствора с учётом усадки:** {V_suh:.2f} м³")
            st.write(f"**Цемент:** {cement_kg:.1f} кг → {math.ceil(cement_kg / bag_weight)} мешков по {bag_weight} кг")
            st.write(f"**Песок:** {sand_kg:.1f} кг")
            st.write(f"**Вода:** {water_l:.1f} л")
            st.write(f"**Полипропиленовая фибра:** {fiber_kg:.2f} кг")

        elif screed_type == "Сухая (сборная)":
            # Керамзит
            rho_keramz = 500  # насыпная плотность кг/м³
            V_keramz = S * h_m
            keramz_kg = V_keramz * rho_keramz * 1.05  # запас 5%
            # ГВЛ
            sheet_area = 0.3335  # 667x500 мм
            sheets_per_layer = math.ceil(S / sheet_area)
            total_sheets = sheets_per_layer * 2  # два слоя
            st.write(f"**Керамзит:** {V_keramz:.2f} м³ ≈ {keramz_kg:.0f} кг")
            st.write(f"**ГВЛ (листы 667×500 мм):** {total_sheets} шт (два слоя)")

        else:  # Наливной пол
            mix_kg = S * h_avg_mm * 1.6
            bags = math.ceil(mix_kg / 25)
            st.write(f"**Готовая смесь:** {mix_kg:.1f} кг → {bags} мешков по 25 кг")

        # Общие материалы
        st.subheader("Дополнительные материалы")
        perim = 2 * math.sqrt(S) * 2  # грубо, но для примера
        primer_l = S * 0.2  # грунтовка 0.2 л/м²
        st.write(f"**Грунтовка:** {primer_l:.1f} л")
        st.write(f"**Демпферная лента:** примерно {perim:.1f} м (периметр)")
        st.write(f"**Армирующая сетка:** рекомендуется площадь сетки = {S:.1f} м² (с нахлёстом)")

# -----------------------------------------------------------------
# Привязка вкладок
# -----------------------------------------------------------------
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
with tabs[7]:
    show_screed()

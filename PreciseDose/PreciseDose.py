#الهه عسکری زاده
"""
نسخهٔ بازنویسی‌شده با Dear PyGui برای دارورسانی شخصی‌شده
تمام محاسبات و معادلات اصلی حفظ شده‌اند
"""

import numpy as np
import dearpygui.dearpygui as dpg
import json
import os
import contextlib
import io
from PIL import Image
import textwrap
#الهه عسکری زاده
# ---- ثابت‌های فیزیکی ----
K_B = 1.380649e-23  # ثابت بولتزمان (J/K)
RESULTS_FILE = "../last_results.json"
RESULTS_STORE = {}


# ---- تابع کمکی برای گرفتن مقدار امن ----
def safe_get(data, key, default):
    val = data.get(key)
    return default if val is None else val


def run_calculations(sender, app_data, user_data):
    data = {}
    # گرفتن ورودی‌ها از UI
    for key in user_data:
        data[key] = dpg.get_value(user_data[key])

    # اصلاح مقادیر None و تنظیم defaults
    data["weight"] = safe_get(data, "weight", 70)
    data["height"] = safe_get(data, "height", 170)
    data["age"] = safe_get(data, "age", 30)
    data["dose"] = safe_get(data, "dose", 100)
    data["lipophilicity"] = safe_get(data, "lipophilicity", 2.5)
    data["mol_radius"] = safe_get(data, "mol_radius", 0.5)
    data["saliva_volume"] = safe_get(data, "saliva_volume", 5.0)
    data["saliva_flow"] = safe_get(data, "saliva_flow", 0.7)
    data["membrane_thickness"] = safe_get(data, "membrane_thickness", 50)
    data["temperature"] = safe_get(data, "temperature", 37)
    data["beta_gene"] = safe_get(data, "beta_gene", 1.0)
    data["theta_nano"] = safe_get(data, "theta_nano", 2.0)
    data["absorption_efficiency"] = safe_get(data, "absorption_efficiency", 0.8)
    data["cl_intrinsic"] = safe_get(data, "cl_intrinsic", 30.0)
    data["serum_creatinine"] = safe_get(data, "serum_creatinine", 1.0)
    data["serum_albumin"] = safe_get(data, "serum_albumin", 4.0)
    data["gender"] = safe_get(data, "gender", 0)

    # اصلاح واحدها
    data["bmi"] = data["weight"] / ((data["height"] / 100) ** 2)
    data["mol_radius"] *= 1e-9
    data["saliva_volume"] /= 1000
    data["saliva_flow"] /= 60000
    data["membrane_thickness"] *= 1e-6
    data["temperature"] += 273.15

    # ---- محاسبات اصلی ----
    viscosity_water = 0.00089
    D = (K_B * data["temperature"]) / (6 * np.pi * viscosity_water * data["mol_radius"])
    K_partition = 10 ** data["lipophilicity"]

    # C_initial در mg/L (دوز تقسیم بر حجم بزاق)
    C_initial = (data["dose"]) / (data["saliva_volume"] * 1000)

    # Flux مقیاس‌شده برای بازه منطقی
    j_basic = max(1e-6, (D * K_partition * C_initial) / (data["membrane_thickness"] * 1e6))
    j_effect = j_basic * data["beta_gene"] * data["theta_nano"]

    # جذب در بخش‌های مختلف
    abs_pharynx = min(data["dose"], data["absorption_efficiency"] * C_initial * 0.02 * 30)
    abs_esophagus = min(data["dose"], 0.04 * C_initial)
    abs_stomach = min(data["dose"], 0.12 * C_initial * (data["weight"] / 70))
    abs_duodenum = min(data["dose"], 0.28 * C_initial)
    abs_jejunum = min(data["dose"], 0.16 * C_initial)

    A_total_absorbed = abs_pharynx + abs_esophagus + abs_stomach + abs_duodenum + abs_jejunum
    A_total_absorbed = min(data["dose"] * 0.8, max(data["dose"] * 0.2, A_total_absorbed))

    # Protein binding
    fu = min(1.0, max(0.01, 0.1 / (1 + 10 ** (data["lipophilicity"] - 2)) * (4.0 / data["serum_albumin"])))

    # Hepatic clearance
    Q_liver = 90 * (data["weight"] / 70)
    E_h = min(1.0, (data["cl_intrinsic"] * fu) / (Q_liver + data["cl_intrinsic"] * fu))
    CL_h = Q_liver * E_h

    # Renal clearance
    if data["gender"] == 0:
        GFR = 0.85 * ((140 - data["age"]) * data["weight"]) / (72 * data["serum_creatinine"])
    else:
        GFR = ((140 - data["age"]) * data["weight"]) / (72 * data["serum_creatinine"])
    CL_r = GFR * fu * 0.06

    # Systemic availability
    systemic_availability = max(0.05, min(0.9, 1 - (CL_h + CL_r) / (A_total_absorbed + 1e-6)))
    systemic_dose = A_total_absorbed * systemic_availability

    # تقسیم ارگان‌ها
    organ_distribution = {
        'Brain': {'percent': 12, 'k': 0.03},
        'Liver': {'percent': 27, 'k': 0.04},
        'Kidney': {'percent': 20, 'k': 0.05},
        'Muscle': {'percent': 15, 'k': 0.02},
        'Skin': {'percent': 5, 'k': 0.01},
        'Spleen': {'percent': 3, 'k': 0.025},
        'Bone': {'percent': 3, 'k': 0.005},
        'Lung': {'percent': 5, 'k': 0.02},
        'Adipose': {'percent': 10, 'k': 0.015}
    }
    times = [30, 60, 120]

    # ---- خروجی ----
    output = []
    output.append("=== Results ===")
    output.append(
        f"Total absorbed dose: {A_total_absorbed:.4f} mg ({A_total_absorbed / data['dose'] * 100:.1f}% of administered dose)"
    )
    output.append(f"Systemic availability (F): {systemic_availability:.4f}")
    output.append(f"Systemic dose: {systemic_dose:.4f} mg")

    output.append("\nOrgan Distribution Over Time (mg):")
    header = "Organ".ljust(15) + "".join([f"t={t}min".ljust(15) for t in times])
    output.append(header)
    for organ, params in organ_distribution.items():
        concentrations = []
        for t in times:
            amount = max(0, (systemic_dose * params['percent'] / 100) * np.exp(-params['k'] * t))
            concentrations.append(f"{amount:.6f}")
        output.append(organ.ljust(15) + "".join([c.ljust(15) for c in concentrations]))

    output.append("\n=== Summary ===")
    output.append(f"Basic flux (j_basic): {j_basic:.6e} mg/m²/s")
    output.append(f"Effective flux (j_effect): {j_effect:.6e} mg/m²/s")
    output.append(f"Pharyngeal absorption: {abs_pharynx:.6f} mg")
    output.append(f"Esophageal absorption: {abs_esophagus:.6f} mg")
    output.append(f"Gastric absorption: {abs_stomach:.6f} mg")
    output.append(f"Duodenal absorption: {abs_duodenum:.6f} mg")
    output.append(f"Jejunal absorption: {abs_jejunum:.6f} mg")
    output.append(f"Hepatic clearance: {CL_h:.6f} L/h")
    output.append(f"Renal clearance: {CL_r:.6f} L/h")
    output.append(f"Bioavailability: {systemic_availability:.4f}")
    output.append("\nOptimization completed successfully!")

    final_text = "\n".join(output)
    dpg.set_value("results_text", final_text)
    # --- ذخیرهٔ خروجی‌های کلیدی برای استفاده در Code Editor user code ---
    try:
        RESULTS_STORE.update({
            "A_total_absorbed": float(A_total_absorbed) if not isinstance(A_total_absorbed, dict) else A_total_absorbed,
            "systemic_availability": float(systemic_availability),
            "systemic_dose": float(systemic_dose),
            "j_basic": float(j_basic),
            "j_effect": float(j_effect),
            "CL_h": float(CL_h),
            "CL_r": float(CL_r),
            "A_total_absorbed_raw": float(A_total_absorbed) if isinstance(A_total_absorbed, (
                int, float, np.floating)) else A_total_absorbed,
            "organ_distribution": organ_distribution
        })
    except Exception:
        # اگر هر چیزی خطا داد نادیده بگیر تا برنامه اصلی کرش نکند
        pass


def load_last_results():
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, "r") as f:
            last = json.load(f)
        dpg.set_value("results_text", last["output"])
    else:
        dpg.set_value("results_text", "No saved results found.")


# ---- تابع‌های کمکی برای Code Editor ----
def load_ready_code(sender, app_data):
    code = ready_codes.get(app_data, "")
    if code:
        dpg.set_value("code_editor", code)


def run_user_code():
    user_code = dpg.get_value("code_editor")
    buffer = io.StringIO()
    try:
        # کتابخانه‌های مورد نیاز که در local scope به کاربر داده می‌شوند
        import numpy as np
        import scipy
        import matplotlib.pyplot as plt
        import seaborn as sns
        import torch
        import sklearn
        from sklearn.cluster import KMeans
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.svm import SVC
        from sklearn.neighbors import KNeighborsClassifier
        from sklearn.linear_model import LinearRegression, LogisticRegression

        # دادهٔ ورودی (inputs) و نتایج محاسبات اصلی (RESULTS_STORE) را در اختیار کد کاربر می‌گذاریم
        local_data = {k: dpg.get_value(inputs[k]) for k in inputs}
        local_results = RESULTS_STORE.copy()  # کپی برای ایمنی

        local_vars = {
            "np": np,
            "scipy": scipy,
            "plt": plt,
            "sns": sns,
            "torch": torch,
            "sklearn": sklearn,
            "KMeans": KMeans,
            "RandomForestClassifier": RandomForestClassifier,
            "SVC": SVC,
            "KNeighborsClassifier": KNeighborsClassifier,
            "LinearRegression": LinearRegression,
            "LogisticRegression": LogisticRegression,
            "data": local_data,  # ورودی‌های UI
            "results": local_results,  # خروجی‌های محاسباتی (systemic_dose, organ_distribution, ...)
            "K_B": 1.380649e-23,
            "dpg": dpg
        }

        # اجرای کد کاربر در محیط محدود
        with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
            exec(user_code, {}, local_vars)

        # خروجی متنی را به results_text اضافه کن
        prev = dpg.get_value("results_text")
        dpg.set_value("results_text", prev + "\n\n=== User Code Output ===\n" + buffer.getvalue())

        # اگر matplotlib تصویر ساخته، آن را به تصویر تبدیل و داخل Results نمایش بده
        if "plt" in local_vars and plt.get_fignums():
            img_buf = io.BytesIO()
            plt.savefig(img_buf, format="png", bbox_inches='tight')
            img_buf.seek(0)

            img = Image.open(img_buf).convert("RGBA")
            arr = np.array(img).astype(np.float32) / 255.0
            height, width, channels = arr.shape

            tex_tag = "plot_texture"
            if not dpg.does_item_exist(tex_tag):
                with dpg.texture_registry(show=False):
                    dpg.add_dynamic_texture(width, height, arr, tag=tex_tag)
                dpg.add_image(tex_tag, parent="results_window")
            else:
                dpg.configure_item(tex_tag, default_value=arr, width=width, height=height)

            plt.close("all")

    except Exception as e:
        prev = dpg.get_value("results_text")
        dpg.set_value("results_text", prev + f"\n\n=== User Code Error ===\n{e}")


# ---- کدهای آماده ----
ready_codes = {
    # --- Basic Descriptive Stats ---
    "Mean / Median / Mode": textwrap.dedent("""\
import numpy as np
from scipy import stats

values = list(data.values())
print("Mean:", np.mean(values))
print("Median:", np.median(values))
print("Mode:", stats.mode(values, keepdims=True).mode[0])
"""),

    "Variance / Std / CV": textwrap.dedent("""\
import numpy as np

values = list(data.values())
var = np.var(values)
std = np.std(values)
cv = std / np.mean(values)
print("Variance:", var)
print("Std Dev:", std)
print("Coefficient of Variation:", cv)
"""),

    # --- Hypothesis Testing ---
    "One-Sample T-Test": textwrap.dedent("""\
import numpy as np
from scipy import stats

values = list(data.values())
t_stat, p_val = stats.ttest_1samp(values, popmean=np.mean(values))
print("T-Statistic:", t_stat, "P-Value:", p_val)
"""),

    "Two-Sample T-Test": textwrap.dedent("""\
import numpy as np
from scipy import stats

#Dividing the data into two hypothetical groups.
vals = list(data.values())
group1, group2 = vals[:len(vals)//2], vals[len(vals)//2:]
t_stat, p_val = stats.ttest_ind(group1, group2, equal_var=False)
print("Two-sample T-test:", t_stat, "P-Value:", p_val)
"""),

    "Paired t-test": """
import numpy as np
from scipy import stats

#Creating data of the same length.
n_samples = min(len(data.get('group1', [])), len(data.get('group2', [])))
if n_samples == 0:
    #Sample data if real data does not exist.
    group1 = np.random.normal(0, 1, 10)
    group2 = np.random.normal(0.5, 1, 10)
else:
    group1 = np.array(data.get('group1', []))[:n_samples]
    group2 = np.array(data.get('group2', []))[:n_samples]

#Run test
t_stat, p_value = stats.ttest_rel(group1, group2)
print(f"T-statistic: {t_stat:.4f}")
print(f"P-value: {p_value:.4f}")
""",

    # --- ANOVA ---
    "ANOVA (One-way)": """
# One-way ANOVA with synthetic groups
from scipy import stats
import numpy as np

g1 = np.random.normal(data.get('systemic_dose', 50), 5, 10)
g2 = np.random.normal(data.get('systemic_dose', 50) * 1.1, 5, 10)
g3 = np.random.normal(data.get('systemic_dose', 50) * 0.9, 5, 10)

f, p = stats.f_oneway(g1, g2, g3)

data["ANOVA F-stat"] = float(f)
data["ANOVA p-value"] = float(p)
print(f"ANOVA F={f:.3f}, p={p:.3f}")
""",

    # --- Chi-Square ---
    "Chi-Square Test": textwrap.dedent("""\
import numpy as np
from scipy import stats

observed = np.array(list(data.values()))
expected = np.full_like(observed, np.mean(observed))
chi2, p_val = stats.chisquare(observed, expected)
print("Chi-Square Test:", chi2, "P-Value:", p_val)
"""),

    # --- Correlation ---
    "Pearson Correlation": """
import numpy as np
from scipy.stats import pearsonr

#Ensuring that arrays are the same length.
x_data = data.get('x', list(range(10)))
y_data = data.get('y', list(range(10, 20)))

min_len = min(len(x_data), len(y_data))
x = np.array(x_data[:min_len])
y = np.array(y_data[:min_len])

corr, p_value = pearsonr(x, y)
print(f"Pearson correlation: {corr:.4f}")
print(f"P-value: {p_value:.4f}")
""",

    "Spearman Correlation": """
import numpy as np
from scipy.stats import spearmanr

x_data = data.get('x', list(range(8)))
y_data = data.get('y', list(range(8)))

#Equalizing arrays.
min_len = min(len(x_data), len(y_data))
x = np.array(x_data[:min_len])
y = np.array(y_data[:min_len])

corr, p_value = spearmanr(x, y)
print(f"Spearman correlation: {corr:.4f}")
print(f"P-value: {p_value:.4f}")
""",

    # --- Regression ---
    "Linear Regression": """
# Simple linear regression with synthetic dataset
import numpy as np
from sklearn.linear_model import LinearRegression
X = np.array(data.get('weight',70)).reshape(-1,1)
y = np.array([data.get('systemic_dose',100)])
model = LinearRegression().fit(X, y)
pred = model.predict([[70]])
data["Linear Regression Prediction"] = float(pred[0])
print("Linear Regression prediction at 70kg:", pred[0])
""",

    "Multiple Linear Regression": textwrap.dedent("""\
import numpy as np
from sklearn.linear_model import LinearRegression

vals = list(data.values())
X = np.column_stack([np.arange(len(vals)), np.random.randn(len(vals))])
y = np.array(vals)
model = LinearRegression().fit(X, y)
print("Coefs:", model.coef_, "Intercept:", model.intercept_)
"""),

    "Logistic Regression": """
# Logistic regression with synthetic binary data
import numpy as np
from sklearn.linear_model import LogisticRegression
X = np.array([[data.get('weight',70)], [80], [60], [90]])
y = np.array([0, 1, 0, 1]) # binary outcome
model = LogisticRegression().fit(X, y)
pred = model.predict([[data.get('weight',70)]])
data["Logistic Regression Prediction"] = int(pred[0])
print("Logistic regression prediction for current weight:", pred[0])
""",

    # --- Factor Analysis & PCA ---
    "Factor Analysis": """
import numpy as np
import pandas as pd
from sklearn.decomposition import FactorAnalysis

#DataFrame
df = pd.DataFrame([data]) #Even if it's just one example.
n_components = min(1, df.shape[0], df.shape[1])

#Factor Analysis
fa = FactorAnalysis(n_components=n_components)
fa_result = fa.fit_transform(df)

data["Factor Loadings"] = fa_result.tolist()
data["Factor Loadings"] = fa_result.tolist()
print("Factor loadings:", fa_result.tolist())
""",

    "PCA": """
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA

#DataFrame
df = pd.DataFrame([data])
n_components = min(2, df.shape[0], df.shape[1])

#PCA
pca = PCA(n_components=n_components)
pca_result = pca.fit_transform(df)

data["PCA Components"] = pca_result.tolist()
data["PCA Components"] = pca_result.tolist()
print("PCA components:", pca_result.tolist())
""",
    # --- Machine Learning ---
    "ML - make_synthetic_features": textwrap.dedent("""\
# Utility: build a numeric feature vector from inputs
import numpy as np
# features: weight, height, dose, lipophilicity, mol_radius (nm)
feat = np.array([
    float(data.get('weight',70)),
    float(data.get('height',170)),
    float(data.get('dose',100)),
    float(data.get('lipophilicity',2.5)),
    float(data.get('mol_radius',0.5))
], dtype=float)
print('Feature vector (weight,height,dose,logP,mol_radius):', feat.tolist())
"""),

    "K-Means Clustering": textwrap.dedent("""\
import numpy as np
from sklearn.cluster import KMeans

#Create sample data for clustering (if available, real data should be substituted.)
X = np.array([
    [data.get('weight', 70), data.get('dose', 100)],
    [data.get('weight', 70)*1.2, data.get('dose', 100)*0.8],
    [data.get('weight', 70)*0.8, data.get('dose', 100)*1.2],
    [data.get('weight', 70)*1.1, data.get('dose', 100)*0.9]
])

kmeans = KMeans(n_clusters=2, random_state=42).fit(X)
cluster_labels = kmeans.predict(X)
print("Cluster labels:", cluster_labels)
print("Cluster centers:", kmeans.cluster_centers_)
print("Input data belongs to cluster:", cluster_labels[0])
"""),

    "Random Forest Classifier": textwrap.dedent("""\
import numpy as np
from sklearn.ensemble import RandomForestClassifier

#Direct use of input data.
X = np.array([[data.get('weight',70), data.get('dose',100), data.get('lipophilicity',2.5)]])
y = np.array([1 if data.get('dose',100) > 80 else 0]) # simple goal

clf = RandomForestClassifier(n_estimators=10, random_state=42)
clf.fit(X, y)
pred = clf.predict(X)[0]
print('RandomForest prediction:', pred)
"""),

    "SVM Classifier": textwrap.dedent("""\
import numpy as np
from sklearn.svm import SVC

#Increasing sample data to create multiple classes.
X = np.array([
    [data.get('weight',70), data.get('dose',100), data.get('lipophilicity',2.5)],
    [80, 120, 3.0], 
    [60, 80, 2.0], 
    [90, 150, 3.5] 
])
y = np.array([1, 1, 0, 1]) # different class

clf = SVC(kernel='linear')
clf.fit(X, y)
pred = clf.predict([[data.get('weight',70), data.get('dose',100), data.get('lipophilicity',2.5)]])[0]
print('SVM prediction:', pred)
"""),

    "K-Nearest Neighbors": textwrap.dedent("""\
import numpy as np
from sklearn.neighbors import KNeighborsClassifier

#Direct use of input data.
X = np.array([[data.get('weight',70), data.get('dose',100), data.get('lipophilicity',2.5)]])
y = np.array([1 if data.get('dose',100) > 80 else 0]) # simple goal

knn = KNeighborsClassifier(n_neighbors=1)
knn.fit(X, y)
pred = knn.predict(X)[0]
print('KNN prediction:', pred)
"""),
    "Bar Chart (Input Values)": textwrap.dedent("""\
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import io
from PIL import Image

# Create bar chart from input values
labels = ['Weight', 'Dose', 'Lipophilicity']
values = [data.get('weight', 70), data.get('dose', 100), data.get('lipophilicity', 2.5)]

plt.figure(figsize=(8, 4))
plt.bar(labels, values, color=['blue', 'green', 'red'])
plt.title('Input Parameters')
plt.ylabel('Values')
plt.xticks(rotation=45)
plt.tight_layout()

# Convert plot to texture
buf = io.BytesIO()
plt.savefig(buf, format='png', bbox_inches='tight')
buf.seek(0)
img = Image.open(buf).convert('RGBA')
arr = np.array(img).astype(np.float32) / 255.0

# Display in DPG
tex_tag = "bar_chart_texture"
if dpg.does_item_exist(tex_tag):
    dpg.configure_item(tex_tag, default_value=arr)
else:
    with dpg.texture_registry(show=False):
        dpg.add_dynamic_texture(width=img.width, height=img.height, default_value=arr, tag=tex_tag)
    dpg.add_image(tex_tag, parent="results_window")

plt.close()
print("Bar chart displayed in results window")
"""),
    # ---- Visualization & Plotting Ready Codes ----
    "Basic Line Plot": """
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import io
from PIL import Image

try:
    # Create simple line plot
    x = np.linspace(0, 10, 100)
    y = np.sin(x)

    plt.figure(figsize=(8, 4))
    plt.plot(x, y, 'b-', linewidth=2)
    plt.title('Sine Wave')
    plt.xlabel('X-axis')
    plt.ylabel('Y-axis')
    plt.grid(True)
    plt.tight_layout()

    # Convert plot to texture for DPG
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    img = Image.open(buf).convert('RGBA')
    arr = np.array(img).astype(np.float32) / 255.0
    height, width, channels = arr.shape

    # Display in results tab
    tex_tag = "basic_line_plot_texture"


    if dpg.does_item_exist(tex_tag):
        dpg.delete_item(tex_tag)


    plot_group_tag = "plot_group_basic_line"
    if dpg.does_item_exist(plot_group_tag):
        dpg.delete_item(plot_group_tag)


    results_tab = None
    for item in dpg.get_all_items():
        if dpg.get_item_label(item) == "Results":
            results_tab = item
            break

    if results_tab:

        with dpg.group(tag=plot_group_tag, parent=results_tab):
            dpg.add_text("=== Basic Line Plot ===")
            with dpg.texture_registry(show=False):
                dpg.add_dynamic_texture(width=width, height=height, default_value=arr, tag=tex_tag)
            dpg.add_image(tex_tag, width=min(600, width))

    plt.close()
    print("✓ Basic line plot displayed in Results tab")

except Exception as e:
    print(f"Error in Basic Line Plot: {e}")
""",

    "Time Series Simulation": """
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import io
from PIL import Image

try:
    # Simulate time series data
    time_points = np.arange(0, 24, 0.1)
    concentration = data.get('dose', 100) * np.exp(-0.1 * time_points)

    plt.figure(figsize=(10, 4))
    plt.plot(time_points, concentration, 'r-', linewidth=2)
    plt.title('Drug Concentration Over Time')
    plt.xlabel('Time (hours)')
    plt.ylabel('Concentration')
    plt.grid(True)
    plt.tight_layout()

    # Convert to texture
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    img = Image.open(buf).convert('RGBA')
    arr = np.array(img).astype(np.float32) / 255.0
    height, width, channels = arr.shape

    # Display in results tab
    tex_tag = "time_series_plot_texture"
    plot_group_tag = "plot_group_time_series"


    if dpg.does_item_exist(tex_tag):
        dpg.delete_item(tex_tag)
    if dpg.does_item_exist(plot_group_tag):
        dpg.delete_item(plot_group_tag)


    results_tab = None
    for item in dpg.get_all_items():
        if dpg.get_item_label(item) == "Results":
            results_tab = item
            break

    if results_tab:
        with dpg.group(tag=plot_group_tag, parent=results_tab):
            dpg.add_text("=== Time Series Plot ===")
            with dpg.texture_registry(show=False):
                dpg.add_dynamic_texture(width=width, height=height, default_value=arr, tag=tex_tag)
            dpg.add_image(tex_tag, width=min(600, width))

    plt.close()
    print("✓ Time series plot displayed in Results tab")

except Exception as e:
    print(f"Error in Time Series Plot: {e}")
""",

    "Simple 2D Plot": """
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import io
from PIL import Image

try:
    # Simple 2D function plot
    x = np.linspace(-5, 5, 100)
    y = x**2 + 2*x + 1

    plt.figure(figsize=(8, 4))
    plt.plot(x, y, 'g-', linewidth=2)
    plt.title('Quadratic Function: y = x² + 2x + 1')
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.grid(True)
    plt.tight_layout()

    # Convert to texture
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    img = Image.open(buf).convert('RGBA')
    arr = np.array(img).astype(np.float32) / 255.0
    height, width, channels = arr.shape

    # Display in results tab
    tex_tag = "quadratic_plot_texture"
    plot_group_tag = "plot_group_quadratic"

    if dpg.does_item_exist(tex_tag):
        dpg.delete_item(tex_tag)
    if dpg.does_item_exist(plot_group_tag):
        dpg.delete_item(plot_group_tag)


    results_tab = None
    for item in dpg.get_all_items():
        if dpg.get_item_label(item) == "Results":
            results_tab = item
            break

    if results_tab:
        with dpg.group(tag=plot_group_tag, parent=results_tab):
            dpg.add_text("=== Quadratic Plot ===")
            with dpg.texture_registry(show=False):
                dpg.add_dynamic_texture(width=width, height=height, default_value=arr, tag=tex_tag)
            dpg.add_image(tex_tag, width=min(600, width))

    plt.close()
    print("✓ Quadratic plot displayed in Results tab")

except Exception as e:
    print(f"Error in Quadratic Plot: {e}")
""",

    "Bar Chart (Input Values)": """
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import io
from PIL import Image

try:
    # Create bar chart from input values
    labels = ['Weight', 'Dose', 'Lipophilicity']
    values = [data.get('weight', 70), data.get('dose', 100), data.get('lipophilicity', 2.5)]

    plt.figure(figsize=(8, 4))
    plt.bar(labels, values, color=['blue', 'green', 'red'], alpha=0.7)
    plt.title('Input Parameters')
    plt.ylabel('Values')
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Convert to texture
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    img = Image.open(buf).convert('RGBA')
    arr = np.array(img).astype(np.float32) / 255.0
    height, width, channels = arr.shape

    # Display in results tab
    tex_tag = "bar_chart_texture"
    plot_group_tag = "plot_group_bar_chart"

    if dpg.does_item_exist(tex_tag):
        dpg.delete_item(tex_tag)
    if dpg.does_item_exist(plot_group_tag):
        dpg.delete_item(plot_group_tag)


    results_tab = None
    for item in dpg.get_all_items():
        if dpg.get_item_label(item) == "Results":
            results_tab = item
            break

    if results_tab:
        with dpg.group(tag=plot_group_tag, parent=results_tab):
            dpg.add_text("=== Bar Chart ===")
            with dpg.texture_registry(show=False):
                dpg.add_dynamic_texture(width=width, height=height, default_value=arr, tag=tex_tag)
            dpg.add_image(tex_tag, width=min(600, width))

    plt.close()
    print("✓ Bar chart displayed in Results tab")

except Exception as e:
    print(f"Error in Bar Chart: {e}")
""",

    "Histogram (Parameter Distribution)": """
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import io
from PIL import Image

try:
    # Create histogram of parameter values
    parameters = [data.get('weight', 70), data.get('dose', 100), 
                  data.get('lipophilicity', 2.5), data.get('age', 30),
                  data.get('mol_radius', 0.5)]

    plt.figure(figsize=(8, 4))
    plt.hist(parameters, bins=8, alpha=0.7, edgecolor='black', color='skyblue')
    plt.title('Parameter Value Distribution')
    plt.xlabel('Values')
    plt.ylabel('Frequency')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    # Convert to texture
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    img = Image.open(buf).convert('RGBA')
    arr = np.array(img).astype(np.float32) / 255.0
    height, width, channels = arr.shape

    # Display in results tab
    tex_tag = "histogram_texture"
    plot_group_tag = "plot_group_histogram"

    if dpg.does_item_exist(tex_tag):
        dpg.delete_item(tex_tag)
    if dpg.does_item_exist(plot_group_tag):
        dpg.delete_item(plot_group_tag)


    results_tab = None
    for item in dpg.get_all_items():
        if dpg.get_item_label(item) == "Results":
            results_tab = item
            break

    if results_tab:
        with dpg.group(tag=plot_group_tag, parent=results_tab):
            dpg.add_text("=== Histogram ===")
            with dpg.texture_registry(show=False):
                dpg.add_dynamic_texture(width=width, height=height, default_value=arr, tag=tex_tag)
            dpg.add_image(tex_tag, width=min(600, width))

    plt.close()
    print("✓ Histogram displayed in Results tab")

except Exception as e:
    print(f"Error in Histogram: {e}")
""",

    "Box Plot (Multiple Parameters)": """
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import io
from PIL import Image

try:
    # Create box plot for multiple parameters
    param_names = ['Weight', 'Dose', 'Lipophilicity', 'Mol Radius']
    param_values = [
        [data.get('weight', 70), 65, 75, 80, 70, 72, 68],
        [data.get('dose', 100), 90, 110, 120, 100, 105, 95],
        [data.get('lipophilicity', 2.5), 2.0, 2.8, 3.2, 2.5, 2.7, 2.3],
        [data.get('mol_radius', 0.5), 0.4, 0.6, 0.55, 0.45, 0.52, 0.48]
    ]

    plt.figure(figsize=(8, 4))
    plt.boxplot(param_values, labels=param_names)
    plt.title('Parameter Distribution Box Plot')
    plt.ylabel('Values')
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Convert to texture
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    img = Image.open(buf).convert('RGBA')
    arr = np.array(img).astype(np.float32) / 255.0
    height, width, channels = arr.shape

    # Display in results tab
    tex_tag = "box_plot_texture"
    plot_group_tag = "plot_group_box_plot"

    if dpg.does_item_exist(tex_tag):
        dpg.delete_item(tex_tag)
    if dpg.does_item_exist(plot_group_tag):
        dpg.delete_item(plot_group_tag)


    results_tab = None
    for item in dpg.get_all_items():
        if dpg.get_item_label(item) == "Results":
            results_tab = item
            break

    if results_tab:
        with dpg.group(tag=plot_group_tag, parent=results_tab):
            dpg.add_text("=== Box Plot ===")
            with dpg.texture_registry(show=False):
                dpg.add_dynamic_texture(width=width, height=height, default_value=arr, tag=tex_tag)
            dpg.add_image(tex_tag, width=min(600, width))

    plt.close()
    print("✓ Box plot displayed in Results tab")

except Exception as e:
    print(f"Error in Box Plot: {e}")
""",

    "Scatter Plot (Weight vs Dose)": """
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import io
from PIL import Image

try:
    # Create scatter plot
    weights = [data.get('weight', 70), 65, 80, 75, 72, 68, 82]
    doses = [data.get('dose', 100), 90, 110, 95, 105, 98, 115]

    plt.figure(figsize=(8, 4))
    plt.scatter(weights, doses, color='red', s=50, alpha=0.7)
    plt.title('Weight vs Dose Relationship')
    plt.xlabel('Weight')
    plt.ylabel('Dose')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    # Convert to texture
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    img = Image.open(buf).convert('RGBA')
    arr = np.array(img).astype(np.float32) / 255.0
    height, width, channels = arr.shape

    # Display in results tab
    tex_tag = "scatter_plot_texture"
    plot_group_tag = "plot_group_scatter"

    if dpg.does_item_exist(tex_tag):
        dpg.delete_item(tex_tag)
    if dpg.does_item_exist(plot_group_tag):
        dpg.delete_item(plot_group_tag)


    results_tab = None
    for item in dpg.get_all_items():
        if dpg.get_item_label(item) == "Results":
            results_tab = item
            break

    if results_tab:
        with dpg.group(tag=plot_group_tag, parent=results_tab):
            dpg.add_text("=== Scatter Plot ===")
            with dpg.texture_registry(show=False):
                dpg.add_dynamic_texture(width=width, height=height, default_value=arr, tag=tex_tag)
            dpg.add_image(tex_tag, width=min(600, width))

    plt.close()
    print("✓ Scatter plot displayed in Results tab")

except Exception as e:
    print(f"Error in Scatter Plot: {e}")
""",
    # ---- Bioinformatics & Pharmaceutical Ready Codes ----
    "Calculate Lipophilicity (logP) from SMILES": textwrap.dedent("""\
# Estimated logP calculation from molecular structure
# Note: This is a simplified estimation
mol_weight = data.get('weight', 70)
dose = data.get('dose', 100)

# Simple logP estimation based on molecular weight and dose
if mol_weight < 200:
    estimated_logP = 1.5 + (dose / 100) * 0.5
elif mol_weight < 400:
    estimated_logP = 2.5 + (dose / 100) * 0.3
else:
    estimated_logP = 3.5 + (dose / 100) * 0.2

print(f"Estimated Lipophilicity (logP): {estimated_logP:.2f}")
print("Note: This is a rough estimation based on molecular weight and dose")
"""),

    "Predict Molecular Radius from Properties": textwrap.dedent("""\
# Estimate molecular radius from molecular weight and lipophilicity
mol_weight = data.get('weight', 70) # Using weight as molecular weight proxy
lipophilicity = data.get('lipophilicity', 2.5)

# Empirical formula for radius estimation (angstroms)
# Based on relationship: radius ∝ (molecular_weight)^(1/3)
estimated_radius = 0.5 * (mol_weight / 100) ** (1/3) * (1 + 0.1 * lipophilicity)

print(f"Estimated Molecular Radius: {estimated_radius:.2f} nm")
print("Note: 0.3-0.6 nm typical for small molecules, 1-10 nm for nanoparticles")
"""),

    "Estimate Membrane Permeability": textwrap.dedent("""\
# Predict membrane permeability based on drug properties
logP = data.get('lipophilicity', 2.5)
mol_weight = data.get('weight', 70) # Molecular weight proxy
mol_radius = data.get('mol_radius', 0.5)

# Simplified permeability prediction
# Optimal logP for permeability: 1-3
if 1.0 <= logP <= 3.0:
    permeability_score = "High"
elif logP < 1.0:
    permeability_score = "Low (too hydrophilic)"
else:
    permeability_score = "Low (too lipophilic)"

# Molecular weight consideration
if mol_weight > 500:
    permeability_score += " - High MW may limit permeability"

print(f"Predicted Membrane Permeability: {permeability_score}")
print(f"Optimal logP range: 1.0 - 3.0")
print(f"Your logP: {logP}")
"""),

    "Predict Oral Bioavailability": textwrap.dedent("""\
# Estimate oral bioavailability based on key parameters
logP = data.get('lipophilicity', 2.5)
mol_weight = data.get('weight', 70)
dose = data.get('dose', 100)

# Bioavailability scoring system
score = 0

# Lipophilicity score
if 1.0 <= logP <= 3.0:
    score += 3
elif 0.5 <= logP < 1.0 or 3.0 < logP <= 4.0:
    score += 1
else:
    score -= 2

# Molecular weight score
if mol_weight < 500:
    score += 2
elif mol_weight < 800:
    score += 1
else:
    score -= 1

# Dose score
if dose < 100:
    score += 2
elif dose < 500:
    score += 1
else:
    score -= 1

# Convert score to bioavailability estimate
if score >= 4:
    bioavailability = "High (>70%)"
elif score >= 2:
    bioavailability = "Moderate (30-70%)"
elif score >= 0:
    bioavailability = "Low (10-30%)"
else:
    bioavailability = "Very Low (<10%)"

print(f"Predicted Oral Bioavailability: {bioavailability}")
print(f"Total Score: {score}/7")
"""),

    "Estimate Plasma Protein Binding": textwrap.dedent("""\
# Predict plasma protein binding percentage
logP = data.get('lipophilicity', 2.5)
mol_weight = data.get('weight', 70)

# Empirical relationship: higher logP → higher protein binding
if logP < 1.0:
    protein_binding = 20 + (logP * 10)
elif logP < 3.0:
    protein_binding = 30 + (logP * 20)
elif logP < 5.0:
    protein_binding = 70 + (logP * 10)
else:
    protein_binding = 95 # Very lipophilic drugs are highly bound

# Adjust for molecular weight
if mol_weight > 500:
    protein_binding = min(99, protein_binding + 10)

print(f"Estimated Plasma Protein Binding: {protein_binding:.1f}%")
print("Typical range: 20-99%")
"""),

    "Predict Volume of Distribution (Vd)": textwrap.dedent("""\
# Estimate volume of distribution
logP = data.get('lipophilicity', 2.5)
mol_weight = data.get('weight', 70)
# Vd estimation based on lipophilicity
# More lipophilic → higher Vd (distributes to tissues)
if logP < 1.0:
    vd = 0.1 * mol_weight # L/kg
elif logP < 3.0:
    vd = 0.3 * mol_weight
elif logP < 5.0:
    vd = 0.7 * mol_weight
else:
    vd = 1.2 * mol_weight

print(f"Estimated Volume of Distribution: {vd:.1f} L")
print(f"Per kg: {vd/mol_weight:.2f} L/kg")
print("Typical Vd: 0.1-20 L/kg")
"""),

    "Predict Half-life (t½)": textwrap.dedent("""\
# Estimate elimination half-life
logP = data.get('lipophilicity', 2.5)
mol_weight = data.get('weight', 70)
vd = 0.5 * mol_weight # Estimated Vd

# Half-life estimation (hours)
# Simplified: t½ ∝ Vd and lipophilicity
half_life = (vd / 10) * (1 + 0.5 * logP)

# Adjust for molecular weight
if mol_weight > 500:
    half_life *= 1.5 # Larger molecules may have longer half-life

print(f"Estimated Elimination Half-life: {half_life:.1f} hours")
print("Typical range: 1-24 hours for most drugs")
"""),

    "Predict Clearance Rate": textwrap.dedent("""\
# Estimate clearance rate
logP = data.get('lipophilicity', 2.5)
mol_weight = data.get('weight', 70)

# Clearance estimation (L/h)
# Hepatic clearance model
if logP < 2.0:
    clearance = 5 + (mol_weight / 10) # More hydrophilic
elif logP < 4.0:
    clearance = 10 + (mol_weight / 8) # Moderate
else:
    clearance = 15 + (mol_weight / 6) # Lipophilic

print(f"Estimated Clearance Rate: {clearance:.1f} L/h")
print("Typical range: 5-50 L/h")
"""),

    "Drug-Drug Interaction Risk": textwrap.dedent("""\
# Predict potential for drug-drug interactions
logP = data.get('lipophilicity', 2.5)
mol_weight = data.get('weight', 70)

# Interaction risk assessment
risk_factors = []

# CYP inhibition risk (lipophilic drugs more likely)
if logP > 3.0:
    risk_factors.append("High lipophilicity → CYP inhibition risk")

# Protein binding displacement risk
if logP > 4.0:
    risk_factors.append("High protein binding → displacement interactions")

# Metabolic stability
if 2.0 <= logP <= 4.0:
    risk_factors.append("Moderate metabolism → potential interactions")

if risk_factors:
    print("Potential Drug-Drug Interaction Risks:")
    for risk in risk_factors:
        print(f"• {risk}")
else:
    print("Low risk of significant drug-drug interactions")
"""),

    "Formulation Recommendation": textwrap.dedent("""\
# Suggest appropriate formulation based on properties
logP = data.get('lipophilicity', 2.5)
mol_weight = data.get('weight', 70)
dose = data.get('dose', 100)

recommendations = []

# Solubility considerations
if logP < 1.0:
    recommendations.append("Highly hydrophilic → good aqueous solubility")
elif logP > 4.0:
    recommendations.append("Highly lipophilic → consider solubilization techniques")

# Dose considerations
if dose > 500:
    recommendations.append("High dose → may require specialized formulation")

# Molecular weight considerations
if mol_weight > 800:
    recommendations.append("Large molecule → consider advanced delivery systems")

print("Formulation Recommendations:")
if recommendations:
    for rec in recommendations:
        print(f"• {rec}")
else:
    print("• Standard immediate-release tablet likely suitable")
""")
}

# ---- ساخت UI ----
dpg.create_context()
dpg.create_viewport(title="Drug Delivery Optimization", width=1200, height=800)

# ---- تم سفید با دکمه‌های رنگی ----
with dpg.theme() as global_theme:
    with dpg.theme_component(dpg.mvAll):
        dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (255, 255, 255, 255), category=dpg.mvThemeCat_Core)
        dpg.add_theme_color(dpg.mvThemeCol_Text, (255, 255, 255, 255), category=dpg.mvThemeCat_Core)
        dpg.add_theme_color(dpg.mvThemeCol_Button, (250, 45, 10, 150), category=dpg.mvThemeCat_Core)  # رنگ دکمه
        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (255, 100, 40, 100), category=dpg.mvThemeCat_Core)
        dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (255, 60, 30, 100), category=dpg.mvThemeCat_Core)

        dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (0, 30, 60, 240),
                            category=dpg.mvThemeCat_Core)  # پس زمینه دو ص دیگه
        dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (0, 30, 60, 255),
                            category=dpg.mvThemeCat_Core)  # هاور برای فرم کد

        dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5, category=dpg.mvThemeCat_Core)
        dpg.add_theme_style(dpg.mvStyleVar_ButtonTextAlign, 0.5, 0.5, category=dpg.mvThemeCat_Core)

    with dpg.theme_component(dpg.mvInputFloat):
        dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (255, 80, 50, 100), category=dpg.mvThemeCat_Core)

    with dpg.theme_component(dpg.mvButton):
        dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 8, category=dpg.mvThemeCat_Core)
        dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 10, 5, category=dpg.mvThemeCat_Core)

dpg.bind_theme(global_theme)

# ---- پنجره اصلی ----
with dpg.window(label="PreciseDose - Drug Delivery Optimization", width=1180, height=760):
    # ---- تب‌ها برای سازماندهی ----
    with dpg.tab_bar():
        # ---- تب پارامترهای ورودی ----
        with dpg.tab(label="Input Parameters"):
            dpg.add_text("Patient & Drug Parameters")
            dpg.add_separator()

            import dearpygui.dearpygui as dpg
            import sys
            import os


            def resource_path(relative_path):
                # وقتی exe شد، فایل‌ها در _MEIPASS هستند
                if hasattr(sys, '_MEIPASS'):
                    return os.path.join(sys._MEIPASS, relative_path)
                return relative_path


            image_path = resource_path("../precise.webp")

            with dpg.child_window(width=1150, height=650):
                try:
                    width, height, channels, data = dpg.load_image(image_path)
                    with dpg.texture_registry():
                        texture_id = dpg.add_static_texture(width, height, data)

                    background = dpg.add_image(texture_id, width=1140, height=400)
                    dpg.bind_item_theme(background, dpg.add_theme_color(dpg.mvThemeCol_WindowBg, [255, 255, 255, 250]))
                except Exception as e:
                    #print(f"خطا در بارگیری تصویر: {e}")
                    dpg.add_text("Enter your case study information.")

                # محتوای اصلی
                with dpg.group():
                    inputs = {}
                    inputs["age"] = dpg.add_input_float(label="Age (years)", default_value=30, min_value=0)
                    inputs["weight"] = dpg.add_input_float(label="Weight (kg)", default_value=70, min_value=10)
                    inputs["height"] = dpg.add_input_float(label="Height (cm)", default_value=170, min_value=40)


                    def validate_gender(sender, app_data, user_data):
                        value = app_data
                        if value not in [0, 1]:
                            dpg.set_value(sender, user_data)
                            print("Error: Gender must be 0 (Female) or 1 (Male)")
                        else:
                            dpg.set_item_user_data(sender, value)


                    def validate_gender(sender, app_data, user_data):
                        """اعتبارسنجی کامل مقدار جنسیت"""
                        value = app_data

                        # بررسی آیا مقدار در محدوده مجاز است
                        if value not in [0, 1]:
                            # بازگشت به مقدار قبلی معتبر
                            dpg.set_value(sender, user_data)

                            # نمایش پیغام خطا (اختیاری)
                            print("Error: Gender must be 0 (Female) or 1 (Male)")
                        else:
                            # ذخیره مقدار معتبر برای استفاده بعدی
                            dpg.set_item_user_data(sender, value)


                    # ایجاد input برای جنسیت
                    inputs["gender"] = dpg.add_input_float(
                        label="Gender (0=Female, 1=Male)",
                        default_value=0,
                        min_value=0,
                        max_value=1,
                        callback=validate_gender,
                        user_data=0  # مقدار معتبر اولیه
                    )

                    # ایجاد تم یکسان با بقیه inputها
                    with dpg.theme() as gender_theme:
                        with dpg.theme_component(dpg.mvInputFloat):
                            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (255, 80, 50, 100))
                            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (120, 70, 170, 100))
                            dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (80, 40, 130, 100))

                    dpg.bind_item_theme(inputs["gender"], gender_theme)
                    inputs["dose"] = dpg.add_input_float(label="Dose (mg)", default_value=100, min_value=1)
                    inputs["lipophilicity"] = dpg.add_input_float(label="Lipophilicity (logP)", default_value=2.5,
                                                                  min_value=-3)
                    inputs["mol_radius"] = dpg.add_input_float(label="Molecular radius (nm)", default_value=0.5,
                                                               min_value=0.2)
                    inputs["saliva_volume"] = dpg.add_input_float(label="Saliva volume (mL)", default_value=5.0,
                                                                  min_value=0.5)
                    inputs["saliva_flow"] = dpg.add_input_float(label="Saliva flow (mL/min)", default_value=0.7,
                                                                min_value=0.1)
                    inputs["membrane_thickness"] = dpg.add_input_float(label="Mucosal thickness (µm)", default_value=50,
                                                                       min_value=10)
                    inputs["temperature"] = dpg.add_input_float(label="Body temperature (°C)", default_value=37,
                                                                min_value=35)
                    inputs["beta_gene"] = dpg.add_input_float(label="Genetic modifier (0.5-2.0)", default_value=1.0,
                                                              min_value=0.5)
                    inputs["theta_nano"] = dpg.add_input_float(label="Nanoformulation scaling (1-10)",
                                                               default_value=2.0,
                                                               min_value=1)
                    inputs["absorption_efficiency"] = dpg.add_input_float(label="Absorption efficiency (0-1)",
                                                                          default_value=0.8, min_value=0, max_value=1)
                    inputs["cl_intrinsic"] = dpg.add_input_float(label="Intrinsic clearance (L/h)", default_value=30.0,
                                                                 min_value=0)
                    inputs["serum_creatinine"] = dpg.add_input_float(label="Serum creatinine (mg/dL)",
                                                                     default_value=1.0,
                                                                     min_value=0.1)
                    inputs["serum_albumin"] = dpg.add_input_float(label="Serum albumin (g/dL)", default_value=4.0,
                                                                  min_value=2.0)

                    with dpg.group(horizontal=True):
                        dpg.add_button(label="Run Optimization", callback=run_calculations, user_data=inputs, width=180)
                        dpg.add_button(label="Load Last Results", callback=load_last_results, width=180)

        # ---- تب نتایج ----
        with dpg.tab(label="Results"):
            dpg.add_input_text(tag="results_text", multiline=True, readonly=True, width=1150, height=650)

        # ---- تب Code Editor ----
        with dpg.tab(label="Code Editor"):
            dpg.add_combo(items=list(ready_codes.keys()), label="Ready-made codes", callback=load_ready_code, width=300)
            dpg.add_input_text(tag="code_editor", multiline=True, width=1150, height=550,
                               default_value="# Write your Python code here")

            # دکمه Run Code با رنگ آبی
            run_code_btn = dpg.add_button(label="Run Code", callback=run_user_code, width=100)




# ---- اجرای اپ ----
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()

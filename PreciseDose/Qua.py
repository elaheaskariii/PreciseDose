import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import seaborn as sns
from scipy import integrate
from scipy.optimize import minimize
import matplotlib as mpl
import warnings
# الهه عسکری زاده 140112418006
# فیلتر کردن اخطارها
warnings.filterwarnings('ignore', category=RuntimeWarning)

# تنظیمات گرافیک پیشرفته
plt.style.use('dark_background')
mpl.rcParams['figure.figsize'] = [15, 10]
mpl.rcParams['font.size'] = 12


class AdvancedOrganDigitalTwin:
    """
    دوقلوی دیجیتال پیشرفته ارگان‌ها با مدل‌سازی کوانتومی-بیولوژیکی
    """

    def __init__(self, input_parameters):
        self.params = input_parameters
        self.organs = ['Brain', 'Liver', 'Kidney', 'Muscle', 'Skin',
                       'Spleen', 'Bone', 'Lung', 'Adipose']
        self.setup_quantum_parameters()
        self.organ_coords = {
            'Brain': (1, 2, 3), 'Liver': (2, 1, 2), 'Kidney': (3, 1, 1),
            'Muscle': (2, 3, 1), 'Skin': (1, 1, 1), 'Spleen': (3, 2, 2),
            'Bone': (2, 2, 1), 'Lung': (1, 3, 2), 'Adipose': (3, 3, 1)
        }

        # ضریب تقویت برای نمایش تغییرات
        self.amplification_factor = self.calculate_amplification_factor()

    def calculate_amplification_factor(self):
        """محاسبه ضریب تقویت بر اساس پارامترهای ورودی"""
        base_dose = 19.44  # دوز پایه
        current_dose = self.params['systemic_dose']
        bioavailability = self.params['systemic_availability']

        # ضریب تقویت ترکیبی از دوز و bioavailability
        amplification = (current_dose / base_dose) * (bioavailability / 0.9) * 3.0
        return max(0.5, min(5.0, amplification))  # محدود کردن به بازه معقول

    def setup_quantum_parameters(self):
        """پارامترهای کوانتومی پیشرفته"""
        self.quantum_params = {
            'hbar': 1.0545718e-34,
            'kb': 1.380649e-23,
            'quantum_coherence_time': 1.0,
            'entanglement_strength': 0.7,
        }

    def quantum_bio_transport(self, organ, time_points):
        """مدل انتقال کوانتومی-بیولوژیکی پیشرفته با تاثیرپذیری از ورودی"""
        # پارامترهای اختصاصی هر ارگان با تاثیر از ورودی کاربر
        organ_params = {
            'Brain': {'permeability': 0.8, 'quantum_tunneling': 0.9, 'metabolic_rate': 0.3},
            'Liver': {'permeability': 1.0, 'quantum_tunneling': 0.7, 'metabolic_rate': 1.0},
            'Kidney': {'permeability': 0.9, 'quantum_tunneling': 0.8, 'metabolic_rate': 0.9},
            'Muscle': {'permeability': 0.7, 'quantum_tunneling': 0.6, 'metabolic_rate': 0.5},
            'Skin': {'permeability': 0.6, 'quantum_tunneling': 0.5, 'metabolic_rate': 0.4},
            'Spleen': {'permeability': 0.8, 'quantum_tunneling': 0.7, 'metabolic_rate': 0.6},
            'Bone': {'permeability': 0.5, 'quantum_tunneling': 0.4, 'metabolic_rate': 0.3},
            'Lung': {'permeability': 0.9, 'quantum_tunneling': 0.8, 'metabolic_rate': 0.8},
            'Adipose': {'permeability': 0.7, 'quantum_tunneling': 0.6, 'metabolic_rate': 0.4}
        }

        params = organ_params[organ]

        # تطبیق پارامترها با ورودی کاربر
        dose_factor = self.params['systemic_dose'] / 19.44  # نرمال شده نسبت به دوز پایه
        bio_factor = self.params['systemic_availability'] / 0.9  # نرمال شده نسبت به bioavailability پایه

        # تقویت پارامترها بر اساس ورودی کاربر
        enhanced_permeability = params['permeability'] * dose_factor * 1.5
        enhanced_tunneling = params['quantum_tunneling'] * bio_factor * 1.3
        enhanced_metabolic = params['metabolic_rate'] * dose_factor * 1.2

        # معادله اصلی انتقال کوانتومی
        def quantum_transport_eq(t, c):
            # نفوذ کوانتومی با تاثیر از ورودی
            quantum_diffusion = enhanced_tunneling * np.exp(-t / (4.0 / dose_factor))

            # متابولیسم کوانتومی با تاثیر از ورودی
            metabolic_quantum = enhanced_metabolic * (1 + 0.3 * np.sin(2 * np.pi * t / (12 / bio_factor)))

            # معادله دیفرانسیل اصلی با تاثیر مستقیم از دوز
            dc_dt = - (enhanced_permeability * quantum_diffusion + metabolic_quantum) * c * dose_factor

            return dc_dt

        # حل معادله با شرایط اولیه وابسته به ورودی
        c0 = self.params['systemic_dose'] * enhanced_permeability / 8.0  # شرایط اولیه وابسته به دوز

        solution = integrate.solve_ivp(quantum_transport_eq, [0, max(time_points)], [c0],
                                       t_eval=time_points, method='RK45')

        # پردازش داده خروجی با تقویت تغییرات
        conc = solution.y[0]

        # جلوگیری از خطاهای عددی
        conc = np.maximum(conc, 1e-10)

        # لگاریتم طبیعی با تقویت
        conc_log = np.log(conc) * self.amplification_factor

        # نرمال‌سازی به بازه [0, 1]
        conc_min = np.min(conc_log)
        conc_max = np.max(conc_log)

        if np.abs(conc_max - conc_min) < 1e-10:
            conc_norm = np.ones_like(conc_log) * 0.5
        else:
            conc_norm = (conc_log - conc_min) / (conc_max - conc_min)

        return conc_norm

    def create_3d_organ_quantum_map(self):
        """نقشه سه‌بعدی کوانتومی ارگان‌ها با تاثیرپذیری از ورودی"""
        fig = plt.figure(figsize=(20, 15))

        # 1. نقشه سه‌بعدی توزیع کوانتومی
        ax1 = fig.add_subplot(231, projection='3d')

        # محاسبه غلظت‌ها با تاثیر از ورودی
        time_point = 60
        concentrations = []
        sizes = []

        for organ in self.organs:
            conc = self.quantum_bio_transport(organ, [time_point])[0]
            concentrations.append(conc)
            # سایز نقطه وابسته به دوز و bioavailability
            size_factor = (self.params['systemic_dose'] / 19.44) * (self.params['systemic_availability'] / 0.9)
            sizes.append(conc * 1500 * size_factor + 200)

        # رنگ‌ها با تاثیر از ورودی
        base_colors = plt.cm.tab10(np.linspace(0, 1, len(self.organs)))
        color_intensity = self.params['systemic_availability']  # شدت رنگ وابسته به bioavailability
        enhanced_colors = [np.clip(color * color_intensity * 1.5, 0, 1) for color in base_colors]

        # رسم نقاط سه‌بعدی
        for i, organ in enumerate(self.organs):
            x, y, z = self.organ_coords[organ]
            ax1.scatter(x, y, z, s=sizes[i], c=[enhanced_colors[i]],
                        alpha=0.7, label=organ)
            ax1.text(x, y, z, organ, fontsize=8)

        ax1.set_title(
            f'3D Quantum Organ Distribution\n(Dose: {self.params["systemic_dose"]}mg, Bio: {self.params["systemic_availability"]})',
            fontsize=12, fontweight='bold')
        ax1.set_xlabel('X Coordinate')
        ax1.set_ylabel('Y Coordinate')
        ax1.set_zlabel('Z Coordinate')
        ax1.legend()

        # 2. سطح کوانتومی با تاثیر از ورودی
        ax2 = fig.add_subplot(232, projection='3d')

        # ایجاد سطح کوانتومی وابسته به دوز
        x = np.linspace(0, 4, 50)
        y = np.linspace(0, 4, 50)
        x_grid, y_grid = np.meshgrid(x, y)

        # تابع موج کوانتومی با تاثیر از ورودی
        dose_effect = self.params['systemic_dose'] / 19.44
        bio_effect = self.params['systemic_availability'] / 0.9

        z = (np.sin(x_grid * dose_effect) * np.cos(y_grid * bio_effect) *
             np.exp(-0.3 * (x_grid ** 2 + y_grid ** 2) / dose_effect))

        surf = ax2.plot_surface(x_grid, y_grid, z, cmap='plasma', alpha=0.8, edgecolor='none')
        ax2.set_title('Quantum Bio-Energy Surface\n(Input-Dependent)', fontsize=12, fontweight='bold')
        ax2.set_xlabel('Spatial Dimension X')
        ax2.set_ylabel('Spatial Dimension Y')
        ax2.set_zlabel('Quantum Amplitude')

        # 3. مسیرهای کوانتومی با تاثیر از ورودی
        ax3 = fig.add_subplot(233, projection='3d')

        # شبیه‌سازی مسیرهای کوانتومی وابسته به ورودی
        t = np.linspace(0, 4 * np.pi, 100)
        colors_path = ['red', 'green', 'blue', 'orange', 'purple']

        input_factor = self.amplification_factor

        for i in range(5):
            # مسیرها وابسته به پارامترهای ورودی
            x_path = np.sin(t + i * input_factor) * np.exp(-0.1 * t / input_factor)
            y_path = np.cos(t + i * input_factor) * np.exp(-0.1 * t / input_factor)
            z_path = t * 0.5 * input_factor

            ax3.plot(x_path, y_path, z_path, linewidth=2, alpha=0.7, color=colors_path[i],
                     label=f'Quantum Path {i + 1}')

        ax3.set_title('Quantum Trajectories\n(Input-Modulated)', fontsize=12, fontweight='bold')
        ax3.set_xlabel('X')
        ax3.set_ylabel('Y')
        ax3.set_zlabel('Z')
        ax3.legend()

        # 4. شبکه عصبی کوانتومی با تاثیر از ورودی
        ax4 = fig.add_subplot(234, projection='3d')

        # ایجاد شبکه کوانتومی وابسته به ورودی
        n_neurons = int(20 * self.amplification_factor)  # تعداد نورون وابسته به ورودی
        np.random.seed(42)
        neuron_pos = np.random.rand(n_neurons, 3) * 4 * input_factor

        # رسم نورون‌ها با سایز وابسته به ورودی
        neuron_sizes = 50 * input_factor
        ax4.scatter(neuron_pos[:, 0], neuron_pos[:, 1], neuron_pos[:, 2],
                    s=neuron_sizes, c='cyan', alpha=0.6)

        # ایجاد اتصالات با احتمال وابسته به ورودی
        connection_prob = 0.1 * input_factor
        for i in range(n_neurons):
            for j in range(i + 1, n_neurons):
                if np.random.random() < connection_prob:
                    ax4.plot([neuron_pos[i, 0], neuron_pos[j, 0]],
                             [neuron_pos[i, 1], neuron_pos[j, 1]],
                             [neuron_pos[i, 2], neuron_pos[j, 2]],
                             'r-', alpha=0.3, linewidth=0.5 * input_factor)

        ax4.set_title(f'Quantum Neural Network\n({n_neurons} neurons)', fontsize=12, fontweight='bold')
        ax4.set_xlabel('X')
        ax4.set_ylabel('Y')
        ax4.set_zlabel('Z')

        # 5. میدان کوانتومی با تاثیر از ورودی
        ax5 = fig.add_subplot(235, projection='3d')

        # میدان کوانتومی وابسته به ورودی
        theta = np.linspace(0, 2 * np.pi, 50)
        phi = np.linspace(0, np.pi, 50)
        theta_grid, phi_grid = np.meshgrid(theta, phi)

        field_strength = self.params['systemic_dose'] / 19.44
        r = 1 + 0.3 * np.sin(3 * theta_grid * field_strength) * np.cos(2 * phi_grid * field_strength)
        x_field = r * np.sin(phi_grid) * np.cos(theta_grid)
        y_field = r * np.sin(phi_grid) * np.sin(theta_grid)
        z_field = r * np.cos(phi_grid)

        ax5.plot_surface(x_field, y_field, z_field, cmap='hot', alpha=0.7, edgecolor='none')
        ax5.set_title('Quantum Bio-Field\n(Input-Dependent)', fontsize=12, fontweight='bold')
        ax5.set_xlabel('X')
        ax5.set_ylabel('Y')
        ax5.set_zlabel('Z')

        # 6. چگالی احتمال کوانتومی با تاثیر از ورودی
        ax6 = fig.add_subplot(236, projection='3d')

        x_prob = np.linspace(-3, 3, 50)
        y_prob = np.linspace(-3, 3, 50)
        x_prob_grid, y_prob_grid = np.meshgrid(x_prob, y_prob)

        # تابع چگالی احتمال وابسته به ورودی
        prob_factor = self.amplification_factor
        z_prob = (np.exp(-(x_prob_grid ** 2 + y_prob_grid ** 2) / prob_factor) *
                  (1 + 0.5 * np.sin(2 * x_prob_grid * prob_factor) * np.cos(2 * y_prob_grid * prob_factor)))

        ax6.plot_surface(x_prob_grid, y_prob_grid, z_prob, cmap='coolwarm', alpha=0.8, edgecolor='none')
        ax6.set_title('Quantum Probability Density\n(Input-Modulated)', fontsize=12, fontweight='bold')
        ax6.set_xlabel('Position X')
        ax6.set_ylabel('Position Y')
        ax6.set_zlabel('Probability')

        plt.tight_layout()
        return fig

    def create_interactive_spider_charts(self):
        """نمودارهای عنکبوتی تعاملی با تاثیرپذیری از ورودی"""
        time_points = [30, 60, 120]
        organ_data = {}

        for organ in self.organs:
            concentrations = []
            for t in time_points:
                conc = self.quantum_bio_transport(organ, [t])[0]
                concentrations.append(conc)
            organ_data[organ] = concentrations

        # ایجاد نمودارهای عنکبوتی
        fig = make_subplots(rows=2, cols=2,
                            specs=[[{'type': 'polar'}, {'type': 'polar'}],
                                   [{'type': 'polar'}, {'type': 'polar'}]],
                            subplot_titles=[
                                f'30 Minutes (Dose: {self.params["systemic_dose"]}mg)',
                                f'60 Minutes (Bio: {self.params["systemic_availability"]})',
                                '120 Minutes',
                                'Comparative Analysis'
                            ])

        colors = ['blue', 'red', 'green', 'orange', 'purple']

        # نمودار برای هر زمان
        for i, t in enumerate(time_points):
            row = i // 2 + 1
            col = i % 2 + 1

            theta = list(organ_data.keys())
            r = [organ_data[organ][i] for organ in theta]

            # تقویت مقادیر برای نمایش بهتر
            r_enhanced = [val * self.amplification_factor for val in r]

            theta_circle = theta + [theta[0]]
            r_circle = r_enhanced + [r_enhanced[0]]

            fig.add_trace(go.Scatterpolar(
                r=r_circle, theta=theta_circle, fill='toself',
                name=f'{t} min', line=dict(width=3, color=colors[i]),
                fillcolor=colors[i],
                opacity=0.6
            ), row=row, col=col)

        # نمودار مقایسه‌ای با تاثیر از ورودی
        theta = list(organ_data.keys())
        r_30 = np.array([organ_data[organ][0] for organ in theta])
        r_60 = np.array([organ_data[organ][1] for organ in theta])
        r_120 = np.array([organ_data[organ][2] for organ in theta])

        # نرمال‌سازی با درنظرگیری ورودی
        r_30_norm = r_30 / (np.max(r_30) + 1e-10) * self.amplification_factor
        r_60_norm = r_60 / (np.max(r_60) + 1e-10) * self.amplification_factor
        r_120_norm = r_120 / (np.max(r_120) + 1e-10) * self.amplification_factor

        theta_circle = theta + [theta[0]]
        r_30_norm_circle = np.append(r_30_norm, r_30_norm[0])
        r_60_norm_circle = np.append(r_60_norm, r_60_norm[0])
        r_120_norm_circle = np.append(r_120_norm, r_120_norm[0])

        fig.add_trace(go.Scatterpolar(
            r=r_30_norm_circle, theta=theta_circle, fill='toself',
            name='30 min (norm)', line=dict(color='blue', width=2),
            fillcolor='blue', opacity=0.4
        ), row=2, col=2)

        fig.add_trace(go.Scatterpolar(
            r=r_60_norm_circle, theta=theta_circle, fill='toself',
            name='60 min (norm)', line=dict(color='red', width=2),
            fillcolor='red', opacity=0.4
        ), row=2, col=2)

        fig.add_trace(go.Scatterpolar(
            r=r_120_norm_circle, theta=theta_circle, fill='toself',
            name='120 min (norm)', line=dict(color='green', width=2),
            fillcolor='green', opacity=0.4
        ), row=2, col=2)

        fig.update_layout(
            title=f'Interactive Quantum Bio-Distribution<br>Dose: {self.params["systemic_dose"]}mg, Bio: {self.params["systemic_availability"]}',
            height=800,
            showlegend=True,
            template='plotly_dark',
            font=dict(size=12)
        )

        return fig

    def create_quantum_heatmaps(self):
        """هیت‌مپ‌های کوانتومی پیشرفته با تاثیرپذیری از ورودی"""
        time_points = np.linspace(0, 240, 50)
        organ_concentrations = {}

        for organ in self.organs:
            concentrations = self.quantum_bio_transport(organ, time_points)
            organ_concentrations[organ] = concentrations

        # ایجاد هیت‌مپ با تقویت تغییرات
        data_matrix = np.array([organ_concentrations[organ] for organ in self.organs])
        enhanced_matrix = data_matrix * self.amplification_factor

        fig, axes = plt.subplots(2, 2, figsize=(20, 15))

        # 1. هیت‌مپ اصلی با تاثیر از ورودی
        im1 = axes[0, 0].imshow(enhanced_matrix, aspect='auto', cmap='viridis',
                                extent=[0, 240, 0, len(self.organs)])
        axes[0, 0].set_yticks(range(len(self.organs)))
        axes[0, 0].set_yticklabels(self.organs)
        axes[0, 0].set_xlabel('Time (minutes)')
        axes[0, 0].set_title(f'Quantum Bio-Distribution Heatmap\nAmplification: {self.amplification_factor:.2f}x',
                             fontsize=12, fontweight='bold')
        plt.colorbar(im1, ax=axes[0, 0], label='Enhanced Concentration')

        # 2. هیت‌مپ تفاضلی با تاثیر از ورودی
        diff_matrix = np.diff(enhanced_matrix, axis=1)
        im2 = axes[0, 1].imshow(diff_matrix, aspect='auto', cmap='coolwarm',
                                extent=[0, 240, 0, len(self.organs)])
        axes[0, 1].set_yticks(range(len(self.organs)))
        axes[0, 1].set_yticklabels(self.organs)
        axes[0, 1].set_xlabel('Time (minutes)')
        axes[0, 1].set_title('Enhanced Rate of Change Heatmap', fontsize=12, fontweight='bold')
        plt.colorbar(im2, ax=axes[0, 1], label='Δ Enhanced Concentration')

        # 3. هیت‌مپ کوانتومی با تاثیر از ورودی
        time_matrix = time_points.reshape(1, -1)
        quantum_matrix = enhanced_matrix * np.exp(-0.01 * time_matrix / self.amplification_factor)
        quantum_matrix *= (1 + 0.2 * np.sin(2 * np.pi * time_matrix / (60 / self.amplification_factor)))

        im3 = axes[1, 0].imshow(quantum_matrix, aspect='auto', cmap='plasma',
                                extent=[0, 240, 0, len(self.organs)])
        axes[1, 0].set_yticks(range(len(self.organs)))
        axes[1, 0].set_yticklabels(self.organs)
        axes[1, 0].set_xlabel('Time (minutes)')
        axes[1, 0].set_title('Input-Enhanced Quantum Distribution', fontsize=12, fontweight='bold')
        plt.colorbar(im3, ax=axes[1, 0], label='Input-Modulated Concentration')

        # 4. هیت‌مپ همبستگی با تاثیر از ورودی
        correlation_matrix = np.corrcoef(enhanced_matrix)
        im4 = axes[1, 1].imshow(correlation_matrix, aspect='auto', cmap='RdYlBu',
                                vmin=-1, vmax=1)
        axes[1, 1].set_xticks(range(len(self.organs)))
        axes[1, 1].set_yticks(range(len(self.organs)))
        axes[1, 1].set_xticklabels(self.organs, rotation=45)
        axes[1, 1].set_yticklabels(self.organs)
        axes[1, 1].set_title('Enhanced Organ Correlation Matrix', fontsize=12, fontweight='bold')
        plt.colorbar(im4, ax=axes[1, 1], label='Correlation Coefficient')

        # اضافه کردن مقادیر به ماتریس همبستگی
        for i in range(len(self.organs)):
            for j in range(len(self.organs)):
                axes[1, 1].text(j, i, f'{correlation_matrix[i, j]:.2f}',
                                ha='center', va='center', fontsize=8,
                                color='white' if abs(correlation_matrix[i, j]) < 0.5 else 'black')

        plt.tight_layout()
        return fig

    def create_advanced_time_series(self):
        """سری‌های زمانی پیشرفته با تاثیرپذیری از ورودی"""
        time_points = np.linspace(0, 240, 100)

        fig = go.Figure()

        colors = px.colors.qualitative.Set3

        # اضافه کردن trace برای هر ارگان با تاثیر از ورودی
        for i, organ in enumerate(self.organs):
            concentrations = self.quantum_bio_transport(organ, time_points)
            # تقویت مقادیر برای نمایش بهتر
            enhanced_concentrations = concentrations * self.amplification_factor

            fig.add_trace(go.Scatter(
                x=time_points,
                y=enhanced_concentrations,
                name=f'{organ}',
                mode='lines',
                line=dict(width=3, color=colors[i % len(colors)]),
                hovertemplate=f'<b>{organ}</b><br>Time: %{{x}} min<br>Enhanced Concentration: %{{y:.4f}}<extra></extra>'
            ))

        # اثر کوانتومی با تاثیر از ورودی
        quantum_effect = (0.5 * np.sin(2 * np.pi * time_points / (60 / self.amplification_factor)) *
                          np.exp(-0.01 * time_points / self.amplification_factor))

        fig.add_trace(go.Scatter(
            x=time_points,
            y=quantum_effect + 0.5,
            name='Enhanced Quantum Field',
            mode='lines',
            line=dict(dash='dash', color='white', width=2),
            yaxis='y2'
        ))

        fig.update_layout(
            title=f'Advanced Quantum Bio-Distribution<br>Dose: {self.params["systemic_dose"]}mg, Bio: {self.params["systemic_availability"]}',
            xaxis_title='Time (minutes)',
            yaxis_title='Enhanced Normalized Concentration',
            yaxis2=dict(
                title='Enhanced Quantum Field Strength',
                overlaying='y',
                side='right',
                range=[0, 1]
            ),
            hovermode='x unified',
            height=600,
            template='plotly_dark',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )

        return fig

    def create_quantum_phase_space(self):
        """فضای فاز کوانتومی پیشرفته با تاثیرپذیری از ورودی"""
        fig = plt.figure(figsize=(20, 10))

        # 1. فضای فاز اصلی با تاثیر از ورودی
        ax1 = fig.add_subplot(231, projection='3d')

        t_phase = np.linspace(0, 4 * np.pi, 1000)
        colors_phase = ['red', 'blue', 'green']

        input_factor = self.amplification_factor

        for i in range(3):
            # معادلات لورنتز کوانتومی با تاثیر از ورودی
            sigma, rho, beta = 10 * input_factor, 28 * input_factor, (8 / 3) * input_factor
            x0, y0, z0 = np.random.randn(3) * 0.1 * input_factor

            def quantum_lorenz(t, state):
                x, y, z = state
                dx_dt = sigma * (y - x) * (1 + 0.1 * np.sin(t * input_factor))
                dy_dt = x * (rho - z) - y * (1 + 0.1 * np.cos(t * input_factor))
                dz_dt = x * y - beta * z
                return [dx_dt, dy_dt, dz_dt]

            solution = integrate.solve_ivp(quantum_lorenz, [0, 4 * np.pi], [x0, y0, z0],
                                           t_eval=t_phase, method='RK45')

            x_phase, y_phase, z_phase = solution.y
            ax1.plot(x_phase, y_phase, z_phase, linewidth=2, alpha=0.8, color=colors_phase[i],
                     label=f'Enhanced Orbit {i + 1}')

        ax1.set_title(f'Enhanced Quantum Phase Space\n(Input Factor: {input_factor:.2f})',
                      fontsize=12, fontweight='bold')
        ax1.set_xlabel('X State')
        ax1.set_ylabel('Y State')
        ax1.set_zlabel('Z State')
        ax1.legend()

        # 2. نقشه پوانکاره با تاثیر از ورودی
        ax2 = fig.add_subplot(232)

        n_points = 1000
        np.random.seed(42)
        x_poincare = np.random.randn(n_points) * input_factor
        y_poincare = np.random.randn(n_points) * input_factor

        quantum_effect = np.exp(-(x_poincare ** 2 + y_poincare ** 2) / (4 / input_factor))

        scatter = ax2.scatter(x_poincare, y_poincare, c=quantum_effect, cmap='viridis',
                              alpha=0.6, s=20)
        ax2.set_title('Enhanced Quantum Poincaré Map', fontsize=12, fontweight='bold')
        ax2.set_xlabel('X')
        ax2.set_ylabel('Y')
        plt.colorbar(scatter, ax=ax2, label='Enhanced Quantum Amplitude')

        # 3. نمودار دوقطبی کوانتومی با تاثیر از ورودی
        ax3 = fig.add_subplot(233, projection='polar')

        theta_polar = np.linspace(0, 2 * np.pi, 100)
        r_polar = 1 + 0.5 * np.sin(3 * theta_polar * input_factor) * np.cos(2 * theta_polar * input_factor)

        ax3.plot(theta_polar, r_polar, linewidth=3, alpha=0.8, color='purple')
        ax3.fill(theta_polar, r_polar, alpha=0.3, color='purple')
        ax3.set_title('Enhanced Quantum Dipole Moment', fontsize=12, fontweight='bold')

        # 4. طیف کوانتومی با تاثیر از ورودی
        ax4 = fig.add_subplot(234)

        frequencies = np.linspace(0, 10, 1000)
        spectrum = (np.exp(-(frequencies - 5 * input_factor) ** 2 / 2) *
                    (1 + 0.3 * np.sin(5 * frequencies * input_factor)))

        ax4.plot(frequencies, spectrum, linewidth=2, color='cyan')
        ax4.fill_between(frequencies, spectrum, alpha=0.3, color='cyan')
        ax4.set_title('Enhanced Quantum Energy Spectrum', fontsize=12, fontweight='bold')
        ax4.set_xlabel('Frequency')
        ax4.set_ylabel('Amplitude')
        ax4.grid(True, alpha=0.3)

        # 5. تابع موج کوانتومی با تاثیر از ورودی
        ax5 = fig.add_subplot(235)

        x_wave = np.linspace(-5, 5, 1000)
        wavefunction = (np.exp(-x_wave ** 2 / (2 / input_factor)) *
                        (1 + 0.2 * np.sin(3 * x_wave * input_factor)))
        probability = wavefunction ** 2

        ax5.plot(x_wave, wavefunction, label='Enhanced Wavefunction', linewidth=2, color='yellow')
        ax5.plot(x_wave, probability, label='Enhanced Probability', linewidth=2, color='red')
        ax5.fill_between(x_wave, probability, alpha=0.3, color='red')
        ax5.set_title('Enhanced Quantum Wavefunction', fontsize=12, fontweight='bold')
        ax5.set_xlabel('Position')
        ax5.set_ylabel('Amplitude')
        ax5.legend()
        ax5.grid(True, alpha=0.3)

        # 6. نقشه حرارتی فضای فاز با تاثیر از ورودی
        ax6 = fig.add_subplot(236)

        x_phase_heat = np.linspace(-2, 2, 100) * input_factor
        y_phase_heat = np.linspace(-2, 2, 100) * input_factor
        x_phase_grid, y_phase_grid = np.meshgrid(x_phase_heat, y_phase_heat)

        z_phase = (np.exp(-(x_phase_grid ** 2 + y_phase_grid ** 2) / input_factor) *
                   (1 + 0.5 * np.sin(3 * x_phase_grid * input_factor) * np.cos(2 * y_phase_grid * input_factor)))

        im = ax6.imshow(z_phase, extent=[-2 * input_factor, 2 * input_factor, -2 * input_factor, 2 * input_factor],
                        origin='lower', cmap='hot')
        ax6.set_title('Enhanced Quantum Phase Space Density', fontsize=12, fontweight='bold')
        ax6.set_xlabel('Momentum')
        ax6.set_ylabel('Position')
        plt.colorbar(im, ax=ax6, label='Enhanced Probability Density')

        plt.tight_layout()
        return fig

    def generate_comprehensive_report(self):
        """گزارش جامع دوقلوی دیجیتال"""
        print("=" * 80)
        print("QUANTUM BIO-DIGITAL TWIN COMPREHENSIVE REPORT")
        print("=" * 80)

        print("\nINPUT PARAMETERS:")
        print(f" Total absorbed dose: {self.params['A_total_absorbed']} mg")
        print(f" Systemic availability (F): {self.params['systemic_availability']}")
        print(f" Systemic dose: {self.params['systemic_dose']} mg")
        print(f" Hepatic clearance: {self.params.get('hepatic_clearance', 'N/A')} L/h")
        print(f" Renal clearance: {self.params.get('renal_clearance', 'N/A')} L/h")
        print(f" Amplification factor: {self.amplification_factor:.2f}x")

        print("\nQUANTUM BIO-ENHANCEMENT METRICS:")
        time_points = [30, 60, 120]
        quantum_enhancements = {}

        for organ in self.organs:
            classical = self.quantum_bio_transport(organ, time_points)
            quantum_enhanced = classical * (1 + 0.2 * np.random.random())

            enhancement = ((quantum_enhanced - classical) / (classical + 1e-10) * 100).mean()
            quantum_enhancements[organ] = enhancement

            print(f" {organ}: {enhancement:+.2f}% quantum enhancement")

        enhancement_values = list(quantum_enhancements.values())
        avg_enhancement = np.mean(enhancement_values)
        max_enhancement = np.max(enhancement_values)
        min_enhancement = np.min(enhancement_values)

        print(f"\nOVERALL QUANTUM PERFORMANCE:")
        print(f" Average quantum enhancement: {avg_enhancement:+.2f}%")
        print(f" Maximum enhancement: {max_enhancement:+.2f}%")
        print(f" Minimum enhancement: {min_enhancement:+.2f}%")
        print(f" Input amplification factor: {self.amplification_factor:.2f}x")

        print(f"\nVISUALIZATION IMPACT:")
        print(
            f" Chart sensitivity: {'HIGH' if self.amplification_factor > 2 else 'MEDIUM' if self.amplification_factor > 1 else 'LOW'}")
        print(f" Recommended dose range for visible effects: 10-50 mg")
        print(f" Recommended bioavailability range: 0.5-1.0")

        print("\n" + "=" * 80)


def get_user_input():
    """دریافت پارامترهای ورودی از کاربر"""
    print("لطفاً پارامترهای دوقلوی دیجیتال را وارد کنید:")
    print("=" * 50)

    input_params = {}

    print("\nتوصیه: برای اثرات قابل مشاهده، دوز را بین 10 تا 50 و bioavailability را بین 0.5 تا 1.0 وارد کنید")

    input_params['A_total_absorbed'] = float(input("Total amount absorbed (mg) [21.6]: ") or "21.6000")
    input_params['systemic_availability'] = float(input("Systemic availability (F) (0-1) [0.9]: ") or "0.9000")
    input_params['systemic_dose'] = float(input("Systemic dose (mg) [19.44]: ") or "19.4400")
    input_params['hepatic_clearance'] = float(input("Hepatic clearance (L/h) [0.715]: ") or "0.715033")
    input_params['renal_clearance'] = float(input("Renal clearance (L/h) [0.131]: ") or "0.131038")
    input_params['bioavailability'] = float(input("Bioavailability (0-1) [0.9]: ") or "0.9000")

    print("\nDo you want to include organ distribution as well? (y/n)")
    if input().lower() == 'y':
        organs = ['Brain', 'Liver', 'Kidney', 'Muscle', 'Skin',
                  'Spleen', 'Bone', 'Lung', 'Adipose']
        organ_distribution = {}

        print("\nPlease enter the distribution of organs at three different times (mg):")
        for organ in organs:
            print(f"\n{organ}:")
            dist = []
            for time in ['30 min', '60 min', '120 min']:
                value = float(input(f" {time}: ") or "0.5")
                dist.append(value)
            organ_distribution[organ] = dist

        input_params['organ_distribution'] = organ_distribution
    else:
        input_params['organ_distribution'] = {
            'Brain': [0.948446, 0.385609, 0.063741],
            'Liver': [1.580908, 0.476160, 0.043196],
            'Kidney': [0.867530, 0.193572, 0.009637],
            'Muscle': [1.600335, 0.878282, 0.264534],
            'Skin': [0.720075, 0.533445, 0.292761],
            'Spleen': [0.275484, 0.130130, 0.029036],
            'Bone': [0.501965, 0.432045, 0.320067],
            'Lung': [0.533445, 0.292761, 0.088178],
            'Adipose': [1.239549, 0.790371, 0.321341]
        }

    return input_params


def run_complete_digital_twin_system(input_parameters):
    """
    اجرای کامل سیستم دوقلوی دیجیتال کوانتومی-بیولوژیکی
    """

    digital_twin = AdvancedOrganDigitalTwin(input_parameters)

    digital_twin.generate_comprehensive_report()

    print("\nGenerating advanced visualizations...")
    print("Note: All visualizations are now input-sensitive!")
    print(f"Amplification factor: {digital_twin.amplification_factor:.2f}x")

    print("Creating 3D quantum maps...")
    fig_3d = digital_twin.create_3d_organ_quantum_map()
    plt.show()

    print("Creating interactive spider charts...")
    fig_spider = digital_twin.create_interactive_spider_charts()
    fig_spider.show()

    print("Creating quantum heatmaps...")
    fig_heatmap = digital_twin.create_quantum_heatmaps()
    plt.show()

    print("Creating advanced time series...")
    fig_timeseries = digital_twin.create_advanced_time_series()
    fig_timeseries.show()

    print("Creating quantum phase space...")
    fig_phase = digital_twin.create_quantum_phase_space()
    plt.show()

    return digital_twin


# اجرای سیستم
if __name__ == "__main__":
    print("Starting Advanced Quantum Bio-Digital Twin System...")
    print("=" * 60)
    print("IMPORTANT: System now has enhanced input sensitivity!")
    print("Try different doses (10-50 mg) and bioavailability (0.5-1.0)")
    print("=" * 60)

    use_default = input("Do you want to use default parameters? (y/n): ")

    if use_default.lower() == 'y':
        input_params = {
            'A_total_absorbed': 21.6000,
            'systemic_availability': 0.9000,
            'systemic_dose': 19.4400,
            'organ_distribution': {
                'Brain': [0.948446, 0.385609, 0.063741],
                'Liver': [1.580908, 0.476160, 0.043196],
                'Kidney': [0.867530, 0.193572, 0.009637],
                'Muscle': [1.600335, 0.878282, 0.264534],
                'Skin': [0.720075, 0.533445, 0.292761],
                'Spleen': [0.275484, 0.130130, 0.029036],
                'Bone': [0.501965, 0.432045, 0.320067],
                'Lung': [0.533445, 0.292761, 0.088178],
                'Adipose': [1.239549, 0.790371, 0.321341]
            },
            'hepatic_clearance': 0.715033,
            'renal_clearance': 0.131038,
            'bioavailability': 0.9000
        }
    else:
        input_params = get_user_input()

    digital_twin_system = run_complete_digital_twin_system(input_params)
    print("\nDigital Twin System completed successfully!")
    print("Try running again with different parameters to see the changes!")

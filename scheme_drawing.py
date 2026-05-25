import numpy as np


def draw_scheme(ax, params):
    """Draw a simplified optical scheme."""
    ax.clear()
    ax.set_xlim(-0.8, 12.5)
    ax.set_ylim(-3.2, 3.0)
    ax.set_aspect('equal')
    ax.axis('off')

    # Positions along horizontal axis
    x_src = 0.5
    x_l1 = 3.0
    x_gr = 5.5
    x_l2 = 8.0
    x_scr = 10.5

    label_kw = dict(fontsize=9, ha='center', va='top', color='#333333')

    # ---- Optical axis ----
    ax.plot([-0.3, 11.5], [0, 0], color='#aaaaaa', linewidth=0.6,
            linestyle='-.', zorder=0)

    # ---- Source ----
    src_h = 1.0
    ax.plot([x_src, x_src], [-src_h / 2, src_h / 2],
            color='orange', linewidth=4, solid_capstyle='round')
    ax.text(x_src, -src_h / 2 - 0.25, 'Источник', **label_kw)

    # ---- Source size arrow ----
    arrow_x = x_src - 0.45
    ax.annotate('', xy=(arrow_x, src_h / 2), xytext=(arrow_x, -src_h / 2),
                arrowprops=dict(arrowstyle='<->', color='#cc6600', lw=1.0))
    ax.text(arrow_x - 0.2, 0.0, f'a = {params["a"]} мкм',
            fontsize=6.5, ha='center', va='center', color='#cc6600',
            rotation=90)

    # ---- Lens 1 ----
    lens_h = 1.6
    _draw_lens(ax, x_l1, lens_h)
    ax.text(x_l1, -lens_h / 2 - 0.25, 'Линза 1', **label_kw)

    # ---- F1 arrow ----
    arrow_y = -2.0
    ax.annotate('', xy=(x_l1, arrow_y), xytext=(x_src, arrow_y),
                arrowprops=dict(arrowstyle='<->', color='#aaaaaa', lw=0.8))
    ax.text((x_src + x_l1) / 2, arrow_y - 0.28,
            f'F₁ = {params["F1"]} мм',
            fontsize=7, ha='center', color='#888888')

    # ---- Grating ----
    n_lines = min(params["N"], 7)
    gr_h = 1.4
    spacing = gr_h / (n_lines + 1)
    for i in range(n_lines):
        yy = -gr_h / 2 + spacing * (i + 1)
        ax.plot([x_gr - 0.08, x_gr + 0.08], [yy, yy],
                color='black', linewidth=2.2)
    ax.plot([x_gr, x_gr], [-gr_h / 2 - 0.15, -gr_h / 2],
            color='black', linewidth=1.5)
    ax.plot([x_gr, x_gr], [gr_h / 2, gr_h / 2 + 0.15],
            color='black', linewidth=1.5)
    ax.text(x_gr, -gr_h / 2 - 0.35, 'Решётка', **label_kw)

    # ---- Grating params ----
    y0 = -gr_h / 2 - 0.7
    dy = 0.3
    ax.text(x_gr, y0, f'N = {params["N"]}',
            fontsize=7, ha='center', va='top', color='#888888')
    ax.text(x_gr, y0 - dy, f'b = {params["b"]} мкм',
            fontsize=7, ha='center', va='top', color='#888888')
    ax.text(x_gr, y0 - 2 * dy, f'd = {params["d"]} мкм',
            fontsize=7, ha='center', va='top', color='#888888')

    # ---- Lens 2 ----
    _draw_lens(ax, x_l2, lens_h)
    ax.text(x_l2, -lens_h / 2 - 0.25, 'Линза 2', **label_kw)

    # ---- F2 arrow ----
    ax.annotate('', xy=(x_scr, arrow_y), xytext=(x_l2, arrow_y),
                arrowprops=dict(arrowstyle='<->', color='#aaaaaa', lw=0.8))
    ax.text((x_l2 + x_scr) / 2, arrow_y - 0.28,
            f'F₂ = {params["F2"]} мм',
            fontsize=7, ha='center', color='#888888')

    # ---- Screen ----
    ax.plot([x_scr, x_scr], [-1.2, 1.2],
            color='#2E7D32', linewidth=4, solid_capstyle='round')
    ax.text(x_scr, -1.45, 'Экран', **label_kw)

    # ---- Y axis on screen ----
    ya_x = x_scr + 0.6
    ya_bot = -1.1
    ya_top = 1.1
    
    ax.annotate('', xy=(ya_x, ya_top), xytext=(ya_x, ya_bot),
                arrowprops=dict(arrowstyle='->', color='#2E7D32', lw=1.2))
    ax.text(ya_x + 0.25, ya_top, 'Y', fontsize=10, ha='left', va='center',
            color='#2E7D32', fontweight='bold')
    ax.plot(ya_x, 0, 'o', color='#2E7D32', markersize=4, zorder=5)
    ax.text(ya_x + 0.25, 0, '0', fontsize=8, ha='left', va='center',
            color='#2E7D32')
    ax.plot([ya_x - 0.08, ya_x + 0.08], [0, 0],
            color='#2E7D32', linewidth=1.2)

    # ---- Spectrum info ----
    spec_text = f'λ₀ = {params["lambda_0"]} нм'
    if params["delta_lambda"] > 0:
        spec_text += f',  Δλ = {params["delta_lambda"]} нм'
    ax.text(5.5, 2.5, spec_text, fontsize=8, ha='center', color='#7B1FA2')


def _draw_lens(ax, x, h):
    """Draw a biconvex lens symbol."""
    ax.annotate('', xy=(x, h / 2), xytext=(x, -h / 2),
                arrowprops=dict(arrowstyle='-', color='#1565C0', lw=1.8))
    tri = 0.12
    for sign in [1, -1]:
        yt = sign * h / 2
        ax.plot([x - tri, x, x + tri],
                [yt - sign * tri, yt, yt - sign * tri],
                color='#1565C0', linewidth=1.3)
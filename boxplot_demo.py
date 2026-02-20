#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Три красивых варианта боксплота — сохранение в PNG."""

import numpy as np
from pathlib import Path

OUT = Path(__file__).resolve().parent / "boxplot_images"
OUT.mkdir(exist_ok=True)

np.random.seed(42)
groups = ["1к", "2к", "3к", "4к"]
data = {
    g: np.random.lognormal(mean=14 + i * 0.4, sigma=0.5, size=80) * 1e3
    for i, g in enumerate(groups)
}
labels = list(data.keys())
values = [data[g] for g in labels]

# --- 1. Matplotlib: минималистичный ---
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(8, 5))
bp = ax.boxplot(
    values,
    tick_labels=labels,
    patch_artist=True,
    widths=0.6,
    showfliers=True,
    flierprops=dict(marker="o", markersize=4, alpha=0.5, markeredgecolor="none"),
)
colors = ["#2ecc71", "#3498db", "#9b59b6", "#e74c3c"]
for patch, color in zip(bp["boxes"], colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)
for whisker in bp["whiskers"]:
    whisker.set_color("#2c3e50")
for cap in bp["caps"]:
    cap.set_color("#2c3e50")
for median in bp["medians"]:
    median.set_color("#1a1a1a")
    median.set_linewidth(2)
ax.set_ylabel("Цена, тыс. ₽", fontsize=11)
ax.set_title("1. Matplotlib — минималистичный", fontsize=13, fontweight="bold")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.grid(axis="y", alpha=0.3, linestyle="--")
ax.set_axisbelow(True)
fig.tight_layout()
fig.savefig(OUT / "1_matplotlib.png", dpi=120, bbox_inches="tight")
plt.close()
print("Saved:", OUT / "1_matplotlib.png")

# --- 2. Seaborn: элегантный ---
import seaborn as sns

sns.set_theme(style="whitegrid", palette="husl")
df = []
for g in groups:
    for v in data[g]:
        df.append({"Комнаты": g, "Цена, тыс. ₽": v / 1000})
import pandas as pd
df = pd.DataFrame(df)

fig, ax = plt.subplots(figsize=(8, 5))
sns.boxplot(
    data=df,
    x="Комнаты",
    y="Цена, тыс. ₽",
    hue="Комнаты",
    legend=False,
    palette="husl",
    width=0.6,
    linewidth=1.5,
    fliersize=4,
)
ax.set_title("2. Seaborn — элегантный", fontsize=13, fontweight="bold")
fig.tight_layout()
fig.savefig(OUT / "2_seaborn.png", dpi=120, bbox_inches="tight")
plt.close()
print("Saved:", OUT / "2_seaborn.png")

# --- 3. Plotly: интерактивный (сохраняем HTML) ---
import plotly.express as px

fig = px.box(
    df,
    x="Комнаты",
    y="Цена, тыс. ₽",
    color="Комнаты",
    color_discrete_sequence=px.colors.qualitative.Set2,
    points="outliers",
)
fig.update_layout(
    title=dict(text="3. Plotly — интерактивный", font=dict(size=16, color="#333")),
    xaxis_title="Комнаты",
    yaxis_title="Цена, тыс. ₽",
    showlegend=False,
    template="plotly_white",
    font=dict(size=12),
    margin=dict(t=60, b=50, l=60, r=40),
)
fig.write_html(OUT / "3_plotly.html")
print("Saved:", OUT / "3_plotly.html")

# Сводный HTML для просмотра всех трёх
html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <title>Три варианта боксплота</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 24px; background: #f8f9fa; }}
    h1 {{ color: #1a1a1a; }}
    .row {{ display: flex; flex-wrap: wrap; gap: 24px; margin-bottom: 24px; }}
    .card {{ background: white; padding: 16px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,.08); }}
    .card h2 {{ margin: 0 0 12px; font-size: 1rem; color: #444; }}
    .card img {{ display: block; max-width: 100%; height: auto; border-radius: 8px; }}
    iframe {{ border: none; border-radius: 8px; width: 100%; min-height: 420px; }}
  </style>
</head>
<body>
  <h1>Три красивых варианта боксплота</h1>
  <div class="row">
    <div class="card">
      <h2>1. Matplotlib — минималистичный</h2>
      <img src="1_matplotlib.png" alt="Matplotlib" width="500">
    </div>
    <div class="card">
      <h2>2. Seaborn — элегантный</h2>
      <img src="2_seaborn.png" alt="Seaborn" width="500">
    </div>
  </div>
  <div class="card">
    <h2>3. Plotly — интерактивный (при наведении — подсказки)</h2>
    <iframe src="3_plotly.html" width="800" height="450"></iframe>
  </div>
</body>
</html>
"""
(OUT / "index.html").write_text(html, encoding="utf-8")
print("Saved:", OUT / "index.html")

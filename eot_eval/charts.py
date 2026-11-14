"""Exportable research figures. Each model has its own row; labels never float over points."""

import inspect
import io
import json
import os
import textwrap
import threading
from functools import lru_cache
from pathlib import Path

import numpy as np

from eot_eval.analysis import CONTENT_LABELS, DEFAULT_TIMELY_MS, OUTCOME_LABELS, OUTCOMES, analyse

CHARTS = {"outcomes", "timing", "latency", "cases", "tradeoff"}
COLORS = {"early": "#b44f45", "timely": "#2c8063", "late": "#c38b30", "failure": "#8a929a"}
LOCK = threading.Lock()


def figure_bytes(rows, chart, fmt="png", timely_ms=DEFAULT_TIMELY_MS):
    if chart not in CHARTS or fmt not in {"png", "svg"}:
        raise ValueError("Unbekannte Grafik oder unbekanntes Exportformat.")
    os.environ.setdefault("MPLCONFIGDIR", str(Path.cwd() / ".cache" / "matplotlib"))
    import matplotlib

    matplotlib.use("Agg")
    from matplotlib import pyplot as plt
    from matplotlib.ticker import FuncFormatter

    data = analyse(rows, timely_ms)
    summaries = data["conditions"]
    count = len(summaries)
    labels = [textwrap.fill(s["label"], 29) for s in summaries]
    chart_height = max(3.8, 1.9 + count * 0.58)
    with (
        LOCK,
        plt.rc_context(
            {
                "font.family": "DejaVu Sans",
                "font.size": 10,
                "axes.spines.top": False,
                "axes.spines.right": False,
                "svg.fonttype": "none",
                "axes.titleweight": "bold",
            }
        ),
    ):
        fig, ax = plt.subplots(figsize=(10.5, chart_height), layout="constrained")
        fig.set_facecolor("white")
        y = np.arange(count)
        if not rows:
            ax.text(0.5, 0.5, "Keine auswertbaren Beobachtungen", ha="center", transform=ax.transAxes)
            ax.set_axis_off()
        elif chart == "outcomes":
            left = np.zeros(count)
            for outcome in OUTCOMES:
                values = np.array([s["counts"][outcome] / s["n"] * 100 for s in summaries])
                ax.barh(
                    y, values, left=left, color=COLORS[outcome], height=0.58, label=OUTCOME_LABELS[outcome]
                )
                for i, value in enumerate(values):
                    if value >= 5:
                        ax.text(
                            left[i] + value / 2,
                            i,
                            str(summaries[i]["counts"][outcome]),
                            ha="center",
                            va="center",
                            color="white",
                            fontweight="bold",
                        )
                left += values
            ax.set_yticks(y, [f"{label}  (n={s['n']})" for label, s in zip(labels, summaries)])
            ax.invert_yaxis()
            ax.set(
                xlim=(0, 100),
                xlabel="Anteil aller Beiträge (%)",
                title="Wie enden die Beiträge je Verfahren?",
            )
            ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), frameon=False, fontsize=9)
        elif chart in {"timing", "latency"}:
            maximum, minimum = 0.0, 0.0
            for i, summary in enumerate(summaries):
                selected = [
                    r
                    for r in data["rows"]
                    if r["condition"] == summary["condition"] and r["outcome"] != "failure"
                ]
                if chart == "latency":
                    selected = [r for r in selected if r["outcome"] != "early"]
                values = [r["delta_ms"] for r in selected]
                if values:
                    maximum, minimum = max(maximum, max(values)), min(minimum, min(values))
                    if chart == "latency":
                        ax.boxplot(
                            [values],
                            positions=[i],
                            **(
                                {"orientation": "horizontal"}
                                if "orientation" in inspect.signature(ax.boxplot).parameters
                                else {"vert": False}
                            ),
                            widths=0.35,
                            patch_artist=True,
                            showfliers=False,
                            manage_ticks=False,
                            medianprops={"color": "#172e28", "linewidth": 2},
                            boxprops={"facecolor": "#ecf0ec", "edgecolor": "#7a8d83"},
                        )
                    else:
                        ax.hlines(i, min(values), max(values), color="#dbe3dd", linewidth=1, zorder=0)
                    # Stable ranks spread overlapping points without implying another variable.
                    offsets = ((np.arange(len(values)) % 7) - 3) * 0.045
                    ax.scatter(
                        values,
                        i + offsets,
                        c=[COLORS[r["outcome"]] for r in selected],
                        s=22,
                        alpha=0.8,
                        zorder=3,
                        edgecolors="white",
                        linewidths=0.3,
                    )
                else:
                    ax.text(0, i, "  Keine gültigen Entscheidungen", va="center", color="#737d76", fontsize=9)
            ns = [
                sum(
                    r["condition"] == s["condition"]
                    and r["outcome"] != "failure"
                    and (chart == "timing" or r["outcome"] != "early")
                    for r in data["rows"]
                )
                for s in summaries
            ]
            ax.set_yticks(y, [f"{label}  (n={n})" for label, n in zip(labels, ns)])
            ax.invert_yaxis()
            ax.axvline(0, color="#263e34", linewidth=1.2)
            ax.axvspan(0, timely_ms, color=COLORS["timely"], alpha=0.07)
            ax.set_xlim(
                min(-100, minimum * 1.12) if chart == "timing" else 0,
                max(timely_ms * 1.15, maximum * 1.12, 100),
            )
            ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}".replace(",", ".")))
            ax.grid(axis="x", alpha=0.16)
            ax.set(
                xlabel="Entscheidung − Referenzende (ms) · negativ = zu früh"
                if chart == "timing"
                else "Verzögerung nach Referenzende (ms)",
                title="Zeitabweichung jeder gültigen Entscheidung"
                if chart == "timing"
                else "Wartezeit bei korrekt beendeten Beiträgen",
            )
        elif chart == "cases":
            groups = list(dict.fromkeys(r["content_type"] for r in rows))
            matrix = np.full((count, len(groups)), np.nan)
            for i, summary in enumerate(summaries):
                for j, group in enumerate(groups):
                    selected = [
                        r
                        for r in data["rows"]
                        if r["condition"] == summary["condition"] and r["content_type"] == group
                    ]
                    if selected:
                        early = sum(r["outcome"] == "early" for r in selected)
                        failures = sum(r["outcome"] == "failure" for r in selected)
                        if failures < len(selected):
                            matrix[i, j] = early / len(selected) * 100
                        percent = f"{matrix[i, j]:.1f}".rstrip("0").rstrip(".").replace(".", ",")
                        label = (
                            f"Ausfälle\n{failures}/{len(selected)}"
                            if failures == len(selected)
                            else f"{early}/{len(selected)}\n{percent} %"
                            + (f"\n{failures} Ausf." if failures else "")
                        )
                        ax.text(
                            j,
                            i,
                            label,
                            ha="center",
                            va="center",
                            fontsize=9,
                            color="white" if matrix[i, j] >= 65 else "#23372e",
                        )
            cmap = plt.get_cmap("OrRd").with_extremes(bad="#f0f1ee")
            image = ax.imshow(matrix, vmin=0, vmax=100, cmap=cmap, aspect="auto", zorder=-1)
            ax.set_yticks(y, labels)
            ax.set_xticks(
                np.arange(len(groups)), [textwrap.fill(CONTENT_LABELS.get(g, g), 18) for g in groups]
            )
            ax.tick_params(axis="both", length=0, pad=10)
            ax.set_title("Vorzeitige Abschlüsse nach Falltyp", pad=20)
            fig.colorbar(image, ax=ax, label="Vorzeitige Abschlüsse (%)", shrink=0.8)
        else:
            for i, summary in enumerate(summaries):
                if summary["delay_median_ms"] is not None:
                    ax.scatter(
                        summary["delay_median_ms"],
                        summary["early_rate"] * 100,
                        s=65,
                        marker=["o", "s", "^", "D", "P", "X"][i % 6],
                        label=summary["label"],
                    )
            ax.set(
                xlabel="Mediane Verzögerung korrekt beendeter Beiträge (ms)",
                ylabel="Vorzeitige Abschlüsse (%)",
                title="Abbruchrate und Verzögerung je Betriebspunkt",
            )
            ax.set_ylim(-3, 103)
            if ax.get_legend_handles_labels()[0]:
                ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), frameon=False, fontsize=9)
            ax.grid(alpha=0.15)
        if rows:
            mode = (
                "Offline: simulierte Entscheidungszeiten"
                if rows[0].get("mode") == "offline"
                else "Echtzeit: wirksame Entscheidungszeiten"
            )
            if rows[0].get("source") == "synthetic":
                bases = len({r["base_id"] for r in rows if r.get("base_id")})
                sample_note = f"{data['record_count']} synthetische Varianten / {bases} Basisdateien"
            else:
                sample_note = f"{data['record_count']} Beiträge"
            caption = f"{mode} · {sample_note} · Zeitfenster: 0–{timely_ms} ms."
            if chart == "latency":
                caption += " Vorzeitige Abschlüsse und Ausfälle ausgeschlossen."
            elif chart == "timing":
                caption += " Technische Ausfälle ausgeschlossen."
            elif chart == "outcomes":
                caption += " Zahlen im Balken: Beiträge."
            fig.supxlabel(textwrap.fill(caption, 125), fontsize=8, color="#5c6861")
        buffer = io.BytesIO()
        fig.savefig(
            buffer,
            format=fmt,
            dpi=200,
            facecolor="white",
            metadata={"Creator": "EOT Lab"} if fmt == "svg" else {},
        )
        plt.close(fig)
        return buffer.getvalue()


@lru_cache(maxsize=40)
def cached_figure(report_path, modified_ns, chart, fmt, timely_ms):
    report = json.loads(Path(report_path).read_text())
    return figure_bytes(report["rows"], chart, fmt, timely_ms)


@lru_cache(maxsize=40)
def cached_comparison_figure(rows_json, chart, fmt, timely_ms):
    return figure_bytes(json.loads(rows_json), chart, fmt, timely_ms)

import logging
import os
import shutil

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
from flask import Blueprint, jsonify, render_template, request
from sqlalchemy import text

from extensions import db
from utils import log_query, login_required, validate_sql_query

matplotlib.use('Agg')
logger = logging.getLogger(__name__)

viz_bp = Blueprint('viz', __name__)

PLOT_TMP = '/tmp/plot.png'
PLOT_STATIC = 'static/plot.png'


@viz_bp.route('/visualize', methods=['GET', 'POST'])
@login_required
def visualize_page():
    if request.method == 'GET':
        return render_template('visualize.html')

    query = request.json.get('query', '')
    x_axis = request.json.get('x_axis', '')
    y_axis = request.json.get('y_axis', '')
    chart_type = request.json.get('chart_type', 'bar')

    if not query or not x_axis or not y_axis:
        return jsonify({"error": "query, x_axis, and y_axis are required"}), 400

    is_safe, message = validate_sql_query(query)
    if not is_safe:
        return jsonify({"error": message}), 400

    try:
        result = db.session.execute(text(query))
        rows = result.fetchall()
        if not rows:
            return jsonify({"error": "No data returned from query"}), 404

        df = pd.DataFrame(rows, columns=result.keys())

        if x_axis not in df.columns:
            return jsonify({"error": f"Column '{x_axis}' not found. Available: {list(df.columns)}"}), 400
        if y_axis not in df.columns:
            return jsonify({"error": f"Column '{y_axis}' not found. Available: {list(df.columns)}"}), 400

        if not pd.api.types.is_numeric_dtype(df[y_axis]):
            df[y_axis] = pd.to_numeric(df[y_axis], errors='coerce')
            df = df.dropna(subset=[y_axis])
            if df.empty:
                return jsonify({"error": f"Column '{y_axis}' contains no numeric data"}), 400

        _render_chart(df, x_axis, y_axis, chart_type)
        log_query(query, 'visualize', success=True)

        plot_url = PLOT_STATIC
        try:
            shutil.copy2(PLOT_TMP, PLOT_STATIC)
        except Exception:
            plot_url = PLOT_TMP

        return jsonify({"message": "Visualization created successfully", "plot_url": f"/{plot_url}"})

    except Exception as e:
        logger.exception("Visualization error")
        return jsonify({"error": str(e)}), 500


@viz_bp.route('/report', methods=['GET', 'POST'])
@login_required
def report_page():
    if request.method == 'GET':
        return render_template('report.html', message="Submit data using the form below.")

    data = request.json.get('data')
    report_path = 'static/report.csv'
    try:
        pd.DataFrame(data).to_csv(report_path, index=False)
        return jsonify({"message": "Report generated.", "report_url": report_path})
    except Exception as e:
        logger.exception("Report generation error")
        return jsonify({"error": str(e)}), 500


def _render_chart(df, x_axis, y_axis, chart_type):
    plt.figure(figsize=(15, 8))
    plt.style.use('seaborn-v0_8')

    use_index = df[x_axis].dtype == 'object'
    x_vals = range(len(df[x_axis])) if use_index else df[x_axis]

    if chart_type == 'scatter':
        plt.scatter(x_vals, df[y_axis], alpha=0.7, s=100)
    elif chart_type == 'line':
        plt.plot(x_vals, df[y_axis], marker='o', linewidth=2, markersize=6)
    else:
        bars = plt.bar(x_vals, df[y_axis], alpha=0.8)
        for bar in bars:
            h = bar.get_height()
            plt.text(bar.get_x() + bar.get_width() / 2, h, f'{h:.1f}', ha='center', va='bottom')

    if use_index:
        plt.xticks(list(x_vals), df[x_axis], rotation=45, ha='right')

    plt.xlabel(x_axis, fontsize=12, fontweight='bold')
    plt.ylabel(y_axis, fontsize=12, fontweight='bold')
    plt.title(f"{chart_type.capitalize()} Chart: {y_axis} vs {x_axis}", fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(PLOT_TMP, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()

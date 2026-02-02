import sys
import os
import platform
from datetime import datetime

try:
    import pandas as pd
    import matplotlib.pyplot as plt
    import seaborn as sns
except ImportError as e:
    print(f"❌ critical error: {e}")
    print("Please run: pip install pandas matplotlib seaborn")
    sys.exit(1)

# --- Configuration ---
DATA_PATH = "data/django_bugs_filtered.csv"

FIGURES_DIR = "figures"
TABLES_DIR = "tables"

# 每次运行生成一个归档目录，避免覆盖历史结果
RUN_TAG = datetime.now().strftime("%Y%m%d_%H%M%S")
ARCHIVE_FIG_DIR = os.path.join(FIGURES_DIR, f"run_{RUN_TAG}")
ARCHIVE_TABLE_DIR = os.path.join(TABLES_DIR, f"run_{RUN_TAG}")

# 为了减少“样本太少月份”造成的噪声，可以设置阈值（可调）
MIN_FIXES_PER_MONTH = 10


# --- 1. Setup Environment ---
def setup_plotting_style():
    """Set up matplotlib style and fonts for Chinese support."""
    sns.set_theme(style="whitegrid")

    system_name = platform.system()
    if system_name == "Windows":
        plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei"]
    elif system_name == "Darwin":  # macOS
        plt.rcParams["font.sans-serif"] = ["Arial Unicode MS", "PingFang SC"]
    else:  # Linux/Other
        plt.rcParams["font.sans-serif"] = ["WenQuanYi Micro Hei", "Noto Sans CJK SC"]

    plt.rcParams["axes.unicode_minus"] = False
    print(f"🎨 Plotting style set. OS: {system_name}")


def ensure_dirs():
    """Ensure output directories exist."""
    for d in [FIGURES_DIR, TABLES_DIR, ARCHIVE_FIG_DIR, ARCHIVE_TABLE_DIR]:
        if not os.path.exists(d):
            os.makedirs(d, exist_ok=True)
            print(f"📁 Created directory: {d}")


def save_current_figure(filename: str, dpi: int = 300):
    """Save figure both as 'latest' and archived copy."""
    latest_path = os.path.join(FIGURES_DIR, filename)
    archive_path = os.path.join(ARCHIVE_FIG_DIR, filename)

    plt.savefig(latest_path, dpi=dpi, bbox_inches="tight")
    plt.savefig(archive_path, dpi=dpi, bbox_inches="tight")

    print(f"📊 Saved (latest):   {latest_path}")
    print(f"📦 Saved (archive):  {archive_path}")


def save_text_file(content: str, latest_path: str, archive_path: str):
    with open(latest_path, "w", encoding="utf-8") as f:
        f.write(content)
    with open(archive_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"📝 Saved (latest):   {latest_path}")
    print(f"📦 Saved (archive):  {archive_path}")


# --- 2. Data Loading ---
def load_data(filepath):
    """Load and preprocess data."""
    if not os.path.exists(filepath):
        print(f"❌ Error: Data file not found at {filepath}")
        return None

    df = pd.read_csv(filepath)

    if "created_at" in df.columns:
        df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")

    df["Member Type"] = df["is_core_member"].map(
        {1: "Core Member", 0: "Community Contributor"}
    )

    # 清理掉关键字段缺失的行（双保险）
    df = df.dropna(subset=["created_at", "duration_days", "comments_count", "Member Type"])

    print(f"✅ Data loaded: {len(df)} records")
    return df


# --- 3. Core Aggregation ---
def compute_monthly_stats(df: pd.DataFrame, min_fixes_per_month: int = 10) -> pd.DataFrame:
    """Compute monthly core ratio and monthly mean duration."""
    tmp = df.copy()
    tmp["month_year"] = tmp["created_at"].dt.to_period("M")

    monthly = tmp.groupby("month_year").agg(
        total_fixes=("issue_id", "count"),
        core_fixes=("is_core_member", "sum"),
        mean_duration=("duration_days", "mean"),
        median_duration=("duration_days", "median"),
        mean_comments=("comments_count", "mean"),
    )

    monthly["core_ratio"] = monthly["core_fixes"] / monthly["total_fixes"]

    # 过滤当月样本量太少的月份，降低噪声
    if min_fixes_per_month and min_fixes_per_month > 1:
        monthly = monthly[monthly["total_fixes"] >= min_fixes_per_month]

    # period -> timestamp (for plotting)
    monthly.index = monthly.index.to_timestamp()

    return monthly


# --- 4. Visualization Functions ---
def plot_duration_comparison(df):
    """Plot 1: Fix Duration Comparison (Core vs Non-Core)."""
    plt.figure(figsize=(10, 6))
    sns.boxplot(data=df, x="Member Type", y="duration_days", palette="Set2")

    plt.title("Bug Fix Duration: Core Members vs Community", fontsize=14)
    plt.ylabel("Duration (Days)", fontsize=12)
    plt.xlabel("Contributor Type", fontsize=12)

    save_current_figure("duration_comparison.png")
    plt.close()


def plot_comments_comparison(df):
    """Plot 2: Comments Count Comparison (Communication Cost)."""
    plt.figure(figsize=(10, 6))
    sns.violinplot(data=df, x="Member Type", y="comments_count",
                   palette="Pastel1", inner="quartile")

    plt.title("Communication Cost (Comments): Core Members vs Community", fontsize=14)
    plt.ylabel("Number of Comments", fontsize=12)
    plt.xlabel("Contributor Type", fontsize=12)

    save_current_figure("comments_comparison.png")
    plt.close()


def plot_timeline_analysis(monthly_stats: pd.DataFrame):
    """Plot 3: Core Member Participation Over Time."""
    plt.figure(figsize=(12, 6))
    sns.lineplot(
        x=monthly_stats.index,
        y=monthly_stats["core_ratio"],
        marker="o",
        color="purple",
    )

    plt.title("Trend of Core Member Participation Ratio", fontsize=14)
    plt.ylabel("Core Member Contribution Ratio", fontsize=12)
    plt.xlabel("Time", fontsize=12)
    plt.ylim(0, 1.1)

    save_current_figure("timeline_analysis.png")
    plt.close()


def plot_core_ratio_vs_mean_duration(monthly_stats: pd.DataFrame):
    """NEW Plot: Correlation between core participation ratio and monthly mean duration."""
    if len(monthly_stats) < 3:
        print("⚠️ Not enough monthly points to draw correlation plot (need >= 3).")
        return

    # Pearson & Spearman correlation (no extra packages needed)
    pearson_r = monthly_stats["core_ratio"].corr(monthly_stats["mean_duration"])
    spearman_rho = monthly_stats["core_ratio"].corr(
        monthly_stats["mean_duration"], method="spearman"
    )

    plt.figure(figsize=(9, 6))
    plot_df = monthly_stats.reset_index().rename(columns={"index": "month"})

    # regplot: scatter + regression line
    sns.regplot(data=plot_df, x="core_ratio", y="mean_duration")

    plt.title(
        "Core Participation vs Monthly Mean Fix Duration\n"
        f"Pearson r={pearson_r:.3f} | Spearman ρ={spearman_rho:.3f}",
        fontsize=13,
    )
    plt.xlabel("Core Member Contribution Ratio", fontsize=12)
    plt.ylabel("Monthly Mean Fix Duration (Days)", fontsize=12)
    plt.xlim(-0.05, 1.05)

    save_current_figure("core_ratio_vs_mean_duration.png")
    plt.close()

    print(f"🔎 Correlation (Pearson r):  {pearson_r:.4f}")
    print(f"🔎 Correlation (Spearman ρ): {spearman_rho:.4f}")


# --- 5. Table 1: Descriptive Statistics ---
def build_table1(df: pd.DataFrame) -> pd.DataFrame:
    """Build Table 1: N, mean, median, Q1, Q3 for duration and comments."""
    def stats_block(g: pd.DataFrame):
        return pd.Series({
            "N": len(g),
            "Duration_mean": g["duration_days"].mean(),
            "Duration_median": g["duration_days"].median(),
            "Duration_Q1": g["duration_days"].quantile(0.25),
            "Duration_Q3": g["duration_days"].quantile(0.75),
            "Comments_mean": g["comments_count"].mean(),
            "Comments_median": g["comments_count"].median(),
            "Comments_Q1": g["comments_count"].quantile(0.25),
            "Comments_Q3": g["comments_count"].quantile(0.75),
        })

    group_table = df.groupby("Member Type").apply(stats_block).reset_index()
    overall = stats_block(df).to_frame().T
    overall.insert(0, "Member Type", "Overall")

    table1 = pd.concat([group_table, overall], ignore_index=True)

    # 更适合报告展示：四舍五入
    for c in table1.columns:
        if c != "Member Type" and c != "N":
            table1[c] = table1[c].astype(float).round(2)
    table1["N"] = table1["N"].astype(int)

    return table1


def df_to_markdown_table(df: pd.DataFrame) -> str:
    """No external dependency (tabulate-free) markdown table."""
    headers = list(df.columns)
    lines = []
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(str(row[h]) for h in headers) + " |")
    return "\n".join(lines) + "\n"


def save_table1_outputs(table1: pd.DataFrame):
    # 1) CSV
    latest_csv = os.path.join(TABLES_DIR, "table1_summary.csv")
    archive_csv = os.path.join(ARCHIVE_TABLE_DIR, "table1_summary.csv")
    table1.to_csv(latest_csv, index=False, encoding="utf-8-sig")
    table1.to_csv(archive_csv, index=False, encoding="utf-8-sig")
    print(f"📄 Saved (latest):   {latest_csv}")
    print(f"📦 Saved (archive):  {archive_csv}")

    # 2) Markdown
    md = df_to_markdown_table(table1)
    latest_md = os.path.join(TABLES_DIR, "table1_summary.md")
    archive_md = os.path.join(ARCHIVE_TABLE_DIR, "table1_summary.md")
    save_text_file(md, latest_md, archive_md)

    # 3) PNG table (for inserting into report as image)
    fig, ax = plt.subplots(figsize=(14, 2.2))
    ax.axis("off")

    display_df = table1.copy()
    # 把列名写得更像“表”
    display_df = display_df.rename(columns={
        "Member Type": "Group",
        "Duration_mean": "Duration mean",
        "Duration_median": "Duration median",
        "Duration_Q1": "Duration Q1",
        "Duration_Q3": "Duration Q3",
        "Comments_mean": "Comments mean",
        "Comments_median": "Comments median",
        "Comments_Q1": "Comments Q1",
        "Comments_Q3": "Comments Q3",
    })

    tbl = ax.table(
        cellText=display_df.values,
        colLabels=display_df.columns,
        cellLoc="center",
        loc="center",
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(10)
    tbl.scale(1, 1.4)

    latest_png = os.path.join(FIGURES_DIR, "table1_summary.png")
    archive_png = os.path.join(ARCHIVE_FIG_DIR, "table1_summary.png")
    plt.savefig(latest_png, dpi=300, bbox_inches="tight")
    plt.savefig(archive_png, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"🖼️ Saved (latest):   {latest_png}")
    print(f"📦 Saved (archive):  {archive_png}")

    print("\n=== Table 1 (printed) ===")
    print(table1.to_string(index=False))


# --- Main Execution ---
if __name__ == "__main__":
    setup_plotting_style()
    ensure_dirs()

    df = load_data(DATA_PATH)

    if df is not None:
        print("🚀 Starting visualization generation...")

        # 旧的三张图（保持与你原脚本一致）:contentReference[oaicite:3]{index=3}
        plot_duration_comparison(df)
        plot_comments_comparison(df)

        # 月统计（趋势图 & 相关性图共用）
        monthly_stats = compute_monthly_stats(df, MIN_FIXES_PER_MONTH)
        print(f"📅 Monthly points used (after filtering): {len(monthly_stats)}")

        plot_timeline_analysis(monthly_stats)

        # 新增：核心参与度 vs 月均修复时长相关性图
        plot_core_ratio_vs_mean_duration(monthly_stats)

        # 新增：表1数据统计表
        table1 = build_table1(df)
        save_table1_outputs(table1)

        print("✅ All outputs generated successfully!")

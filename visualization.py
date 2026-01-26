import sys
try:
    import pandas as pd
    import matplotlib.pyplot as plt
    import seaborn as sns
except ImportError as e:
    print(f"❌ critical error: {e}")
    print("Please run: pip install pandas matplotlib seaborn")
    sys.exit(1)
import os
import platform

# --- Configuration ---
DATA_PATH = 'data/django_bugs_filtered.csv'
FIGURES_DIR = 'figures'

# --- 1. Setup Environment ---
def setup_plotting_style():
    """Set up matplotlib style and fonts for Chinese support."""
    sns.set_theme(style="whitegrid")
    
    # Check OS directly using platform
    system_name = platform.system()
    if system_name == 'Windows':
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
    elif system_name == 'Darwin':  # macOS
        plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'PingFang SC']
    else:  # Linux/Other
        plt.rcParams['font.sans-serif'] = ['WenQuanYi Micro Hei', 'Noto Sans CJK SC']
        
    plt.rcParams['axes.unicode_minus'] = False
    print(f"🎨 Plotting style set. OS: {system_name}")

def ensure_dirs():
    """Ensure figures directory exists."""
    if not os.path.exists(FIGURES_DIR):
        os.makedirs(FIGURES_DIR)
        print(f"📁 Created directory: {FIGURES_DIR}")

# --- 2. Data Loading ---
def load_data(filepath):
    """Load and preprocess data."""
    if not os.path.exists(filepath):
        print(f"❌ Error: Data file not found at {filepath}")
        return None
        
    df = pd.read_csv(filepath)
    # Convert dates
    if 'created_at' in df.columns:
        df['created_at'] = pd.to_datetime(df['created_at'])
        
    # Map is_core_member to readable labels
    df['Member Type'] = df['is_core_member'].map({1: 'Core Member', 0: 'Community Contributor'})
    
    print(f"✅ Data loaded: {len(df)} records")
    return df

# --- 3. Visualization Functions ---

def plot_duration_comparison(df):
    """Plot 1: Fix Duration Comparison (Core vs Non-Core)."""
    plt.figure(figsize=(10, 6))
    
    # Removing extreme outliers for better visualization if needed
    # q_high = df['duration_days'].quantile(0.95)
    # data_filtered = df[df['duration_days'] < q_high]
    data_filtered = df 
    
    sns.boxplot(data=data_filtered, x='Member Type', y='duration_days', palette="Set2")
    
    plt.title('Bug Fix Duration: Core Members vs Community', fontsize=14)
    plt.ylabel('Duration (Days)', fontsize=12)
    plt.xlabel('Contributor Type', fontsize=12)
    
    save_path = os.path.join(FIGURES_DIR, 'duration_comparison.png')
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"📊 Saved: {save_path}")
    plt.close()

def plot_comments_comparison(df):
    """Plot 2: Comments Count Comparison (Communication Cost)."""
    plt.figure(figsize=(10, 6))
    
    sns.violinplot(data=df, x='Member Type', y='comments_count', palette="Pastel1", inner="quartile")
    
    plt.title('Communication Cost (Comments): Core Members vs Community', fontsize=14)
    plt.ylabel('Number of Comments', fontsize=12)
    plt.xlabel('Contributor Type', fontsize=12)
    
    save_path = os.path.join(FIGURES_DIR, 'comments_comparison.png')
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"📊 Saved: {save_path}")
    plt.close()

def plot_timeline_analysis(df):
    """Plot 3: Core Member Participation Over Time."""
    # Ensure datetime index
    df['month_year'] = df['created_at'].dt.to_period('M')
    
    # Calculate ratio per month
    monthly_stats = df.groupby('month_year').agg(
        total_fixes=('issue_id', 'count'),
        core_fixes=('is_core_member', 'sum')
    )
    monthly_stats['core_ratio'] = monthly_stats['core_fixes'] / monthly_stats['total_fixes']
    
    # Convert back to timestamp for plotting
    monthly_stats.index = monthly_stats.index.to_timestamp()
    
    plt.figure(figsize=(12, 6))
    sns.lineplot(data=monthly_stats, x=monthly_stats.index, y='core_ratio', marker='o', color='purple')
    
    plt.title('Trend of Core Member Participation Ratio', fontsize=14)
    plt.ylabel('Core Member Contribution Ratio', fontsize=12)
    plt.xlabel('Time', fontsize=12)
    plt.ylim(0, 1.1)
    
    save_path = os.path.join(FIGURES_DIR, 'timeline_analysis.png')
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"📊 Saved: {save_path}")
    plt.close()

# --- Main Execution ---
if __name__ == "__main__":
    setup_plotting_style()
    ensure_dirs()
    
    df = load_data(DATA_PATH)
    
    if df is not None:
        print("🚀 Starting visualization generation...")
        plot_duration_comparison(df)
        plot_comments_comparison(df)
        plot_timeline_analysis(df)
        print("✅ All visualizations generated successfully!")

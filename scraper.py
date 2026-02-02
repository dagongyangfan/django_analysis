import os
import time
import pandas as pd
from github import Github, Auth, RateLimitExceededException
from datetime import datetime

# --- 1. 配置区域 ---
TOKEN = os.getenv("GITHUB_TOKEN")
if not TOKEN:
    print("⚠️  警告：未检测到环境变量 GITHUB_TOKEN")
    TOKEN = input("👉 请手动输入 Token: ").strip()

REPO_NAME = "django/django"   # 目标仓库
MAX_ISSUES = 2000             # 采集数量扩大到 2000
CORE_LIMIT = 20               # 前 20 个贡献者视为核心成员

def save_to_csv(data_list):
    if not data_list:
        print("⚠️ 没有收集到数据，跳过保存。")
        return
    df = pd.DataFrame(data_list)
    os.makedirs('data', exist_ok=True)
    save_path = "data/django_bugs_analysis.csv"
    df.to_csv(save_path, index=False, encoding='utf-8-sig')
    print(f"\n💾 数据已保存至: {save_path}")
    print(f"📊 最终收集行数: {len(df)}")

def get_bug_data():
    auth = Auth.Token(TOKEN)
    g = Github(auth=auth)
    
    try:
        repo = g.get_repo(REPO_NAME)
        print(f"🔗 已连接到仓库: {REPO_NAME}")
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return []

    print("🕵️  正在识别核心贡献者...")
    contributors = repo.get_contributors()
    core_members = [c.login for c in contributors[:CORE_LIMIT]]
    print(f"✅ 核心成员名单: {core_members}")

    print("🚀 开始扫描 issues（按创建时间 asc）...")
    issues = repo.get_issues(state='closed', sort='created', direction='asc')
    
    bug_data = []
    scanned_count = 0

    try:
        for issue in issues:
            scanned_count += 1
            if scanned_count % 100 == 0:
                print(f"已扫描 {scanned_count} 条，已收集 {len(bug_data)} 条...")

            if len(bug_data) >= MAX_ISSUES:
                break

            title_lower = issue.title.lower()
            labels = [l.name.lower() for l in issue.labels]

            is_fix = (
                'fix' in title_lower or 
                'bug' in title_lower or 
                'fixed' in title_lower or
                any('bug' in lab for lab in labels)
            )
            if not is_fix:
                continue

            fixer = issue.user.login if issue.user else "Unknown"
            created = issue.created_at
            closed = issue.closed_at
            if not closed:
                continue

            duration = (closed - created).total_seconds() / 86400

            bug_data.append({
                "issue_id": issue.number,
                "type": "PR" if issue.pull_request else "Issue",
                "title": issue.title[:50],
                "duration_days": round(duration, 2),
                "comments_count": issue.comments,
                "fixer_login": fixer,
                "is_core_member": 1 if fixer in core_members else 0,
                "created_at": created.strftime('%Y-%m-%d')
            })

    except KeyboardInterrupt:
        print("🛑 手动中断，保存已有数据...")
    except RateLimitExceededException:
        print("🛑 触发 GitHub API 限速，请稍后重试或换 token。")

    return bug_data

if __name__ == "__main__":
    start_time = time.time()
    data = get_bug_data()
    save_to_csv(data)
    print(f"⏱️ 总耗时: {round(time.time() - start_time, 2)} 秒")

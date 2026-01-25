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
MAX_ISSUES = 500              # 建议先设为 200，保证快速出结果
CORE_LIMIT = 20               # 识别前 20 名核心成员

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

    # --- 2. 识别核心成员 ---
    print("🕵️  正在识别核心贡献者...")
    contributors = repo.get_contributors()
    core_members = [c.login for c in contributors[:CORE_LIMIT]]
    print(f"✅ 核心成员名单: {core_members}")

    # --- 3. 抓取循环 ---
    print(f"🚀 开始扫描 (将包含 PR 以获取有效修复数据)...")
    
    # 获取最近更新的已关闭记录
    issues = repo.get_issues(state='closed', sort='updated', direction='desc')
    
    bug_data = []
    scanned_count = 0
    
    try:
        for issue in issues:
            scanned_count += 1
            
            # 心跳提示
            if scanned_count % 50 == 0:
                print(f"running... [扫描: {scanned_count} | 收集: {len(bug_data)}] ...")

            if len(bug_data) >= MAX_ISSUES:
                break
            
            # --- Django 专属判定逻辑 ---
            title_lower = issue.title.lower()
            labels = [l.name.lower() for l in issue.labels]
            
            # 判断是否为修复类任务：标题含 fix/bug/regression 或标签含 bug
            is_fix = (
                'fix' in title_lower or 
                'bug' in title_lower or 
                'fixed' in title_lower or
                any('bug' in lab for lab in labels)
            )
            
            if not is_fix:
                continue 

            # 4. 提取数据
            # 优先获取提交者 (PR 的作者)，如果没有则取关闭者
            fixer = issue.user.login if issue.user else "Unknown"
            
            created = issue.created_at
            closed = issue.closed_at
            if not closed: continue

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
        print("\n🛑 手动停止，正在保存...")
    except RateLimitExceededException:
        print("🛑 触发限速，请稍后再试或更换 Token。")
    
    return bug_data

if __name__ == "__main__":
    start_time = time.time()
    data = get_bug_data()
    save_to_csv(data)
    print(f"⏱️ 总耗时: {round(time.time() - start_time, 2)} 秒")
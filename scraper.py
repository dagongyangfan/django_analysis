import os
from github import Github
import pandas as pd
from datetime import datetime

# 1. 初始化（申请Token，分析的项目为django）
token = os.getenv("GITHUB_TOKEN")
if not token:
    print("错误：未找到环境变量 GITHUB_TOKEN。请先在系统中设置。")
else:
    g = Github(token)
    try:
        user = g.get_user()
        print(f"验证成功！当前登录用户: {user.login}")
    except Exception as e:
        print(f"验证失败: {e}")

repo = g.get_repo("django/django")

# 2. 定义数据存储列表
bug_data = []

# 3. 抓取已关闭的 Bug Issue (这里限制数量以便演示)
issues = repo.get_issues(state='closed', labels=['bug'])

print("开始抓取数据...")
for i, issue in enumerate(issues):
    if i >= 500: break  # 先抓取500条进行分析
    
    # 获取修复时间（即关闭时间）
    creation_date = issue.created_at
    closed_date = issue.closed_at
    duration = (closed_date - creation_date).days # 修复周期（天）
    
    # 获取修复者（通常是关闭者或关联PR的作者，此处简化取关闭者）
    fixer = issue.closed_by.login if issue.closed_by else "Unknown"
    
    bug_data.append({
        "id": issue.number,
        "created_at": creation_date,
        "weekday": creation_date.weekday(), # 0=周一, 6=周日
        "hour": creation_date.hour,
        "duration": duration,
        "fixer": fixer
    })

df = pd.DataFrame(bug_data)
df.to_csv("django_bugs.csv", index=False)
print("数据保存成功！")
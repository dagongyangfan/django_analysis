import seaborn as sns
import matplotlib.pyplot as plt

# 统计周一到周日的平均修复耗时
plt.figure(figsize=(10,6))
sns.barplot(x='weekday', y='duration', data=df)
plt.title("Average Bug Fix Duration by Weekday")
plt.show()
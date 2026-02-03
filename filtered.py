import pandas as pd
import csv


def filter_django_bugs(input_file, output_file):
    """
    过滤Django bug数据中的测试数据和无用数据行

    参数:
        input_file: 输入CSV文件路径
        output_file: 输出CSV文件路径
    """

    # 读取CSV文件
    try:
        df = pd.read_csv(input_file)
        print(f"原始数据行数: {len(df)}")
    except FileNotFoundError:
        print(f"错误: 找不到文件 '{input_file}'")
        return
    except Exception as e:
        print(f"读取文件时出错: {e}")
        return

    # 过滤前的数据统计
    original_count = len(df)

    # 应用过滤条件

    # 条件1: 过滤测试ticket编号
    test_ticket_filter = ~df['title'].str.contains('#99999|my-feature', case=False, na=False)
    removed_test_tickets = len(df) - len(df[test_ticket_filter])

    # 条件2: 过滤自动化测试PR (Stitch Remote SWE)
    stitch_filter = ~df['title'].str.startswith('[Stitch Remote SWE]', na=False)
    removed_stitch = len(df[test_ticket_filter]) - len(df[test_ticket_filter & stitch_filter])

    # 条件3: 过滤零评论PR
    comments_filter = df['comments_count'] > 0
    removed_zero_comments = len(df[test_ticket_filter & stitch_filter]) - len(
        df[test_ticket_filter & stitch_filter & comments_filter])

    # 条件4: 过滤关键字段缺失的行
    missing_data_filter = df['issue_id'].notna() & df['title'].notna() & df['fixer_login'].notna()
    removed_missing = len(df[test_ticket_filter & stitch_filter & comments_filter]) - len(
        df[test_ticket_filter & stitch_filter & comments_filter & missing_data_filter])

    # 应用所有过滤条件
    filtered_df = df[test_ticket_filter & stitch_filter & comments_filter & missing_data_filter].copy()

    # 过滤后的数据统计
    filtered_count = len(filtered_df)
    removed_total = original_count - filtered_count

    # 打印过滤统计信息
    print("\n=== 过滤统计 ===")
    print(f"1. 测试ticket编号过滤: {removed_test_tickets} 行")
    print(f"2. 自动化测试PR过滤: {removed_stitch} 行")
    print(f"3. 零评论PR过滤: {removed_zero_comments} 行")
    print(f"4. 缺失数据过滤: {removed_missing} 行")
    print(f"总计过滤: {removed_total} 行")
    print(f"保留数据: {filtered_count} 行")
    print(f"过滤率: {(removed_total / original_count) * 100:.1f}%")

    # 保存过滤后的数据到新的CSV文件
    try:
        filtered_df.to_csv(output_file, index=False, quoting=csv.QUOTE_ALL)
        print(f"\n过滤后的数据已保存到: {output_file}")
    except Exception as e:
        print(f"保存文件时出错: {e}")
        return

    # 显示过滤前后数据对比
    print("\n=== 数据样本对比 ===")
    print("\n原始数据样本:")
    print(df[['issue_id', 'title', 'duration_days', 'comments_count']].head(3).to_string())

    print("\n过滤后数据样本:")
    print(filtered_df[['issue_id', 'title', 'duration_days', 'comments_count']].head(3).to_string())

    return filtered_df


if __name__ == "__main__":
    # 输入输出文件路径（修正为 data 文件夹）
    input_csv = "data/django_bugs_analysis.csv"
    output_csv = "data/django_bugs_filtered.csv"

    # 执行过滤
    filtered_data = filter_django_bugs(input_csv, output_csv)

    # 显示过滤后数据的简要统计
    if filtered_data is not None:
        print("\n=== 过滤后数据特征 ===")
        print(f"平均处理时长: {filtered_data['duration_days'].mean():.2f} 天")
        print(f"中位处理时长: {filtered_data['duration_days'].median():.2f} 天")
        print(f"平均评论数: {filtered_data['comments_count'].mean():.2f}")
        print(f"核心成员贡献占比: {(filtered_data['is_core_member'].sum() / len(filtered_data)) * 100:.1f}%")

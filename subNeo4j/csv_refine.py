import pandas as pd
import os


def merge_and_deduplicate_nodes(input_file):
    df = pd.read_csv(input_file)

    # 创建一个新的DataFrame，包含'start_node'和'end_node'的所有节点及其对应的ID
    start_nodes = (df[['start_node', 'start_node_id', 'start_node_label']].
                   rename(columns={'start_node': 'name', 'start_node_id': 'id:ID', 'start_node_label': 'label'}))
    end_nodes = (df[['end_node', 'end_node_id', 'end_node_label']].
                 rename(columns={'end_node': 'name', 'end_node_id': 'id:ID', 'end_node_label': 'label'}))
    doi_nodes = df[['doi', 'end_node_id']].rename(columns={'doi': 'name', 'end_node_id': 'id:ID'})
    doi_nodes['id:ID'] = doi_nodes['id:ID'] + 5000000
    doi_nodes['label'] = 'mention'

    # 将两个DataFrame垂直合并（concatenate）
    combined_df = pd.concat([start_nodes, end_nodes, doi_nodes], ignore_index=True)
    combined_df = combined_df.applymap(lambda x: x.lower().replace('_', ' ') if isinstance(x, str) else x)

    # 去重：根据'name'列去除重复的行，保留第一个出现的'node_id'
    return combined_df.drop_duplicates(subset='name', keep='first')

    # # 保存去重后的DataFrame到新的CSV文件
    # deduplicated_df.to_csv(output_file, index=False)
    # print(f"Merged and deduplicated nodes have been saved to {output_file}")


def extract_columns_to_csv(input_file, output_folder, columns_to_extract, output_filename):
    """
    Extract columns from a csv file.
    :param input_file:
    :param output_folder:
    :param columns_to_extract:
    :param output_filename:
    :return:
    """
    # 确保输出文件夹存在
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    # 构建输出文件路径
    base_filename = os.path.basename(input_file)
    name, ext = os.path.splitext(base_filename)
    output_file = os.path.join(output_folder, f"{output_filename}_extracted{ext}")

    # 读取原始CSV文件
    df = pd.read_csv(input_file)
    df['mention'] = 'mention'
    df.drop_duplicates()

    # 检查要提取的列是否都在DataFrame中
    missing_cols = set(columns_to_extract) - set(df.columns)
    if missing_cols:
        raise ValueError(f"The following columns are missing in the input CSV: {missing_cols}")

    # 提取指定的列
    extracted_df = df[columns_to_extract].dropna(how='any')  # 可选：删除所有值任意为空的行
    extracted_df = extracted_df.drop_duplicates(subset=columns_to_extract)

    # 将提取的列保存为新的CSV文件
    extracted_df.to_csv(output_file, index=False)
    print(f"Extracted columns have been saved to {output_file}")


# 指定输入文件路径、输出文件夹路径和要提取的列
input_csv = r'F:\WORK\flow_battery_pdf\CSV\output\output_csv.csv'  # 替换为你的CSV文件路径
output_directory = r'F:\WORK\flow_battery_pdf\CSV\output\output_csv_new'  # 替换为你想要保存新CSV文件的文件夹路径
start_node_columns_to_extract = ['start_node_id', 'start_node', 'doi']    # 结点类型
end_node_columns_to_extract = ['end_node_id', 'end_node', 'doi']    # 结点类型
relation_columns_to_extract = ['start_node_id', 'end_node_id', 'relationship']    # 关系类型


if __name__ == "__main__":
    # 调用函数进行提取和保存
    # extract_columns_to_csv(input_csv, output_directory, start_node_columns_to_extract, 'start_node')
    # extract_columns_to_csv(input_csv, output_directory, end_node_columns_to_extract, 'end_node')
    extract_columns_to_csv(input_csv, output_directory, relation_columns_to_extract, 'ref_relationship')
    # 构建输出文件路径
    base_filename = os.path.basename(input_csv)
    name, ext = os.path.splitext(base_filename)
    output_file = os.path.join(output_directory, f"new_node_extracted{ext}")  # ext = .csv
    # deduplicated_df = merge_and_deduplicate_nodes(input_csv)  # 合并去重node结点
    # deduplicated_df.to_csv(output_file, index=False)
    #
    #
    # # 读取CSV文件到DataFrame
    # df = pd.read_csv(output_file)

    # 检查是否已存在':LABEL'列，如果不存在则创建它并复制'name'列的值
    # if ':LABEL' not in df.columns:
        # df[':LABEL'] = df['name']
    # else:
        # 如果':LABEL'列已存在，可以选择更新或者保持原样
        # 这里选择更新':LABEL'列
        # df[':LABEL'].update(df['name'])

    # 将更改保存回CSV文件
    # df.to_csv(f'{output_directory}\\node_extracted_label_new.csv', index=False)






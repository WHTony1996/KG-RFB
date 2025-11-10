import csv
import json

from tqdm import tqdm
import os
import logging
import pandas as pd
pd.set_option('display.max_columns',None)


def write_json_to_csv(csv_file_path):
    with open(csv_file_path, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['start_node', 'relationship', 'end_node', 'start_node_label', 'end_node_label', 'doi'])
        for file in tqdm(os.listdir(r"F:\WORK\flow_battery_pdf\jsonfile_4")):
            file_path = os.path.join(r"F:\WORK\flow_battery_pdf\jsonfile_4", file)
            # print(f"file_path is :{file_path}")
            # 读取JSON文件
            for jsonfile in os.listdir(file_path):

                json_path = os.path.join(file_path, jsonfile)
                if json_path.endswith('.json') is False:
                    continue
                with open(json_path, 'r', encoding='utf-8') as f:
                    try:
                        import_data = json.load(f)
                    except json.JSONDecodeError as j_e:
                        logging.error(f"json_path:{json_path},{j_e}")
                        continue

                    # 定义需要检查的键
                    required_keys = {"start_node", "relationship", "end_node", "start_node_label", "end_node_label"}
                    # 过滤出包含所有所需键的字典
                    try:
                        valid_dicts = [item for item in import_data if required_keys.issubset(item.keys())]
                        # 写入数据行
                        for item in valid_dicts:
                            writer.writerow([item['start_node'].lower().replace("_", " "),
                                             item['relationship'].lower().replace("_", " "),
                                             item['end_node'].lower().replace("_", " "),
                                             item['start_node_label'].lower().replace("_", " "),
                                             item['end_node_label'].lower().replace("_", " "),
                                             file.title()])
                        # logging.info(f"txt_filename is :{txt_filename}")
                    except AttributeError as a:
                        logging.error(f"json_path:{json_path}\t{a}")


def add_unique_id_to_csv(input_file, output_file):
    # 读取原始CSV文件
    df = pd.read_csv(input_file, encoding='UTF-8')
    df.sort_values(by='doi', inplace=True, ascending=False)
    print(f"df_head{df.head()}")
    cleaned_df = df.dropna(how='any').copy()
    # print(f"{cleaned_df.head()}cleaned_df.head()")
    # print(f"cleaned_df[cleaned_df['doi'] == '996942':{cleaned_df[cleaned_df['doi'].str.contains('')]}")
    # 创建一个空的映射字典，用于存储节点到ID的映射

    node_to_id = {}
    next_id = 1  # 从1开始编号
    # 定义一个函数，用于根据节点获取或生成ID
    def get_or_assign_id(node):
        nonlocal next_id
        if node not in node_to_id:
            node_to_id[node] = next_id
            next_id += 1
        return node_to_id[node]

    # 应用get_or_assign_id函数到'start_node'和'end_node'列，生成新的ID列
    cleaned_df.loc[:, 'start_node_id'] = cleaned_df['start_node'].apply(get_or_assign_id)
    cleaned_df.loc[:, 'end_node_id'] = cleaned_df['end_node'].apply(get_or_assign_id)

    # 确保标题行存在并且列名正确
    # 如果你想自定义列名，可以在这里进行修改
    # result_df.columns = ['start_node', 'relationship', 'end_node', 'doi', 'start_node_id', 'end_node_id']
    # 保存带有新ID的DataFrame到新的CSV文件，确保包含标题行
    cleaned_df.to_csv(output_file, index=False, encoding='UTF-8')
    print(f"Node IDs have been added and saved to {output_file}")
    print(cleaned_df)


if __name__ == "__main__":
    # 清空日志文件
    with open('.\\log\\log_toneo4j.log', 'w'):
        pass  # 这将创建一个空文件或清空现有文件
    # 设置日志配置
    logging.basicConfig(filename='.\\log\\log_toneo4j.log', level=logging.INFO, format='%(asctime)s %(filename)s [line:%(lineno)d]  - %(levelname)s - %(message)s')

    csv_file_path = r'F:\WORK\flow_battery_pdf\CSV\output\output.csv'
    write_json_to_csv(csv_file_path)

    # 指定输入和输出文件路径以及要用于生成ID的列
    input_csv = csv_file_path  # 替换为你的CSV文件路径
    output_csv = r'F:\WORK\flow_battery_pdf\CSV\output\output_csv.csv'  # 替换为你想要保存的新CSV文件路径

    # 调用函数进行处理
    add_unique_id_to_csv(input_csv, output_csv)


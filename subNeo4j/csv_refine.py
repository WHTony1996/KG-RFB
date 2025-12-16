import pandas as pd
import os
import csv
import json
import logging
from tqdm import tqdm


class CSVRefiner:
    def __init__(self, json_root_dir, output_dir):
        """
        :param json_root_dir: 存放 JSON 文件夹的根目录 (例如 jsonfile_4)
        :param output_dir: CSV 输出目录
        """
        self.json_root_dir = json_root_dir
        self.output_dir = output_dir

        # 定义关键文件路径
        self.raw_csv = os.path.join(output_dir, 'output.csv')
        self.id_csv = os.path.join(output_dir, 'output_with_ids.csv')

        # 拆分后的文件路径
        self.node_path = os.path.join(output_dir, 'node_extracted.csv')
        self.relation_path = os.path.join(output_dir, 'relation_extracted.csv')
        self.ref_rel_path = os.path.join(output_dir, 'ref_relationship_extracted.csv')  # DOI 相关

        # 确保输出目录存在
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def step_1_json_to_csv(self):
        """遍历 JSON 文件夹合并为一个 CSV"""
        print("Step 1: Converting JSONs to raw CSV...")
        with open(self.raw_csv, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['start_node', 'relationship', 'end_node', 'start_node_label', 'end_node_label', 'doi'])
            # 1. 获取 F:\Data 下所有的子文件夹 (例如 DOI_file1, DOI_file2...)
            subfolders = [d for d in os.listdir(self.json_root_dir) if
                          os.path.isdir(os.path.join(self.json_root_dir, d))]
            for folder_name in tqdm(subfolders, desc="Processing DOIs"):
                folder_path = os.path.join(self.json_root_dir, folder_name)
                # 2. 遍历每个 DOI 文件夹
                # DOI 名称就是文件夹名称 (去除可能的路径干扰，只取名)
                current_doi = folder_name
                # 3. 遍历文件夹内的所有文件 (0.json, 1.json, 2.json...)
                for filename in os.listdir(folder_path):
                    if not filename.endswith('.json'):
                        continue

                    json_path = os.path.join(folder_path, filename)
                    try:
                        with open(json_path, 'r', encoding='utf-8') as jf:
                            import_data = json.load(jf)

                        # 兼容处理：内容可能是 list 也可能是 dict
                        data_list = import_data if isinstance(import_data, list) else [import_data]

                        required_keys = {"start_node", "relationship", "end_node"}

                        # 4. 写入 CSV
                        for item in data_list:
                            if not isinstance(item, dict): continue
                            if not required_keys.issubset(item.keys()): continue

                            writer.writerow([
                                str(item.get('start_node', '')).strip().lower().replace("_", " "),
                                str(item.get('relationship', '')).strip().lower().replace("_", " "),
                                str(item.get('end_node', '')).strip().lower().replace("_", " "),
                                str(item.get('start_node_label', '')).strip().lower().replace("_", " "),
                                str(item.get('end_node_label', '')).strip().lower().replace("_", " "),
                                current_doi  # 这里确保了 0.json 和 1.json 都归属于同一个 DOI
                            ])
                    except Exception as e:
                        logging.error(f"Error processing {json_path}: {e}")
            return True

    def step_2_add_unique_ids(self):
        """为 CSV 添加唯一 ID"""
        print("Step 2: Generating unique IDs for nodes...")
        if not os.path.exists(self.raw_csv):
            print("Error: Raw CSV not found.")
            return

        df = pd.read_csv(self.raw_csv, encoding='utf-8')
        df.sort_values(by='doi', inplace=True, ascending=False)
        cleaned_df = df.dropna(how='any').copy()

        node_to_id = {}
        next_id = 1

        def get_or_assign_id(node):
            nonlocal next_id
            node_key = str(node).strip()
            if node_key not in node_to_id:
                node_to_id[node_key] = next_id
                next_id += 1
            return node_to_id[node_key]

        cleaned_df['start_node_id'] = cleaned_df['start_node'].apply(get_or_assign_id)
        cleaned_df['end_node_id'] = cleaned_df['end_node'].apply(get_or_assign_id)

        cleaned_df.to_csv(self.id_csv, index=False, encoding='utf-8')
        print(f"IDs added. Saved to {self.id_csv}")

    def step_3_split_nodes_relations(self):
        """提取 Node, Relation, Reference 表"""
        print("Step 3: Splitting into Node, Relation, and Reference tables...")
        if not os.path.exists(self.id_csv): return

        df = pd.read_csv(self.id_csv)

        # 1. 提取关系 (Relation)
        # 假设普通关系列提取
        rel_cols = ['start_node_id', 'end_node_id', 'relationship']
        df_rel = df[rel_cols].dropna().drop_duplicates()
        df_rel.to_csv(self.relation_path, index=False)

        # 2. 提取节点 (Node) - 仅提取 start 和 end node
        # 这里需要合并 start 和 end node 的信息
        start_nodes = df[['start_node', 'start_node_id', 'start_node_label']].rename(
            columns={'start_node': 'name', 'start_node_id': 'id:ID', 'start_node_label': 'label'})
        end_nodes = df[['end_node', 'end_node_id', 'end_node_label']].rename(
            columns={'end_node': 'name', 'end_node_id': 'id:ID', 'end_node_label': 'label'})

        df_node = pd.concat([start_nodes, end_nodes], ignore_index=True)
        df_node = df_node.drop_duplicates(subset='id:ID')
        # 暂时保存，Step 4 会追加 DOI 节点
        df_node.to_csv(self.node_path, index=False)

        # 3. 提取 DOI 引用关系 (Reference)
        # 假设我们要记录文章引用了哪些节点，或者文章与节点的关系
        # 根据你的代码逻辑，这里似乎是用 doi 列作为 reference
        ref_cols = ['start_node_id', 'end_node_id', 'doi']
        df_ref = df[ref_cols].dropna().drop_duplicates()
        df_ref.to_csv(self.ref_rel_path, index=False)

    def step_4_process_doi_indices(self):
        """处理 DOI 索引，建立文献引用关系 (Reference Index)"""
        print("Step 4: Creating Reference Index and linking DOIs...")

        # 读取 Step 3 生成的文件
        if not (os.path.exists(self.ref_rel_path) and os.path.exists(self.node_path) and os.path.exists(
                self.relation_path)):
            print("Missing intermediate CSV files.")
            return

        df_ref = pd.read_csv(self.ref_rel_path)
        df_node = pd.read_csv(self.node_path)
        df_rel = pd.read_csv(self.relation_path)  # 普通关系

        # --- 1. 处理 DOI 节点 ---
        # 为 DOI 创建唯一的 ID (假设从 500000 开始)
        unique_dois = df_ref['doi'].unique()
        doi_map = {name: i + 500000 for i, name in enumerate(unique_dois)}

        doi_nodes = pd.DataFrame(list(doi_map.items()), columns=['name', 'id:ID'])
        doi_nodes['label'] = 'reference'  # 你的代码里是 refenence

        # 将 DOI 节点合并到主节点表
        df_node_final = pd.concat([df_node, doi_nodes], ignore_index=True)
        df_node_final.drop_duplicates(subset='id:ID', inplace=True)

        # 保存最终节点表 (供 Neo4j 导入)
        final_node_csv = os.path.join(self.output_dir, 'node_new.csv')
        df_node_final.to_csv(final_node_csv, index=False)
        print(f"Final Nodes saved to {final_node_csv}")

        # --- 2. 建立 DOI 引用关系 ---
        # 你的逻辑：StartNode -> Mention -> DOI <- Mention <- EndNode
        # 意思似乎是该文章(DOI)提到了这些节点

        # 映射 DOI 名字到 ID
        df_ref['doi_id'] = df_ref['doi'].map(doi_map)

        # 构建 Mention 关系表
        # 关系 1: Node -> Mention -> DOI (或者 DOI -> Mention -> Node，看你需求，这里照搬你的逻辑)
        # 原逻辑：':START_ID' = start_node_id, ':END_ID' = doi_ID

        mentions_1 = pd.DataFrame({
            ':START_ID': df_ref['start_node_id'],
            ':END_ID': df_ref['doi_id'],
            'relationship': 'mention'
        })

        mentions_2 = pd.DataFrame({
            ':START_ID': df_ref['end_node_id'],
            ':END_ID': df_ref['doi_id'],
            'relationship': 'mention'
        })

        all_mentions = pd.concat([mentions_1, mentions_2], ignore_index=True)
        all_mentions.dropna(inplace=True)

        # --- 3. 整理普通关系表 ---
        # 普通关系表需要重命名列以匹配 neo4j-admin import 格式
        df_rel_renamed = df_rel.rename(columns={
            'start_node_id': ':START_ID',
            'end_node_id': ':END_ID',
            # 'relationship': 'relationship' # 保持不变
        })

        # 合并普通关系和引用关系
        final_rel_df = pd.concat([df_rel_renamed, all_mentions], ignore_index=True)

        # 保存最终关系表
        final_rel_df.drop_duplicates(inplace=True)
        final_rel_csv = os.path.join(self.output_dir, 'relation_new.csv')
        final_rel_df.to_csv(final_rel_csv, index=False)
        print(f"Final Relations saved to {final_rel_csv}")


def run_pipeline(txt_dir_path):
    """主入口：串联所有步骤"""
    # 自动定义 CSV 输出目录 (在 txt 目录同级创建 CSV_Output)
    # 假设 txt_dir_path 是 .../jsonfile_4
    # output_dir 将是 .../CSV_Output
    parent_dir = os.path.dirname(txt_dir_path)
    output_dir = os.path.join(parent_dir, 'CSV_Output')

    print(f"\n--- Starting Full CSV Pipeline ---")
    print(f"Input JSON Dir: {txt_dir_path}")
    print(f"Output CSV Dir: {output_dir}")

    refiner = CSVRefiner(json_root_dir=txt_dir_path, output_dir=output_dir)

    refiner.step_1_json_to_csv()
    refiner.step_2_add_unique_ids()
    refiner.step_3_split_nodes_relations()
    refiner.step_4_process_doi_indices()

    print("\n--- Pipeline Completed Successfully ---")
    print(
        f"Import files ready:\n 1. {os.path.join(output_dir, 'node_new.csv')}\n 2. {os.path.join(output_dir, 'relation_new.csv')}")
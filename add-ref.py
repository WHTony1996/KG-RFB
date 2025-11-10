import pandas as pd
import os

ref_path = r'F:\WORK\flow_battery_pdf\CSV\output\\ref_relationship_extracted.csv'
node_path = r'F:\WORK\flow_battery_pdf\CSV\output\\node_extracted_new.csv'
relation_path = r'F:\WORK\flow_battery_pdf\CSV\output\\relation_extracted.csv'
doi_path = r'F:\WORK\flow_battery_pdf\CSV\output\output_csv_new\ref_relationship_extracted.csv'

df_ref = pd.read_csv(ref_path)
df_node = pd.read_csv(node_path)
df_rel = pd.read_csv(relation_path)

# df_rel = df_rel.drop(columns=df_rel.columns[0])
# df_rel.to_csv(relation_path, index=False)
# df_node = df_node.drop(columns=df_node.columns[0])
# df_node.to_csv(node_path, index=False)

# 为 doi创建id
df_doi = pd.read_csv(doi_path)
df_doi['unique_id'] = df_doi['name'].astype('category').cat.codes.astype('int64') + 500000
df_doi.drop('id:ID', axis=1, inplace=True)
doi_nodes = df_doi[['name', 'unique_id']].rename(columns={'name': 'name', 'unique_id': 'id:ID'})

doi_nodes.drop_duplicates(subset='name', keep='first', inplace=True)
doi_nodes[':LABEL'] = 'refenence'


df_node = pd.concat([df_node, doi_nodes], ignore_index=True)
print(df_node.columns)
df_node.to_csv(node_path)

# 创建映射
name_to_id = doi_nodes.set_index('name')['id:ID'].to_dict()
tmp_df_ref = df_ref.copy()
tmp_df_ref['doi_ID'] = df_ref['doi'].map(name_to_id)

tmp_df = pd.DataFrame(columns=df_rel.columns.tolist())
tmp_df.columns = df_rel.columns
tmp_df[':START_ID'] = tmp_df_ref['start_node_id']
tmp_df[':END_ID'] = tmp_df_ref['doi_ID']
tmp_df['relationship'] = 'mention'
# print(tmp_df)
tmp2_df = pd.DataFrame(columns=df_rel.columns.tolist())
tmp2_df[':START_ID'] = tmp_df_ref['end_node_id']
tmp2_df[':END_ID'] = tmp_df_ref['doi_ID']
tmp2_df['relationship'] = 'mention'
# print(tmp2_df)
tmp_df = pd.concat([tmp_df, tmp2_df], ignore_index=True)

# doi_rel = df_ref[['start_node_id', 'id:ID']].rename(columns={'start_node_id': ':START_ID', 'id:ID': ':END_ID'})
# doi_rel2 = df_ref[['end_node_id', 'id:ID']].rename(columns={'end_node_id': ':START_ID', 'id:ID': ':END_ID'})
# doi_rel = pd.concat([doi_rel, doi_rel2], ignore_index=True)
# doi_rel['relationship'] = 'mention'
df_rel = pd.concat([df_rel, tmp_df], ignore_index=True)
df_rel.to_csv(relation_path)

print(df_rel.columns)

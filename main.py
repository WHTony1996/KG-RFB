from pathlib import Path
import pdf_extract_text
import chat_client as cc
import subNeo4j.csv_refine as csv_refine
import llm_with_neo4j
import subprocess
import txt_2_json

command = """neo4j-admin database import full --nodes=Node="{node_csv}" --relationships=ORDERED="{rel_csv}" --trim-strings=true neo4j --multiline-fields=true --overwrite-destination --verbose"""

tasks = ['quit',
         'Extract node information',
        'Process Data (TXT -> JSON -> CSV + Reference Index)',
        'Write to the neo4j platform',
        'Use a question and answer system']

def run_powershell_command(command):
    # Run commands using PowerShell as a subprocess
    result = subprocess.run(
        ["powershell", "-Command", command],
        capture_output=True,  # Capture output
        text=True             # Decode the output as a string.
    )
    return result.stdout, result.stderr

if __name__ == "__main__":
    for i, task in enumerate(tasks):
        print(f"{i}, {task}")

    while True:
        task_input = input("Please enter the task number to execute the task (enter 'exit' or '0' to exit):")
        if task_input.lower() == "exit" or task_input == "0":
            print("The program has exited.")
            break
        try:
            task_num = int(task_input)
            if task_num < 1 or task_num >= len(tasks):
                print(f"Input error: Please enter a valid number between 1 and {len(tasks) - 1}.")
                continue
            if task_num == 1:
                pdf_extract_text.main()
            elif task_num == 2:
                target_directory = input("Please enter the ROOT directory path (containing DOI folders): ").strip()
                target_directory = target_directory.strip('"').strip("'")
                root_path = Path(target_directory)
                if not root_path.exists():
                    print("Error: Directory does not exist.")
                    continue
                print("\n--- Phase 1: Cleaning TXT to JSON ---")
                subdirs = [str(p) for p in root_path.iterdir() if p.is_dir()]
                if not subdirs:
                    print("Warning: No subdirectories found. Processing the root path only.")
                    subdirs = [str(root_path)]

                txt_2_json.process_txt_to_json(subdirs)
                print("\n--- Phase 2: Building Reference Index & CSVs ---")
                csv_refine.run_pipeline(str(root_path))
                # # --- Configuration---
                # # Please replace the following path with the directory path where the. txt file you want to process is located
                # # For example: target-directory=r "C: \ Users \ YourUser \ Documents \ MyJsonTxts"
                # # Alternatively, in Linux/macOS: target-directory="/home/Youruser/documents/myjsontxts"
                # target_directory = input("Please enter the directory path of TXT file:").strip()
                # # target_directory  = r"F:\WORK\flow_battery_pdf\jsonfile_4"
                # filePath = [f for f in Path(target_directory).iterdir() if f.is_dir()]
                #
                # # --- Ensure backup of important data before operation ---
                # print("\nThis script will read a. txt file and attempt to create a. json file.")
                # print("If a. json file with the same name already exists, it may be overwritten.")
                # print("Before continuing, it is recommended that you back up the relevant data!")
                # confirm = input("Are you sure you want to continue? (y/n): ").strip().lower()
                #
                # if confirm == 'y':
                #     txt_2_json.process_txt_to_json(filePath)
                # else:
                #     print("The operation has been canceled.")
                #     continue

            elif task_num == 3:
                print("\n--- Task 3: Import to Neo4j ---")
                csv_dir_input = input("Please enter the 'CSV_Output' directory path: ").strip().strip('"')
                csv_dir = Path(csv_dir_input)

                if not csv_dir.exists():
                    print("Error: Directory not found. Please check your path.")
                    continue

                node_csv_path = csv_dir / "node_new.csv"
                rel_csv_path = csv_dir / "relation_new.csv"
                if not node_csv_path.exists():
                    print(f"Error: Node file missing: {node_csv_path}")
                    continue
                if not rel_csv_path.exists():
                    print(f"Error: Relation file missing: {rel_csv_path}")
                    continue
                final_command = command.format(
                    node_csv=str(node_csv_path),
                    rel_csv=str(rel_csv_path)
                ).replace("\n", " ").strip()
                stdout, stderr = run_powershell_command(final_command)
                if stdout:
                    print(f"\n[Neo4j Output]:\n{stdout}")
                if stderr:
                    # Note: Many normal logs of Neo4j will also be output in STDerr,
                    # which may not necessarily result in errors
                    print(f"\n[Neo4j Log]:\n{stderr}")
                if "IMPORT DONE" in stdout:
                    print("\n✅ SUCCESS: Data successfully imported into Neo4j!")
            elif task_num == 4:
                llm_with_neo4j.main()
        except ValueError:
            print("Input error: Please enter a valid numeric code.")

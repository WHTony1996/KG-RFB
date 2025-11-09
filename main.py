import pdf_extract_text
import chat_client as cc
import csv_refine
import txt2json
import llm_with_neo4j
import subprocess

command = """neo4j-admin database import full `
       --nodes=Node=C:/Soft/Neo4j/neo4j-community-5.25.1/import/import/node_new.csv `
       --relationships=ORDERED=C:/Soft/Neo4j/neo4j-community-5.25.1/import/import/relation_new.csv `
       --trim-strings=true neo4j `
       --multiline-fields=true `
       --overwrite-destination `
       --verbose"""

tasks = ['quit',
         'Extract node information',
        'Add a reference index',
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
                csv_refine.extract_columns_to_csv()
            elif task_num == 3:
                stdout, stderr = run_powershell_command(command)
                if stdout:
                    print(f"Standard output：{stdout}")
                if stderr:
                    print(f"Error output：{stderr}")
            elif task_num == 4:
                llm_with_neo4j.main()
        except ValueError:
            print("Input error: Please enter a valid numeric code.")

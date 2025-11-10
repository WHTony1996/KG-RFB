import os
import json
import ast # For literal_eval
import re
from pathlib import Path

def repair_json_string(json_like_string):
    """
    Attempt to fix common JSON formatting issues.
    Return the repaired string, and if it cannot be fixed to a parsed level, return the original string.
    """
    original_string = json_like_string
    repaired_string = json_like_string

    # 1. Attempt to remove common comments (single line and multiple line)
    repaired_string = re.sub(r"//.*", "", repaired_string) # 移除 // 注释
    repaired_string = re.sub(r"/\*.*?\*/", "", repaired_string, flags=re.DOTALL) # 移除 /* */ 注释

    # 2. Replace Python's True/False/None with JSON's true/false/null
    repaired_string = re.sub(r"\bTrue\b", "true", repaired_string)
    repaired_string = re.sub(r"\bFalse\b", "false", repaired_string)
    repaired_string = re.sub(r"\bNone\b", "null", repaired_string)

    # 3. Attempt to remove trailing commas
    # Remove the comma after the last attribute in the object: ,} -> } and ,\n} -> \n}
    repaired_string = re.sub(r",\s*([}\]])", r"\1", repaired_string)

    # 4. Attempt to convert single quote keys and values into double quotes (this is a rough attempt and may not be perfect)
    # Note: This replacement is quite aggressive and may break the string content containing single quotes.
    # A better approach is to rely on ast.liter eval or more complex parsers.
    # But for demonstration purposes, let's briefly handle it here.
    # First, try replacing the part that looks like a key: 'key': ->'key':
    # repaired_string = re.sub(r"(')([^']+)(')\s*:", r'"\2"\g<0>:', repaired_string) #  This line is too complex and prone to errors, please comment it out first
    # A simpler (but risky) way:
    # Repareed_string=repareed_string. replace ("" "," "") # This is too rough and will break strings like "it's"

    return repaired_string

def process_txt_to_json(file_paths):
    """
    Traverse all. txt files in the specified directory and attempt to parse their contents as JSON,
    Fix common errors and save as a. json file with the same name.
    """
    if not file_paths:
        print("Error: No directory found.")
        return
    if len(file_paths) >= 1:
        for directory_path in file_paths:
            if not os.path.isdir(directory_path):
                print(f"Error: Catalog '{directory_path}' is not exist.")
                return
            print(f"Processing directory: {directory_path}")
            processed_files = 0
            successful_conversions = 0
            failed_conversions = 0

            for filename in os.listdir(directory_path):
                if filename.lower().endswith(".txt"):
                    txt_filepath = os.path.join(directory_path, filename)
                    base_name = os.path.splitext(filename)[0]
                    json_filepath = os.path.join(directory_path, base_name + ".json")

                    print(f"\n--- Processing: {filename} ---")
                    processed_files += 1

                    try:
                        with open(txt_filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                    except Exception as e:
                        print(f"Error: Unable to read file '{filename}': {e}")
                        failed_conversions += 1
                        continue

                    if not content.strip():
                        print(f"Warning: The file '{filename}' is empty and has been skipped.")
                        failed_conversions += 1
                        continue

                    parsed_data = None
                    error_message = ""

                    # Attempt 1: Directly parse using json. loads
                    try:
                        parsed_data = json.loads(content)
                        print(f"Success (direct parsing): '{filename}'")
                    except json.JSONDecodeError as e_direct:
                        error_message = f"Direct parsing failed: {e_direct}\n"
                        #Attempt 2: Use ast.literaleval (to handle Python style literals)
                        try:
                            # Ast.literaleval may be slower or have depth limitations for very large or deeply nested structures
                            # But it is very effective for most "JSON like" Python dictionaries/list strings
                            py_object = ast.literal_eval(content)
                            # If ast.literaleval is successful, py_order is a Python object
                            # Now we use json. dumps to convert it into a standard JSON string
                            # This will automatically handle True/False/None and quotation mark issues
                            json_string_from_ast = json.dumps(py_object, ensure_ascii=False, indent=4)
                            # Verify again with json. loads to ensure that the output of json. dumps is valid JSON
                            parsed_data = json.loads(json_string_from_ast)
                            print(f"Success (converted through ast.liter eval): '{filename}'")
                        except (ValueError, SyntaxError, TypeError) as e_ast:
                            error_message += f"ast.literal_eval failed: {e_ast}\n"
                            #Attempt 3: Perform some string repairs before attempting json. loads
                            repaired_content = repair_json_string(content)
                            try:
                                parsed_data = json.loads(repaired_content)
                                print(f"Success (resolved after repair): '{filename}'")
                            except json.JSONDecodeError as e_repaired:
                                error_message += f"Failed to parse after repair: {e_repaired}\n"
                                print(f"Error: Unable to parse '{filename}' into JSON. Error message attempted:\n{error_message}")
                                failed_conversions += 1
                                continue # Skip the save step
                        except Exception as e_general_ast: # Capture other ast related errors
                            error_message += f"ast.literal_eval An unexpected error occurred: {e_general_ast}\n"
                            print(f"Error: Unable to parse '{filename}' into JSON. Error message attempted:\n{error_message}")
                            failed_conversions += 1
                            continue


                    if parsed_data is not None:
                        try:
                            with open(json_filepath, 'w', encoding='utf-8') as jf:
                                json.dump(parsed_data, jf, ensure_ascii=False, indent=4)
                            print(f"Saved as: '{json_filepath}'")
                            successful_conversions += 1
                        except Exception as e:
                            print(f"Error: Unable to write JSON file '{json_filepath}': {e}")
                            failed_conversions += 1

        print(f"\n--- OVER ---")
        print(f"Total number of scanned files: {processed_files}")
        print(f"Successfully converted and saved: {successful_conversions}")
        print(f"Conversion failed or skipped: {failed_conversions}")

if __name__ == "__main__":

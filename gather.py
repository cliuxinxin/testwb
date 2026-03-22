import os

def extract_python_files(root_dir, output_file):
    # 1. 获取当前脚本的文件名，避免把自己也提进去
    current_script_name = os.path.basename(__file__)
    # 获取输出文件的文件名
    output_file_name = os.path.basename(output_file)
    
    # 需要忽略的目录
    exclude_dirs = {'.git', '__pycache__', 'venv', '.venv', '.idea', '.vscode', 'build', 'dist'}
    
    with open(output_file, 'w', encoding='utf-8') as f_out:
        for root, dirs, files in os.walk(root_dir):
            # 排除不需要的目录
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                # 2. 判断逻辑：是 .py 文件，且不是当前脚本，也不是输出文件
                if file.endswith('.py') and file != current_script_name and file != output_file_name:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, root_dir)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f_in:
                            content = f_in.read()
                            
                            # 按照要求的格式写入
                            f_out.write(f"文件位置：{relative_path}\n")
                            f_out.write("文件内容：\n")
                            f_out.write("```python\n")
                            f_out.write(content)
                            f_out.write("\n```\n")
                            f_out.write("-" * 50 + "\n\n")
                            
                        print(f"已提取: {relative_path}")
                    except Exception as e:
                        print(f"读取失败 {relative_path}: {e}")

if __name__ == "__main__":
    # 配置
    project_path = "."  # 目标代码库路径
    output_name = "project_context.txt"  # 生成的上下文文件名
    
    extract_python_files(project_path, output_name)
    print(f"\n提取完成！已排除脚本自身。结果见: {output_name}")
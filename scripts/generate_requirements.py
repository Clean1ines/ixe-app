#!/usr/bin/env python3
import sys
import subprocess

def get_python_version():
    version = sys.version_info
    return f"py{version.major}{version.minor}"

def compile_requirements():
    target = get_python_version()
    print(f"Generating requirements for {target}")
    
    # Use pip-tools if available, otherwise generate manually
    try:
        subprocess.run([
            sys.executable, "-m", "piptools", "compile", 
            "--allow-unsafe", "--generate-hashes",
            "--extra", target, "requirements.in", 
            "-o", "requirements.txt"
        ], check=True)
    except (subprocess.CalledProcessError, ImportError):
        print("pip-tools not available, generating basic requirements.txt")
        with open("requirements.in", "r") as f:
            content = f.read()
        
        # Simple parser for conditional dependencies
        lines = content.split('\n')
        output_lines = []
        in_section = False
        current_section = None
        
        for line in lines:
            if line.startswith('[') and line.endswith(']'):
                in_section = True
                current_section = line[1:-1]
                if current_section == target:
                    continue
                else:
                    in_section = False
                    continue
            elif line.strip() == '':
                in_section = False
                current_section = None
            
            if not in_section and not line.startswith('[') and line.strip() != '':
                output_lines.append(line)
        
        with open("requirements.txt", "w") as f:
            f.write('\n'.join(output_lines))
        
        print("Generated requirements.txt")

if __name__ == "__main__":
    compile_requirements()

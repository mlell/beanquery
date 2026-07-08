#!/usr/bin/env python3
"""
Script to update branch information in branches.yml and generate markdown tables.

This script:
1. Updates base-commit for each branch by finding the merge base with main
2. Updates merge status by checking if branch is merged into main
3. Can generate markdown table using pandoc

Usage:
    python fork_scripts/update_branches.py [--update] [--table] [--pandoc]
"""

import argparse
import subprocess
import yaml
from pathlib import Path
from typing import Dict, List, Any


def run_git_command(cmd: List[str]) -> str:
    """Run a git command and return output."""
    try:
        result = subprocess.run(
            ['git'] + cmd, 
            capture_output=True, 
            text=True, 
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Git command failed: {' '.join(['git'] + cmd)}")
        print(f"Error: {e.stderr}")
        return ""


def get_merge_base(branch: str, target: str = "main") -> str:
    """Get the merge base commit between branch and target."""
    return run_git_command(['merge-base', branch, target])


def get_author_date(commit: str) -> str:
    """Get the author date of a commit in ISO format."""
    return run_git_command(['show', '-s', '--format=%ai', commit])


def update_branches_info(yaml_file: Path, upstream_branch: str = "master", use_local: bool = False) -> bool:
    """Update base-commit and base-date for all branches in YAML file.
    
    Args:
        yaml_file: Path to branches.yml
        upstream_branch: Branch to calculate merge base against (default: master)
        use_local: If True, use local branch names; if False, use origin/branch (default: False)
    
    Note: The 'merged' field is not updated by this script and must be maintained manually.
    """
    try:
        with open(yaml_file, 'r') as f:
            data = yaml.safe_load(f)
        
        if 'branches' not in data:
            print("No 'branches' section found in YAML file")
            return False
        
        updated = False
        for branch_info in data['branches']:
            branch_name = branch_info['name']
            
            # Skip main/master branches
            if branch_name in ['main', 'master']:
                branch_info['base-commit'] = ""
                branch_info['base-date'] = ""
                continue
            
            # Use origin/branch by default, local branch if --local flag is set
            merge_base_branch = f"origin/{branch_name}" if not use_local else branch_name
            print(f"Updating branch: {merge_base_branch}")
            
            # Get merge base against upstream
            base_commit = get_merge_base(merge_base_branch, upstream_branch)
            if base_commit:
                old_base = branch_info.get('base-commit', '')
                short_commit = base_commit[:9]
                branch_info['base-commit'] = short_commit
                if old_base != short_commit:
                    updated = True
                    print(f"  Base commit: {short_commit}")
                
                # Get author date
                author_date = get_author_date(base_commit)
                old_date = branch_info.get('base-date', '')
                branch_info['base-date'] = author_date
                if old_date != author_date:
                    updated = True
                    print(f"  Base date: {author_date}")
            else:
                print(f"  Failed to get merge base for {branch_name}")
                continue
        
        # Write updated data back to file
        if updated:
            with open(yaml_file, 'w') as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
            print(f"Updated {yaml_file}")
        else:
            print("No changes needed")
        
        return True
    
    except Exception as e:
        print(f"Error updating branches: {e}")
        return False


def generate_markdown_table(yaml_file: Path, output_file: Path = None) -> bool:
    """Generate markdown table from branch information."""
    try:
        with open(yaml_file, 'r') as f:
            data = yaml.safe_load(f)
        
        if 'branches' not in data:
            print("No 'branches' section found in YAML file")
            return False
        
        # Generate markdown table
        markdown = "# Branch Information\n\n"
        markdown += "| Name | Base Commit | Base Date | Merged | Description |\n"
        markdown += "|------|-------------|-----------|--------|-------------|\n"
        
        for branch_info in data['branches']:
            name = branch_info['name']
            base_commit = branch_info.get('base-commit', '')
            base_date = branch_info.get('base-date', '')
            merged = "✓" if branch_info.get('merged', False) else "✗"
            description = branch_info.get('description', '')
            
            markdown += f"| {name} | `{base_commit}` | {base_date} | {merged} | {description} |\n"
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(markdown)
            print(f"Markdown table written to {output_file}")
        else:
            print(markdown)
        
        return True
    
    except Exception as e:
        print(f"Error generating markdown table: {e}")
        return False


def generate_pandoc_table(yaml_file: Path, output_file: Path = None) -> bool:
    """Generate table using pandoc for better formatting."""
    try:
        # First generate markdown table
        with open(yaml_file, 'r') as f:
            data = yaml.safe_load(f)
        
        if 'branches' not in data:
            print("No 'branches' section found in YAML file")
            return False
        
        # Create CSV for pandoc
        import csv
        import tempfile
        
        csv_data = []
        csv_data.append(['Name', 'Base Commit', 'Base Date', 'Merged', 'Description'])
        
        for branch_info in data['branches']:
            name = branch_info['name']
            base_commit = branch_info.get('base-commit', '')
            base_date = branch_info.get('base-date', '')
            merged = "Yes" if branch_info.get('merged', False) else "No"
            description = branch_info.get('description', '')
            
            csv_data.append([name, base_commit, base_date, merged, description])
        
        # Write temporary CSV
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_csv:
            writer = csv.writer(tmp_csv)
            writer.writerows(csv_data)
            csv_file = tmp_csv.name
        
        try:
            # Use pandoc to convert CSV to markdown
            cmd = [
                'pandoc', 
                '-f', 'csv',
                '-t', 'markdown',
                '--table-cols=left,left,left,center,left',
                csv_file
            ]
            
            if output_file:
                cmd.extend(['-o', str(output_file)])
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                if not output_file:
                    print(result.stdout)
                else:
                    print(f"Pandoc table written to {output_file}")
                return True
            else:
                print(f"Pandoc failed: {result.stderr}")
                return False
        
        finally:
            import os
            os.unlink(csv_file)
    
    except FileNotFoundError:
        print("Pandoc not found. Please install pandoc to use this feature.")
        return False
    except Exception as e:
        print(f"Error generating pandoc table: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Update branch information and generate tables")
    parser.add_argument('--update', action='store_true', help='Update base-commit and base-date')
    parser.add_argument('--table', action='store_true', help='Generate markdown table')
    parser.add_argument('--pandoc', action='store_true', help='Generate table using pandoc')
    parser.add_argument('--output', '-o', type=str, help='Output file for table generation')
    parser.add_argument('--yaml', default='fork_scripts/branches.yml', help='YAML file with branch info')
    parser.add_argument('--upstream', default='master', help='Upstream branch for merge base calculation (default: master)')
    parser.add_argument('--local', action='store_true', help='Use local branch names instead of origin/branch for merge base calculation')
    
    args = parser.parse_args()
    
    yaml_file = Path(args.yaml)
    
    if not yaml_file.exists():
        print(f"YAML file {yaml_file} not found")
        return 1
    
    success = True
    
    if args.update:
        print(f"Updating branch information (upstream: {args.upstream}, local: {args.local})...")
        success &= update_branches_info(yaml_file, args.upstream, args.local)
    
    if args.table:
        print("Generating markdown table...")
        output_file = Path(args.output) if args.output else None
        success &= generate_markdown_table(yaml_file, output_file)
    
    if args.pandoc:
        print("Generating pandoc table...")
        output_file = Path(args.output) if args.output else None
        success &= generate_pandoc_table(yaml_file, output_file)
    
    if not any([args.update, args.table, args.pandoc]):
        parser.print_help()
        return 1
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())

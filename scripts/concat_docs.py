#!/usr/bin/env python3
"""
Smart Documentation Concatenation Script

This script recursively finds all markdown files in the project, orders them logically,
and concatenates them into a single LLM-friendly document with smart delimiters.
"""

import os
import re
import fnmatch
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timezone
import subprocess

class DocConcatenator:
    """Smart documentation concatenator with logical ordering"""
    
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.output_file = self.root_dir / "LLM-DOCS-FULL.md"
        
        # Logical ordering rules - files matching these patterns get priority ordering
        self.priority_patterns = [
            # Main documentation in logical order
            ("docs/README.md", 1),
            ("docs/VCP_SYSTEM_OVERVIEW.md", 2),
            ("docs/VCP_SCHEMA_SPECIFICATION.md", 3),
            ("docs/PROVIDER_INTEGRATION_GUIDE.md", 4),
            ("docs/DEPLOYMENT_OPERATIONS_GUIDE.md", 5),
            
            # Root documentation
            ("README.md", 10),
            ("GETTING_STARTED.md", 11),
            ("INSTALLATION.md", 12),
            ("CONFIGURATION.md", 13),
            
            # Integration and API docs
            ("*INTEGRATION*.md", 20),
            ("*API*.md", 21),
            ("*WEBHOOK*.md", 22),
            
            # Operational docs
            ("*DEPLOYMENT*.md", 30),
            ("*MONITORING*.md", 31),
            ("*SECURITY*.md", 32),
            
            # Development docs
            ("*DEVELOPMENT*.md", 40),
            ("*CONTRIBUTING*.md", 41),
            ("*TESTING*.md", 42),
            
            # Troubleshooting and help
            ("*TROUBLESHOOTING*.md", 50),
            ("*FAQ*.md", 51),
            ("*HELP*.md", 52),
        ]
        
        # Patterns to exclude (dependency READMEs, etc.)
        self.exclude_patterns = [
            "*/node_modules/*",
            "*/venv/*",
            "*/env/*",
            "*/.venv/*",
            "*/site-packages/*",
            "*/vendor/*",
            "*/dist/*",
            "*/build/*",
            "*/__pycache__/*",
            "*/.git/*",
            "*/target/*",  # Rust build directory
            "*/pkg/*",     # Go packages
        ]
    
    def should_include_file(self, file_path: Path) -> bool:
        """Check if a markdown file should be included"""
        if not file_path.name.endswith('.md'):
            return False
        
        # Convert to string for pattern matching
        path_str = str(file_path.relative_to(self.root_dir))
        
        # Exclude patterns
        for pattern in self.exclude_patterns:
            if fnmatch.fnmatch(path_str, pattern):
                return False
        
        # Exclude the output file itself
        if file_path == self.output_file:
            return False
        
        return True
    
    def get_file_priority(self, file_path: Path) -> int:
        """Get priority order for a file based on patterns"""
        relative_path = str(file_path.relative_to(self.root_dir))
        
        for pattern, priority in self.priority_patterns:
            if fnmatch.fnmatch(relative_path, pattern):
                return priority
        
        # Default priority based on directory structure
        parts = Path(relative_path).parts
        
        if parts[0] == "docs":
            return 100  # Documentation directory
        elif len(parts) == 1:
            return 200  # Root level files
        else:
            return 1000 + len(parts)  # Nested files, deeper = later
    
    def extract_title(self, content: str, file_path: Path) -> str:
        """Extract title from markdown content"""
        lines = content.strip().split('\n')
        
        # Look for the first H1 heading
        for line in lines[:20]:  # Check first 20 lines
            line = line.strip()
            if line.startswith('# '):
                return line[2:].strip()
        
        # Fallback to filename without extension
        return file_path.stem.replace('_', ' ').replace('-', ' ').title()
    
    def build_file_tree(self, md_files: List[Path]) -> str:
        """Build a visual file tree of included markdown files"""
        tree_lines = ["# Documentation File Tree", "", "```"]
        
        # Group files by directory
        dirs: Dict[str, List[str]] = {}
        
        for file_path in md_files:
            rel_path = file_path.relative_to(self.root_dir)
            dir_name = str(rel_path.parent) if rel_path.parent != Path('.') else 'root'
            
            if dir_name not in dirs:
                dirs[dir_name] = []
            dirs[dir_name].append(rel_path.name)
        
        # Sort directories and files
        for dir_name in sorted(dirs.keys()):
            if dir_name == 'root':
                tree_lines.append(".")
            else:
                tree_lines.append(f"{dir_name}/")
            
            # Sort files within directory
            for filename in sorted(dirs[dir_name]):
                if dir_name == 'root':
                    tree_lines.append(f"├── {filename}")
                else:
                    tree_lines.append(f"│   ├── {filename}")
        
        tree_lines.extend(["```", ""])
        return '\n'.join(tree_lines)
    
    def create_smart_delimiter(self, file_path: Path, title: str, file_size: int) -> str:
        """Create a smart delimiter for file content"""
        rel_path = file_path.relative_to(self.root_dir)
        delimiter = "=" * 80
        
        return f"""
{delimiter}
📄 FILE: {rel_path}
📝 TITLE: {title}
📊 SIZE: {file_size:,} bytes
⏰ PROCESSED: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
{delimiter}
"""
    
    def process_content(self, content: str, file_path: Path) -> str:
        """Process markdown content for better LLM consumption"""
        # Remove excessive blank lines
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        
        # Ensure code blocks are properly formatted
        content = re.sub(r'^```(\w+)?\s*$', r'```\1', content, flags=re.MULTILINE)
        
        # Add file path context to relative links
        def fix_relative_links(match):
            link_path = match.group(1)
            if link_path.startswith(('http', 'https', '#', '/')):
                return match.group(0)  # Keep absolute links and anchors
            
            # Convert relative links to be relative to project root
            file_dir = file_path.parent
            resolved_path = (file_dir / link_path).relative_to(self.root_dir)
            return f"]({resolved_path})"
        
        content = re.sub(r'\]([^)]+\.(md|png|jpg|jpeg|gif|svg|pdf))', fix_relative_links, content)
        
        return content.strip()
    
    def find_markdown_files(self) -> List[Path]:
        """Recursively find all markdown files"""
        md_files = []
        
        for file_path in self.root_dir.rglob('*.md'):
            if self.should_include_file(file_path):
                md_files.append(file_path)
        
        return md_files
    
    def concatenate_docs(self) -> None:
        """Main concatenation function"""
        print(f"🔍 Scanning for markdown files in {self.root_dir}")
        
        # Find all markdown files
        md_files = self.find_markdown_files()
        print(f"📁 Found {len(md_files)} markdown files")
        
        if not md_files:
            print("❌ No markdown files found!")
            return
        
        # Sort files by priority
        md_files.sort(key=self.get_file_priority)
        
        print("📋 Files in processing order:")
        for i, file_path in enumerate(md_files, 1):
            rel_path = file_path.relative_to(self.root_dir)
            priority = self.get_file_priority(file_path)
            print(f"  {i:2d}. {rel_path} (priority: {priority})")
        
        # Build the concatenated document
        output_parts = []
        
        # Header
        header = f"""# VoiceLens Scripts - Complete Documentation

**Generated**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}  
**Total Files**: {len(md_files)}  
**Purpose**: Complete documentation context for LLM consumption

> This file is automatically generated by concatenating all project markdown files.
> Do not edit directly - changes will be overwritten.

---

"""
        output_parts.append(header)
        
        # File tree
        output_parts.append(self.build_file_tree(md_files))
        output_parts.append("---\n")
        
        # Process each file
        total_size = 0
        processed_files = []
        
        for file_path in md_files:
            try:
                print(f"📖 Processing: {file_path.relative_to(self.root_dir)}")
                
                # Read file content
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                file_size = len(content.encode('utf-8'))
                total_size += file_size
                
                # Extract title and process content
                title = self.extract_title(content, file_path)
                processed_content = self.process_content(content, file_path)
                
                # Add to output
                delimiter = self.create_smart_delimiter(file_path, title, file_size)
                output_parts.append(delimiter)
                output_parts.append(processed_content)
                output_parts.append("\n")
                
                processed_files.append({
                    'path': str(file_path.relative_to(self.root_dir)),
                    'title': title,
                    'size': file_size
                })
                
            except Exception as e:
                print(f"❌ Error processing {file_path}: {e}")
                continue
        
        # Footer with summary
        footer = f"""
{'=' * 80}
📊 DOCUMENTATION SUMMARY
{'=' * 80}

**Total Files Processed**: {len(processed_files)}
**Total Content Size**: {total_size:,} bytes ({total_size / 1024:.1f} KB)
**Generated At**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}

## Files Included:

"""
        
        for file_info in processed_files:
            footer += f"- **{file_info['path']}** - {file_info['title']} ({file_info['size']:,} bytes)\n"
        
        footer += f"""
---

*This consolidated documentation provides complete context about the VoiceLens Scripts project,
including the Voice Context Protocol (VCP) system, provider integrations, deployment guides,
and operational procedures.*

**Repository**: https://github.com/prompted365/voicelens-scripts
**Documentation Directory**: docs/
**Last Updated**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
"""
        
        output_parts.append(footer)
        
        # Write output file
        final_content = '\n'.join(output_parts)
        
        print(f"💾 Writing to {self.output_file}")
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write(final_content)
        
        final_size = len(final_content.encode('utf-8'))
        print(f"✅ Success! Generated {final_size:,} bytes ({final_size / 1024:.1f} KB)")
        print(f"📄 Output: {self.output_file}")

def main():
    """Main execution function"""
    try:
        # Get the script directory and project root
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        
        print(f"🚀 VoiceLens Documentation Concatenator")
        print(f"📂 Project Root: {project_root}")
        
        # Create concatenator and run
        concatenator = DocConcatenator(str(project_root))
        concatenator.concatenate_docs()
        
    except KeyboardInterrupt:
        print("\n❌ Cancelled by user")
    except Exception as e:
        print(f"💥 Error: {e}")
        raise

if __name__ == "__main__":
    main()
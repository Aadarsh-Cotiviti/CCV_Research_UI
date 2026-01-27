#!/usr/bin/env python3
"""
NCCI RAG Build Pipeline - Build All Indices

This script executes all build steps in sequence, from PDF extraction to index building.

Usage:
    python ncci_rag/build_all.py
    
Or from ncci_rag directory:
    cd ncci_rag && python build_all.py
"""

import os
import sys
import subprocess
from pathlib import Path

# Color output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_step(step_num, total_steps, description):
    """Print step header"""
    print(f"\n{Colors.HEADER}{'='*70}{Colors.ENDC}")
    print(f"{Colors.BOLD}📍 Step {step_num}/{total_steps}: {description}{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*70}{Colors.ENDC}\n")

def print_success(message):
    """Print success message"""
    print(f"{Colors.OKGREEN}✅ {message}{Colors.ENDC}")

def print_error(message):
    """Print error message"""
    print(f"{Colors.FAIL}❌ {message}{Colors.ENDC}")

def print_warning(message):
    """Print warning message"""
    print(f"{Colors.WARNING}⚠️  {message}{Colors.ENDC}")

def run_command(command, description):
    """Run command and check result"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        print_success(f"{description} - Completed")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"{description} - Failed")
        print(f"Error output:\n{e.stderr}")
        return False

def check_prerequisites():
    """Check prerequisites"""
    print_step(0, 6, "Check Prerequisites")
    
    # Determine base directory
    if os.path.exists("ncci_rag/data"):
        base_dir = "ncci_rag/"
    elif os.path.exists("data"):
        base_dir = ""
    else:
        print_error("Cannot determine project root directory")
        return False
    
    # Check PDF file
    pdf_path = f"{base_dir}data/ncci_manual.pdf"
    if not os.path.exists(pdf_path):
        print_error(f"NCCI manual PDF file not found: {pdf_path}")
        print_warning("Please place ncci_manual.pdf in ncci_rag/data/ directory")
        return False
    print_success(f"PDF file found: {pdf_path}")
    
    # Check required Python packages
    required_packages = [
        ('fitz', 'PyMuPDF'),
        ('regex', 'regex'),
        ('rank_bm25', 'rank-bm25'),
        ('chromadb', 'chromadb'),
        ('pydantic', 'pydantic'),
    ]
    
    missing_packages = []
    for module_name, package_name in required_packages:
        try:
            __import__(module_name)
            print_success(f"Installed: {package_name}")
        except ImportError:
            missing_packages.append(package_name)
            print_warning(f"Missing dependency: {package_name}")
    
    if missing_packages:
        print_error(f"Missing dependencies: {', '.join(missing_packages)}")
        print(f"\nPlease run the following command to install:")
        print(f"{Colors.OKCYAN}pip install {' '.join(missing_packages)}{Colors.ENDC}\n")
        return False
    
    # Create build directory
    build_dir = f"{base_dir}build"
    os.makedirs(build_dir, exist_ok=True)
    print_success(f"Build directory ready: {build_dir}")
    
    return True

def main():
    """Main build process"""
    print(f"\n{Colors.BOLD}{Colors.OKBLUE}")
    print("╔═══════════════════════════════════════════════════════════════════╗")
    print("║         NCCI RAG Pipeline - Index Build Tool v1.0                 ║")
    print("║         Build all indices for NCCI manual retrieval               ║")
    print("╚═══════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}\n")
    
    # Check prerequisites
    if not check_prerequisites():
        print_error("Prerequisites check failed, build aborted")
        sys.exit(1)
    
    # Determine base directory and Python path
    if os.path.exists("ncci_rag/data"):
        base_dir = "ncci_rag/"
        python_cmd = sys.executable
    else:
        base_dir = ""
        python_cmd = sys.executable
    
    # Build steps definition
    steps = [
        {
            "num": 1,
            "cmd": f"{python_cmd} {base_dir}src/extract_pdf.py",
            "desc": "Extract PDF text to JSONL",
            "output": f"{base_dir}build/pages.jsonl"
        },
        {
            "num": 2,
            "cmd": f"{python_cmd} {base_dir}src/extract_toc.py",
            "desc": "Extract table of contents",
            "output": f"{base_dir}build/table_of_contents.json"
        },
        {
            "num": 3,
            "cmd": f"{python_cmd} {base_dir}src/chunk_and_tag.py",
            "desc": "Chunk and tag text",
            "output": f"{base_dir}build/chunks.jsonl"
        },
        {
            "num": 4,
            "cmd": f"{python_cmd} {base_dir}src/build_range_index.py",
            "desc": "Build CPT code range index",
            "output": f"{base_dir}build/cpt_range_index.db"
        },
        {
            "num": 5,
            "cmd": f"{python_cmd} {base_dir}src/build_bm25.py",
            "desc": "Build BM25 lexical index",
            "output": f"{base_dir}build/bm25_index.pkl"
        },
        {
            "num": 6,
            "cmd": f"{python_cmd} {base_dir}src/build_embeddings_chroma.py",
            "desc": "Build semantic vector index (ChromaDB)",
            "output": f"{base_dir}build/chroma_db"
        }
    ]
    
    total_steps = len(steps)
    failed_steps = []
    skipped_steps = []
    
    # Execute each step
    for step in steps:
        print_step(step["num"], total_steps, step["desc"])
        
        # Check if output already exists
        if os.path.exists(step["output"]):
            if os.path.isdir(step["output"]):
                print_success(f"Output directory already exists: {step['output']}")
            else:
                file_size = os.path.getsize(step["output"]) / 1024  # KB
                print_success(f"Output file already exists: {step['output']} ({file_size:.2f} KB)")
            print(f"{Colors.OKCYAN}⏭️  Skipping Step {step['num']} - already built{Colors.ENDC}\n")
            skipped_steps.append(step["num"])
            continue
        
        # Run build command
        if not run_command(step["cmd"], step["desc"]):
            failed_steps.append(step["num"])
            print_error(f"Step {step['num']} failed, continuing with remaining steps...")
            continue
        
        # Verify output file was created
        if os.path.exists(step["output"]):
            if os.path.isdir(step["output"]):
                print_success(f"Output directory created: {step['output']}")
            else:
                file_size = os.path.getsize(step["output"]) / 1024  # KB
                print_success(f"Output file created: {step['output']} ({file_size:.2f} KB)")
        else:
            print_warning(f"Output file not found: {step['output']}")
    
    # Build completion summary
    print(f"\n{Colors.HEADER}{'='*70}{Colors.ENDC}")
    print(f"{Colors.BOLD}🎉 Build Process Completed{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*70}{Colors.ENDC}\n")
    
    # Print summary
    built_steps = [s for s in range(1, total_steps + 1) if s not in failed_steps and s not in skipped_steps]
    
    if skipped_steps:
        print(f"{Colors.OKCYAN}⏭️  Skipped (already exist): {len(skipped_steps)} step(s){Colors.ENDC}")
    if built_steps:
        print(f"{Colors.OKGREEN}✅ Built: {len(built_steps)} step(s){Colors.ENDC}")
    if failed_steps:
        print(f"{Colors.FAIL}❌ Failed: {len(failed_steps)} step(s){Colors.ENDC}")
    
    if failed_steps:
        print(f"\n{Colors.WARNING}Following steps failed: {', '.join([f'Step {s}' for s in failed_steps])}{Colors.ENDC}")
        print_warning("Please check error logs and re-run corresponding steps")
        sys.exit(1)
    else:
        print_success("\nAll required indices are ready!")
        print(f"\n{Colors.OKBLUE}📁 Build output directory:{Colors.ENDC} {base_dir}build/")
        print(f"\n{Colors.OKGREEN}✨ Now you can run Section 5 (NCCI Compliance)!{Colors.ENDC}\n")
        
        # Show next steps
        print(f"{Colors.OKCYAN}💡 Next steps:{Colors.ENDC}")
        print(f"   1. Start Streamlit app: streamlit run app.py")
        print(f"   2. Navigate to Section 5: NCCI Compliance Check")
        print(f"   3. Or test retrieval: python {base_dir}src/retrieve.py --cpt 99213\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}⚠️  Build process interrupted by user{Colors.ENDC}\n")
        sys.exit(1)
    except Exception as e:
        print_error(f"Build process encountered unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

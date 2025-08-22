#!/usr/bin/env python3
"""
Minimal Axiom CLI - Clean interface without system message pollution
Self-sufficient AI assistant that can create its own tools
"""

import argparse
import sys
import json
from pathlib import Path
from .core import MinimalAxiom

def cmd_execute(args):
    """Execute Python code"""
    axiom = MinimalAxiom()
    result = axiom.execute_code(args.code)
    
    if result['success']:
        if result['output']:
            print(result['output'])
        else:
            print("✅ Code executed successfully (no output)")
    else:
        print(f"❌ Execution failed: {result['error']}")

def cmd_analyze(args):
    """Analyze code file"""
    axiom = MinimalAxiom()
    result = axiom.analyze_code(args.file)
    
    if result['status'] == 'success':
        print(f"📁 File: {result['file_path']}")
        print(f"📊 Lines: {result['lines']}")
        print(f"🔧 Functions: {len(result['functions'])}")
        print(f"🏗️  Classes: {len(result['classes'])}")
        print(f"📦 Imports: {len(result['imports'])}")
        
        if args.verbose:
            if result['functions']:
                print("\n🔧 Functions:")
                for func in result['functions']:
                    print(f"  • {func['name']}({', '.join(func['args'])}) - line {func['line']}")
            
            if result['classes']:
                print("\n🏗️  Classes:")
                for cls in result['classes']:
                    print(f"  • {cls['name']} - line {cls['line']}")
    else:
        print(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")

def cmd_coherence(args):
    """Check code coherence"""
    axiom = MinimalAxiom()
    
    if args.file:
        code = axiom.read_file(args.file)
        if not code:
            print(f"❌ Could not read file: {args.file}")
            return
    else:
        code = args.code
    
    result = axiom.check_coherence(code)
    
    if result['coherent']:
        print(f"✅ COHERENT (score: {result['score']:.3f})")
    else:
        print(f"❌ INCOHERENT (score: {result['score']:.3f})")
        if result['contradictions']:
            print("🚨 Issues found:")
            for contradiction in result['contradictions']:
                print(f"  • {contradiction}")

def cmd_create_tool(args):
    """Create a new tool"""
    axiom = MinimalAxiom()
    
    # Read tool code from file or stdin
    if args.file:
        tool_code = axiom.read_file(args.file)
        if not tool_code:
            print(f"❌ Could not read file: {args.file}")
            return
    else:
        print("Enter tool code (Ctrl+D to finish):")
        tool_code = sys.stdin.read()
    
    result = axiom.create_tool(args.name, tool_code)
    
    if result['success']:
        print(f"✅ Tool '{args.name}' created successfully")
        print(f"📁 Location: {result['tool_path']}")
        print(f"🎯 Coherence score: {result['coherence_score']:.3f}")
    else:
        print(f"❌ Tool creation failed: {result['error']}")

def cmd_bash(args):
    """Execute bash command"""
    axiom = MinimalAxiom()
    result = axiom.execute_bash(args.command, timeout=args.timeout)
    
    if result['success']:
        if result['output']:
            print(result['output'])
        else:
            print("✅ Command executed successfully (no output)")
    else:
        print(f"❌ Command failed: {result['error']}")

def cmd_create_file(args):
    """Create a file"""
    axiom = MinimalAxiom()
    
    if args.content:
        content = args.content
    else:
        print("Enter file content (Ctrl+D to finish):")
        content = sys.stdin.read()
    
    success = axiom.create_file(args.path, content)
    
    if success:
        print(f"✅ File created: {args.path}")
    else:
        print(f"❌ Failed to create file: {args.path}")

def cmd_read_file(args):
    """Read a file"""
    axiom = MinimalAxiom()
    content = axiom.read_file(args.path)
    
    if content:
        print(content)
    else:
        print(f"❌ Could not read file: {args.path}")

def cmd_interactive(args):
    """Interactive mode"""
    print("🚀 Minimal Axiom - Interactive Mode")
    print("Type 'help' for commands, 'exit' to quit")
    
    axiom = MinimalAxiom()
    
    while True:
        try:
            command = input("\naxiom> ").strip()
            
            if command in ['exit', 'quit']:
                print("👋 Goodbye!")
                break
            elif command == 'help':
                print("""
Available commands:
  exec <code>           - Execute Python code
  analyze <file>        - Analyze code file
  coherence <code>      - Check code coherence
  bash <command>        - Execute bash command
  create <path>         - Create file (enter content)
  read <path>           - Read file
  help                  - Show this help
  exit                  - Quit
""")
            elif command.startswith('exec '):
                code = command[5:]
                result = axiom.execute_code(code)
                if result['success']:
                    if result['output']:
                        print(result['output'])
                else:
                    print(f"❌ {result['error']}")
            
            elif command.startswith('analyze '):
                file_path = command[8:]
                result = axiom.analyze_code(file_path)
                if result['status'] == 'success':
                    print(f"Functions: {len(result['functions'])}, Classes: {len(result['classes'])}")
                else:
                    print(f"❌ {result.get('error', 'Analysis failed')}")
            
            elif command.startswith('coherence '):
                code = command[10:]
                result = axiom.check_coherence(code)
                status = "✅ COHERENT" if result['coherent'] else "❌ INCOHERENT"
                print(f"{status} (score: {result['score']:.3f})")
            
            elif command.startswith('bash '):
                bash_cmd = command[5:]
                result = axiom.execute_bash(bash_cmd)
                if result['success'] and result['output']:
                    print(result['output'])
                elif not result['success']:
                    print(f"❌ {result['error']}")
            
            elif command.startswith('read '):
                file_path = command[5:]
                content = axiom.read_file(file_path)
                if content:
                    print(content)
                else:
                    print(f"❌ Could not read: {file_path}")
            
            elif command.startswith('create '):
                file_path = command[7:]
                print("Enter content (Ctrl+D to finish):")
                try:
                    content = sys.stdin.read()
                    success = axiom.create_file(file_path, content)
                    if success:
                        print(f"✅ Created: {file_path}")
                    else:
                        print(f"❌ Failed to create: {file_path}")
                except KeyboardInterrupt:
                    print("\n❌ Cancelled")
            
            elif command:
                print(f"❌ Unknown command: {command}")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except EOFError:
            print("\n👋 Goodbye!")
            break

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Minimal Axiom - Self-sufficient AI assistant")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Execute command
    exec_parser = subparsers.add_parser('exec', help='Execute Python code')
    exec_parser.add_argument('code', help='Python code to execute')
    exec_parser.set_defaults(func=cmd_execute)
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze code file')
    analyze_parser.add_argument('file', help='File to analyze')
    analyze_parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    analyze_parser.set_defaults(func=cmd_analyze)
    
    # Coherence command
    coherence_parser = subparsers.add_parser('coherence', help='Check code coherence')
    coherence_group = coherence_parser.add_mutually_exclusive_group(required=True)
    coherence_group.add_argument('--code', help='Code to check')
    coherence_group.add_argument('--file', help='File to check')
    coherence_parser.set_defaults(func=cmd_coherence)
    
    # Create tool command
    tool_parser = subparsers.add_parser('create-tool', help='Create a new tool')
    tool_parser.add_argument('name', help='Tool name')
    tool_parser.add_argument('--file', help='File containing tool code')
    tool_parser.set_defaults(func=cmd_create_tool)
    
    # Bash command
    bash_parser = subparsers.add_parser('bash', help='Execute bash command')
    bash_parser.add_argument('command', help='Bash command to execute')
    bash_parser.add_argument('--timeout', type=int, default=30, help='Timeout in seconds')
    bash_parser.set_defaults(func=cmd_bash)
    
    # File operations
    create_parser = subparsers.add_parser('create', help='Create a file')
    create_parser.add_argument('path', help='File path')
    create_parser.add_argument('--content', help='File content')
    create_parser.set_defaults(func=cmd_create_file)
    
    read_parser = subparsers.add_parser('read', help='Read a file')
    read_parser.add_argument('path', help='File path')
    read_parser.set_defaults(func=cmd_read_file)
    
    # Interactive mode
    interactive_parser = subparsers.add_parser('interactive', help='Interactive mode')
    interactive_parser.set_defaults(func=cmd_interactive)
    
    args = parser.parse_args()
    
    if hasattr(args, 'func'):
        args.func(args)
    else:
        # Default to interactive mode
        cmd_interactive(args)

if __name__ == "__main__":
    main()
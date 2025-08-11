#!/usr/bin/env python3
"""
Comprehensive benchmark suite for Mom's interactive command system.
"""

import time
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, asdict
import statistics

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from momo_mom.interactive import MomInteractiveSystem
from momo_mom.agents.base import ExecutionContext, CommandResult


@dataclass
class BenchmarkResult:
    """Result of a benchmark test."""
    test_name: str
    command: str
    expected_agent: str
    actual_agent: str
    execution_time: float
    success: bool
    error_message: str = ""
    interaction_count: int = 0
    
    @property
    def agent_match(self) -> bool:
        return self.expected_agent == self.actual_agent
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MomBenchmarkSuite:
    """Comprehensive benchmark suite for Mom's interactive system."""
    
    def __init__(self):
        self.config = self._get_benchmark_config()
        self.system = MomInteractiveSystem(self.config)
        self.results: List[BenchmarkResult] = []
        self._setup_test_callback()
    
    def _get_benchmark_config(self) -> Dict[str, Any]:
        """Get configuration for benchmarking."""
        return {
            'interactive': {
                'enable_executing_agent': True,
                'enable_specialized_agents': True,
                'enable_general_agent': True,
                'plugins': [],
            },
            'user_preferences': {
                'author': 'Benchmark User',
                'email': 'benchmark@example.com',
                'license': 'MIT',
                'git_username': 'benchmarkuser',
                'git_email': 'benchmark@example.com',
            },
            'output': {
                'format': 'structured',
                'head_lines': 5,
                'tail_lines': 5,
            }
        }
    
    def _setup_test_callback(self):
        """Setup test callback for executing agent."""
        def benchmark_callback(request: Dict[str, Any]) -> str:
            """Benchmark callback that provides consistent responses."""
            prompt = request.get('prompt', '').lower()
            
            # Provide consistent test responses
            if 'continue' in prompt or '(y/n)' in prompt:
                return 'y'
            elif 'name' in prompt:
                return 'benchmark-project'
            elif 'version' in prompt:
                return '1.0.0'
            elif 'description' in prompt:
                return 'Benchmark test project'
            elif 'author' in prompt:
                return 'Benchmark User'
            elif 'license' in prompt:
                return 'MIT'
            else:
                return ''
        
        self.system.set_executing_agent_callback(benchmark_callback)
    
    def run_all_benchmarks(self) -> Dict[str, Any]:
        """Run all benchmark tests."""
        print("🚀 Mom Interactive System Benchmark Suite")
        print("=" * 60)
        
        # Run test suites
        self._benchmark_agent_selection()
        self._benchmark_command_execution()
        self._benchmark_specialized_agents()
        self._benchmark_performance()
        self._benchmark_error_handling()
        self._benchmark_cli_integration()
        
        # Generate comprehensive report
        return self._generate_report()
    
    def _benchmark_agent_selection(self):
        """Benchmark agent selection logic."""
        print("\n🎯 Benchmarking Agent Selection")
        
        test_cases = [
            ("npm init my-project", "NpmAgent"),
            ("npm create react-app", "NpmAgent"),
            ("yarn init", "NpmAgent"),
            ("git commit -m 'test'", "GitAgent"),
            ("git config user.name", "GitAgent"),
            ("docker run ubuntu", "DockerAgent"),
            ("docker build .", "DockerAgent"),
            ("pip install requests", "PythonAgent"),
            ("poetry init", "PythonAgent"),
            ("echo hello world", "GeneralAgent"),
            ("ls -la", "GeneralAgent"),
            ("unknown command", "GeneralAgent"),
        ]
        
        for command, expected_agent in test_cases:
            start_time = time.time()
            
            try:
                context = self.system.create_execution_context("benchmark test")
                agent = self.system.registry.find_agent(command, context)
                actual_agent = agent.name if agent else "None"
                
                execution_time = time.time() - start_time
                success = agent is not None
                
                result = BenchmarkResult(
                    test_name="agent_selection",
                    command=command,
                    expected_agent=expected_agent,
                    actual_agent=actual_agent,
                    execution_time=execution_time,
                    success=success
                )
                
                self.results.append(result)
                
                status = "✅" if result.agent_match else "❌"
                print(f"  {command:30} -> {actual_agent:15} {status} ({execution_time*1000:.1f}ms)")
                
            except Exception as e:
                result = BenchmarkResult(
                    test_name="agent_selection",
                    command=command,
                    expected_agent=expected_agent,
                    actual_agent="ERROR",
                    execution_time=time.time() - start_time,
                    success=False,
                    error_message=str(e)
                )
                self.results.append(result)
                print(f"  {command:30} -> ERROR: {e}")
    
    def _benchmark_command_execution(self):
        """Benchmark actual command execution."""
        print("\n⚡ Benchmarking Command Execution")
        
        # Safe commands for benchmarking
        test_commands = [
            ("echo 'Hello Benchmark'", "GeneralAgent"),
            ("pwd", "GeneralAgent"),
            ("date", "GeneralAgent"),
            ("ls /tmp", "GeneralAgent"),
            ("whoami", "GeneralAgent"),
        ]
        
        for command, expected_agent in test_commands:
            start_time = time.time()
            
            try:
                context = self.system.create_execution_context("benchmark execution")
                result = self.system.execute_command(command, context)
                
                execution_time = time.time() - start_time
                
                benchmark_result = BenchmarkResult(
                    test_name="command_execution",
                    command=command,
                    expected_agent=expected_agent,
                    actual_agent=result.agent_used or "Unknown",
                    execution_time=execution_time,
                    success=result.success,
                    interaction_count=len(result.interaction_log)
                )
                
                self.results.append(benchmark_result)
                
                status = "✅" if result.success else "❌"
                print(f"  {command:30} -> {status} ({execution_time*1000:.1f}ms)")
                
            except Exception as e:
                benchmark_result = BenchmarkResult(
                    test_name="command_execution",
                    command=command,
                    expected_agent=expected_agent,
                    actual_agent="ERROR",
                    execution_time=time.time() - start_time,
                    success=False,
                    error_message=str(e)
                )
                self.results.append(benchmark_result)
                print(f"  {command:30} -> ERROR: {e}")
    
    def _benchmark_specialized_agents(self):
        """Benchmark specialized agent responses."""
        print("\n🎯 Benchmarking Specialized Agents")
        
        test_cases = [
            ("npm init", "NpmAgent", "package name:", "Should return project name"),
            ("npm init", "NpmAgent", "version:", "Should return version"),
            ("npm init", "NpmAgent", "description:", "Should return description"),
            ("git commit", "GitAgent", "commit message:", "Should return commit message"),
            ("git config", "GitAgent", "user.name:", "Should return username"),
            ("docker run", "DockerAgent", "container name:", "Should return container name"),
            ("pip install", "PythonAgent", "package name:", "Should return package name"),
        ]
        
        for command, agent_name, test_prompt, description in test_cases:
            start_time = time.time()
            
            try:
                context = self.system.create_execution_context("benchmark specialized")
                agent = self.system.registry.find_agent(command, context)
                
                if agent and agent.name == agent_name:
                    response = agent.handle_prompt(test_prompt, command, context)
                    execution_time = time.time() - start_time
                    
                    # Check if response is reasonable
                    success = bool(response.strip()) and len(response.strip()) > 0
                    
                    benchmark_result = BenchmarkResult(
                        test_name="specialized_agents",
                        command=f"{command} -> {test_prompt}",
                        expected_agent=agent_name,
                        actual_agent=agent.name,
                        execution_time=execution_time,
                        success=success
                    )
                    
                    self.results.append(benchmark_result)
                    
                    status = "✅" if success else "❌"
                    print(f"  {agent_name:15} {test_prompt:20} -> '{response[:30]}...' {status}")
                    
                else:
                    print(f"  {agent_name:15} {test_prompt:20} -> Agent not found ❌")
                    
            except Exception as e:
                print(f"  {agent_name:15} {test_prompt:20} -> ERROR: {e} ❌")
    
    def _benchmark_performance(self):
        """Benchmark system performance."""
        print("\n⚡ Benchmarking Performance")
        
        # Test agent selection speed
        command = "npm init test"
        iterations = 1000
        
        times = []
        for _ in range(iterations):
            start_time = time.time()
            context = self.system.create_execution_context("perf test")
            agent = self.system.registry.find_agent(command, context)
            times.append(time.time() - start_time)
        
        avg_time = statistics.mean(times)
        median_time = statistics.median(times)
        p95_time = sorted(times)[int(0.95 * len(times))]
        
        print(f"  Agent selection ({iterations}x):")
        print(f"    Average: {avg_time*1000:.2f}ms")
        print(f"    Median:  {median_time*1000:.2f}ms")
        print(f"    P95:     {p95_time*1000:.2f}ms")
        
        # Test context creation speed
        times = []
        for _ in range(iterations):
            start_time = time.time()
            context = self.system.create_execution_context("perf test")
            times.append(time.time() - start_time)
        
        avg_time = statistics.mean(times)
        print(f"  Context creation ({iterations}x): {avg_time*1000:.2f}ms avg")
        
        # Record performance results
        benchmark_result = BenchmarkResult(
            test_name="performance",
            command=f"agent_selection_{iterations}x",
            expected_agent="N/A",
            actual_agent="N/A",
            execution_time=avg_time,
            success=avg_time < 0.001  # Should be under 1ms
        )
        self.results.append(benchmark_result)
    
    def _benchmark_error_handling(self):
        """Benchmark error handling and recovery."""
        print("\n🛡️ Benchmarking Error Handling")
        
        error_cases = [
            ("", "Empty command"),
            ("invalid; rm -rf /", "Dangerous command"),
            ("command with unicode 🚀", "Unicode command"),
            ("very " * 100 + "long command", "Very long command"),
        ]
        
        for command, description in error_cases:
            start_time = time.time()
            
            try:
                context = self.system.create_execution_context("error test")
                result = self.system.execute_command(command, context)
                execution_time = time.time() - start_time
                
                # Error handling is successful if it doesn't crash
                success = True
                
                benchmark_result = BenchmarkResult(
                    test_name="error_handling",
                    command=command[:50] + "..." if len(command) > 50 else command,
                    expected_agent="Any",
                    actual_agent=result.agent_used or "None",
                    execution_time=execution_time,
                    success=success
                )
                
                self.results.append(benchmark_result)
                print(f"  {description:30} -> ✅ Handled gracefully")
                
            except Exception as e:
                execution_time = time.time() - start_time
                
                benchmark_result = BenchmarkResult(
                    test_name="error_handling",
                    command=command[:50] + "..." if len(command) > 50 else command,
                    expected_agent="Any",
                    actual_agent="ERROR",
                    execution_time=execution_time,
                    success=False,
                    error_message=str(e)
                )
                
                self.results.append(benchmark_result)
                print(f"  {description:30} -> ❌ Error: {e}")
    
    def _benchmark_cli_integration(self):
        """Benchmark CLI integration."""
        print("\n🖥️ Benchmarking CLI Integration")
        
        cli_commands = [
            (["run", "echo", "CLI test"], "Basic run command"),
            (["--help"], "Help command"),
            (["config", "--show"], "Config command"),
        ]
        
        for cmd_args, description in cli_commands:
            start_time = time.time()
            
            try:
                cmd = ["uv", "run", "python", "-m", "momo_mom.cli"] + cmd_args
                result = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True, 
                    timeout=10,
                    cwd=Path(__file__).parent.parent
                )
                
                execution_time = time.time() - start_time
                success = result.returncode == 0
                
                benchmark_result = BenchmarkResult(
                    test_name="cli_integration",
                    command=" ".join(cmd_args),
                    expected_agent="CLI",
                    actual_agent="CLI",
                    execution_time=execution_time,
                    success=success,
                    error_message=result.stderr if not success else ""
                )
                
                self.results.append(benchmark_result)
                
                status = "✅" if success else "❌"
                print(f"  {description:30} -> {status} ({execution_time*1000:.1f}ms)")
                
            except Exception as e:
                execution_time = time.time() - start_time
                
                benchmark_result = BenchmarkResult(
                    test_name="cli_integration",
                    command=" ".join(cmd_args),
                    expected_agent="CLI",
                    actual_agent="ERROR",
                    execution_time=execution_time,
                    success=False,
                    error_message=str(e)
                )
                
                self.results.append(benchmark_result)
                print(f"  {description:30} -> ❌ Error: {e}")
    
    def _generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive benchmark report."""
        print("\n📊 Benchmark Report")
        print("=" * 60)
        
        # Calculate statistics
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r.success)
        agent_matches = sum(1 for r in self.results if r.agent_match and r.expected_agent != "N/A")
        total_matchable = sum(1 for r in self.results if r.expected_agent != "N/A")
        
        execution_times = [r.execution_time for r in self.results if r.execution_time > 0]
        avg_execution_time = statistics.mean(execution_times) if execution_times else 0
        median_execution_time = statistics.median(execution_times) if execution_times else 0
        
        # Group by test type
        test_types = {}
        for result in self.results:
            if result.test_name not in test_types:
                test_types[result.test_name] = []
            test_types[result.test_name].append(result)
        
        # Print summary
        success_rate = successful_tests / total_tests * 100 if total_tests > 0 else 0
        agent_match_rate = agent_matches / total_matchable * 100 if total_matchable > 0 else 0
        
        print(f"📈 Overall Results:")
        print(f"  Total Tests:        {total_tests}")
        print(f"  Successful:         {successful_tests} ({success_rate:.1f}%)")
        print(f"  Agent Matches:      {agent_matches}/{total_matchable} ({agent_match_rate:.1f}%)")
        print(f"  Avg Execution Time: {avg_execution_time*1000:.2f}ms")
        print(f"  Median Time:        {median_execution_time*1000:.2f}ms")
        
        print(f"\n📋 Test Type Breakdown:")
        for test_type, results in test_types.items():
            success_rate = sum(1 for r in results if r.success) / len(results) * 100
            avg_time = statistics.mean([r.execution_time for r in results])
            print(f"  {test_type:20} -> {len(results):3} tests, {success_rate:5.1f}% success, {avg_time*1000:6.1f}ms avg")
        
        # System info
        print(f"\n🔧 System Information:")
        print(f"  Total Agents:       {len(self.system.registry.get_all_agents())}")
        print(f"  Executing Agent:    {'✅' if self.system.registry.executing_agent else '❌'}")
        print(f"  Specialized Agents: {len(self.system.registry.specialized_agents)}")
        print(f"  General Agent:      {'✅' if self.system.registry.general_agent else '❌'}")
        
        # Performance grades
        print(f"\n🏆 Performance Grades:")
        if success_rate >= 95:
            print("  Overall:            A+ (Excellent)")
        elif success_rate >= 90:
            print("  Overall:            A  (Very Good)")
        elif success_rate >= 80:
            print("  Overall:            B  (Good)")
        elif success_rate >= 70:
            print("  Overall:            C  (Fair)")
        else:
            print("  Overall:            F  (Needs Work)")
        
        if avg_execution_time < 0.001:
            print("  Speed:              A+ (Very Fast)")
        elif avg_execution_time < 0.01:
            print("  Speed:              A  (Fast)")
        elif avg_execution_time < 0.1:
            print("  Speed:              B  (Good)")
        else:
            print("  Speed:              C  (Could be faster)")
        
        # Generate JSON report
        report = {
            'summary': {
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'success_rate': success_rate / 100,
                'agent_match_rate': agent_match_rate / 100,
                'average_execution_time': avg_execution_time,
                'median_execution_time': median_execution_time,
            },
            'test_types': {
                test_type: {
                    'count': len(results),
                    'success_rate': sum(1 for r in results if r.success) / len(results),
                    'avg_time': statistics.mean([r.execution_time for r in results]),
                    'median_time': statistics.median([r.execution_time for r in results]),
                }
                for test_type, results in test_types.items()
            },
            'system_info': {
                'total_agents': len(self.system.registry.get_all_agents()),
                'agent_names': [agent.name for agent in self.system.registry.get_all_agents()],
                'executing_agent_available': self.system.registry.executing_agent is not None,
                'specialized_agents_count': len(self.system.registry.specialized_agents),
                'general_agent_available': self.system.registry.general_agent is not None,
            },
            'detailed_results': [result.to_dict() for result in self.results],
            'timestamp': time.time(),
        }
        
        return report


def main():
    """Run the benchmark suite."""
    benchmark = MomBenchmarkSuite()
    report = benchmark.run_all_benchmarks()
    
    # Save report
    report_path = Path(__file__).parent / "benchmark_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: {report_path}")
    
    # Print final status
    success_rate = report['summary']['success_rate']
    if success_rate >= 0.95:
        print("🎉 EXCELLENT: System performing exceptionally well!")
    elif success_rate >= 0.9:
        print("✅ VERY GOOD: System performing very well!")
    elif success_rate >= 0.8:
        print("👍 GOOD: System performing well with minor issues")
    elif success_rate >= 0.7:
        print("⚠️  FAIR: System has some issues that need attention")
    else:
        print("❌ POOR: System needs significant improvements")


if __name__ == "__main__":
    main()
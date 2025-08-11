#!/usr/bin/env python3
"""
Testing and benchmark demonstration - shows scientific validation capabilities.

This script demonstrates comprehensive testing framework and performance
benchmarking for workflow validation and optimization.
"""

import json
import time
from pathlib import Path
from momo_workflow import (
    WorkflowEngine,
    run_workflow_test_suite,
    create_failure_test_scenario,
    create_performance_test_scenario,
)
from momo_workflow.testing import (
    WorkflowTestFixture,
    WorkflowTestCase,
    TestWorkflowStep,
)


def demonstrate_test_framework():
    """Show workflow testing framework capabilities."""
    print("🧪 Workflow Testing Framework")
    print("-" * 40)

    # Create test fixture
    fixture = WorkflowTestFixture()
    test_case = WorkflowTestCase(fixture)

    print("📋 Creating test scenarios...")

    # Test 1: Successful workflow
    print("\n1. Testing successful workflow execution:")
    workflow, context = create_performance_test_scenario(5, 0.05)

    engine = WorkflowEngine()
    result = engine.execute_workflow(workflow, context)

    try:
        test_case.assert_workflow_success(result)
        print("  ✅ Success test PASSED")
    except AssertionError as e:
        print(f"  ❌ Success test FAILED: {e}")

    # Test 2: Workflow failure handling
    print("\n2. Testing workflow failure handling:")
    workflow, context = create_failure_test_scenario(2, 5, False)
    result = engine.execute_workflow(workflow, context, rollback_on_failure=False)

    try:
        test_case.assert_workflow_failure(result, "step_3")
        print("  ✅ Failure test PASSED")
    except AssertionError as e:
        print(f"  ❌ Failure test FAILED: {e}")

    # Test 3: Performance bounds
    print("\n3. Testing performance bounds:")
    workflow, context = create_performance_test_scenario(3, 0.01)
    result = engine.execute_workflow(workflow, context)

    try:
        test_case.assert_performance_bounds(result, max_duration=1.0)
        print("  ✅ Performance test PASSED")
    except AssertionError as e:
        print(f"  ❌ Performance test FAILED: {e}")

    fixture.cleanup()
    print("\n✨ Test framework demonstration completed")


def demonstrate_custom_test_scenario():
    """Create and run custom test scenario."""
    print("\n🎯 Custom Test Scenario")
    print("-" * 40)

    # Create custom test steps with specific behaviors
    steps = [
        TestWorkflowStep("init_step", "Initialize test", execution_time=0.1),
        TestWorkflowStep(
            "file_creation",
            "Create test files",
            execution_time=0.2,
            artifacts=["test1.txt", "test2.txt"],
        ),
        TestWorkflowStep(
            "processing_step",
            "Process data",
            execution_time=0.3,
            should_fail=False,  # Change to True to test failure scenarios
        ),
        TestWorkflowStep("cleanup_step", "Clean up resources", execution_time=0.1),
    ]

    fixture = WorkflowTestFixture()
    workflow = fixture.create_simple_workflow(
        steps, workflow_id="custom_test", test_parameter="custom_value"
    )
    context = fixture.create_test_context()

    print(f"📋 Executing custom workflow with {len(steps)} steps")

    engine = WorkflowEngine()
    result = engine.execute_workflow(workflow, context)

    print(f"\n📊 Custom Test Results:")
    print(f"Status: {result.status.value}")
    print(f"Success Rate: {result.success_rate:.2%}")
    print(f"Duration: {result.total_duration:.3f}s")
    print(f"Artifacts: {len(result.artifacts_produced)}")

    # Verify test step states
    print(f"\n🔍 Step Execution Verification:")
    for i, step in enumerate(steps):
        if hasattr(step, "executed"):
            execution_status = "✅ Executed" if step.executed else "⏸️  Not executed"
            rollback_status = (
                "🔄 Rolled back" if getattr(step, "rolled_back", False) else ""
            )
            print(f"  {i + 1}. {step.step_id}: {execution_status} {rollback_status}")

    fixture.cleanup()


def run_comprehensive_test_suite():
    """Run the complete workflow test suite."""
    print("\n🏃 Comprehensive Test Suite")
    print("-" * 40)

    engine = WorkflowEngine()

    print("Running comprehensive test suite...")
    test_results = run_workflow_test_suite(engine)

    print(f"\n📈 Test Suite Results:")
    print(f"Total Tests: {test_results['test_count']}")
    print(f"Passed: {test_results['passed']}")
    print(f"Failed: {test_results['failed']}")
    print(f"Success Rate: {test_results['passed'] / test_results['test_count']:.2%}")

    print(f"\n📋 Individual Test Results:")
    for test_result in test_results["test_results"]:
        status_emoji = "✅" if test_result["status"] == "PASSED" else "❌"
        print(f"  {status_emoji} {test_result['name']}: {test_result['status']}")
        if "error" in test_result:
            print(f"     Error: {test_result['error']}")


def run_performance_benchmarks():
    """Run performance benchmarks."""
    print("\n🚀 Performance Benchmarking")
    print("-" * 40)

    # Import benchmark suite
    try:
        from momo_workflow.benchmarks.performance_benchmarks import (
            WorkflowBenchmarkSuite,
        )

        print("Initializing benchmark suite...")
        benchmark_output = Path("benchmark_output")
        suite = WorkflowBenchmarkSuite(benchmark_output)

        print("⚡ Running performance benchmarks (this may take a moment)...")
        results = suite.run_full_benchmark_suite()

        print("\n📊 Benchmark Summary:")
        summary = results.get("summary", {})
        print(f"Total Benchmarks: {summary.get('total_benchmarks', 0)}")
        print(f"Successful: {summary.get('successful_benchmarks', 0)}")
        print(f"Failed: {summary.get('failed_benchmarks', 0)}")

        if "performance_highlights" in summary:
            highlights = summary["performance_highlights"]
            print(f"\n🏆 Performance Highlights:")

            if "execution_category" in highlights:
                print(f"  Execution Performance: {highlights['execution_category']}")

            if "mean_throughput_steps_per_sec" in highlights:
                throughput = highlights["mean_throughput_steps_per_sec"]
                print(f"  Mean Throughput: {throughput:.2f} steps/second")

        # Show benchmark file locations
        print(f"\n📄 Detailed results saved to:")
        print(f"  📁 {benchmark_output}")

        latest_file = benchmark_output / "latest_benchmark.json"
        if latest_file.exists():
            print(f"  📄 Latest results: {latest_file}")

    except ImportError as e:
        print(f"❌ Benchmark suite not available: {e}")
    except Exception as e:
        print(f"❌ Benchmark execution failed: {e}")


def demonstrate_rollback_testing():
    """Demonstrate rollback functionality testing."""
    print("\n🔄 Rollback Testing")
    print("-" * 40)

    # Create workflow with rollback-enabled steps
    rollback_steps = []

    def create_rollback_action(step_name):
        def rollback_action(context, result):
            print(f"🔄 Custom rollback executed for {step_name}")

        return rollback_action

    for i in range(3):
        step = TestWorkflowStep(
            f"rollback_step_{i + 1}",
            f"Rollback test step {i + 1}",
            execution_time=0.1,
            reversible=True,
            artifacts=[f"rollback_artifact_{i + 1}.txt"],
            rollback_action=create_rollback_action(f"step_{i + 1}"),
        )
        rollback_steps.append(step)

    # Add failing step to trigger rollback
    rollback_steps.append(
        TestWorkflowStep(
            "failing_step", "Step that fails to trigger rollback", should_fail=True
        )
    )

    fixture = WorkflowTestFixture()
    workflow = fixture.create_simple_workflow(rollback_steps, "rollback_test")
    context = fixture.create_test_context()

    print("📋 Executing workflow with rollback scenario...")

    engine = WorkflowEngine()
    result = engine.execute_workflow(workflow, context, rollback_on_failure=True)

    print(f"\n📊 Rollback Test Results:")
    print(f"Status: {result.status.value}")
    print(f"Rollback Points: {result.rollback_points}")
    print(f"Steps Rolled Back: {len(result.rollback_points)}")

    # Check which steps were rolled back
    print(f"\n🔍 Rollback Verification:")
    for i, step in enumerate(rollback_steps[:-1]):  # Exclude failing step
        rollback_status = (
            "🔄 Rolled back"
            if getattr(step, "rolled_back", False)
            else "⏸️  Not rolled back"
        )
        print(f"  {i + 1}. {step.step_id}: {rollback_status}")

    fixture.cleanup()


def main():
    """Run testing and benchmark demonstrations."""
    print("🔬 Workflow Testing & Benchmarking Demonstration")
    print("=" * 50)

    # Run different demonstration modules
    demonstrate_test_framework()
    demonstrate_custom_test_scenario()
    run_comprehensive_test_suite()
    demonstrate_rollback_testing()
    run_performance_benchmarks()

    print("\n🎉 All testing and benchmarking demonstrations completed!")
    print("\nNext steps:")
    print("• Review detailed benchmark results in 'benchmark_output/' directory")
    print("• Use test framework for validating custom workflows")
    print("• Implement custom test scenarios for specific use cases")


if __name__ == "__main__":
    main()

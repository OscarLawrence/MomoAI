"""
ADR workflow for logging system standardization using momo-agent framework.

This demonstrates the momo-agent framework by executing a structured ADR workflow
for analyzing and improving the logging system across the MomoAI codebase.
"""

import asyncio
import json
import time
from pathlib import Path

from momo_agent import (
    AgentExecutionContext,
    AgentWorkflowEngine,
    BaseAgentTask,
    BaseAgentWorkflow,
    AgentTaskType,
    TaskPriority,
)
from momo_workflow.types import StepStatus


class ADRAnalysisTask(BaseAgentTask):
    """Task for conducting structured analysis for ADR creation."""

    def __init__(self, task_id: str, analysis_type: str, focus_area: str):
        super().__init__(
            task_id=task_id,
            description=f"Conduct {analysis_type} analysis for {focus_area}",
            task_type=AgentTaskType.COMPLEX,
            priority=TaskPriority.HIGH,
            estimated_duration=30.0,
            is_reversible=True,
        )
        self._analysis_type = analysis_type
        self._focus_area = focus_area

    async def execute(self, context):
        """Execute structured analysis task."""
        start_time = time.time()

        # Simulate comprehensive analysis work
        print(f"🔍 Conducting {self._analysis_type} analysis for {self._focus_area}...")
        await asyncio.sleep(0.5)  # Simulate analysis time

        # Generate structured findings
        findings = self._generate_findings()

        return self._create_result(
            status=StepStatus.SUCCESS,
            start_time=start_time,
            outputs={
                "analysis_type": self._analysis_type,
                "focus_area": self._focus_area,
                "findings": findings,
                "confidence": "high",
            },
            rollback_data={
                "analysis_artifacts": [f"{self.metadata.task_id}_analysis.json"],
            },
        )

    def _generate_findings(self):
        """Generate structured findings based on the comprehensive analysis."""
        if self._analysis_type == "current_state":
            return {
                "momo_logger_strengths": [
                    "Excellent protocol-based architecture",
                    "Comprehensive async support",
                    "AI-optimized logging levels",
                    "Rich structured metadata support",
                    "Performance-optimized implementation",
                ],
                "adoption_status": {
                    "using_momo_logger": [
                        "momo-store-document",
                        "momo-vector-store",
                        "momo-graph-store",
                    ],
                    "using_standard_logging": [
                        "momo-agent",
                        "momo-workflow",
                        "momo-mom",
                    ],
                    "using_print_statements": ["momo-graph", "various scripts"],
                },
                "integration_quality": "inconsistent_across_modules",
            }
        elif self._analysis_type == "gap":
            return {
                "missing_integrations": [
                    "momo-agent lacks momo-logger dependency",
                    "momo-workflow should use scientific workflow tracking",
                    "momo-mom needs agent communication logging",
                    "momo-graph has no structured logging",
                ],
                "pattern_inconsistencies": [
                    "Mixed logging approaches across modules",
                    "No standardized agent identification",
                    "Inconsistent user-facing vs system logging",
                    "No trace correlation between agent workflows",
                ],
                "architecture_gaps": [
                    "No unified logging configuration",
                    "Missing agent-aware logging middleware",
                    "No centralized log aggregation strategy",
                    "Missing structured log analysis tools",
                ],
            }
        elif self._analysis_type == "solution":
            return {
                "integration_strategy": {
                    "phase_1": "Core agent modules (momo-agent, momo-workflow, momo-mom)",
                    "phase_2": "Graph modules with print statement replacement",
                    "phase_3": "Advanced features (trace correlation, analysis tools)",
                },
                "technical_approach": [
                    "Add momo-logger dependencies to core modules",
                    "Create standardized agent context patterns",
                    "Implement trace correlation infrastructure",
                    "Develop migration guides and tooling",
                ],
                "success_metrics": [
                    "100% structured logging adoption across modules",
                    "Consistent agent identification patterns",
                    "Sub-millisecond logging overhead",
                    "Complete trace correlation for workflows",
                ],
            }

        return {"analysis_type": self._analysis_type, "completed": True}

    async def rollback(self, context, result):
        """Clean up analysis artifacts if needed."""
        print(f"🔄 Rolling back analysis: {self._analysis_type}")


class ADRDocumentationTask(BaseAgentTask):
    """Task for creating structured ADR documentation."""

    def __init__(self, task_id: str, document_type: str):
        super().__init__(
            task_id=task_id,
            description=f"Create {document_type} ADR documentation",
            task_type=AgentTaskType.MULTI_STEP,
            priority=TaskPriority.HIGH,
            estimated_duration=15.0,
        )
        self._document_type = document_type

    async def execute(self, context):
        """Create structured ADR documentation."""
        start_time = time.time()

        print(f"📝 Creating {self._document_type} ADR documentation...")
        await asyncio.sleep(0.3)

        # Extract findings from context shared state
        all_findings = {}
        for task_id, findings in context.shared_state.items():
            if "findings" in findings:
                all_findings[task_id] = findings["findings"]

        # Create ADR structure
        adr_content = self._create_adr_content(all_findings)

        return self._create_result(
            status=StepStatus.SUCCESS,
            start_time=start_time,
            outputs={
                "document_type": self._document_type,
                "adr_content": adr_content,
                "word_count": len(str(adr_content).split()),
            },
        )

    def _create_adr_content(self, findings):
        """Create comprehensive ADR content structure."""
        return {
            "adr_id": "008",
            "title": "Standardize Logging Architecture Across MomoAI Codebase",
            "status": "DRAFT",
            "problem_statement": self._create_problem_statement(findings),
            "research_summary": self._create_research_summary(findings),
            "decision": self._create_decision(findings),
            "implementation_strategy": self._create_implementation_strategy(findings),
            "success_metrics": self._create_success_metrics(findings),
            "created": time.time(),
        }

    def _create_problem_statement(self, findings):
        return {
            "challenge": "Inconsistent logging approaches across MomoAI modules prevent effective debugging, monitoring, and agent workflow analysis",
            "core_issues": [
                "Fragmented logging implementations using different approaches (momo-logger, standard logging, print statements)",
                "Missing agent context and trace correlation in multi-agent workflows",
                "No standardized approach for AI-optimized logging levels and structured metadata",
                "Inconsistent error handling and user-facing message patterns",
            ],
            "impact": "Reduced observability, difficult debugging, missed optimization opportunities",
        }

    def _create_research_summary(self, findings):
        return {
            "current_state_analysis": findings.get("current_state_analysis", {}),
            "gap_analysis": findings.get("gap_analysis", {}),
            "momo_logger_capabilities": [
                "Protocol-based async architecture",
                "AI-optimized logging levels (AI_SYSTEM, AI_USER, AI_AGENT)",
                "Rich structured metadata with agent context",
                "High-performance implementation with caching",
                "Comprehensive test coverage and benchmarking",
            ],
        }

    def _create_decision(self, findings):
        return {
            "decision": "Standardize all MomoAI modules to use momo-logger with consistent agent-aware patterns",
            "rationale": [
                "Leverage existing high-quality momo-logger infrastructure",
                "Enable comprehensive agent workflow observability",
                "Provide consistent debugging and monitoring capabilities",
                "Support AI-optimized logging for better agent interaction analysis",
            ],
        }

    def _create_implementation_strategy(self, findings):
        solution_findings = findings.get("solution_analysis", {})
        return solution_findings.get(
            "integration_strategy",
            {
                "phase_1": "Core modules integration",
                "phase_2": "Print statement replacement",
                "phase_3": "Advanced observability features",
            },
        )

    def _create_success_metrics(self, findings):
        solution_findings = findings.get("solution_analysis", {})
        return solution_findings.get(
            "success_metrics",
            [
                "Complete logging standardization",
                "Agent workflow observability",
                "Performance optimization",
            ],
        )


async def execute_adr_logging_workflow():
    """Execute the complete ADR workflow for logging system standardization."""

    # Create structured analysis tasks
    tasks = [
        ADRAnalysisTask(
            "current_state_analysis", "current_state", "momo-logger adoption"
        ),
        ADRAnalysisTask("gap_analysis", "gap", "logging inconsistencies"),
        ADRAnalysisTask("solution_analysis", "solution", "standardization strategy"),
        ADRDocumentationTask("adr_documentation", "comprehensive"),
    ]

    # Create workflow
    workflow = BaseAgentWorkflow(
        workflow_id="adr-008-logging-standardization",
        name="ADR-008: Logging System Standardization Analysis",
        tasks=tasks,
    )

    # Create execution context with shared state for findings
    context = AgentExecutionContext(
        session_id="adr-logging-analysis",
        current_task="logging_standardization_adr",
        working_directory=Path.cwd(),
        shared_state={},
    )

    # Execute workflow with scientific measurement
    engine = AgentWorkflowEngine()

    print("🚀 Executing ADR-008 Logging Standardization Workflow")
    print("=" * 60)

    result = await engine.execute_workflow(workflow, context, rollback_on_failure=True)

    # Display results
    print(f"\n📊 Workflow Results:")
    print(f"Status: {result.status}")
    print(f"Duration: {result.overall_metrics.duration_seconds:.2f}s")
    print(f"Tasks completed: {result.completed_tasks}/{result.total_tasks}")

    # Extract and display ADR content
    adr_task_result = None
    for task_result in result.task_results:
        if task_result.task_id == "adr_documentation":
            adr_task_result = task_result
            break

    if adr_task_result and adr_task_result.success:
        adr_content = adr_task_result.outputs["adr_content"]

        print(f"\n📄 Generated ADR-008 Structure:")
        print(f"Title: {adr_content['title']}")
        print(f"Status: {adr_content['status']}")
        print(f"Word Count: {adr_task_result.outputs['word_count']}")

        # Save ADR content to file
        adr_file = Path("adr-008-logging-standardization.json")
        with open(adr_file, "w") as f:
            json.dump(adr_content, f, indent=2, default=str)

        print(f"💾 ADR content saved to: {adr_file}")

        # Store findings for analysis collection
        context.shared_state["final_adr"] = adr_content

    # Display workflow performance metrics
    print(f"\n⚡ Performance Metrics:")
    for task_result in result.task_results:
        duration = task_result.metrics.duration_seconds
        print(f"  {task_result.task_id}: {duration:.2f}s")

    # Engine statistics
    engine_stats = engine.get_execution_summary()
    print(f"\n🔧 Engine Statistics:")
    print(f"  Total executions: {engine_stats['total_executions']}")
    print(
        f"  Success rate: {engine_stats['successful_tasks']}/{engine_stats['total_executions']}"
    )
    print(f"  Average duration: {engine_stats['average_duration']:.2f}s")

    return result


if __name__ == "__main__":
    # Execute ADR workflow using momo-agent framework
    result = asyncio.run(execute_adr_logging_workflow())

    print(f"\n✅ ADR-008 Logging Standardization Workflow Complete!")
    print(
        f"Framework successfully demonstrated structured ADR analysis and documentation."
    )

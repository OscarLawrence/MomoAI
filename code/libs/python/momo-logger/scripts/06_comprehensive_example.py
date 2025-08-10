#!/usr/bin/env python3
"""
Comprehensive Example - All Features Working Together

This example demonstrates a realistic usage scenario for momo-logger
in a multi-agent AI system, showing all features working together.
"""

import asyncio
import tempfile
import os
from momo_logger import get_logger, LogLevel


class MomoAgent:
    """A simple mock agent to demonstrate logging in a multi-agent system."""

    def __init__(self, agent_name, agent_role):
        self.agent_name = agent_name
        self.agent_role = agent_role
        self.logger = get_logger(f"agent.{agent_name}", level=LogLevel.DEBUG)

    async def process_task(self, task_id, task_data):
        """Process a task with comprehensive logging."""
        async with self.logger.context(agent=self.agent_name, task_id=task_id):
            await self.logger.ai_system(
                f"Agent {self.agent_name} starting task {task_id}"
            )

            # Log based on agent role
            if self.agent_role == "developer":
                await self.logger.developer(
                    "Processing development task",
                    task_type=task_data.get("type"),
                    complexity=task_data.get("complexity"),
                )
            elif self.agent_role == "tester":
                await self.logger.tester(
                    "Processing test task",
                    test_suite=task_data.get("suite"),
                    test_cases=task_data.get("cases", 0),
                )
            elif self.agent_role == "architect":
                await self.logger.architect(
                    "Processing architecture task",
                    component=task_data.get("component"),
                    impact=task_data.get("impact"),
                )

            # Simulate work
            await asyncio.sleep(0.1)  # Simulate async work

            # Log progress
            await self.logger.debug(
                "Task processing in progress", progress=50, estimated_time=0.5
            )

            # Simulate more work
            await asyncio.sleep(0.1)

            # Log completion
            await self.logger.info(
                "Task completed successfully", duration=0.2, result="success"
            )

            await self.logger.ai_user(f"Task {task_id} completed successfully")

            return {"status": "success", "task_id": task_id}

    async def communicate_with_agent(self, target_agent, message):
        """Simulate communication between agents."""
        await self.logger.ai_agent(
            f"Sending message to {target_agent}",
            target_agent=target_agent,
            message_content=message,
        )

        # Simulate receiving response
        await asyncio.sleep(0.05)

        await self.logger.ai_agent(
            f"Received response from {target_agent}",
            source_agent=target_agent,
            response_status="acknowledged",
        )


async def main():
    print("🤖 Momo Logger - Comprehensive Multi-Agent Example")
    print("=" * 60)

    # Create system logger
    system_logger = get_logger("system.main", level=LogLevel.INFO)

    # Global context for the entire system
    async with system_logger.context(system="momo-logger-demo", version="1.0"):
        await system_logger.info("System starting up")

        # Create agents
        developer_agent = MomoAgent("CodeDeveloper", "developer")
        tester_agent = MomoAgent("QualityTester", "tester")
        architect_agent = MomoAgent("SystemArchitect", "architect")

        await system_logger.info(
            "Agents initialized",
            agents=["CodeDeveloper", "QualityTester", "SystemArchitect"],
        )

        # Process tasks
        print("\n📋 Processing Tasks:")
        print("-" * 30)

        # Developer task
        dev_task = {
            "type": "feature_implementation",
            "complexity": "medium",
            "requirements": ["logging", "context", "formatters"],
        }
        await developer_agent.process_task("DEV-001", dev_task)

        # Tester task
        test_task = {"suite": "logger_tests", "cases": 15, "priority": "high"}
        await tester_agent.process_task("TEST-001", test_task)

        # Architect task
        arch_task = {
            "component": "logging_system",
            "impact": "system_wide",
            "dependencies": ["pydantic", "asyncio"],
        }
        await architect_agent.process_task("ARCH-001", arch_task)

        # Agent communication
        print("\n💬 Agent Communication:")
        print("-" * 30)
        await developer_agent.communicate_with_agent(
            "QualityTester", "Feature implementation complete, ready for testing"
        )
        await tester_agent.communicate_with_agent(
            "CodeDeveloper", "Testing completed, all tests passed"
        )
        await architect_agent.communicate_with_agent(
            "SystemArchitect", "Architecture review complete"
        )

        # System operations with different backends
        print("\n📂 Backend Operations:")
        print("-" * 30)

        # File logging for audit trail
        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as tmp_file:
            audit_log_file = tmp_file.name

        try:
            audit_logger = get_logger(
                "system.audit",
                level=LogLevel.INFO,
                backend="file",
                filepath=audit_log_file,
                formatter="json",
            )

            await audit_logger.info(
                "System audit record",
                operation="task_processing",
                tasks_completed=3,
                agents_involved=3,
            )

            await audit_logger.flush()
            await audit_logger.close()

            # Show audit log
            print("Audit log contents:")
            with open(audit_log_file, "r") as f:
                print(f.read())

        finally:
            if os.path.exists(audit_log_file):
                os.unlink(audit_log_file)

        await system_logger.info(
            "System shutting down", tasks_processed=3, agents_active=3
        )

    print("\n🎉 Comprehensive multi-agent example completed!")


if __name__ == "__main__":
    asyncio.run(main())

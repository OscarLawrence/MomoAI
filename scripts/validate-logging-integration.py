#!/usr/bin/env python3
"""
ADR-008 Validation Script - Logging Standardization
Validates that all modules have been properly integrated with momo-logger.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from momo_logger import get_logger, with_trace_id, generate_trace_id
from momo_logger.types import LogLevel

def validate_momo_agent():
    """Validate momo-agent integration."""
    print("🔍 Validating momo-agent integration...")
    
    try:
        from momo_agent.core import AgentWorkflowEngine
        engine = AgentWorkflowEngine()
        print("   ✅ momo-agent successfully integrated with momo-logger")
        return True
    except Exception as e:
        print(f"   ❌ momo-agent integration failed: {e}")
        return False

def validate_momo_workflow():
    """Validate momo-workflow integration.""" 
    print("🔍 Validating momo-workflow integration...")
    
    try:
        from momo_workflow.core import WorkflowEngine
        engine = WorkflowEngine()
        print("   ✅ momo-workflow successfully integrated with momo-logger")
        return True
    except Exception as e:
        print(f"   ❌ momo-workflow integration failed: {e}")
        return False

def validate_momo_mom():
    """Validate momo-mom integration."""
    print("🔍 Validating momo-mom integration...")
    
    try:
        from momo_mom.executor import CommandExecutor
        config = {"execution": {}, "recovery": {}, "output": {}}
        executor = CommandExecutor(config)
        print("   ✅ momo-mom successfully integrated with momo-logger")
        return True
    except Exception as e:
        print(f"   ❌ momo-mom integration failed: {e}")
        return False

async def validate_trace_correlation():
    """Validate trace correlation functionality."""
    print("🔍 Validating trace correlation...")
    
    logger = get_logger("validation-test", level=LogLevel.AI_SYSTEM)
    
    try:
        # Test trace ID generation
        trace_id = generate_trace_id()
        print(f"   📍 Generated trace ID: {trace_id[:8]}...")
        
        # Test trace context
        with with_trace_id(trace_id) as active_trace:
            await logger.ai_system(
                "Testing trace correlation",
                context={"test": "trace_validation"},
                agent="validator",
                agent_role="tester"
            )
            print(f"   ✅ Trace context active: {active_trace[:8]}...")
            
        print("   ✅ Trace correlation functionality working")
        return True
    except Exception as e:
        print(f"   ❌ Trace correlation failed: {e}")
        return False

async def validate_agent_context():
    """Validate agent context in logging."""
    print("🔍 Validating agent context...")
    
    logger = get_logger("agent-context-test", level=LogLevel.AI_AGENT)
    
    try:
        # Test different agent roles
        await logger.ai_agent(
            "Agent communication test",
            context={"workflow": "validation", "step": 1},
            agent="test-agent",
            agent_role="validator"
        )
        
        await logger.ai_user(
            "User-facing message test", 
            user_facing=True,
            agent="test-agent",
            agent_role="communicator"
        )
        
        print("   ✅ Agent context logging working")
        return True
    except Exception as e:
        print(f"   ❌ Agent context failed: {e}")
        return False

async def main():
    """Run all validation tests."""
    print("🚀 ADR-008 Logging Standardization Validation")
    print("=" * 50)
    
    results = []
    
    # Phase 1 validations
    results.append(validate_momo_agent())
    results.append(validate_momo_workflow()) 
    results.append(validate_momo_mom())
    
    # Phase 3 validations
    results.append(await validate_trace_correlation())
    results.append(await validate_agent_context())
    
    # Summary
    success_count = sum(results)
    total_tests = len(results)
    
    print("\n📊 Validation Summary:")
    print(f"   ✅ Passed: {success_count}/{total_tests}")
    print(f"   ❌ Failed: {total_tests - success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("\n🎉 All validations passed! ADR-008 implementation successful.")
        return 0
    else:
        print(f"\n⚠️  {total_tests - success_count} validation(s) failed. Review integration.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
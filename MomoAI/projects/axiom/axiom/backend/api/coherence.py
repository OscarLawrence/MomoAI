"""
Coherence Validation API Endpoints
RESTful interface for coherence validation operations
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any

from core.session_manager import SessionManager
from core.input_validator import UserInputValidator, CoherenceResult
from core.output_validator import AIOutputValidator, ValidationResult
from core.contracts import coherence_contract, ComplexityClass

router = APIRouter(prefix="/coherence", tags=["coherence"])

# Dependency to get session manager
def get_session_manager() -> SessionManager:
    from ..main import session_manager
    return session_manager

def get_input_validator() -> UserInputValidator:
    return UserInputValidator()

def get_output_validator() -> AIOutputValidator:
    return AIOutputValidator()


class InputValidationRequest(BaseModel):
    """Request model for input validation"""
    content: str


class InputValidationResponse(BaseModel):
    """Response model for input validation"""
    level: str
    score: float
    contradictions: List[str]
    suggestions: List[str]
    confidence: float


class OutputValidationRequest(BaseModel):
    """Request model for output validation"""
    content: str


class OutputValidationResponse(BaseModel):
    """Response model for output validation"""
    has_contracts: bool
    contracts_valid: bool
    contracts_verified: bool
    violations: List[str]
    suggestions: List[str]
    confidence: float


class CoherenceSettingsRequest(BaseModel):
    """Request model for coherence settings"""
    enabled: bool = True
    level: str = "standard"  # permissive, standard, strict


class CoherenceSettingsResponse(BaseModel):
    """Response model for coherence settings"""
    enabled: bool
    level: str


@router.post("/validate-input", response_model=InputValidationResponse)
@coherence_contract(
    input_types={"request": "InputValidationRequest"},
    output_type="InputValidationResponse",
    requires=["len(request.content.strip()) > 0"],
    complexity_time=ComplexityClass.LINEAR,
    pure=True
)
async def validate_input(
    request: InputValidationRequest,
    validator: UserInputValidator = Depends(get_input_validator)
) -> InputValidationResponse:
    """
    Validate user input for logical coherence
    Returns coherence level, contradictions, and suggestions
    """
    try:
        result = validator.validate_prompt(request.content)
        
        return InputValidationResponse(
            level=result.level.name,
            score=result.score,
            contradictions=result.contradictions,
            suggestions=result.suggestions or [],
            confidence=result.confidence
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error validating input: {str(e)}"
        )


@router.post("/validate-output", response_model=OutputValidationResponse)
@coherence_contract(
    input_types={"request": "OutputValidationRequest"},
    output_type="OutputValidationResponse",
    requires=["len(request.content.strip()) > 0"],
    complexity_time=ComplexityClass.LINEAR,
    pure=True
)
async def validate_output(
    request: OutputValidationRequest,
    validator: AIOutputValidator = Depends(get_output_validator)
) -> OutputValidationResponse:
    """
    Validate AI output for formal contracts and correctness
    Returns contract validation status and violations
    """
    try:
        result = validator.validate_response(request.content)
        
        return OutputValidationResponse(
            has_contracts=result.has_contracts,
            contracts_valid=result.contracts_valid,
            contracts_verified=result.contracts_verified,
            violations=result.violations,
            suggestions=result.suggestions,
            confidence=result.confidence
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error validating output: {str(e)}"
        )


@router.get("/session/{session_id}/settings", response_model=CoherenceSettingsResponse)
@coherence_contract(
    input_types={"session_id": "str"},
    output_type="CoherenceSettingsResponse",
    requires=["len(session_id.strip()) > 0"],
    complexity_time=ComplexityClass.CONSTANT,
    pure=True
)
async def get_coherence_settings(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
) -> CoherenceSettingsResponse:
    """Get coherence validation settings for session"""
    session = session_manager.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return CoherenceSettingsResponse(
        enabled=session.coherence_enabled,
        level=session.coherence_level
    )


@router.put("/session/{session_id}/settings")
@coherence_contract(
    input_types={"session_id": "str", "settings": "CoherenceSettingsRequest"},
    requires=["len(session_id.strip()) > 0"],
    complexity_time=ComplexityClass.CONSTANT,
    pure=False,
    modifies=["session.coherence_enabled", "session.coherence_level"]
)
async def update_coherence_settings(
    session_id: str,
    settings: CoherenceSettingsRequest,
    session_manager: SessionManager = Depends(get_session_manager)
) -> CoherenceSettingsResponse:
    """Update coherence validation settings for session"""
    session = session_manager.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Validate coherence level
    valid_levels = ["permissive", "standard", "strict"]
    if settings.level not in valid_levels:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid coherence level. Must be one of: {valid_levels}"
        )
    
    # Update settings
    await session_manager.update_coherence_settings(session_id, {
        "enabled": settings.enabled,
        "level": settings.level
    })
    
    return CoherenceSettingsResponse(
        enabled=settings.enabled,
        level=settings.level
    )


@router.get("/health")
@coherence_contract(
    output_type="Dict[str, str]",
    complexity_time=ComplexityClass.CONSTANT,
    pure=True
)
async def coherence_health_check() -> Dict[str, str]:
    """Health check for coherence validation system"""
    return {
        "status": "healthy",
        "input_validator": "ready",
        "output_validator": "ready",
        "version": "1.0.0"
    }
"""
Risk Management Component - Portfolio Protection
Collaboration-first: Protects both individual and systemic market stability.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum
import math


class RiskLevel(Enum):
    """Risk levels optimized for collaborative market participation."""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate" 
    AGGRESSIVE = "aggressive"
    COLLABORATIVE = "collaborative"  # Balances profit with market stability


@dataclass
class PositionSizer:
    """
    Position sizing with collaboration-first principles.
    Prevents excessive concentration that could destabilize markets.
    """
    max_position_size: float  # % of portfolio
    max_sector_exposure: float  # % of portfolio per sector
    max_correlation_exposure: float  # % in correlated assets
    volatility_adjustment: bool = True
    

class RiskManager:
    """
    Risk management engine with collaboration-first design.
    Optimizes for sustainable returns while protecting market ecosystem.
    """
    
    def __init__(self, 
                 portfolio_value: float,
                 risk_level: RiskLevel = RiskLevel.COLLABORATIVE):
        """Initialize with collaboration-optimized defaults."""
        self.portfolio_value = portfolio_value
        self.risk_level = risk_level
        
        # Collaboration-first risk parameters
        self.risk_params = self._get_risk_parameters()
        self.max_daily_loss = self.portfolio_value * self.risk_params['max_daily_loss_pct']
        self.max_drawdown = self.portfolio_value * self.risk_params['max_drawdown_pct']
        
        # Track current exposure
        self.current_positions: Dict[str, float] = {}
        self.sector_exposure: Dict[str, float] = {}
        self.daily_pnl = 0.0
        self.peak_value = portfolio_value
        
    def _get_risk_parameters(self) -> Dict[str, float]:
        """Get risk parameters based on collaboration-first principles."""
        params = {
            RiskLevel.CONSERVATIVE: {
                'max_position_size': 0.05,      # 5% max per position
                'max_sector_exposure': 0.20,    # 20% max per sector
                'max_daily_loss_pct': 0.01,     # 1% daily loss limit
                'max_drawdown_pct': 0.05,       # 5% drawdown limit
                'volatility_multiplier': 0.5,   # Reduce size in volatile markets
            },
            RiskLevel.MODERATE: {
                'max_position_size': 0.08,
                'max_sector_exposure': 0.30,
                'max_daily_loss_pct': 0.02,
                'max_drawdown_pct': 0.10,
                'volatility_multiplier': 0.75,
            },
            RiskLevel.AGGRESSIVE: {
                'max_position_size': 0.12,
                'max_sector_exposure': 0.40,
                'max_daily_loss_pct': 0.03,
                'max_drawdown_pct': 0.15,
                'volatility_multiplier': 1.0,
            },
            RiskLevel.COLLABORATIVE: {
                'max_position_size': 0.06,      # Balanced approach
                'max_sector_exposure': 0.25,    # Diversified
                'max_daily_loss_pct': 0.015,    # Moderate protection
                'max_drawdown_pct': 0.08,       # Sustainable drawdown
                'volatility_multiplier': 0.7,   # Stability-focused
                'market_impact_limit': 0.5,     # Limit market disruption
            }
        }
        return params[self.risk_level]
    
    def calculate_position_size(self, 
                              signal_confidence: float,
                              current_price: float,
                              stop_loss: float,
                              symbol: str,
                              sector: str = "unknown",
                              market_impact_score: float = 0.0) -> float:
        """
        Calculate optimal position size with collaboration constraints.
        Balances profit potential with market stability.
        """
        # Base position size from confidence
        base_size = signal_confidence * self.risk_params['max_position_size']
        
        # Risk-based position sizing (Kelly-like approach)
        if stop_loss > 0 and current_price > 0:
            risk_per_share = abs(current_price - stop_loss)
            risk_percentage = risk_per_share / current_price
            
            # Adjust for risk
            if risk_percentage > 0:
                max_risk_amount = self.portfolio_value * 0.01  # 1% portfolio risk
                max_shares = max_risk_amount / risk_per_share
                max_position_value = max_shares * current_price
                risk_adjusted_size = min(base_size, max_position_value / self.portfolio_value)
            else:
                risk_adjusted_size = base_size
        else:
            risk_adjusted_size = base_size
            
        # Apply collaboration constraints
        if self.risk_level == RiskLevel.COLLABORATIVE:
            # Reduce size for high market impact
            collaboration_adjustment = 1.0 - (market_impact_score * 0.5)
            risk_adjusted_size *= collaboration_adjustment
            
        # Check position limits
        current_position_pct = self.current_positions.get(symbol, 0.0)
        available_position_capacity = self.risk_params['max_position_size'] - current_position_pct
        
        # Check sector limits
        current_sector_pct = self.sector_exposure.get(sector, 0.0)
        available_sector_capacity = self.risk_params['max_sector_exposure'] - current_sector_pct
        
        # Take minimum of all constraints
        final_size = min(
            risk_adjusted_size,
            available_position_capacity,
            available_sector_capacity
        )
        
        return max(0.0, final_size)  # Ensure non-negative
    
    def check_risk_limits(self) -> Dict[str, bool]:
        """
        Check all risk limits with collaboration considerations.
        Returns dict of limit checks.
        """
        current_drawdown = (self.peak_value - self.portfolio_value) / self.peak_value
        
        checks = {
            'daily_loss_ok': abs(self.daily_pnl) <= self.max_daily_loss,
            'drawdown_ok': current_drawdown <= self.risk_params['max_drawdown_pct'],
            'position_concentration_ok': all(
                pos <= self.risk_params['max_position_size'] 
                for pos in self.current_positions.values()
            ),
            'sector_concentration_ok': all(
                exp <= self.risk_params['max_sector_exposure']
                for exp in self.sector_exposure.values()
            )
        }
        
        # Additional collaboration check
        if self.risk_level == RiskLevel.COLLABORATIVE:
            total_high_impact_exposure = sum(
                pos for pos in self.current_positions.values() 
                if pos > 0.04  # Positions > 4% considered high impact
            )
            checks['collaboration_ok'] = total_high_impact_exposure <= 0.15  # Max 15% in high-impact positions
            
        return checks
    
    def update_portfolio_state(self, 
                             new_portfolio_value: float,
                             daily_pnl: float,
                             positions: Dict[str, float],
                             sector_exposures: Dict[str, float]):
        """Update portfolio state for risk monitoring."""
        self.portfolio_value = new_portfolio_value
        self.daily_pnl = daily_pnl
        self.current_positions = positions.copy()
        self.sector_exposure = sector_exposures.copy()
        
        # Update peak for drawdown calculation
        if new_portfolio_value > self.peak_value:
            self.peak_value = new_portfolio_value
    
    def get_risk_metrics(self) -> Dict[str, float]:
        """Get current risk metrics for monitoring."""
        current_drawdown = (self.peak_value - self.portfolio_value) / self.peak_value
        
        metrics = {
            'current_drawdown': current_drawdown,
            'daily_pnl_pct': self.daily_pnl / self.portfolio_value,
            'max_position_exposure': max(self.current_positions.values()) if self.current_positions else 0.0,
            'max_sector_exposure': max(self.sector_exposure.values()) if self.sector_exposure else 0.0,
            'total_exposure': sum(self.current_positions.values()),
            'portfolio_value': self.portfolio_value
        }
        
        # Add collaboration metrics
        if self.risk_level == RiskLevel.COLLABORATIVE:
            high_impact_positions = sum(
                pos for pos in self.current_positions.values() if pos > 0.04
            )
            metrics['high_impact_exposure'] = high_impact_positions
            metrics['collaboration_score'] = 1.0 - (high_impact_positions / 0.15)  # Higher = better
            
        return metrics
    
    def should_reduce_exposure(self) -> bool:
        """Determine if exposure should be reduced based on risk limits."""
        risk_checks = self.check_risk_limits()
        return not all(risk_checks.values())
    
    def get_emergency_actions(self) -> List[str]:
        """Get recommended emergency actions if risk limits breached."""
        risk_checks = self.check_risk_limits()
        actions = []
        
        if not risk_checks['daily_loss_ok']:
            actions.append("STOP_TRADING_TODAY")
        if not risk_checks['drawdown_ok']:
            actions.append("REDUCE_ALL_POSITIONS_50PCT")
        if not risk_checks['position_concentration_ok']:
            actions.append("REDUCE_OVERSIZED_POSITIONS")
        if not risk_checks['sector_concentration_ok']:
            actions.append("REDUCE_SECTOR_CONCENTRATION")
            
        if self.risk_level == RiskLevel.COLLABORATIVE and not risk_checks.get('collaboration_ok', True):
            actions.append("REDUCE_HIGH_IMPACT_POSITIONS")
            
        return actions
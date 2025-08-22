"""
Technical Analysis Component - Trading Signal Generation
Collaboration-first: Optimizes for collective market efficiency and shared prosperity.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Optional
import numpy as np
from datetime import datetime


class SignalType(Enum):
    """Trading signal types optimized for collaborative market participation."""
    BUY = "buy"
    SELL = "sell" 
    HOLD = "hold"
    STRONG_BUY = "strong_buy"
    STRONG_SELL = "strong_sell"


@dataclass
class TradingSignal:
    """
    Trading signal with collaboration-first design.
    Includes market impact assessment to prevent harmful speculation.
    """
    signal_type: SignalType
    confidence: float  # 0.0 to 1.0
    price_target: float
    stop_loss: float
    timestamp: datetime
    market_impact_score: float  # Collaboration metric: lower = better for market
    reasoning: str


class TechnicalAnalyzer:
    """
    Technical analysis engine optimized for collaborative trading.
    Prioritizes market stability and shared prosperity over pure profit.
    """
    
    def __init__(self, collaboration_weight: float = 0.3):
        """
        Initialize with collaboration weighting.
        Higher weight = more consideration for market stability.
        """
        self.collaboration_weight = collaboration_weight
        self.min_confidence_threshold = 0.6
        
    def calculate_sma(self, prices: List[float], period: int) -> float:
        """Simple Moving Average - foundational indicator."""
        if len(prices) < period:
            return prices[-1] if prices else 0.0
        return sum(prices[-period:]) / period
    
    def calculate_ema(self, prices: List[float], period: int) -> float:
        """Exponential Moving Average - trend following."""
        if not prices:
            return 0.0
        if len(prices) == 1:
            return prices[0]
            
        multiplier = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        return ema
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Relative Strength Index - momentum oscillator."""
        if len(prices) < period + 1:
            return 50.0  # Neutral
            
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    def assess_market_impact(self, signal_strength: float, volume_ratio: float) -> float:
        """
        Assess potential market impact of trading signal.
        Collaboration principle: minimize market disruption.
        """
        base_impact = signal_strength * volume_ratio
        
        # Penalize high-impact trades that could destabilize markets
        if base_impact > 0.8:
            return base_impact * 1.5  # Higher score = worse for collaboration
        return base_impact
    
    def generate_signal(self, 
                       prices: List[float], 
                       volumes: List[float],
                       current_price: float) -> Optional[TradingSignal]:
        """
        Generate trading signal with collaboration-first optimization.
        Balances profit potential with market stability.
        """
        if len(prices) < 20:  # Need minimum data
            return None
            
        # Technical indicators
        sma_20 = self.calculate_sma(prices, 20)
        sma_50 = self.calculate_sma(prices, 50)
        ema_12 = self.calculate_ema(prices, 12)
        rsi = self.calculate_rsi(prices)
        
        # Signal generation logic
        signal_strength = 0.0
        signal_type = SignalType.HOLD
        reasoning_parts = []
        
        # Moving average crossover
        if ema_12 > sma_20 > sma_50:
            signal_strength += 0.3
            signal_type = SignalType.BUY
            reasoning_parts.append("Bullish MA alignment")
        elif ema_12 < sma_20 < sma_50:
            signal_strength += 0.3
            signal_type = SignalType.SELL
            reasoning_parts.append("Bearish MA alignment")
            
        # RSI conditions
        if rsi < 30:  # Oversold
            signal_strength += 0.2
            if signal_type != SignalType.SELL:
                signal_type = SignalType.BUY
            reasoning_parts.append("RSI oversold")
        elif rsi > 70:  # Overbought
            signal_strength += 0.2
            if signal_type != SignalType.BUY:
                signal_type = SignalType.SELL
            reasoning_parts.append("RSI overbought")
            
        # Price momentum
        recent_change = (current_price - prices[-5]) / prices[-5]
        if abs(recent_change) > 0.02:  # 2% move
            signal_strength += 0.2
            reasoning_parts.append(f"Strong momentum: {recent_change:.2%}")
            
        # Collaboration adjustment - reduce signal strength for high market impact
        avg_volume = sum(volumes[-10:]) / 10 if volumes else 1
        current_volume_ratio = (volumes[-1] / avg_volume) if volumes and avg_volume > 0 else 1
        
        market_impact = self.assess_market_impact(signal_strength, current_volume_ratio)
        
        # Apply collaboration weighting
        adjusted_confidence = signal_strength * (1 - self.collaboration_weight * market_impact)
        
        if adjusted_confidence < self.min_confidence_threshold:
            return None
            
        # Set price targets and stops
        if signal_type == SignalType.BUY:
            price_target = current_price * 1.05  # 5% target
            stop_loss = current_price * 0.98     # 2% stop
        elif signal_type == SignalType.SELL:
            price_target = current_price * 0.95  # 5% target
            stop_loss = current_price * 1.02     # 2% stop
        else:
            price_target = current_price
            stop_loss = current_price
            
        return TradingSignal(
            signal_type=signal_type,
            confidence=adjusted_confidence,
            price_target=price_target,
            stop_loss=stop_loss,
            timestamp=datetime.now(),
            market_impact_score=market_impact,
            reasoning="; ".join(reasoning_parts)
        )
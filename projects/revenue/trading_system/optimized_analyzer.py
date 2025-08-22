"""
Optimized Technical Analysis Component - Enhanced for Micro-Trading
Improved signal generation frequency while maintaining risk controls.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Optional
import numpy as np
from datetime import datetime


class SignalType(Enum):
    """Trading signal types optimized for micro-trading."""
    BUY = "buy"
    SELL = "sell" 
    HOLD = "hold"
    STRONG_BUY = "strong_buy"
    STRONG_SELL = "strong_sell"


@dataclass
class TradingSignal:
    """Enhanced trading signal with micro-trading optimizations."""
    signal_type: SignalType
    confidence: float  # 0.0 to 1.0
    price_target: float
    stop_loss: float
    timestamp: datetime
    market_impact_score: float
    reasoning: str
    momentum_score: float  # New: momentum strength
    volatility_adjusted: bool  # New: volatility adaptation


class OptimizedTechnicalAnalyzer:
    """
    Optimized technical analysis engine for micro-trading.
    Enhanced signal generation with maintained risk controls.
    """
    
    def __init__(self, collaboration_weight: float = 0.15):
        """Initialize with optimized parameters for micro-trading."""
        self.collaboration_weight = collaboration_weight  # Reduced from 0.3
        self.min_confidence_threshold = 0.5  # Reduced from 0.6
        self.momentum_boost_enabled = True
        self.volatility_scaling_enabled = True
        
    def calculate_enhanced_momentum(self, prices: List[float]) -> float:
        """Calculate enhanced momentum indicator."""
        if len(prices) < 10:
            return 0.0
            
        # Multiple timeframe momentum
        short_momentum = (prices[-1] - prices[-3]) / prices[-3]  # 3-period
        medium_momentum = (prices[-1] - prices[-5]) / prices[-5]  # 5-period
        long_momentum = (prices[-1] - prices[-10]) / prices[-10]  # 10-period
        
        # Weighted momentum score
        momentum_score = (short_momentum * 0.5 + 
                         medium_momentum * 0.3 + 
                         long_momentum * 0.2)
        
        return momentum_score
    
    def calculate_volatility_adjustment(self, prices: List[float]) -> float:
        """Calculate volatility-based adjustment factor."""
        if len(prices) < 20:
            return 1.0
            
        returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
        volatility = np.std(returns) if returns else 0.0
        
        # Higher volatility = more conservative signals
        # Lower volatility = more aggressive signals
        if volatility > 0.02:  # High volatility (>2%)
            return 0.8  # Reduce signal strength
        elif volatility < 0.005:  # Low volatility (<0.5%)
            return 1.2  # Boost signal strength
        else:
            return 1.0  # Normal volatility
    
    def generate_enhanced_signal(self, 
                                prices: List[float], 
                                volumes: List[float],
                                current_price: float) -> Optional[TradingSignal]:
        """Generate enhanced trading signal with micro-trading optimizations."""
        if len(prices) < 20:
            return None
            
        # Standard technical indicators
        sma_20 = self.calculate_sma(prices, 20)
        sma_50 = self.calculate_sma(prices, 50) if len(prices) >= 50 else sma_20
        ema_12 = self.calculate_ema(prices, 12)
        rsi = self.calculate_rsi(prices)
        
        # Enhanced indicators
        momentum_score = self.calculate_enhanced_momentum(prices)
        volatility_adjustment = self.calculate_volatility_adjustment(prices)
        
        # Signal generation with enhancements
        signal_strength = 0.0
        signal_type = SignalType.HOLD
        reasoning_parts = []
        
        # Moving average signals (enhanced)
        if ema_12 > sma_20:
            signal_strength += 0.25
            if sma_20 > sma_50:
                signal_strength += 0.15  # Trend confirmation
            signal_type = SignalType.BUY
            reasoning_parts.append("Bullish MA alignment")
        elif ema_12 < sma_20:
            signal_strength += 0.25
            if sma_20 < sma_50:
                signal_strength += 0.15
            signal_type = SignalType.SELL
            reasoning_parts.append("Bearish MA alignment")
            
        # RSI signals (enhanced thresholds)
        if rsi < 35:  # Slightly less oversold for more signals
            signal_strength += 0.2
            if signal_type != SignalType.SELL:
                signal_type = SignalType.BUY
            reasoning_parts.append("RSI oversold")
        elif rsi > 65:  # Slightly less overbought
            signal_strength += 0.2
            if signal_type != SignalType.BUY:
                signal_type = SignalType.SELL
            reasoning_parts.append("RSI overbought")
            
        # Momentum enhancement
        if self.momentum_boost_enabled:
            if abs(momentum_score) > 0.01:  # 1% momentum threshold
                momentum_boost = min(abs(momentum_score) * 10, 0.3)  # Cap at 0.3
                signal_strength += momentum_boost
                
                if momentum_score > 0 and signal_type != SignalType.SELL:
                    signal_type = SignalType.BUY
                elif momentum_score < 0 and signal_type != SignalType.BUY:
                    signal_type = SignalType.SELL
                    
                reasoning_parts.append(f"Momentum: {momentum_score:.3f}")
        
        # Volume confirmation
        if volumes:
            avg_volume = sum(volumes[-10:]) / 10
            current_volume_ratio = volumes[-1] / avg_volume if avg_volume > 0 else 1
            
            if current_volume_ratio > 1.2:  # Above average volume
                signal_strength += 0.1
                reasoning_parts.append("High volume")
        
        # Apply volatility adjustment
        if self.volatility_scaling_enabled:
            signal_strength *= volatility_adjustment
            volatility_adjusted = True
        else:
            volatility_adjusted = False
        
        # Market impact assessment (simplified for micro-trading)
        market_impact = signal_strength * 0.5  # Reduced impact for smaller positions
        
        # Apply collaboration weighting (reduced)
        adjusted_confidence = signal_strength * (1 - self.collaboration_weight * market_impact)
        
        # Lower threshold for micro-trading
        if adjusted_confidence < self.min_confidence_threshold:
            return None
            
        # Enhanced price targets for micro-trading
        if signal_type == SignalType.BUY:
            price_target = current_price * 1.02  # 2% target (reduced from 5%)
            stop_loss = current_price * 0.99     # 1% stop
        elif signal_type == SignalType.SELL:
            price_target = current_price * 0.98  # 2% target
            stop_loss = current_price * 1.01     # 1% stop
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
            reasoning="; ".join(reasoning_parts),
            momentum_score=momentum_score,
            volatility_adjusted=volatility_adjusted
        )
    
    # Include existing methods from original analyzer
    def calculate_sma(self, prices: List[float], period: int) -> float:
        """Simple Moving Average."""
        if len(prices) < period:
            return prices[-1] if prices else 0.0
        return sum(prices[-period:]) / period
    
    def calculate_ema(self, prices: List[float], period: int) -> float:
        """Exponential Moving Average."""
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
        """Relative Strength Index."""
        if len(prices) < period + 1:
            return 50.0
            
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

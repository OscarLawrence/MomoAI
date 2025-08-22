"""
Backtesting Engine Component - Strategy Validation
Collaboration-first: Tests strategies for both profitability and market stability impact.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import statistics


class BacktestStatus(Enum):
    """Backtest execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class BacktestResult:
    """
    Comprehensive backtest results with collaboration metrics.
    Includes both profit metrics and market impact assessment.
    """
    # Performance metrics
    total_return: float
    annualized_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    
    # Collaboration metrics
    market_impact_score: float  # Lower = better for market stability
    volatility_contribution: float  # How much strategy adds to market volatility
    liquidity_impact: float  # Impact on market liquidity
    
    # Trade statistics
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_trade_duration: float  # hours
    
    # Risk metrics
    var_95: float  # Value at Risk 95%
    expected_shortfall: float
    calmar_ratio: float
    
    # Execution details
    start_date: datetime
    end_date: datetime
    status: BacktestStatus
    execution_time: float  # seconds


class BacktestEngine:
    """
    Backtesting engine with collaboration-first validation.
    Tests strategies for sustainable profitability and positive market impact.
    """
    
    def __init__(self, initial_capital: float = 100000.0):
        """Initialize backtesting engine."""
        self.initial_capital = initial_capital
        self.commission_rate = 0.001  # 0.1% per trade
        self.slippage_rate = 0.0005   # 0.05% slippage
        
        # Collaboration parameters
        self.market_impact_penalty = 0.1  # Penalty for high market impact
        self.min_collaboration_score = 0.6  # Minimum acceptable collaboration score
        
    def run_backtest(self,
                    price_data: List[Dict],  # [{'timestamp', 'open', 'high', 'low', 'close', 'volume'}]
                    strategy_signals: List[Dict],  # [{'timestamp', 'signal', 'confidence', 'market_impact'}]
                    risk_params: Dict) -> BacktestResult:
        """
        Run comprehensive backtest with collaboration assessment.
        """
        start_time = datetime.now()
        
        # Initialize tracking variables
        portfolio_value = self.initial_capital
        cash = self.initial_capital
        positions = {}
        trade_history = []
        daily_returns = []
        portfolio_values = [self.initial_capital]
        
        # Market impact tracking
        total_market_impact = 0.0
        volatility_contributions = []
        liquidity_impacts = []
        
        # Process each time period
        for i, price_bar in enumerate(price_data):
            current_time = price_bar['timestamp']
            current_price = price_bar['close']
            current_volume = price_bar['volume']
            
            # Find corresponding signal
            signal = self._find_signal_for_time(strategy_signals, current_time)
            
            if signal and self._should_execute_trade(signal, portfolio_value, positions):
                # Execute trade with collaboration considerations
                trade_result = self._execute_trade(
                    signal, current_price, current_volume, cash, positions, portfolio_value
                )
                
                if trade_result:
                    cash = trade_result['new_cash']
                    positions = trade_result['new_positions']
                    trade_history.append(trade_result['trade_record'])
                    
                    # Track market impact
                    total_market_impact += signal.get('market_impact', 0.0)
                    volatility_contributions.append(self._calculate_volatility_contribution(signal, price_bar))
                    liquidity_impacts.append(self._calculate_liquidity_impact(signal, current_volume))
            
            # Update portfolio value
            position_value = self._calculate_position_value(positions, current_price)
            portfolio_value = cash + position_value
            portfolio_values.append(portfolio_value)
            
            # Calculate daily return
            if i > 0:
                daily_return = (portfolio_value - portfolio_values[-2]) / portfolio_values[-2]
                daily_returns.append(daily_return)
        
        # Calculate final metrics
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        return self._calculate_backtest_metrics(
            portfolio_values, daily_returns, trade_history,
            total_market_impact, volatility_contributions, liquidity_impacts,
            price_data[0]['timestamp'], price_data[-1]['timestamp'], execution_time
        )
    
    def _find_signal_for_time(self, signals: List[Dict], target_time: datetime) -> Optional[Dict]:
        """Find the signal closest to the target time."""
        for signal in signals:
            if abs((signal['timestamp'] - target_time).total_seconds()) < 3600:  # Within 1 hour
                return signal
        return None
    
    def _should_execute_trade(self, signal: Dict, portfolio_value: float, positions: Dict) -> bool:
        """Determine if trade should be executed based on collaboration principles."""
        # Basic confidence check
        if signal.get('confidence', 0.0) < 0.6:
            return False
            
        # Collaboration check - avoid high market impact trades
        market_impact = signal.get('market_impact', 0.0)
        if market_impact > 0.8:
            return False
            
        # Position size check
        signal_strength = signal.get('confidence', 0.0)
        max_position_size = portfolio_value * 0.1  # 10% max position
        
        return True
    
    def _execute_trade(self, signal: Dict, price: float, volume: float, 
                      cash: float, positions: Dict, portfolio_value: float) -> Optional[Dict]:
        """Execute trade with realistic costs and collaboration considerations."""
        signal_type = signal.get('signal', 'hold')
        confidence = signal.get('confidence', 0.0)
        
        if signal_type == 'hold':
            return None
            
        # Calculate position size (collaboration-adjusted)
        market_impact = signal.get('market_impact', 0.0)
        collaboration_adjustment = 1.0 - (market_impact * self.market_impact_penalty)
        
        base_position_size = portfolio_value * confidence * 0.1  # Base: 10% * confidence
        adjusted_position_size = base_position_size * collaboration_adjustment
        
        # Apply transaction costs
        gross_cost = adjusted_position_size
        commission = gross_cost * self.commission_rate
        slippage = gross_cost * self.slippage_rate
        net_cost = gross_cost + commission + slippage
        
        if signal_type in ['buy', 'strong_buy'] and cash >= net_cost:
            # Buy trade
            shares = adjusted_position_size / price
            new_cash = cash - net_cost
            new_positions = positions.copy()
            new_positions['stock'] = new_positions.get('stock', 0) + shares
            
            trade_record = {
                'timestamp': signal['timestamp'],
                'type': 'buy',
                'shares': shares,
                'price': price,
                'cost': net_cost,
                'commission': commission,
                'slippage': slippage,
                'market_impact': market_impact
            }
            
            return {
                'new_cash': new_cash,
                'new_positions': new_positions,
                'trade_record': trade_record
            }
            
        elif signal_type in ['sell', 'strong_sell'] and positions.get('stock', 0) > 0:
            # Sell trade
            available_shares = positions.get('stock', 0)
            shares_to_sell = min(available_shares, adjusted_position_size / price)
            
            gross_proceeds = shares_to_sell * price
            net_proceeds = gross_proceeds - commission - slippage
            
            new_cash = cash + net_proceeds
            new_positions = positions.copy()
            new_positions['stock'] = new_positions.get('stock', 0) - shares_to_sell
            
            trade_record = {
                'timestamp': signal['timestamp'],
                'type': 'sell',
                'shares': shares_to_sell,
                'price': price,
                'proceeds': net_proceeds,
                'commission': commission,
                'slippage': slippage,
                'market_impact': market_impact
            }
            
            return {
                'new_cash': new_cash,
                'new_positions': new_positions,
                'trade_record': trade_record
            }
        
        return None
    
    def _calculate_position_value(self, positions: Dict, current_price: float) -> float:
        """Calculate current value of all positions."""
        return positions.get('stock', 0) * current_price
    
    def _calculate_volatility_contribution(self, signal: Dict, price_bar: Dict) -> float:
        """Calculate how much the signal contributes to market volatility."""
        price_range = price_bar['high'] - price_bar['low']
        price_volatility = price_range / price_bar['close']
        signal_strength = signal.get('confidence', 0.0)
        
        return price_volatility * signal_strength
    
    def _calculate_liquidity_impact(self, signal: Dict, volume: float) -> float:
        """Calculate impact on market liquidity."""
        signal_strength = signal.get('confidence', 0.0)
        # Higher signal strength with lower volume = higher liquidity impact
        if volume > 0:
            return signal_strength / (volume / 1000000)  # Normalize by million shares
        return signal_strength
    
    def _calculate_backtest_metrics(self, portfolio_values: List[float], daily_returns: List[float],
                                  trade_history: List[Dict], total_market_impact: float,
                                  volatility_contributions: List[float], liquidity_impacts: List[float],
                                  start_date: datetime, end_date: datetime, execution_time: float) -> BacktestResult:
        """Calculate comprehensive backtest metrics."""
        
        # Basic performance metrics
        total_return = (portfolio_values[-1] - portfolio_values[0]) / portfolio_values[0]
        
        # Annualized return
        days = (end_date - start_date).days
        years = days / 365.25
        annualized_return = (1 + total_return) ** (1/years) - 1 if years > 0 else total_return
        
        # Risk metrics
        if daily_returns:
            returns_std = statistics.stdev(daily_returns) if len(daily_returns) > 1 else 0.0
            sharpe_ratio = (statistics.mean(daily_returns) * 252) / (returns_std * (252**0.5)) if returns_std > 0 else 0.0
            
            # Drawdown calculation
            peak = portfolio_values[0]
            max_drawdown = 0.0
            for value in portfolio_values:
                if value > peak:
                    peak = value
                drawdown = (peak - value) / peak
                max_drawdown = max(max_drawdown, drawdown)
        else:
            sharpe_ratio = 0.0
            max_drawdown = 0.0
        
        # Trade statistics
        total_trades = len(trade_history)
        winning_trades = sum(1 for trade in trade_history if self._is_winning_trade(trade))
        losing_trades = total_trades - winning_trades
        win_rate = winning_trades / total_trades if total_trades > 0 else 0.0
        
        # Collaboration metrics
        avg_market_impact = total_market_impact / total_trades if total_trades > 0 else 0.0
        avg_volatility_contribution = statistics.mean(volatility_contributions) if volatility_contributions else 0.0
        avg_liquidity_impact = statistics.mean(liquidity_impacts) if liquidity_impacts else 0.0
        
        # Additional metrics
        profit_factor = self._calculate_profit_factor(trade_history)
        avg_trade_duration = self._calculate_avg_trade_duration(trade_history)
        var_95 = self._calculate_var(daily_returns, 0.95) if daily_returns else 0.0
        expected_shortfall = self._calculate_expected_shortfall(daily_returns, 0.95) if daily_returns else 0.0
        calmar_ratio = annualized_return / max_drawdown if max_drawdown > 0 else 0.0
        
        return BacktestResult(
            total_return=total_return,
            annualized_return=annualized_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            profit_factor=profit_factor,
            market_impact_score=avg_market_impact,
            volatility_contribution=avg_volatility_contribution,
            liquidity_impact=avg_liquidity_impact,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            avg_trade_duration=avg_trade_duration,
            var_95=var_95,
            expected_shortfall=expected_shortfall,
            calmar_ratio=calmar_ratio,
            start_date=start_date,
            end_date=end_date,
            status=BacktestStatus.COMPLETED,
            execution_time=execution_time
        )
    
    def _is_winning_trade(self, trade: Dict) -> bool:
        """Determine if a trade was profitable."""
        if trade['type'] == 'buy':
            return False  # Can't determine until sell
        # Simplified - would need more sophisticated tracking in real implementation
        return trade.get('proceeds', 0) > trade.get('cost', 0)
    
    def _calculate_profit_factor(self, trade_history: List[Dict]) -> float:
        """Calculate profit factor (gross profit / gross loss)."""
        gross_profit = sum(trade.get('proceeds', 0) - trade.get('cost', 0) 
                          for trade in trade_history 
                          if trade.get('proceeds', 0) > trade.get('cost', 0))
        gross_loss = abs(sum(trade.get('proceeds', 0) - trade.get('cost', 0) 
                            for trade in trade_history 
                            if trade.get('proceeds', 0) < trade.get('cost', 0)))
        
        return gross_profit / gross_loss if gross_loss > 0 else float('inf')
    
    def _calculate_avg_trade_duration(self, trade_history: List[Dict]) -> float:
        """Calculate average trade duration in hours."""
        if len(trade_history) < 2:
            return 0.0
        
        durations = []
        for i in range(1, len(trade_history)):
            duration = (trade_history[i]['timestamp'] - trade_history[i-1]['timestamp']).total_seconds() / 3600
            durations.append(duration)
        
        return statistics.mean(durations) if durations else 0.0
    
    def _calculate_var(self, returns: List[float], confidence: float) -> float:
        """Calculate Value at Risk."""
        if not returns:
            return 0.0
        sorted_returns = sorted(returns)
        index = int((1 - confidence) * len(sorted_returns))
        return abs(sorted_returns[index]) if index < len(sorted_returns) else 0.0
    
    def _calculate_expected_shortfall(self, returns: List[float], confidence: float) -> float:
        """Calculate Expected Shortfall (Conditional VaR)."""
        if not returns:
            return 0.0
        sorted_returns = sorted(returns)
        index = int((1 - confidence) * len(sorted_returns))
        tail_returns = sorted_returns[:index] if index > 0 else [sorted_returns[0]]
        return abs(statistics.mean(tail_returns)) if tail_returns else 0.0
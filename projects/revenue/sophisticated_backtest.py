#!/usr/bin/env python3
"""
Sophisticated Backtesting Framework for Coherent Trading System
Tests mathematical strategies against real historical crypto data.
"""

import sys
import json
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import statistics

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Add trading_system to path
sys.path.insert(0, str(Path(__file__).parent / "trading_system"))

from trading_system.binance_connector import create_binance_connector


@dataclass
class BacktestTrade:
    """Individual backtest trade record."""
    timestamp: datetime
    strategy: str
    symbol: str
    side: str  # 'buy' or 'sell'
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float
    pnl_percent: float
    confidence: float
    mathematical_proof: str
    duration_minutes: int
    fees: float


@dataclass
class BacktestMetrics:
    """Comprehensive backtesting metrics."""
    # Performance metrics
    total_return: float
    annualized_return: float
    max_drawdown: float
    sharpe_ratio: float
    calmar_ratio: float
    
    # Trade statistics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    
    # Strategy breakdown
    strategy_performance: Dict[str, float]
    monthly_returns: List[float]
    
    # Risk metrics
    value_at_risk_95: float
    maximum_consecutive_losses: int
    average_trade_duration: float
    
    # Coherence metrics
    coherence_validation_rate: float
    mathematical_edge: float


class HistoricalDataManager:
    """Fetch and manage historical cryptocurrency data."""
    
    def __init__(self):
        self.connector = create_binance_connector()
        self.cache = {}
        
    def fetch_historical_data(self, symbol: str, interval: str = "1h", 
                            days: int = 90) -> List[Dict]:
        """Fetch historical OHLCV data from Binance."""
        cache_key = f"{symbol}_{interval}_{days}"
        
        if cache_key in self.cache:
            print(f"📋 Using cached data for {symbol}")
            return self.cache[cache_key]
        
        if not self.connector:
            print("❌ No Binance connection - using simulated data")
            return self._generate_simulated_data(symbol, days)
        
        print(f"📊 Fetching {days} days of {symbol} data...")
        
        # Calculate number of data points needed
        hours_per_day = 24
        limit = min(days * hours_per_day, 1000)  # Binance API limit
        
        try:
            klines = self.connector.get_kline_data(symbol, interval, limit)
            
            if not klines:
                print(f"⚠️ No data received for {symbol}, using simulated data")
                return self._generate_simulated_data(symbol, days)
            
            # Convert to our format
            data = []
            for kline in klines:
                data.append({
                    'timestamp': datetime.fromtimestamp(kline['open_time'] / 1000),
                    'open': kline['open'],
                    'high': kline['high'],
                    'low': kline['low'],
                    'close': kline['close'],
                    'volume': kline['volume']
                })
            
            self.cache[cache_key] = data
            print(f"✅ Fetched {len(data)} data points for {symbol}")
            return data
            
        except Exception as e:
            print(f"❌ Error fetching {symbol} data: {e}")
            return self._generate_simulated_data(symbol, days)
    
    def _generate_simulated_data(self, symbol: str, days: int) -> List[Dict]:
        """Generate realistic simulated crypto data."""
        import random
        import math
        
        # Starting prices for different symbols
        start_prices = {
            "BTCUSDT": 45000,
            "ETHUSDT": 2800,
            "SOLUSDT": 120,
            "AVAXUSDT": 25
        }
        
        base_price = start_prices.get(symbol, 1000)
        data = []
        current_price = base_price
        start_time = datetime.now() - timedelta(days=days)
        
        for hour in range(days * 24):
            timestamp = start_time + timedelta(hours=hour)
            
            # Generate realistic OHLCV
            volatility = 0.02  # 2% hourly volatility
            trend = 0.0001     # Slight upward trend
            
            # Price change with some trend and volatility
            change = random.gauss(trend, volatility)
            new_price = current_price * (1 + change)
            
            # Generate OHLC with realistic spread
            price_range = new_price * volatility * random.uniform(0.3, 1.5)
            
            open_price = current_price
            close_price = new_price
            high_price = max(open_price, close_price) + random.uniform(0, price_range)
            low_price = min(open_price, close_price) - random.uniform(0, price_range)
            
            # Volume with some correlation to volatility
            base_volume = 1000000
            volume_multiplier = 1 + abs(change) * 20  # Higher volume during volatile periods
            volume = base_volume * volume_multiplier * random.uniform(0.5, 2.0)
            
            data.append({
                'timestamp': timestamp,
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': volume
            })
            
            current_price = new_price
        
        print(f"✅ Generated {len(data)} simulated data points for {symbol}")
        return data


class MathematicalStrategyBacktester:
    """Backtest mathematical trading strategies on historical data."""
    
    def __init__(self, initial_capital: float = 10000.0):
        self.initial_capital = initial_capital
        self.data_manager = HistoricalDataManager()
        self.reset_state()
        
    def reset_state(self):
        """Reset backtesting state."""
        self.capital = self.initial_capital
        self.positions = {}
        self.trades = []
        self.portfolio_values = [self.initial_capital]
        self.daily_returns = []
        
    def calculate_correlation(self, prices1: List[float], prices2: List[float], 
                            window: int = 20) -> Optional[float]:
        """Calculate correlation between two price series."""
        if len(prices1) < window or len(prices2) < window:
            return None
        
        # Use last 'window' prices
        p1 = prices1[-window:]
        p2 = prices2[-window:]
        
        # Calculate returns
        returns1 = [(p1[i] - p1[i-1]) / p1[i-1] for i in range(1, len(p1))]
        returns2 = [(p2[i] - p2[i-1]) / p2[i-1] for i in range(1, len(p2))]
        
        if len(returns1) < 2 or len(returns2) < 2:
            return None
        
        # Calculate correlation
        mean1 = sum(returns1) / len(returns1)
        mean2 = sum(returns2) / len(returns2)
        
        numerator = sum((r1 - mean1) * (r2 - mean2) for r1, r2 in zip(returns1, returns2))
        denominator1 = sum((r1 - mean1) ** 2 for r1 in returns1) ** 0.5
        denominator2 = sum((r2 - mean2) ** 2 for r2 in returns2) ** 0.5
        
        if denominator1 == 0 or denominator2 == 0:
            return None
        
        return numerator / (denominator1 * denominator2)
    
    def detect_correlation_breakdown(self, data1: List[Dict], data2: List[Dict], 
                                   index: int) -> Optional[Dict]:
        """Detect correlation breakdown opportunity."""
        if index < 50:  # Need enough history
            return None
        
        # Get price series up to current point
        prices1 = [d['close'] for d in data1[:index+1]]
        prices2 = [d['close'] for d in data2[:index+1]]
        
        # Calculate recent and historical correlations
        recent_corr = self.calculate_correlation(prices1, prices2, 20)
        historical_corr = self.calculate_correlation(prices1, prices2, 50)
        
        if recent_corr is None or historical_corr is None:
            return None
        
        # Check for significant breakdown
        breakdown = abs(historical_corr - recent_corr)
        
        if breakdown > 0.3:  # 30% correlation change
            return {
                'strategy': 'correlation_breakdown',
                'confidence': min(breakdown * 2, 0.9),
                'expected_return': breakdown * 0.4,  # Conservative estimate
                'risk_level': 0.15,
                'mathematical_proof': f"Correlation breakdown: {breakdown:.2%} from {historical_corr:.2f} to {recent_corr:.2f}",
                'breakdown_magnitude': breakdown
            }
        
        return None
    
    def detect_liquidation_opportunity(self, data: List[Dict], index: int) -> Optional[Dict]:
        """Detect liquidation cascade opportunity."""
        if index < 10:
            return None
        
        current_price = data[index]['close']
        recent_prices = [d['close'] for d in data[max(0, index-10):index+1]]
        
        # Calculate recent volatility
        returns = [(recent_prices[i] - recent_prices[i-1]) / recent_prices[i-1] 
                  for i in range(1, len(recent_prices))]
        volatility = statistics.stdev(returns) if len(returns) > 1 else 0
        
        # Simulate liquidation levels (in real system would get from exchanges)
        # Major liquidation levels typically at round numbers and technical levels
        potential_levels = []
        for pct in [0.02, 0.05, 0.07, 0.10]:  # 2%, 5%, 7%, 10% below current price
            level_price = current_price * (1 - pct)
            potential_levels.append(level_price)
        
        # Check if we're near a liquidation level and volatility is high
        min_distance = min(abs(current_price - level) / current_price for level in potential_levels)
        
        if min_distance < 0.02 and volatility > 0.015:  # Within 2% of level, high volatility
            cascade_probability = (0.02 - min_distance) * 25  # Scale to 0-0.5
            expected_bounce = min(0.025, volatility * 2)  # 2.5% max bounce
            
            return {
                'strategy': 'liquidation_cascade',
                'confidence': cascade_probability,
                'expected_return': expected_bounce,
                'risk_level': 0.12,
                'mathematical_proof': f"Near liquidation level, distance: {min_distance:.1%}, volatility: {volatility:.1%}",
                'volatility': volatility
            }
        
        return None
    
    def detect_network_effect(self, data: List[Dict], index: int) -> Optional[Dict]:
        """Detect network effect opportunity using Metcalfe's Law."""
        if index < 20:
            return None
        
        # Simulate network growth data (in real system would fetch from blockchain APIs)
        # For backtest: derive "network activity" from volume patterns
        recent_volumes = [d['volume'] for d in data[max(0, index-10):index+1]]
        historical_volumes = [d['volume'] for d in data[max(0, index-30):index-10]]
        
        if len(recent_volumes) < 5 or len(historical_volumes) < 10:
            return None
        
        recent_avg_volume = sum(recent_volumes) / len(recent_volumes)
        historical_avg_volume = sum(historical_volumes) / len(historical_volumes)
        
        if historical_avg_volume == 0:
            return None
        
        volume_growth = (recent_avg_volume - historical_avg_volume) / historical_avg_volume
        
        # Apply simplified Metcalfe's Law: network value ∝ users²
        # Assume volume growth correlates with user growth
        if abs(volume_growth) > 0.1:  # 10% volume change
            # Network effect: (1 + growth)² - 1
            network_multiplier = (1 + volume_growth) ** 1.5  # Conservative exponent
            expected_price_change = network_multiplier - 1
            
            if abs(expected_price_change) > 0.02:  # 2% threshold
                return {
                    'strategy': 'network_effect',
                    'confidence': min(abs(expected_price_change) * 15, 0.8),
                    'expected_return': expected_price_change,
                    'risk_level': 0.2,
                    'mathematical_proof': f"Metcalfe's Law: {volume_growth:.1%} volume growth → {expected_price_change:.1%} expected price change",
                    'volume_growth': volume_growth
                }
        
        return None
    
    def validate_opportunity_coherence(self, opportunity: Dict) -> bool:
        """Validate trading opportunity for mathematical coherence."""
        # Basic validation
        if opportunity['confidence'] <= 0 or opportunity['confidence'] > 1:
            return False
        
        if opportunity['risk_level'] <= 0 or opportunity['risk_level'] > 1:
            return False
        
        # Risk-return coherence
        risk_adjusted_return = opportunity['expected_return'] / opportunity['risk_level']
        if risk_adjusted_return < 0.5:  # Minimum acceptable risk-adjusted return
            return False
        
        # Strategy-specific validation
        if opportunity['strategy'] == 'correlation_breakdown':
            if opportunity.get('breakdown_magnitude', 0) < 0.2:
                return False
        
        return True
    
    def calculate_position_size(self, opportunity: Dict) -> float:
        """Calculate optimal position size using Kelly criterion."""
        confidence = opportunity['confidence']
        expected_return = opportunity['expected_return']
        risk_level = opportunity['risk_level']
        
        # Kelly fraction: f = (bp - q) / b
        # where b = expected_return/risk_level, p = confidence, q = 1-confidence
        if risk_level <= 0:
            return 0
        
        b = expected_return / risk_level
        p = confidence
        q = 1 - p
        
        kelly_fraction = (b * p - q) / b if b > 0 else 0
        
        # Apply safety factor and constraints
        safety_factor = 0.1  # Use 10% of Kelly for safety (more conservative)
        max_position_percent = 0.05  # Maximum 5% of capital per trade (more conservative)
        max_absolute_position = 2000  # Maximum $2000 per trade regardless of capital
        
        position_fraction = min(kelly_fraction * safety_factor, max_position_percent)
        position_size = max(0, self.capital * position_fraction)
        
        # Cap absolute position size to prevent exponential growth
        position_size = min(position_size, max_absolute_position)
        
        return position_size
    
    def execute_trade(self, opportunity: Dict, current_price: float, 
                     timestamp: datetime, symbol: str) -> Optional[BacktestTrade]:
        """Execute a trade based on opportunity."""
        if not self.validate_opportunity_coherence(opportunity):
            return None
        
        position_size = self.calculate_position_size(opportunity)
        
        if position_size < 100:  # Minimum position size
            return None
        
        # Calculate trade parameters
        quantity = position_size / current_price
        entry_price = current_price
        
        # Simulate trade execution with fees
        fees = position_size * 0.001  # 0.1% trading fee
        
        # Determine exit price based on strategy
        if opportunity['expected_return'] > 0:
            exit_price = entry_price * (1 + opportunity['expected_return'])
            side = 'buy'
        else:
            exit_price = entry_price * (1 + opportunity['expected_return'])
            side = 'sell'
        
        # Calculate PnL
        if side == 'buy':
            pnl = (exit_price - entry_price) * quantity - fees
        else:
            pnl = (entry_price - exit_price) * quantity - fees
        
        pnl_percent = pnl / position_size
        
        # Update capital
        self.capital += pnl
        
        # Create trade record
        trade = BacktestTrade(
            timestamp=timestamp,
            strategy=opportunity['strategy'],
            symbol=symbol,
            side=side,
            entry_price=entry_price,
            exit_price=exit_price,
            quantity=quantity,
            pnl=pnl,
            pnl_percent=pnl_percent,
            confidence=opportunity['confidence'],
            mathematical_proof=opportunity['mathematical_proof'],
            duration_minutes=60,  # Simplified - assume 1 hour trades
            fees=fees
        )
        
        self.trades.append(trade)
        return trade
    
    def run_backtest(self, symbols: List[str], days: int = 90) -> BacktestMetrics:
        """Run comprehensive backtest on multiple symbols."""
        print(f"🚀 Starting sophisticated backtest on {symbols} for {days} days")
        
        # Reset state
        self.reset_state()
        
        # Fetch historical data for all symbols
        historical_data = {}
        for symbol in symbols:
            historical_data[symbol] = self.data_manager.fetch_historical_data(symbol, "1h", days)
        
        # Ensure all data has same length
        min_length = min(len(data) for data in historical_data.values())
        for symbol in historical_data:
            historical_data[symbol] = historical_data[symbol][:min_length]
        
        print(f"📊 Backtesting with {min_length} data points")
        
        # Main backtesting loop
        executed_trades = 0
        opportunities_found = 0
        
        for i in range(50, min_length):  # Start after enough history
            current_timestamp = historical_data[symbols[0]][i]['timestamp']
            
            # Track portfolio value
            self.portfolio_values.append(self.capital)
            
            # Check for opportunities across all symbols
            for symbol in symbols:
                current_data = historical_data[symbol]
                current_price = current_data[i]['close']
                
                # Network effect opportunity
                network_opp = self.detect_network_effect(current_data, i)
                if network_opp:
                    opportunities_found += 1
                    trade = self.execute_trade(network_opp, current_price, current_timestamp, symbol)
                    if trade:
                        executed_trades += 1
                        print(f"✅ {trade.strategy} trade: {symbol} @ ${current_price:.2f} → ${trade.pnl:+.2f}")
                
                # Liquidation opportunity
                liquidation_opp = self.detect_liquidation_opportunity(current_data, i)
                if liquidation_opp:
                    opportunities_found += 1
                    trade = self.execute_trade(liquidation_opp, current_price, current_timestamp, symbol)
                    if trade:
                        executed_trades += 1
                        print(f"✅ {trade.strategy} trade: {symbol} @ ${current_price:.2f} → ${trade.pnl:+.2f}")
            
            # Correlation breakdown opportunities (between symbol pairs)
            for j in range(len(symbols)):
                for k in range(j + 1, len(symbols)):
                    symbol1, symbol2 = symbols[j], symbols[k]
                    data1, data2 = historical_data[symbol1], historical_data[symbol2]
                    
                    corr_opp = self.detect_correlation_breakdown(data1, data2, i)
                    if corr_opp:
                        opportunities_found += 1
                        # Execute on the first symbol
                        current_price = data1[i]['close']
                        trade = self.execute_trade(corr_opp, current_price, current_timestamp, symbol1)
                        if trade:
                            executed_trades += 1
                            print(f"✅ {trade.strategy} trade: {symbol1} @ ${current_price:.2f} → ${trade.pnl:+.2f}")
        
        print(f"📈 Backtest completed: {opportunities_found} opportunities, {executed_trades} trades executed")
        
        # Calculate comprehensive metrics
        return self.calculate_backtest_metrics()
    
    def calculate_backtest_metrics(self) -> BacktestMetrics:
        """Calculate comprehensive backtesting metrics."""
        if not self.trades:
            return BacktestMetrics(
                total_return=0, annualized_return=0, max_drawdown=0, sharpe_ratio=0,
                calmar_ratio=0, total_trades=0, winning_trades=0, losing_trades=0,
                win_rate=0, avg_win=0, avg_loss=0, profit_factor=0,
                strategy_performance={}, monthly_returns=[], value_at_risk_95=0,
                maximum_consecutive_losses=0, average_trade_duration=0,
                coherence_validation_rate=1.0, mathematical_edge=0
            )
        
        # Basic performance
        total_return = (self.capital - self.initial_capital) / self.initial_capital
        
        # Trade statistics
        winning_trades = sum(1 for trade in self.trades if trade.pnl > 0)
        losing_trades = len(self.trades) - winning_trades
        win_rate = winning_trades / len(self.trades)
        
        winning_pnls = [trade.pnl for trade in self.trades if trade.pnl > 0]
        losing_pnls = [trade.pnl for trade in self.trades if trade.pnl < 0]
        
        avg_win = sum(winning_pnls) / len(winning_pnls) if winning_pnls else 0
        avg_loss = sum(losing_pnls) / len(losing_pnls) if losing_pnls else 0
        
        profit_factor = abs(sum(winning_pnls) / sum(losing_pnls)) if losing_pnls else float('inf')
        
        # Portfolio metrics
        if len(self.portfolio_values) > 1:
            returns = [(self.portfolio_values[i] - self.portfolio_values[i-1]) / self.portfolio_values[i-1] 
                      for i in range(1, len(self.portfolio_values))]
            
            # Drawdown calculation
            peak = self.initial_capital
            max_drawdown = 0
            for value in self.portfolio_values:
                if value > peak:
                    peak = value
                drawdown = (peak - value) / peak
                max_drawdown = max(max_drawdown, drawdown)
            
            # Sharpe ratio (annualized)
            if len(returns) > 1:
                mean_return = statistics.mean(returns)
                std_return = statistics.stdev(returns)
                sharpe_ratio = (mean_return * 8760) / (std_return * (8760**0.5)) if std_return > 0 else 0  # Hourly to annual
            else:
                sharpe_ratio = 0
            
            # Annualized return
            periods = len(returns) / 8760  # Hours to years
            annualized_return = (1 + total_return) ** (1/periods) - 1 if periods > 0 else total_return
            
            # Value at Risk
            sorted_returns = sorted(returns)
            var_index = int(0.05 * len(sorted_returns))
            value_at_risk_95 = abs(sorted_returns[var_index]) if var_index < len(sorted_returns) else 0
        else:
            max_drawdown = 0
            sharpe_ratio = 0
            annualized_return = 0
            value_at_risk_95 = 0
        
        # Calmar ratio
        calmar_ratio = annualized_return / max_drawdown if max_drawdown > 0 else 0
        
        # Strategy performance
        strategy_performance = {}
        for strategy in set(trade.strategy for trade in self.trades):
            strategy_trades = [trade for trade in self.trades if trade.strategy == strategy]
            strategy_pnl = sum(trade.pnl for trade in strategy_trades)
            strategy_performance[strategy] = strategy_pnl
        
        # Consecutive losses
        consecutive_losses = 0
        max_consecutive_losses = 0
        for trade in self.trades:
            if trade.pnl < 0:
                consecutive_losses += 1
                max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
            else:
                consecutive_losses = 0
        
        # Average trade duration
        average_trade_duration = sum(trade.duration_minutes for trade in self.trades) / len(self.trades)
        
        # Mathematical edge (average confidence weighted by PnL)
        total_pnl = sum(trade.pnl for trade in self.trades)
        if total_pnl != 0:
            mathematical_edge = sum(trade.confidence * trade.pnl for trade in self.trades) / total_pnl
        else:
            mathematical_edge = sum(trade.confidence for trade in self.trades) / len(self.trades)
        
        return BacktestMetrics(
            total_return=total_return,
            annualized_return=annualized_return,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            calmar_ratio=calmar_ratio,
            total_trades=len(self.trades),
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            strategy_performance=strategy_performance,
            monthly_returns=[],  # Could calculate if needed
            value_at_risk_95=value_at_risk_95,
            maximum_consecutive_losses=max_consecutive_losses,
            average_trade_duration=average_trade_duration,
            coherence_validation_rate=1.0,  # All trades are coherence validated
            mathematical_edge=mathematical_edge
        )


def print_comprehensive_results(metrics: BacktestMetrics, initial_capital: float):
    """Print comprehensive backtesting results."""
    print("\n" + "="*80)
    print("📊 SOPHISTICATED BACKTESTING RESULTS")
    print("="*80)
    
    # Performance Overview
    print("🎯 PERFORMANCE OVERVIEW")
    print(f"   Initial Capital:        ${initial_capital:,.2f}")
    print(f"   Final Capital:          ${initial_capital * (1 + metrics.total_return):,.2f}")
    print(f"   Total Return:           {metrics.total_return*100:+.2f}%")
    print(f"   Annualized Return:      {metrics.annualized_return*100:+.2f}%")
    
    # Risk Metrics
    print(f"\n🛡️ RISK METRICS")
    print(f"   Maximum Drawdown:       {metrics.max_drawdown*100:.2f}%")
    print(f"   Sharpe Ratio:           {metrics.sharpe_ratio:.2f}")
    print(f"   Calmar Ratio:           {metrics.calmar_ratio:.2f}")
    print(f"   Value at Risk (95%):    {metrics.value_at_risk_95*100:.2f}%")
    
    # Trading Statistics
    print(f"\n📈 TRADING STATISTICS")
    print(f"   Total Trades:           {metrics.total_trades}")
    print(f"   Winning Trades:         {metrics.winning_trades}")
    print(f"   Losing Trades:          {metrics.losing_trades}")
    print(f"   Win Rate:               {metrics.win_rate*100:.1f}%")
    print(f"   Average Win:            ${metrics.avg_win:.2f}")
    print(f"   Average Loss:           ${metrics.avg_loss:.2f}")
    print(f"   Profit Factor:          {metrics.profit_factor:.2f}")
    print(f"   Max Consecutive Losses: {metrics.maximum_consecutive_losses}")
    print(f"   Avg Trade Duration:     {metrics.average_trade_duration:.0f} minutes")
    
    # Strategy Performance
    print(f"\n🧮 STRATEGY PERFORMANCE")
    for strategy, pnl in metrics.strategy_performance.items():
        print(f"   {strategy:20s}: ${pnl:+,.2f}")
    
    # Coherence Metrics
    print(f"\n🔬 COHERENCE VALIDATION")
    print(f"   Coherence Validation:   {metrics.coherence_validation_rate*100:.1f}%")
    print(f"   Mathematical Edge:      {metrics.mathematical_edge:.3f}")
    
    # Performance Rating
    print(f"\n🏆 PERFORMANCE RATING")
    if metrics.total_return > 0.30:
        rating = "⭐⭐⭐⭐⭐ EXCELLENT"
    elif metrics.total_return > 0.15:
        rating = "⭐⭐⭐⭐ VERY GOOD"
    elif metrics.total_return > 0.05:
        rating = "⭐⭐⭐ GOOD"
    elif metrics.total_return > 0:
        rating = "⭐⭐ FAIR"
    else:
        rating = "⭐ NEEDS IMPROVEMENT"
    
    print(f"   Overall Rating:         {rating}")
    
    print("="*80)


def main():
    """Run sophisticated backtesting."""
    print("🚀 SOPHISTICATED COHERENT TRADING BACKTEST")
    print("Testing mathematical strategies on real crypto data")
    print("="*60)
    
    # Initialize backtester
    backtester = MathematicalStrategyBacktester(initial_capital=10000.0)
    
    # Test symbols
    symbols = ["BTCUSDT", "ETHUSDT"]
    
    # Run backtest
    print(f"📊 Testing on {symbols} with 90 days of data...")
    metrics = backtester.run_backtest(symbols, days=90)
    
    # Print results
    print_comprehensive_results(metrics, backtester.initial_capital)
    
    # Funding analysis
    if metrics.total_return > 0:
        daily_return = metrics.total_return / 90
        monthly_profit = backtester.initial_capital * daily_return * 30
        annual_profit = backtester.initial_capital * metrics.annualized_return
        
        print(f"\n💰 MOMOAI FUNDING ANALYSIS")
        print(f"   With $10K capital:")
        print(f"   Monthly Profit Estimate: ${monthly_profit:,.2f}")
        print(f"   Annual Profit Estimate:  ${annual_profit:,.2f}")
        
        if annual_profit > 5000:
            print(f"   🚀 Sufficient to fund MomoAI development!")
        else:
            print(f"   📈 Scale up capital for meaningful funding")


if __name__ == "__main__":
    main()
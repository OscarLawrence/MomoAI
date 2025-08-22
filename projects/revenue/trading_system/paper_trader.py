"""
Paper Trading Component - Live Strategy Testing
Collaboration-first: Real-time testing without market impact.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum
import threading
import time


class TradeStatus(Enum):
    """Trade execution status."""
    PENDING = "pending"
    FILLED = "filled"
    PARTIAL = "partial"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass
class TradeExecution:
    """
    Trade execution record with collaboration tracking.
    """
    trade_id: str
    symbol: str
    side: str  # 'buy' or 'sell'
    quantity: float
    price: float
    timestamp: datetime
    status: TradeStatus
    fill_price: Optional[float] = None
    fill_quantity: Optional[float] = None
    commission: float = 0.0
    market_impact_score: float = 0.0
    collaboration_rating: float = 1.0  # 1.0 = fully collaborative


class PaperTrader:
    """
    Paper trading engine for risk-free strategy validation.
    Tests collaboration-first trading in real market conditions.
    """
    
    def __init__(self, initial_capital: float = 100000.0):
        """Initialize paper trading environment."""
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions: Dict[str, float] = {}
        self.pending_orders: Dict[str, TradeExecution] = {}
        self.trade_history: List[TradeExecution] = []
        
        # Collaboration tracking
        self.collaboration_score = 1.0
        self.market_impact_total = 0.0
        self.trade_count = 0
        
        # Realistic simulation parameters
        self.commission_rate = 0.001  # 0.1%
        self.slippage_range = 0.0005  # 0.05%
        self.fill_probability = 0.95  # 95% fill rate
        
        # Threading for real-time simulation
        self.is_running = False
        self.market_data_thread = None
        
    def start_trading(self):
        """Start paper trading session."""
        self.is_running = True
        self.market_data_thread = threading.Thread(target=self._market_simulation_loop)
        self.market_data_thread.start()
        print(f"Paper trading started with ${self.initial_capital:,.2f}")
        
    def stop_trading(self):
        """Stop paper trading session."""
        self.is_running = False
        if self.market_data_thread:
            self.market_data_thread.join()
        print("Paper trading stopped")
        
    def submit_order(self, symbol: str, side: str, quantity: float, 
                    price: float, market_impact_score: float = 0.0) -> str:
        """
        Submit paper trade order with collaboration assessment.
        """
        trade_id = f"{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Collaboration check
        collaboration_rating = self._assess_collaboration_impact(
            symbol, side, quantity, price, market_impact_score
        )
        
        if collaboration_rating < 0.3:  # Reject highly disruptive trades
            print(f"Order {trade_id} rejected: Low collaboration rating ({collaboration_rating:.2f})")
            return ""
            
        # Create trade execution record
        trade = TradeExecution(
            trade_id=trade_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price,
            timestamp=datetime.now(),
            status=TradeStatus.PENDING,
            market_impact_score=market_impact_score,
            collaboration_rating=collaboration_rating
        )
        
        self.pending_orders[trade_id] = trade
        print(f"Order submitted: {side} {quantity} {symbol} @ ${price:.2f} (ID: {trade_id})")
        return trade_id
        
    def cancel_order(self, trade_id: str) -> bool:
        """Cancel pending order."""
        if trade_id in self.pending_orders:
            self.pending_orders[trade_id].status = TradeStatus.CANCELLED
            del self.pending_orders[trade_id]
            print(f"Order {trade_id} cancelled")
            return True
        return False
        
    def get_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """Calculate current portfolio value."""
        position_value = sum(
            quantity * current_prices.get(symbol, 0.0)
            for symbol, quantity in self.positions.items()
        )
        return self.cash + position_value
        
    def get_positions(self) -> Dict[str, float]:
        """Get current positions."""
        return self.positions.copy()
        
    def get_trade_history(self) -> List[TradeExecution]:
        """Get complete trade history."""
        return self.trade_history.copy()
        
    def get_performance_metrics(self, current_prices: Dict[str, float]) -> Dict[str, float]:
        """Get performance and collaboration metrics."""
        current_value = self.get_portfolio_value(current_prices)
        total_return = (current_value - self.initial_capital) / self.initial_capital
        
        # Calculate collaboration metrics
        avg_market_impact = (self.market_impact_total / self.trade_count) if self.trade_count > 0 else 0.0
        
        return {
            'portfolio_value': current_value,
            'cash': self.cash,
            'total_return': total_return,
            'total_return_pct': total_return * 100,
            'total_trades': self.trade_count,
            'collaboration_score': self.collaboration_score,
            'avg_market_impact': avg_market_impact,
            'position_count': len(self.positions)
        }
        
    def _assess_collaboration_impact(self, symbol: str, side: str, 
                                   quantity: float, price: float, 
                                   market_impact_score: float) -> float:
        """
        Assess collaboration impact of proposed trade.
        Returns score from 0.0 (harmful) to 1.0 (fully collaborative).
        """
        base_score = 1.0
        
        # Penalize high market impact
        impact_penalty = market_impact_score * 0.5
        base_score -= impact_penalty
        
        # Penalize large position sizes (concentration risk)
        trade_value = quantity * price
        portfolio_value = self.get_portfolio_value({symbol: price})
        position_size_ratio = trade_value / portfolio_value if portfolio_value > 0 else 0
        
        if position_size_ratio > 0.1:  # >10% position
            concentration_penalty = (position_size_ratio - 0.1) * 2
            base_score -= concentration_penalty
            
        # Reward diversification
        if len(self.positions) < 5 and symbol not in self.positions:
            base_score += 0.1  # Diversification bonus
            
        return max(0.0, min(1.0, base_score))
        
    def _market_simulation_loop(self):
        """Simulate market conditions and process orders."""
        while self.is_running:
            try:
                # Process pending orders
                for trade_id, trade in list(self.pending_orders.items()):
                    if self._should_fill_order(trade):
                        self._execute_trade(trade)
                        del self.pending_orders[trade_id]
                        
                time.sleep(1)  # Check every second
                
            except Exception as e:
                print(f"Error in market simulation: {e}")
                
    def _should_fill_order(self, trade: TradeExecution) -> bool:
        """Determine if order should be filled based on market conditions."""
        # Simulate realistic fill probability
        import random
        return random.random() < self.fill_probability
        
    def _execute_trade(self, trade: TradeExecution):
        """Execute trade with realistic slippage and costs."""
        import random
        
        # Simulate slippage
        slippage_factor = 1 + random.uniform(-self.slippage_range, self.slippage_range)
        fill_price = trade.price * slippage_factor
        
        # Calculate costs
        trade_value = trade.quantity * fill_price
        commission = trade_value * self.commission_rate
        
        # Execute based on side
        if trade.side.lower() == 'buy':
            total_cost = trade_value + commission
            if self.cash >= total_cost:
                self.cash -= total_cost
                self.positions[trade.symbol] = self.positions.get(trade.symbol, 0) + trade.quantity
                
                trade.status = TradeStatus.FILLED
                trade.fill_price = fill_price
                trade.fill_quantity = trade.quantity
                trade.commission = commission
                
                print(f"BUY FILLED: {trade.quantity} {trade.symbol} @ ${fill_price:.2f}")
            else:
                trade.status = TradeStatus.REJECTED
                print(f"BUY REJECTED: Insufficient cash for {trade.symbol}")
                
        elif trade.side.lower() == 'sell':
            if self.positions.get(trade.symbol, 0) >= trade.quantity:
                proceeds = trade_value - commission
                self.cash += proceeds
                self.positions[trade.symbol] -= trade.quantity
                
                # Remove position if zero
                if self.positions[trade.symbol] == 0:
                    del self.positions[trade.symbol]
                    
                trade.status = TradeStatus.FILLED
                trade.fill_price = fill_price
                trade.fill_quantity = trade.quantity
                trade.commission = commission
                
                print(f"SELL FILLED: {trade.quantity} {trade.symbol} @ ${fill_price:.2f}")
            else:
                trade.status = TradeStatus.REJECTED
                print(f"SELL REJECTED: Insufficient shares of {trade.symbol}")
                
        # Update collaboration tracking
        if trade.status == TradeStatus.FILLED:
            self.trade_history.append(trade)
            self.trade_count += 1
            self.market_impact_total += trade.market_impact_score
            
            # Update collaboration score (running average)
            self.collaboration_score = (
                (self.collaboration_score * (self.trade_count - 1) + trade.collaboration_rating) 
                / self.trade_count
            )
            
    def generate_trading_report(self, current_prices: Dict[str, float]) -> str:
        """Generate comprehensive trading report."""
        metrics = self.get_performance_metrics(current_prices)
        
        report = f"""
=== PAPER TRADING REPORT ===
Portfolio Value: ${metrics['portfolio_value']:,.2f}
Cash: ${metrics['cash']:,.2f}
Total Return: {metrics['total_return_pct']:.2f}%
Total Trades: {metrics['total_trades']}

=== COLLABORATION METRICS ===
Collaboration Score: {metrics['collaboration_score']:.3f}/1.000
Avg Market Impact: {metrics['avg_market_impact']:.3f}
Position Count: {metrics['position_count']}

=== CURRENT POSITIONS ===
"""
        
        for symbol, quantity in self.positions.items():
            current_price = current_prices.get(symbol, 0.0)
            position_value = quantity * current_price
            report += f"{symbol}: {quantity:.2f} shares @ ${current_price:.2f} = ${position_value:,.2f}\n"
            
        if self.pending_orders:
            report += "\n=== PENDING ORDERS ===\n"
            for trade_id, trade in self.pending_orders.items():
                report += f"{trade.side.upper()} {trade.quantity} {trade.symbol} @ ${trade.price:.2f} (ID: {trade_id})\n"
                
        return report
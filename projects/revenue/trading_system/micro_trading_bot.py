"""
Micro-Trading Bot - $64.10 Capital Deployment System
Implements high-frequency micro-trades for rapid capital multiplication.
"""

import time
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from .technical_analysis import TechnicalAnalyzer, TradingSignal, SignalType
from .risk_management import RiskManager, PositionSizer
from .binance_connector import BinanceConnector, create_binance_connector, OrderResult


@dataclass
class TradingSession:
    """Trading session statistics."""
    start_time: datetime
    start_balance: float
    current_balance: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    total_profit_loss: float
    max_drawdown: float
    active_positions: int


class MicroTradingBot:
    """
    High-frequency micro-trading bot for rapid capital multiplication.
    Target: $64 → $128 → $256 → $512 (exponential growth)
    """
    
    def __init__(self):
        self.connector = create_binance_connector()
        if not self.connector:
            raise ValueError("Failed to initialize Binance connector - check API credentials")
        
        self.analyzer = TechnicalAnalyzer(collaboration_weight=0.2)  # Reduced for profit focus
        self.risk_manager = RiskManager(portfolio_value=1000.0)  # Will update with actual balance
        
        # Trading parameters from TRADING_DEPLOYMENT.md
        self.target_pairs = ["BTCUSDC", "ETHUSDC"]
        self.scan_interval = 60  # 1 minute between scans
        self.max_concurrent_positions = 5
        self.profit_withdrawal_threshold = 100.0  # 100% gains
        
        # Session tracking
        self.session: Optional[TradingSession] = None
        self.trade_history: List[Dict] = []
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('trading_bot.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def start_trading_session(self) -> bool:
        """Initialize a new trading session."""
        try:
            # Get initial account balance
            balances = self.connector.get_account_info()
            # Check for USDC or USDC
            USDC_balance = balances.get("USDC") or balances.get("USDC")
            
            if not USDC_balance or USDC_balance.total < 50.0:
                self.logger.error(f"Insufficient balance to start trading: ${USDC_balance.total if USDC_balance else 0:.2f}")
                return False
            
            self.session = TradingSession(
                start_time=datetime.now(),
                start_balance=USDC_balance.total,
                current_balance=USDC_balance.total,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                total_profit_loss=0.0,
                max_drawdown=0.0,
                active_positions=0
            )
            
            self.logger.info(f"Trading session started with ${USDC_balance.total:.2f} capital")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start trading session: {e}")
            return False
    
    def get_market_data(self, symbol: str) -> Optional[Dict]:
        """Get comprehensive market data for analysis."""
        try:
            # Get kline data for technical analysis
            klines = self.connector.get_kline_data(symbol, "1m", 100)
            if not klines:
                return None
            
            prices = [k["close"] for k in klines]
            volumes = [k["volume"] for k in klines]
            current_price = self.connector.get_current_price(symbol)
            
            if not current_price:
                return None
            
            return {
                "symbol": symbol,
                "prices": prices,
                "volumes": volumes,
                "current_price": current_price,
                "timestamp": datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get market data for {symbol}: {e}")
            return None
    
    def analyze_trading_opportunity(self, market_data: Dict) -> Optional[TradingSignal]:
        """Analyze market data and generate trading signal."""
        try:
            signal = self.analyzer.generate_signal(
                prices=market_data["prices"],
                volumes=market_data["volumes"],
                current_price=market_data["current_price"]
            )
            
            if signal:
                self.logger.info(f"Signal generated for {market_data['symbol']}: "
                               f"{signal.signal_type.value} (confidence: {signal.confidence:.2f})")
            
            return signal
            
        except Exception as e:
            self.logger.error(f"Failed to analyze trading opportunity: {e}")
            return None
    
    def execute_trade(self, signal: TradingSignal, symbol: str) -> bool:
        """Execute a trade based on the signal."""
        try:
            # Check if we can take more positions
            if self.session.active_positions >= self.max_concurrent_positions:
                self.logger.info("Maximum concurrent positions reached, skipping trade")
                return False
            
            # Execute the trade
            result = self.connector.execute_trading_signal(signal, symbol)
            
            if result.success:
                self.session.total_trades += 1
                if result.order_id != "HOLD":
                    self.session.active_positions += 1
                
                # Log trade execution
                trade_record = {
                    "timestamp": datetime.now(),
                    "symbol": symbol,
                    "signal_type": signal.signal_type.value,
                    "confidence": signal.confidence,
                    "order_id": result.order_id,
                    "quantity": result.filled_qty,
                    "price": result.avg_price,
                    "reasoning": signal.reasoning
                }
                
                self.trade_history.append(trade_record)
                
                self.logger.info(f"Trade executed: {signal.signal_type.value} {symbol} "
                               f"@ ${result.avg_price:.4f} (Qty: {result.filled_qty:.6f})")
                return True
            else:
                self.logger.warning(f"Trade execution failed: {result.error_message}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to execute trade: {e}")
            return False
    
    def update_session_stats(self):
        """Update trading session statistics."""
        try:
            if not self.session:
                return
            
            # Get current balance
            balances = self.connector.get_account_info()
            USDC_balance = balances.get("USDC")
            
            if USDC_balance:
                self.session.current_balance = USDC_balance.total
                self.session.total_profit_loss = USDC_balance.total - self.session.start_balance
                
                # Calculate drawdown
                drawdown = (self.session.start_balance - USDC_balance.total) / self.session.start_balance
                self.session.max_drawdown = max(self.session.max_drawdown, drawdown)
                
                # Check profit withdrawal threshold
                profit_percentage = (USDC_balance.total / self.session.start_balance - 1) * 100
                if profit_percentage >= self.profit_withdrawal_threshold:
                    self.logger.info(f"Profit target reached: {profit_percentage:.1f}% gain!")
                    # In a real implementation, you might want to withdraw profits here
            
        except Exception as e:
            self.logger.error(f"Failed to update session stats: {e}")
    
    def print_session_summary(self):
        """Print current session summary."""
        if not self.session:
            return
        
        runtime = datetime.now() - self.session.start_time
        win_rate = (self.session.winning_trades / max(self.session.total_trades, 1)) * 100
        profit_percentage = (self.session.current_balance / self.session.start_balance - 1) * 100
        
        print("\n" + "="*60)
        print("MICRO-TRADING BOT SESSION SUMMARY")
        print("="*60)
        print(f"Runtime: {runtime}")
        print(f"Start Balance: ${self.session.start_balance:.2f}")
        print(f"Current Balance: ${self.session.current_balance:.2f}")
        print(f"Profit/Loss: ${self.session.total_profit_loss:.2f} ({profit_percentage:+.2f}%)")
        print(f"Total Trades: {self.session.total_trades}")
        print(f"Win Rate: {win_rate:.1f}%")
        print(f"Max Drawdown: {self.session.max_drawdown:.2f}%")
        print(f"Active Positions: {self.session.active_positions}")
        print("="*60)
    
    def run_trading_cycle(self):
        """Run one complete trading cycle across all target pairs."""
        for symbol in self.target_pairs:
            try:
                # Get market data
                market_data = self.get_market_data(symbol)
                if not market_data:
                    continue
                
                # Analyze for trading opportunities
                signal = self.analyze_trading_opportunity(market_data)
                if not signal:
                    continue
                
                # Execute trade if signal is strong enough
                if signal.confidence >= 0.7:  # High confidence threshold for live trading
                    self.execute_trade(signal, symbol)
                
            except Exception as e:
                self.logger.error(f"Error in trading cycle for {symbol}: {e}")
        
        # Update session statistics
        self.update_session_stats()
    
    def run(self, duration_hours: int = 24):
        """Run the trading bot for specified duration."""
        if not self.start_trading_session():
            return False
        
        self.logger.info(f"Starting micro-trading bot for {duration_hours} hours")
        
        end_time = datetime.now() + timedelta(hours=duration_hours)
        
        try:
            while datetime.now() < end_time:
                # Run trading cycle
                self.run_trading_cycle()
                
                # Print periodic updates
                if self.session.total_trades % 10 == 0 and self.session.total_trades > 0:
                    self.print_session_summary()
                
                # Wait before next cycle
                time.sleep(self.scan_interval)
                
        except KeyboardInterrupt:
            self.logger.info("Trading bot stopped by user")
        except Exception as e:
            self.logger.error(f"Trading bot error: {e}")
        finally:
            self.print_session_summary()
            self.logger.info("Trading session ended")
        
        return True


if __name__ == "__main__":
    # Quick test run
    bot = MicroTradingBot()
    bot.run(duration_hours=1)  # Run for 1 hour test
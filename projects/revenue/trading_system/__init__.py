"""
Trading Algorithm Framework - Revenue Generation System
Micro-component architecture for rapid deployment and monetization.
"""

from .technical_analysis import TechnicalAnalyzer, TradingSignal
from .risk_management import RiskManager, PositionSizer
from .backtesting_engine import BacktestEngine, BacktestResult
from .paper_trader import PaperTrader, TradeExecution
from .binance_connector import BinanceConnector, create_binance_connector
from .micro_trading_bot import MicroTradingBot

__all__ = [
    'TechnicalAnalyzer', 'TradingSignal',
    'RiskManager', 'PositionSizer', 
    'BacktestEngine', 'BacktestResult',
    'PaperTrader', 'TradeExecution',
    'BinanceConnector', 'create_binance_connector',
    'MicroTradingBot'
]

__version__ = "1.0.0"
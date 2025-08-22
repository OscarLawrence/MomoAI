"""
Binance API Integration Component - Live Trading Execution
Micro-component for real-time trading with $64.10 capital deployment.
"""

import os
import time
import hmac
import hashlib
import requests
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime
from .technical_analysis import TradingSignal, SignalType


@dataclass
class BinanceCredentials:
    """Secure credential management for Binance API."""
    api_key: str
    api_secret: str
    testnet: bool = True  # Start with testnet for safety


@dataclass
class OrderResult:
    """Result of order execution."""
    success: bool
    order_id: Optional[str]
    filled_qty: float
    avg_price: float
    error_message: Optional[str]


@dataclass
class AccountBalance:
    """Account balance information."""
    asset: str
    free: float
    locked: float
    total: float


class BinanceConnector:
    """
    Binance API connector for micro-trading strategy execution.
    Implements the $64.10 capital deployment with risk controls.
    """
    
    def __init__(self, credentials: BinanceCredentials):
        self.credentials = credentials
        self.base_url = "https://testnet.binance.vision" if credentials.testnet else "https://api.binance.com"
        self.session = requests.Session()
        self.session.headers.update({
            'X-MBX-APIKEY': credentials.api_key
        })
        
        # Trading parameters from TRADING_DEPLOYMENT.md
        self.max_risk_per_trade = 0.02  # 2% max risk
        self.stop_loss_threshold = 0.01  # 1% stop loss
        self.position_size_range = (10.0, 20.0)  # $10-20 per trade
        self.emergency_stop_threshold = 50.0  # Emergency stop if capital < $50
        self.max_concurrent_positions = 5
        self.target_pairs = ["BTCUSDC", "ETHUSDC"]  # High-volume, low-spread pairs
        
    def _generate_signature(self, query_string: str) -> str:
        """Generate HMAC SHA256 signature for authenticated requests."""
        return hmac.new(
            self.credentials.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None, signed: bool = False) -> Dict:
        """Make authenticated request to Binance API."""
        if params is None:
            params = {}
            
        if signed:
            params['timestamp'] = int(time.time() * 1000)
            query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
            params['signature'] = self._generate_signature(query_string)
        
        url = f"{self.base_url}/api/v3/{endpoint}"
        
        try:
            if method == "GET":
                response = self.session.get(url, params=params)
            elif method == "POST":
                response = self.session.post(url, params=params)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
    
    def get_account_info(self) -> Dict[str, AccountBalance]:
        """Get current account balances."""
        result = self._make_request("GET", "account", signed=True)
        
        if "error" in result:
            return {}
            
        balances = {}
        for balance in result.get("balances", []):
            asset = balance["asset"]
            free = float(balance["free"])
            locked = float(balance["locked"])
            
            if free > 0 or locked > 0:  # Only include non-zero balances
                balances[asset] = AccountBalance(
                    asset=asset,
                    free=free,
                    locked=locked,
                    total=free + locked
                )
        
        return balances
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for a trading pair."""
        result = self._make_request("GET", "ticker/price", {"symbol": symbol})
        
        if "error" in result or "price" not in result:
            return None
            
        return float(result["price"])
    
    def get_kline_data(self, symbol: str, interval: str = "1m", limit: int = 100) -> List[Dict]:
        """Get historical kline/candlestick data."""
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        }
        
        result = self._make_request("GET", "klines", params)
        
        if "error" in result:
            return []
            
        klines = []
        for kline in result:
            klines.append({
                "open_time": int(kline[0]),
                "open": float(kline[1]),
                "high": float(kline[2]),
                "low": float(kline[3]),
                "close": float(kline[4]),
                "volume": float(kline[5]),
                "close_time": int(kline[6])
            })
        
        return klines
    
    def calculate_position_size(self, signal: TradingSignal, available_balance: float) -> float:
        """Calculate position size based on risk management rules."""
        # Ensure we don't exceed position size limits
        max_position = min(self.position_size_range[1], available_balance * self.max_risk_per_trade)
        min_position = min(self.position_size_range[0], max_position)
        
        # Adjust based on signal confidence
        confidence_multiplier = min(signal.confidence, 1.0)
        position_size = min_position + (max_position - min_position) * confidence_multiplier
        
        return round(position_size, 2)
    
    def place_market_order(self, symbol: str, side: str, quantity: float) -> OrderResult:
        """Place a market order."""
        params = {
            "symbol": symbol,
            "side": side.upper(),
            "type": "MARKET",
            "quantity": f"{quantity:.6f}",
            "newOrderRespType": "FULL"
        }
        
        result = self._make_request("POST", "order", params, signed=True)
        
        if "error" in result:
            return OrderResult(
                success=False,
                order_id=None,
                filled_qty=0.0,
                avg_price=0.0,
                error_message=result["error"]
            )
        
        # Parse successful order response
        filled_qty = float(result.get("executedQty", 0))
        avg_price = 0.0
        
        if "fills" in result and result["fills"]:
            total_value = sum(float(fill["price"]) * float(fill["qty"]) for fill in result["fills"])
            avg_price = total_value / filled_qty if filled_qty > 0 else 0.0
        
        return OrderResult(
            success=True,
            order_id=result.get("orderId"),
            filled_qty=filled_qty,
            avg_price=avg_price,
            error_message=None
        )
    
    def execute_trading_signal(self, signal: TradingSignal, symbol: str) -> OrderResult:
        """Execute a trading signal with full risk management."""
        # Get current account balance
        balances = self.get_account_info()
        # Check for USDC or USDC
        USDC_balance = balances.get("USDC") or balances.get("USDC", AccountBalance("USDC", 0, 0, 0))
        
        # Emergency stop check
        if USDC_balance.total < self.emergency_stop_threshold:
            return OrderResult(
                success=False,
                order_id=None,
                filled_qty=0.0,
                avg_price=0.0,
                error_message=f"Emergency stop: Balance ${USDC_balance.total:.2f} below ${self.emergency_stop_threshold}"
            )
        
        # Calculate position size
        position_size_usd = self.calculate_position_size(signal, USDC_balance.free)
        current_price = self.get_current_price(symbol)
        
        if not current_price:
            return OrderResult(
                success=False,
                order_id=None,
                filled_qty=0.0,
                avg_price=0.0,
                error_message="Could not get current price"
            )
        
        # Calculate quantity based on position size
        if signal.signal_type in [SignalType.BUY, SignalType.STRONG_BUY]:
            quantity = position_size_usd / current_price
            side = "BUY"
        elif signal.signal_type in [SignalType.SELL, SignalType.STRONG_SELL]:
            # For sell orders, we need to check if we have the asset
            base_asset = symbol.replace("USDC", "")
            asset_balance = balances.get(base_asset, AccountBalance(base_asset, 0, 0, 0))
            quantity = min(asset_balance.free, position_size_usd / current_price)
            side = "SELL"
            
            if quantity <= 0:
                return OrderResult(
                    success=False,
                    order_id=None,
                    filled_qty=0.0,
                    avg_price=0.0,
                    error_message=f"Insufficient {base_asset} balance for sell order"
                )
        else:
            # HOLD signal - no action
            return OrderResult(
                success=True,
                order_id="HOLD",
                filled_qty=0.0,
                avg_price=current_price,
                error_message=None
            )
        
        # Execute the order
        return self.place_market_order(symbol, side, quantity)


def create_binance_connector() -> Optional[BinanceConnector]:
    """Factory function to create Binance connector from environment variables."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # dotenv not available, assume env vars already set
    
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    testnet = os.getenv("BINANCE_TESTNET", "true").lower() == "true"
    
    if not api_key or not api_secret:
        print("ERROR: Binance API credentials not found in environment variables.")
        print("Please set BINANCE_API_KEY and BINANCE_API_SECRET")
        return None
    
    credentials = BinanceCredentials(
        api_key=api_key,
        api_secret=api_secret,
        testnet=testnet
    )
    
    return BinanceConnector(credentials)
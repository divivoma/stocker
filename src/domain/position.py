from dataclasses import dataclass
from typing import Optional
from enum import Enum


class TriggerStatus(Enum):
    NONE = "none"
    NEAR_TAKE_PROFIT = "near_take_profit"
    NEAR_STOP_LOSS = "near_stop_loss"
    TAKE_PROFIT_HIT = "take_profit_hit"
    STOP_LOSS_HIT = "stop_loss_hit"


@dataclass
class Position:
    ticker: str
    entry_price: float
    quantity: float
    take_profit_pct: float  # e.g., 0.20 for 20%
    stop_loss_pct: float    # e.g., 0.10 for 10% (stored as positive)

    def calculate_pnl(self, current_price: float) -> dict:
        """
        Calculate unrealized P&L and trigger proximity.
        Returns dict with all position metrics.
        """
        if not current_price or current_price <= 0:
            return {
                "unrealized_pnl": None,
                "unrealized_pnl_pct": None,
                "trigger_status": TriggerStatus.NONE,
                "trigger_proximity_pct": None,
                "take_profit_price": None,
                "stop_loss_price": None,
            }

        # Calculate P&L
        unrealized_pnl = (current_price - self.entry_price) * self.quantity
        unrealized_pnl_pct = (current_price - self.entry_price) / self.entry_price

        # Calculate trigger prices
        take_profit_price = self.entry_price * (1 + self.take_profit_pct)
        stop_loss_price = self.entry_price * (1 - self.stop_loss_pct)

        # Determine trigger status and proximity
        trigger_status = TriggerStatus.NONE
        trigger_proximity_pct = None

        if current_price >= take_profit_price:
            trigger_status = TriggerStatus.TAKE_PROFIT_HIT
            trigger_proximity_pct = 0.0
        elif current_price <= stop_loss_price:
            trigger_status = TriggerStatus.STOP_LOSS_HIT
            trigger_proximity_pct = 0.0
        else:
            # Calculate proximity to nearest trigger
            dist_to_tp = (take_profit_price - current_price) / current_price
            dist_to_sl = (current_price - stop_loss_price) / current_price

            if dist_to_tp <= 0.05:  # Within 5% of take profit
                trigger_status = TriggerStatus.NEAR_TAKE_PROFIT
                trigger_proximity_pct = dist_to_tp
            elif dist_to_sl <= 0.05:  # Within 5% of stop loss
                trigger_status = TriggerStatus.NEAR_STOP_LOSS
                trigger_proximity_pct = dist_to_sl
            else:
                # Report distance to take profit as default
                trigger_proximity_pct = dist_to_tp

        return {
            "unrealized_pnl": unrealized_pnl,
            "unrealized_pnl_pct": unrealized_pnl_pct,
            "trigger_status": trigger_status,
            "trigger_proximity_pct": trigger_proximity_pct,
            "take_profit_price": take_profit_price,
            "stop_loss_price": stop_loss_price,
        }


def format_trigger_status(status: TriggerStatus, proximity_pct: Optional[float]) -> str:
    """Format trigger status for UI display."""
    if status == TriggerStatus.TAKE_PROFIT_HIT:
        return "🎯 Take Profit Hit!"
    elif status == TriggerStatus.STOP_LOSS_HIT:
        return "⛔ Stop Loss Hit!"
    elif status == TriggerStatus.NEAR_TAKE_PROFIT:
        return f"📈 {proximity_pct*100:.1f}% to Take Profit"
    elif status == TriggerStatus.NEAR_STOP_LOSS:
        return f"📉 {proximity_pct*100:.1f}% to Stop Loss"
    elif proximity_pct is not None:
        return f"{proximity_pct*100:.1f}% to Take Profit"
    return "--"

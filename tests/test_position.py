import pytest
from src.domain.position import Position, TriggerStatus, format_trigger_status


class TestPosition:
    def test_calculate_pnl_positive(self):
        """Test P&L calculation with profit."""
        position = Position(
            ticker="NVDA",
            entry_price=100.0,
            quantity=10,
            take_profit_pct=0.20,
            stop_loss_pct=0.10,
        )
        result = position.calculate_pnl(current_price=115.0)

        assert result["unrealized_pnl"] == 150.0  # (115-100) * 10
        assert result["unrealized_pnl_pct"] == 0.15  # 15%
        assert result["take_profit_price"] == 120.0
        assert result["stop_loss_price"] == 90.0

    def test_calculate_pnl_negative(self):
        """Test P&L calculation with loss."""
        position = Position(
            ticker="NVDA",
            entry_price=100.0,
            quantity=10,
            take_profit_pct=0.20,
            stop_loss_pct=0.10,
        )
        result = position.calculate_pnl(current_price=95.0)

        assert result["unrealized_pnl"] == -50.0  # (95-100) * 10
        assert result["unrealized_pnl_pct"] == -0.05  # -5%

    def test_take_profit_hit(self):
        """Test when take profit is triggered."""
        position = Position(
            ticker="NVDA",
            entry_price=100.0,
            quantity=10,
            take_profit_pct=0.20,
            stop_loss_pct=0.10,
        )
        result = position.calculate_pnl(current_price=125.0)

        assert result["trigger_status"] == TriggerStatus.TAKE_PROFIT_HIT
        assert result["trigger_proximity_pct"] == 0.0

    def test_stop_loss_hit(self):
        """Test when stop loss is triggered."""
        position = Position(
            ticker="NVDA",
            entry_price=100.0,
            quantity=10,
            take_profit_pct=0.20,
            stop_loss_pct=0.10,
        )
        result = position.calculate_pnl(current_price=85.0)

        assert result["trigger_status"] == TriggerStatus.STOP_LOSS_HIT
        assert result["trigger_proximity_pct"] == 0.0

    def test_near_take_profit(self):
        """Test when price is near take profit (within 5%)."""
        position = Position(
            ticker="NVDA",
            entry_price=100.0,
            quantity=10,
            take_profit_pct=0.20,
            stop_loss_pct=0.10,
        )
        result = position.calculate_pnl(current_price=117.0)  # 2.5% from TP at 120

        assert result["trigger_status"] == TriggerStatus.NEAR_TAKE_PROFIT

    def test_near_stop_loss(self):
        """Test when price is near stop loss (within 5%)."""
        position = Position(
            ticker="NVDA",
            entry_price=100.0,
            quantity=10,
            take_profit_pct=0.20,
            stop_loss_pct=0.10,
        )
        result = position.calculate_pnl(current_price=92.0)  # ~2% from SL at 90

        assert result["trigger_status"] == TriggerStatus.NEAR_STOP_LOSS

    def test_invalid_price(self):
        """Test handling of invalid/missing price."""
        position = Position(
            ticker="NVDA",
            entry_price=100.0,
            quantity=10,
            take_profit_pct=0.20,
            stop_loss_pct=0.10,
        )
        result = position.calculate_pnl(current_price=None)

        assert result["unrealized_pnl"] is None
        assert result["trigger_status"] == TriggerStatus.NONE


class TestFormatTriggerStatus:
    def test_take_profit_hit(self):
        text = format_trigger_status(TriggerStatus.TAKE_PROFIT_HIT, 0.0)
        assert "Take Profit Hit" in text

    def test_stop_loss_hit(self):
        text = format_trigger_status(TriggerStatus.STOP_LOSS_HIT, 0.0)
        assert "Stop Loss Hit" in text

    def test_near_take_profit(self):
        text = format_trigger_status(TriggerStatus.NEAR_TAKE_PROFIT, 0.03)
        assert "3.0%" in text
        assert "Take Profit" in text

    def test_near_stop_loss(self):
        text = format_trigger_status(TriggerStatus.NEAR_STOP_LOSS, 0.02)
        assert "2.0%" in text
        assert "Stop Loss" in text

    def test_none_status(self):
        text = format_trigger_status(TriggerStatus.NONE, None)
        assert text == "--"

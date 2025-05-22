import numpy as np
import pandas as pd
import pytest

from backend.src.modules.indicators import (calculate_ema,
                                            calculate_indicators,
                                            calculate_rsi)


@pytest.fixture
def sample_data():
    """Test data för indikatorberäkningar"""
    return pd.DataFrame(
        {
            "datetime": pd.date_range(start="2024-01-01", periods=100, freq="1H"),
            "open": np.random.randn(100).cumsum() + 100,
            "high": np.random.randn(100).cumsum() + 102,
            "low": np.random.randn(100).cumsum() + 98,
            "close": np.random.randn(100).cumsum() + 100,
            "volume": np.random.randint(1000, 10000, 100),
        }
    )


@pytest.mark.indicators
class TestIndicators:
    """Test för tekniska indikatorer"""

    @pytest.mark.unit
    def test_calculate_indicators(self, sample_data):
        """Test beräkning av alla indikatorer"""
        result = calculate_indicators(
            sample_data,
            ema_length=20,
            volume_multiplier=1.5,
            trading_start_hour=9,
            trading_end_hour=17,
        )

        assert "ema" in result.columns
        assert "atr" in result.columns
        assert "rsi" in result.columns
        assert "adx" in result.columns
        assert "high_volume" in result.columns
        assert "within_trading_hours" in result.columns

    @pytest.mark.unit
    def test_calculate_ema(self, sample_data):
        """Test EMA-beräkning"""
        ema = calculate_ema(sample_data["close"], 20)
        assert len(ema) == len(sample_data)
        assert not np.isnan(ema).all()

    @pytest.mark.unit
    def test_calculate_rsi(self, sample_data):
        """Test RSI-beräkning"""
        rsi = calculate_rsi(sample_data["close"], 14)
        assert len(rsi) == len(sample_data)
        assert not np.isnan(rsi).all()
        assert all(0 <= x <= 100 for x in rsi if not np.isnan(x))

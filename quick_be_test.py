import asyncio
import json
from datetime import datetime, timedelta
import argparse

from app.services.backtest_engine import BacktestEngine, BacktestConfig


class _Agg:
    value = 'MODERATE'


class _StubManager:
    current_aggressiveness = _Agg()

    async def initialize(self):
        return True

    def set_strategy_config(self, cfg):
        return None


class _SimpleStrategyConfig:
    def get_current_config(self):
        return {
            'strategy_type': 'adaptive',
            'aggressiveness': 'moderate',
            'ai_mode': 'semi_auto'
        }


async def run_once(symbol: str, timeframe: str, days: int):
    cfg = BacktestConfig(initial_capital=10000.0)
    engine = BacktestEngine(cfg)
    engine.strategy_manager = _StubManager()

    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    res = await engine.run_backtest(
        _SimpleStrategyConfig(),
        [symbol],
        start_date,
        end_date,
        timeframe
    )

    metrics = res.get('metrics', {})
    out = {
        'symbol': symbol,
        'timeframe': timeframe,
        'days': days,
        'metrics': metrics,
        'summary': res.get('summary', {})
    }
    print(json.dumps(out, ensure_ascii=False))


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--symbol', default='BTCUSDT')
    parser.add_argument('--timeframe', default='1h')
    parser.add_argument('--days', type=int, default=30)
    args = parser.parse_args()

    await run_once(args.symbol, args.timeframe, args.days)


if __name__ == '__main__':
    asyncio.run(main())

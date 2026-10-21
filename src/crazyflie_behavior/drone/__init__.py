"""The drone interface, the telemetry buffer and the adapters behind them.

Only the safety layer and the tick loop use this package; behaviors never
import it (ADR-0008).
"""

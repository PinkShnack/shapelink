
from .. import test_sorting_features as tsf


def test_benchmark_simulator_sorting_send_features(benchmark):
    """Benchmark `test_rtdc_sorting_send_features`"""
    benchmark.pedantic(tsf.test_rtdc_sorting_send_features,
                       rounds=5, iterations=1)


def test_benchmark_simulator_sorting_gate(benchmark):
    """Benchmark `test_rtdc_sorting_gate`"""
    benchmark.pedantic(tsf.test_rtdc_sorting_gate,
                       rounds=5, iterations=1)

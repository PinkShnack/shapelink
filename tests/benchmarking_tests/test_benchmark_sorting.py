
from tests import test_sorting_features as tsf


def test_benchmark_simulator_sorting_send_features(benchmark):
    """Benchmark `test_feature_transfer_speed_single_scalar`"""
    benchmark.pedantic(tsf.test_rtdc_sorting_send_features,
                       rounds=5, iterations=1)


def test_benchmark_simulator_sorting_gate(benchmark):
    """Benchmark `test_feature_transfer_speed_single_scalar`"""
    benchmark.pedantic(tsf.test_rtdc_sorting_gate,
                       rounds=5, iterations=1)

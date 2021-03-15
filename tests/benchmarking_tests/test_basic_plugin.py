
from tests import test_basic


def test_benchmark_simulator(benchmark):
    benchmark(test_basic.test_run_plugin_with_simulator)

# def test_benchmark_simulator_ped(benchmark):
#     benchmark.pedantic(test_basic.test_run_plugin_with_simulator,
#                        iterations=5, rounds=5)

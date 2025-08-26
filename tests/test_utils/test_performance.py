from industrialstats.utils.performance import profile_function


def sample_func():
    total = 0
    for i in range(1000):
        total += i
    return total


def test_profile_function():
    stats = profile_function(sample_func)
    assert stats.total_calls > 0

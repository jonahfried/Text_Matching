import cProfile
import pstats
from matching import *
import matching_concurrent

print("CURRENT VERSION:")
cProfile.run('main()', "matching_stats")
p = pstats.Stats('matching_stats')
p.strip_dirs().sort_stats('cumtime').print_stats(20)

print("COMPARISON VERSION:")
cProfile.run("matching_concurrent.main()", "matching_stats")
p = pstats.Stats('matching_stats')
p.strip_dirs().sort_stats('cumtime').print_stats(20)

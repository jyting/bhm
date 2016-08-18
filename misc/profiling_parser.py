import cProfile
import pstats
import sys

stat_dir = 'stats/'

def get_stats(stat_file):
    stat_path = stat_dir + stat_file
    p = pstats.Stats(stat_path)
    p.sort_stats('cumtime').print_stats(15)
    return p

print(sys.argv)
print(len(sys.argv))
if len(sys.argv) <= 1:
    print("Please enter profile file in stats folder to read")
    sys.exit(0)
# 
# # stat_file = 'profile_fixed_dK_evals_20points'
# # stat_file = 'toydata.profile'
stat_file = sys.argv[1]

p = get_stats(stat_file)

import numpy as np
import config as cf
import matrix_DX7 as md

mix = md.generate_from_config(cf.config)
print('mix shape:', mix.shape)
print('max abs:', np.max(np.abs(mix)))
print('max:', np.max(mix))
print('min:', np.min(mix))
print('mean:', np.mean(mix))
print('nonzero count:', np.count_nonzero(mix))
# save small diagnostics
with open('mix_stats.txt', 'w') as f:
    f.write('\n'.join([f"{k}: {v}" for k,v in {
        'shape': mix.shape,
        'max_abs': float(np.max(np.abs(mix))),
        'max': float(np.max(mix)),
        'min': float(np.min(mix)),
        'mean': float(np.mean(mix)),
        'nonzero': int(np.count_nonzero(mix))
    }.items()]))

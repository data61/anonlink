from array import array
from itertools import repeat
from operator import itemgetter

def dice_coefficient_python(datasets, threshold, k=None):
    """Pure python method for determining Bloom Filter similarity

    Both arguments are 3-tuples - bitarray with bloom filter for record, index of record, bitcount

    :return: A list of tuples *k* for each entity in filters1.
    The tuple comprises:
        - the index in filters1
        - the similarity score between 0 and 1 of the k matches above threshold
        - The index in filters2 of the best match
    """
    n_datasets = len(datasets)
    if n_datasets < 2:
        raise ValueError(f'not enough datasets (expected 2, got {n_datasets})')
    elif n_datasets > 2:
        raise ValueError(f'too many datasets (expected 2, got {n_datasets})')
    filters0, filters1 = datasets

    result_sims = array('d')
    result_indices0 = array('I')
    result_indices1 = array('I')

    if not filters0 or not filters1:
        # Empty result of the correct type.
        return result_sims, (result_indices0, result_indices1)

    f1_counts = tuple(f1.count() for f1 in filters1)

    for i, f0 in enumerate(filters0):
        f0_count = f0.count()
        if f0_count:
            coeffs = (2 * (f0 & f1).count() / (f0_count + f1_count)
                      for f1, f1_count in zip(filters1, f1_counts))
        else:  # Avoid division by zero.
            coeffs = repeat(0., len(filters1))
        
        cands = filter(lambda c: c[1] >= threshold, enumerate(coeffs))
        top_k = sorted(cands, key=itemgetter(1), reverse=True)[:k]

        result_sims.extend(sim for _, sim in top_k)
        result_indices0.extend(repeat(i, len(top_k)))
        result_indices1.extend(j for j, _ in top_k)
    
    return result_sims, (result_indices0, result_indices1)

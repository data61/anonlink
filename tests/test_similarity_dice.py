import pytest
from bitarray import bitarray
from clkhash import bloomfilter, randomnames
from clkhash.key_derivation import generate_key_lists
from hypothesis import given, strategies

import anonlink.similarities
from anonlink import similarities

FLOAT_ARRAY_TYPES = 'fd'
UINT_ARRAY_TYPES = 'BHILQ'

SIM_FUNS = [similarities.dice_coefficient_python,
            similarities.dice_coefficient_accelerated]


class TestBloomFilterComparison:
    @classmethod
    def setup_class(cls):
        cls.proportion = 0.8
        nl = randomnames.NameList(300)
        s1, s2 = nl.generate_subsets(200, cls.proportion)

        keys = generate_key_lists('secret', len(nl.schema_types))
        cls.filters1 = tuple(
            f[0]
            for f in bloomfilter.stream_bloom_filters(s1, keys, nl.SCHEMA))
        cls.filters2 = tuple(
            f[0]
            for f in bloomfilter.stream_bloom_filters(s2, keys, nl.SCHEMA))
        cls.filters = cls.filters1, cls.filters2

        cls.default_k = 10
        cls.default_threshold = 0.5

    def _check_proportion(self, candidate_pairs):
        sims, _ = candidate_pairs
        exact_matches = sum(sim == 1 for sim in sims)

        assert (exact_matches / len(self.filters1)
                == pytest.approx(self.proportion))
        assert (exact_matches / len(self.filters2)
                == pytest.approx(self.proportion))

    def assert_similarity_matrices_equal(self, M, N):
        M_sims, (M_indices0, M_indices1) = M
        N_sims, (N_indices0, N_indices1) = N
        assert (set(zip(M_sims, M_indices0, M_indices1))
                == set(zip(N_sims, N_indices0, N_indices1)))

    def test_accelerated_manual(self):
        nl = randomnames.NameList(30)
        s1, s2 = nl.generate_subsets(5, 1.0)
        keys = generate_key_lists('secret', len(nl.schema_types))
        f1 = tuple(
            f[0]
            for f in bloomfilter.stream_bloom_filters(s1, keys, nl.SCHEMA))
        f2 = tuple(
            f[0]
            for f in bloomfilter.stream_bloom_filters(s2, keys, nl.SCHEMA))

        py_similarity = similarities.dice_coefficient_python(
            (f1, f2), self.default_threshold, self.default_k)
        c_similarity = similarities.dice_coefficient_accelerated(
            (f1, f2), self.default_threshold, self.default_k)
        self.assert_similarity_matrices_equal(py_similarity, c_similarity)

    def test_accelerated(self):
        similarity = similarities.dice_coefficient_accelerated(
            self.filters, self.default_threshold, self.default_k)
        self._check_proportion(similarity)

    def test_python(self):
        similarity = similarities.dice_coefficient_python(
            self.filters, self.default_threshold, self.default_k)
        self._check_proportion(similarity)

    def test_default(self):
        similarity = similarities.dice_coefficient(
            self.filters, self.default_threshold, self.default_k)
        self._check_proportion(similarity)

    def test_same_score(self):
        c_cands = similarities.dice_coefficient_accelerated(
            self.filters, self.default_threshold, self.default_k)
        c_scores, _ = c_cands
        python_cands = similarities.dice_coefficient_python(
            self.filters, self.default_threshold, self.default_k)
        python_scores, _ = python_cands
        assert c_scores == python_scores

    def test_same_score_k_none(self):
        c_cands = similarities.dice_coefficient_accelerated(
            self.filters, self.default_threshold, None)
        c_scores, _ = c_cands
        python_cands = similarities.dice_coefficient_python(
            self.filters, self.default_threshold, None)
        python_scores, _ = python_cands
        assert c_scores == python_scores

    def test_empty_input_a(self):
        candidate_pairs = similarities.dice_coefficient(
            ((), self.filters2), self.default_threshold, self.default_k)
        sims, (indices0, indices1) = candidate_pairs
        assert len(sims) == len(indices0) == len(indices1) == 0
        assert sims.typecode in FLOAT_ARRAY_TYPES
        assert indices0.typecode in UINT_ARRAY_TYPES
        assert indices1.typecode in UINT_ARRAY_TYPES

    def test_empty_input_b(self):
        candidate_pairs = similarities.dice_coefficient(
            (self.filters1, ()), self.default_threshold, self.default_k)
        sims, (indices0, indices1) = candidate_pairs
        assert len(sims) == len(indices0) == len(indices1) == 0
        assert sims.typecode in FLOAT_ARRAY_TYPES
        assert indices0.typecode in UINT_ARRAY_TYPES
        assert indices1.typecode in UINT_ARRAY_TYPES

    def test_small_input_a(self):
        py_similarity = similarities.dice_coefficient_python(
            (self.filters1[:10], self.filters2),
            self.default_threshold, self.default_k)
        c_similarity = similarities.dice_coefficient_accelerated(
            (self.filters1[:10], self.filters2),
            self.default_threshold, self.default_k)
        self.assert_similarity_matrices_equal(py_similarity, c_similarity)

    def test_small_input_b(self):
        py_similarity = similarities.dice_coefficient_python(
            (self.filters1, self.filters2[:10]),
            self.default_threshold, self.default_k)
        c_similarity = similarities.dice_coefficient_accelerated(
            (self.filters1, self.filters2[:10]),
            self.default_threshold, self.default_k)
        self.assert_similarity_matrices_equal(py_similarity, c_similarity)

    def test_memory_use(self):
        n = 10
        f1 = self.filters1[:n]
        f2 = self.filters2[:n]
        # If memory is not handled correctly, then this would allocate
        # several terabytes of RAM.
        big_k = 1 << 50
        py_similarity = similarities.dice_coefficient_python(
            (f1, f2), self.default_threshold, big_k)
        c_similarity = similarities.dice_coefficient_accelerated(
            (f1, f2), self.default_threshold, big_k)
        self.assert_similarity_matrices_equal(py_similarity, c_similarity)

    @pytest.mark.parametrize('sim_fun', SIM_FUNS)
    @pytest.mark.parametrize('dataset_n', [0, 1])
    @pytest.mark.parametrize('k', [None, 0, 1, 2, 3, 5])
    @pytest.mark.parametrize('threshold', [0., .5, 1.])
    def test_too_few_datasets(self, sim_fun, dataset_n, k, threshold):
        datasets = [[bitarray('01001011') * 8, bitarray('01001011' * 8)]
                    for _ in range(dataset_n)]
        with pytest.raises(ValueError):
            sim_fun(datasets, threshold, k=k)

    @pytest.mark.parametrize('sim_fun', SIM_FUNS)
    @pytest.mark.parametrize('p_arity', [3, 5])
    @pytest.mark.parametrize('k', [None, 0, 1, 2])
    @pytest.mark.parametrize('threshold', [0., .5, 1.])
    def test_unsupported_p_arity(self, sim_fun, p_arity, k, threshold):
        datasets = [[bitarray('01001011') * 8, bitarray('01001011' * 8)]
                    for _ in range(p_arity)]
        with pytest.raises(NotImplementedError):
            sim_fun(datasets, threshold, k=k)
    
    @pytest.mark.parametrize('sim_fun', SIM_FUNS)
    @pytest.mark.parametrize('k', [None, 0, 1, 2, 3, 5])
    @pytest.mark.parametrize('threshold', [0., .5, 1.])
    def test_inconsistent_filter_length(self, sim_fun, k, threshold):
        datasets = [[bitarray('01001011') * 8, bitarray('01001011') * 16],
                    [bitarray('01001011') * 8, bitarray('01001011') * 8]]
        with pytest.raises(ValueError):
            sim_fun(datasets, threshold, k=k)

        datasets = [[bitarray('01001011') * 16, bitarray('01001011') * 8],
                    [bitarray('01001011') * 8, bitarray('01001011') * 8]]
        with pytest.raises(ValueError):
            sim_fun(datasets, threshold, k=k)
            
        datasets = [[bitarray('01001011') * 8, bitarray('01001011') * 8],
                    [bitarray('01001011') * 16, bitarray('01001011') * 8]]
        with pytest.raises(ValueError):
            sim_fun(datasets, threshold, k=k)
            
        datasets = [[bitarray('01001011') * 16, bitarray('01001011') * 8],
                    [bitarray('01001011') * 8, bitarray('01001011') * 16]]
        with pytest.raises(ValueError):
            sim_fun(datasets, threshold, k=k)
            
        datasets = [[bitarray('01001011') * 16, bitarray('01001011') * 8],
                    [bitarray('01001011') * 16, bitarray('01001011') * 8]]
        with pytest.raises(ValueError):
            sim_fun(datasets, threshold, k=k)
            
        datasets = [[bitarray('01001011') * 16, bitarray('01001011') * 16],
                    [bitarray('01001011') * 8, bitarray('01001011') * 8]]
        with pytest.raises(ValueError):
            sim_fun(datasets, threshold, k=k)

    @pytest.mark.parametrize('k', [None, 0, 1, 2, 3, 5])
    @pytest.mark.parametrize('threshold', [0., .5, 1.])
    @pytest.mark.parametrize('bytes_n', [1, 7, 9, 15, 17, 23, 25])
    def test_not_multiple_of_64(self, k, threshold, bytes_n):
        datasets = [[bitarray('01001011') * bytes_n],
                    [bitarray('01001011') * bytes_n]]

        py_similarity = similarities.dice_coefficient_python(
            datasets, self.default_threshold, k)
        c_similarity = similarities.dice_coefficient_accelerated(datasets, threshold, k=k)
        self.assert_similarity_matrices_equal(py_similarity, c_similarity)

    def test_not_multiple_of_8_raises(self,):
        datasets = [[bitarray('010')],
                    [bitarray('010')]]
        with pytest.raises(NotImplementedError):
            similarities.dice_coefficient_accelerated(datasets, threshold=self.default_threshold)

    @pytest.mark.parametrize('sim_fun', SIM_FUNS)
    @pytest.mark.parametrize('k', [None, 0, 1])
    @pytest.mark.parametrize('threshold', [0., .5, 1.])
    def test_empty(self, sim_fun, k, threshold):
        datasets = [[], [bitarray('01001011') * 8]]
        sims, (rec_is0, rec_is1) = sim_fun(datasets, threshold, k=k) 
        assert len(sims) == len(rec_is0) == len(rec_is1) == 0
        assert sims.typecode in FLOAT_ARRAY_TYPES
        assert (rec_is0.typecode in UINT_ARRAY_TYPES
                and rec_is1.typecode in UINT_ARRAY_TYPES)

        datasets = [[bitarray('01001011') * 8], []]
        sims, (rec_is0, rec_is1) = sim_fun(datasets, threshold, k=k) 
        assert len(sims) == len(rec_is0) == len(rec_is1) == 0
        assert sims.typecode in FLOAT_ARRAY_TYPES
        assert (rec_is0.typecode in UINT_ARRAY_TYPES
                and rec_is1.typecode in UINT_ARRAY_TYPES)

    @pytest.mark.parametrize('sim_fun', SIM_FUNS)
    @pytest.mark.parametrize('k', [None, 0, 1])
    @pytest.mark.parametrize('threshold', [0., .5])
    def test_all_low(self, sim_fun, k, threshold):
        datasets = [[bitarray('01001011') * 8],
                    [bitarray('00000000') * 8]]
        sims, (rec_is0, rec_is1) = sim_fun(datasets, threshold, k=k) 
        assert (len(sims) == len(rec_is0) == len(rec_is1)
                == (1 if threshold == 0. and k != 0 else 0))
        assert sims.typecode in FLOAT_ARRAY_TYPES
        assert (rec_is0.typecode in UINT_ARRAY_TYPES
                and rec_is1.typecode in UINT_ARRAY_TYPES)

        datasets = [[bitarray('00000000') * 8],
                    [bitarray('01001011') * 8]]
        sims, (rec_is0, rec_is1) = sim_fun(datasets, threshold, k=k) 
        assert (len(sims) == len(rec_is0) == len(rec_is1)
                == (1 if threshold == 0. and k != 0 else 0))
        assert sims.typecode in FLOAT_ARRAY_TYPES
        assert (rec_is0.typecode in UINT_ARRAY_TYPES
                and rec_is1.typecode in UINT_ARRAY_TYPES)

    def test_candidate_stream_right_low(self):
        datasets = list(zip(*[[bitarray('01001011') * 8],
                    [bitarray('00000000') * 8]]))
        sims = anonlink.similarities.dice_coefficient_pairs_python(datasets)
        assert len(sims) == 1
        assert all(s == 0.0 for s in sims)

    def test_candidate_stream_all_low(self):
        datasets = list(zip(*[[bitarray('00000000') * 8],
                    [bitarray('00000000') * 8]]))
        sims = anonlink.similarities.dice_coefficient_pairs_python(datasets)

        assert len(sims) == 1
        assert all(s == 0.0 for s in sims)

    @pytest.mark.parametrize('sim_fun', SIM_FUNS)
    def test_order(self, sim_fun):
        similarity = sim_fun(
            self.filters, self.default_threshold, self.default_k)
        sims, (rec_is0, rec_is1) = similarity
        for i in range(len(sims) - 1):
            sim_a, rec_i0_a, rec_i1_a = sims[i], rec_is0[i], rec_is1[i]
            sim_b, rec_i0_b, rec_i1_b = sims[i+1], rec_is0[i+1], rec_is1[i+1]
            if sim_a > sim_b:
                pass  # Correctly ordered!
            elif sim_a == sim_b:
                if rec_i0_a < rec_i0_b:
                    pass  # Correctly ordered!
                elif rec_i0_a == rec_i0_b:
                    if rec_i1_a < rec_i1_b:
                        pass  # Correctly ordered!
                    elif rec_i1_a == rec_i1_b:
                        assert False, 'duplicate entry'
                    else:
                        assert False, 'incorrect tiebreaking on second index'
                else:
                    assert False, 'incorrect tiebreaking on first index'
            else:
                assert False, 'incorrect similarity sorting'


def _to_bitarray(bytes_):
    ba = bitarray()
    ba.frombytes(bytes_)
    return ba


@given(strategies.data(), strategies.floats(min_value=0, max_value=1))
@pytest.mark.parametrize('sim_fun', SIM_FUNS)
def test_bytes_bitarray_agree(sim_fun, data, threshold):
    bytes_length = data.draw(strategies.integers(
        min_value=0,
        max_value=4096  # Let's not get too carried away...
    ))
    filters0_bytes = data.draw(strategies.lists(strategies.binary(
        min_size=bytes_length, max_size=bytes_length)))
    filters1_bytes = data.draw(strategies.lists(strategies.binary(
        min_size=bytes_length, max_size=bytes_length)))

    filters0_ba = tuple(map(_to_bitarray, filters0_bytes))
    filters1_ba = tuple(map(_to_bitarray, filters1_bytes))

    res_bytes = sim_fun([filters0_bytes, filters1_bytes], threshold)
    res_ba = sim_fun([filters0_ba, filters1_ba], threshold)
    assert (res_bytes == res_ba)


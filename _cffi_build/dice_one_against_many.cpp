#include <algorithm>
#include <vector>
#include <queue>
#include <stdint.h>
#include <cstdlib>
#include <ctime>
#include <cassert>
#include <climits>

static constexpr int WORD_BYTES = sizeof(uint64_t);

/**
 * The popcount of n elements of buf is the sum of c0, c1, c2, c3.
 */
template<int n>
static inline void
popcount(
        uint64_t &c0, uint64_t &c1, uint64_t &c2, uint64_t &c3,
        const uint64_t *buf) {
    popcount<4>(c0, c1, c2, c3, buf);
    popcount<n - 4>(c0, c1, c2, c3, buf + 4);
}

// Fast Path
//
// Source: http://danluu.com/assembly-intrinsics/
// https://stackoverflow.com/questions/25078285/replacing-a-32-bit-loop-count-variable-with-64-bit-introduces-crazy-performance
//
// NB: Dan Luu's original assembly (and the SO answer it was based on)
// is incorrect because it clobbers registers marked as "input only"
// (see warning at
// https://gcc.gnu.org/onlinedocs/gcc/Extended-Asm.html#InputOperands
// -- this mistake does not materialise with GCC (4.9), but it does
// with Clang (3.6 and 3.8)).  We fix the mistake by explicitly
// loading the contents of buf into registers and using these same
// registers for the intermediate popcnts.
/**
 * The popcount of 4 elements of buf is the sum of c0, c1, c2, c3.
 */
template<>
inline void
popcount<4>(
        uint64_t &c0, uint64_t &c1, uint64_t &c2, uint64_t &c3,
        const uint64_t *buf) {
    uint64_t b0, b1, b2, b3;
    b0 = buf[0]; b1 = buf[1]; b2 = buf[2]; b3 = buf[3];
    __asm__(
        "popcnt %4, %4  \n\t"
        "add %4, %0     \n\t"
        "popcnt %5, %5  \n\t"
        "add %5, %1     \n\t"
        "popcnt %6, %6  \n\t"
        "add %6, %2     \n\t"
        "popcnt %7, %7  \n\t"
        "add %7, %3     \n\t"
        : "+r" (c0), "+r" (c1), "+r" (c2), "+r" (c3),
          "+r" (b0), "+r" (b1), "+r" (b2), "+r" (b3));
}

// Slow paths
// TODO: Assumes sizeof(long) == 8
//
// NB: The specialisation to n=3 is not currently used but included
// for completeness (i.e. so that popcount<n> is defined for all
// non-negative n) and in anticipation of its use in the near future.
#if 0
template<>
inline void
popcount<3>(
        uint64_t &c0, uint64_t &c1, uint64_t &c2, uint64_t &,
        const uint64_t *buf) {
    c0 += __builtin_popcountl(buf[0]);
    c1 += __builtin_popcountl(buf[1]);
    c2 += __builtin_popcountl(buf[2]);
}
#endif

/**
 * The popcount of 2 elements of buf is the sum of c0, c1.
 */
template<>
inline void
popcount<2>(
        uint64_t &c0, uint64_t &c1, uint64_t &, uint64_t &,
        const uint64_t *buf) {
    c0 += __builtin_popcountl(buf[0]);
    c1 += __builtin_popcountl(buf[1]);
}

/**
 * The popcount *buf is in c0.
 */
template<>
inline void
popcount<1>(
        uint64_t &c0, uint64_t &, uint64_t &, uint64_t &,
        const uint64_t *buf) {
    c0 += __builtin_popcountl(buf[0]);
}


/**
 * Calculate population counts of an array of inputs of nwords elements.
 *
 * 'arrays' must point to narrays*nwords*WORD_BYTES bytes
 * 'counts' must point to narrays*sizeof(uint32_t) bytes.
 * For i = 0 to narrays - 1, the population count of the nwords elements
 *
 *   arrays[i * nwords] ... arrays[(i + 1) * nwords - 1]
 *
 * is put in counts[i].
 */
template<int nwords>
static void
_popcount_arrays(uint32_t *counts, const uint64_t *arrays, int narrays) {
    uint64_t c0, c1, c2, c3;
    for (int i = 0; i < narrays; ++i, arrays += nwords) {
        c0 = c1 = c2 = c3 = 0;
        popcount<nwords>(c0, c1, c2, c3, arrays);
        counts[i] = c0 + c1 + c2 + c3;
    }
}

/**
 * Return the popcount of the nwords elements starting at array.
 */
static uint32_t
_popcount_array(const uint64_t *array, int nwords) {
    uint64_t c0, c1, c2, c3;
    c0 = c1 = c2 = c3 = 0;

    while (nwords >= 16) {
        popcount<16>(c0, c1, c2, c3, array);
        array += 16;
        nwords -= 16;
    }
    // nwords < 16
    if (nwords >= 8) {
        popcount<8>(c0, c1, c2, c3, array);
        array += 8;
        nwords -= 8;
    }
    // nwords < 8
    if (nwords >= 4) {
        popcount<4>(c0, c1, c2, c3, array);
        array += 4;
        nwords -= 4;
    }
    // nwords < 4
    if (nwords >= 2) {
        popcount<2>(c0, c1, c2, c3, array);
        array += 2;
        nwords -= 2;
    }
    // nwords < 2
    if (nwords == 1)
        popcount<1>(c0, c1, c2, c3, array);
    return c0 + c1 + c2 + c3;
}

/**
 * The popcount of the logical AND of n corresponding elements of buf1
 * and buf2 is the sum of c0, c1, c2, c3.
 */
template<int n>
static inline void
popcount_logand(
        uint64_t &c0, uint64_t &c1, uint64_t &c2, uint64_t &c3,
        const uint64_t *buf1, const uint64_t *buf2) {
    popcount_logand<4>(c0, c1, c2, c3, buf1, buf2);
    popcount_logand<n - 4>(c0, c1, c2, c3, buf1 + 4, buf2 + 4);
}

/**
 * The popcount of the logical AND of 4 corresponding elements of buf1
 * and buf2 is the sum of c0, c1, c2, c3.
 */
template<>
inline void
popcount_logand<4>(
        uint64_t &c0, uint64_t &c1, uint64_t &c2, uint64_t &c3,
        const uint64_t *buf1, const uint64_t *buf2) {
    uint64_t b[4];
    b[0] = buf1[0] & buf2[0];
    b[1] = buf1[1] & buf2[1];
    b[2] = buf1[2] & buf2[2];
    b[3] = buf1[3] & buf2[3];
    popcount<4>(c0, c1, c2, c3, b);
}

/**
 * Return the popcount of the logical AND of len corresponding
 * elements of u and v.
 */
static uint32_t
_popcount_logand_array(const uint64_t *u, const uint64_t *v, int len) {
    // NB: The switch statement at the end of this function must have
    // cases for all i = 1, ..., LOOP_LEN - 1.
    static constexpr int LOOP_LEN = 4;
    uint64_t c0, c1, c2, c3;
    c0 = c1 = c2 = c3 = 0;

    int i = 0;
    for ( ; i + LOOP_LEN <= len; i += LOOP_LEN) {
        popcount_logand<LOOP_LEN>(c0, c1, c2, c3, u, v);
        u += LOOP_LEN;
        v += LOOP_LEN;
    }

    // NB: The "fall through" comments are necessary to tell GCC and
    // Clang not to complain about the fact that the case clauses
    // don't have break statements in them.
    switch (len - i) {
    case 3: c2 += __builtin_popcountl(u[2] & v[2]);  /* fall through */
    case 2: c1 += __builtin_popcountl(u[1] & v[1]);  /* fall through */
    case 1: c0 += __builtin_popcountl(u[0] & v[0]);  /* fall through */
    }

    return c0 + c1 + c2 + c3;
}

/**
 * Return the Sorensen-Dice coefficient of nwords length arrays u and
 * v, whose popcounts are given in u_popc and v_popc respectively.
 */
static inline double
_dice_coeff_generic(
        const uint64_t *u, uint32_t u_popc,
        const uint64_t *v, uint32_t v_popc,
        int nwords) {
    uint32_t uv_popc = _popcount_logand_array(u, v, nwords);
    return (2 * uv_popc) / (double) (u_popc + v_popc);
}

/**
 * Return the Sorensen-Dice coefficient of nwords length arrays u and
 * v, whose popcounts are given in u_popc and v_popc respectively.
 */
template<int nwords>
static inline double
_dice_coeff(
        const uint64_t *u, uint32_t u_popc,
        const uint64_t *v, uint32_t v_popc) {
    uint64_t c0, c1, c2, c3;
    c0 = c1 = c2 = c3 = 0;
    popcount_logand<nwords>(c0, c1, c2, c3, u, v);
    uint32_t uv_popc = c0 + c1 + c2 + c3;
    return (2 * uv_popc) / (double) (u_popc + v_popc);
}

class Node {
public:
    int index;
    double score;

    // Constructor with default
    Node( int n_index = -1, double n_score = -1.0 )
        :index(n_index), score( n_score ) { }
};

struct score_cmp {
    bool operator()(const Node& a, const Node& b) const {
        return a.score > b.score;
    }
};


/**
 *
 */
static inline uint32_t
calculate_max_difference(uint32_t popcnt_a, double threshold) {
    return 2 * popcnt_a * (1/threshold - 1);
}

/**
 * Convert clock measurement t to milliseconds.
 *
 * t should have been obtained as the difference of calls to clock()
 * for this to make sense.
 */
static inline double
to_millis(clock_t t) {
    static constexpr double CPS = (double)CLOCKS_PER_SEC;
    return t * 1.0E3 / CPS;
}

static inline uint32_t
abs_diff(uint32_t a, uint32_t b) {
    if (a > b)
        return a - b;
    return b - a;
}


extern "C"
{
    /**
     * Calculate population counts of an array of inputs; return how
     * long it took in milliseconds.
     *
     * 'arrays' must point to narrays*array_bytes bytes
     * 'counts' must point to narrays*sizeof(uint32_t) bytes.
     * For i = 0 to n - 1, the population count of the array_bytes*8 bits
     *
     *   arrays[i * array_bytes] ... arrays[(i + 1) * array_bytes - 1]
     *
     * is put in counts[i].
     *
     * ASSUMES: array_bytes is divisible by 8.
     */
    double
    popcount_arrays(
            uint32_t *counts,
            const char *arrays, int narrays, int array_bytes) {
        // assumes WORD_BYTES divides array_bytes
        int nwords = array_bytes / WORD_BYTES;
        const uint64_t *u = reinterpret_cast<const uint64_t *>(arrays);

        // assumes WORD_PER_POPCOUNT divides nwords
        clock_t t = clock();
        switch (nwords) {
        case 32: _popcount_arrays<32>(counts, u, narrays); break;
        case 16: _popcount_arrays<16>(counts, u, narrays); break;
        case  8: _popcount_arrays< 8>(counts, u, narrays); break;
        default:
            for (int i = 0; i < narrays; ++i, u += nwords)
                counts[i] = _popcount_array(u, nwords);
        }
        return to_millis(clock() - t);
    }

    /**
     * Compute the Dice coefficient similarity measure of two arrays
     * of length array_bytes.
     *
     * ASSUMES: array_bytes is divisible by 8.
     */
    double
    dice_coeff(
            const char *array1,
            const char *array2,
            int array_bytes) {
        const uint64_t *u, *v;
        uint32_t u_popc, v_popc;
        // assumes WORD_BYTES divides array_bytes
        int nwords = array_bytes / WORD_BYTES;

        u = reinterpret_cast<const uint64_t *>(array1);
        v = reinterpret_cast<const uint64_t *>(array2);

        // If the popcount of one of the arrays is zero, then the
        // popcount of the "intersection" (logical AND) will be zero,
        // hence the whole Dice coefficient will be zero.
        u_popc = _popcount_array(u, nwords);
        if (u_popc == 0)
            return 0.0;
        v_popc = _popcount_array(v, nwords);
        if (v_popc == 0)
            return 0.0;

        return _dice_coeff_generic(u, u_popc, v, v_popc, nwords);
    }

    /**
     * Calculate up to the top k indices and scores.  Returns the
     * number matched above the given threshold or -1 if keybytes is
     * not a multiple of 8.
     */
    int match_one_against_many_dice_k_top(
            const char *one,
            const char *many,
            const uint32_t *counts_many,
            int n,
            int keybytes,
            uint32_t k,
            double threshold,
            int *indices,
            double *scores) {

        if (keybytes % WORD_BYTES != 0)
            return -1;
        int keywords = keybytes / WORD_BYTES;
        const uint64_t *comp1 = reinterpret_cast<const uint64_t *>(one);
        const uint64_t *comp2 = reinterpret_cast<const uint64_t *>(many);

        // Here we create top_k_scores on the stack by providing it
        // with a vector in which to put its elements. We do this so
        // that we can reserve the amount of space needed for the
        // scores in advance and avoid potential memory reallocation
        // and copying.
        typedef std::vector<Node> node_vector;
        typedef std::priority_queue<Node, std::vector<Node>, score_cmp> node_queue;
        node_vector vec;
        vec.reserve(k + 1);
        node_queue top_k_scores(score_cmp(), std::move(vec));

        uint32_t count_one = _popcount_array(comp1, keywords);
        if (count_one == 0)
            return 0;

        uint32_t max_popcnt_delta = keybytes * CHAR_BIT; // = bits per key
        if(threshold > 0) {
            max_popcnt_delta = calculate_max_difference(count_one, threshold);
        }

        auto push_score = [&](double score, int idx) {
            if (score >= threshold) {
                top_k_scores.push(Node(idx, score));
                if (top_k_scores.size() > k) {
                    // Popping the top element is O(log(k))!
                    top_k_scores.pop();
                }
            }
        };

        const uint64_t *current = comp2;

        // NB: For any key length that must run at maximum speed, we
        // need to specialise a block in the following 'if' statement
        // (which is an example of specialising to keywords == 16).
        if (keywords == 16) {
            for (int j = 0; j < n; j++, current += 16) {
                const uint32_t counts_many_j = counts_many[j];
                if (abs_diff(count_one, counts_many_j) <= max_popcnt_delta) {
                    double score = _dice_coeff<16>(comp1, count_one, current, counts_many_j);
                    push_score(score, j);
                }
            }
        } else {
            for (int j = 0; j < n; j++, current += keywords) {
                const uint32_t counts_many_j = counts_many[j];
                if (abs_diff(count_one, counts_many_j) <= max_popcnt_delta) {
                    double score = _dice_coeff_generic(comp1, count_one, current, counts_many_j, keywords);
                    push_score(score, j);
                }
            }
        }

        int i = 0;
        while ( ! top_k_scores.empty()) {
           scores[i] = top_k_scores.top().score;
           indices[i] = top_k_scores.top().index;
           // Popping the top element is O(log(k))!
           top_k_scores.pop();
           i += 1;
        }

        return i;
    }
}

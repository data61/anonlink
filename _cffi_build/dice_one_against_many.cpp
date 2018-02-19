#include <algorithm>
#include <vector>
#include <queue>
#include <cstdint>
#include <cstdlib>
#include <ctime>
#include <cassert>
#include <climits>

// WORDS_PER_POPCOUNT determines how much we unroll the popcounting in
// each iteration of a loop. Currently 16, which corresponds to 16*64
// = 1024 bits per loop.
static constexpr int WORDS_PER_POPCOUNT = 16;
static constexpr int WORD_BYTES = sizeof(uint64_t);

template<int n>
void popcount(
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
template<>
void popcount<4>(
        uint64_t &c0, uint64_t &c1, uint64_t &c2, uint64_t &c3,
        const uint64_t* buf) {
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
template<>
void popcount<3>(
        uint64_t &c0, uint64_t &c1, uint64_t &c2, uint64_t &,
        const uint64_t* buf) {
    c0 += __builtin_popcountl(buf[0]);
    c1 += __builtin_popcountl(buf[1]);
    c2 += __builtin_popcountl(buf[2]);
}

template<>
void popcount<2>(
        uint64_t &c0, uint64_t &c1, uint64_t &, uint64_t &,
        const uint64_t* buf) {
    c0 += __builtin_popcountl(buf[0]);
    c1 += __builtin_popcountl(buf[1]);
}

template<>
void popcount<1>(
        uint64_t &c0, uint64_t &, uint64_t &, uint64_t &,
        const uint64_t* buf) {
    c0 += __builtin_popcountl(buf[0]);
}


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

static uint32_t
_popcount_combined_array(
        const uint64_t *array1,
        const uint64_t *array2,
        int nwords) {
    uint64_t combined[WORDS_PER_POPCOUNT];
    uint64_t c0, c1, c2, c3;
    c0 = c1 = c2 = c3 = 0;
    for (int i = 0; i < nwords; i += WORDS_PER_POPCOUNT) {
        for (int j = 0; j < WORDS_PER_POPCOUNT; ++j)
            combined[j] = array1[i + j] & array2[i + j];
        popcount<WORDS_PER_POPCOUNT>(c0, c1, c2, c3, combined);
    }
    return c0 + c1 + c2 + c3;
}

// assumes u_popc or v_popc is nonzero.
static inline double
_dice_coeff(
        const uint64_t *u, uint32_t u_popc,
        const uint64_t *v, uint32_t v_popc,
        int nwords) {
    uint32_t uv_popc = _popcount_combined_array(u, v, nwords);
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
        for (int i = 0; i < narrays; ++i, u += nwords)
            counts[i] = _popcount_array(u, nwords);
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

        return _dice_coeff(u, u_popc, v, v_popc, nwords);
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
        const uint64_t *comp1 = (const uint64_t *) one;
        const uint64_t *comp2 = (const uint64_t *) many;

        // Here we create max_k_scores on the stack by providing it
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
        uint32_t max_popcnt_delta = keybytes * CHAR_BIT; // = bits per key
        if(threshold > 0) {
            max_popcnt_delta = calculate_max_difference(count_one, threshold);
        }

        const uint64_t *current = comp2;
        for (int j = 0; j < n; j++, current += keywords) {
            const uint32_t counts_many_j = counts_many[j];

            if (abs_diff(count_one, counts_many_j) <= max_popcnt_delta) {
                double score = _dice_coeff(comp1, count_one, current, counts_many_j, keywords);
                if (score >= threshold) {
                    top_k_scores.push(Node(j, score));
                    if (top_k_scores.size() > k) {
                        // Popping the top element is O(log(k))!
                        top_k_scores.pop();
                    }
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

    int match_one_against_many_dice(const char *one, const char *many, int n, double *score) {

        static const int array_bytes = 128;
        static const double threshold = 0.0;
        static const int k = 1;
        int idx_unused;
        uint32_t *counts_many = new uint32_t[n];
        popcount_arrays(counts_many, many, n, array_bytes);
        int res = match_one_against_many_dice_k_top(
            one, many, counts_many, n, array_bytes, k, threshold, &idx_unused, score);
        delete[] counts_many;

        return res;
    }
}

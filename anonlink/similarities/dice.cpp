#include <memory>
#include <functional>
#include <algorithm>
#include <vector>
#include <queue>
#include <stdint.h>
#include <cstdlib>
#include <ctime>
#include <cassert>
#include <climits>
#include "libpopcount.h"

static constexpr int WORD_BYTES = sizeof(uint64_t);

/**
 * Popcount of n elements of buf.
 */
template<int n>
static inline void
#if defined (_MSC_VER)
// code specific to Visual Studio compiler
// With MSVC we call libpopcnt with the whole data and return the popcount in c0
popcount( uint64_t &c0, uint64_t &, uint64_t &, uint64_t &, const uint64_t *buf) {
    c0 += popcnt(buf, n*WORD_BYTES);
#else
// The popcount of n elements of buf is the sum of c0, c1, c2, c3.
popcount( uint64_t &c0, uint64_t &c1, uint64_t &c2, uint64_t &c3, const uint64_t *buf) {
    popcount<4>(c0, c1, c2, c3, buf);
    popcount<n - 4>(c0, c1, c2, c3, buf + 4);
#endif
}

/**
 * The popcount of 4 elements of buf is the sum of c0, c1, c2, c3.
 */
template<>
inline void
popcount<4>( uint64_t &c0, uint64_t &c1, uint64_t &c2, uint64_t &c3, const uint64_t *buf) {

// Although `popcnt` from libpopcount.h works on Linux & MacOS
// The handrolled assembler is faster for 32 byte buffers
#if defined (_MSC_VER)
    c0 += popcnt(buf, 4*WORD_BYTES);
    c1 += 0; c2 += 0; c3 += 0;
#else
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
#endif
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
        uint64_t &c0, uint64_t &, uint64_t &, uint64_t &,
        const uint64_t *buf) {
    c0 += popcnt(buf, 3*WORD_BYTES);
}
#endif

/**
 * The popcount of 2 elements of buf is the sum of c0.
 */
template<>
inline void
popcount<2>(
        uint64_t &c0, uint64_t &, uint64_t &, uint64_t &,
        const uint64_t *buf) {
    c0 += popcnt(buf, 2*WORD_BYTES);
}

/**
 * The popcount *buf is in c0.
 */
template<>
inline void
popcount<1>(
        uint64_t &c0, uint64_t &, uint64_t &, uint64_t &,
        const uint64_t *buf) {
    c0 += popcnt(buf, WORD_BYTES);
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
        counts[i] = static_cast<uint32_t>(c0 + c1 + c2 + c3);
    }
}

/**
 * Return the popcount of the nwords elements starting at array.
 */
static uint32_t
_popcount_array(const uint64_t *array, int nwords) {
    uint64_t c0, c1, c2, c3;
    c0 = c1 = c2 = c3 = 0;
    while (nwords >= 64) {
        c0 += popcnt(array, 64 * WORD_BYTES);
        array += 64;
        nwords -= 64;
    }
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
    return static_cast<uint32_t>(c0 + c1 + c2 + c3);
}

/**
 * The popcount of the logical AND of n corresponding elements of buf1
 * and buf2 is returned. The AND of the two input buffers is placed
 * in buf1n2.
 * Byte version, see below for word aligned version.
 */
static inline uint64_t
popcount_logand_chars(
        char *buf1n2,
        const char *buf1,
        const char *buf2,
        int n
        ) {
    for (int i = 0; i < n; i++) {
        buf1n2[i] = buf1[i] & buf2[i];
    }
    return popcnt(&buf1n2[0], n);
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
#if defined (_MSC_VER)
    uint64_t b[n];
    for (int i = 0; i < n; i++) {
        b[i] = buf1[i] & buf2[i];
    }
    c0 += popcnt(b, n*WORD_BYTES);
    //popcount<n>(c0, c1, c2, c3, b);
#else
    popcount_logand<4>(c0, c1, c2, c3, buf1, buf2);
    popcount_logand<n - 4>(c0, c1, c2, c3, buf1 + 4, buf2 + 4);
#endif
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
    // cases for all cases not covered earlier

    uint64_t c0, c1, c2, c3;
    c0 = c1 = c2 = c3 = 0;
    int nwords = len;
#if defined (_MSC_VER)
    while (nwords >= 128) {
        popcount_logand<128>(c0, c1, c2, c3, u, v);
        u += 128;
        v += 128;
        nwords -= 128;
    }
    // 16 <= nwords < 128
    while (nwords >= 16) {
        popcount_logand<16>(c0, c1, c2, c3, u, v);
        u += 16;
        v += 16;
        nwords -= 16;
    }
#endif
    // 4 <= nwords < 128
    while (nwords >= 4) {
        popcount_logand<4>(c0, c1, c2, c3, u, v);
        u += 4;
        v += 4;
        nwords -= 4;
    }

    // NB: The "fall through" comments are necessary to tell GCC and
    // Clang not to complain about the fact that the case clauses
    // don't have break statements in them.
    switch (nwords) {
    case 3: c2 += popcnt64(u[2] & v[2]);  /* fall through */
    case 2: c1 += popcnt64(u[1] & v[1]);  /* fall through */
    case 1: c0 += popcnt64(u[0] & v[0]);  /* fall through */
    }

    return c0 + c1 + c2 + c3;
}

/**
 * Return the Sorensen-Dice coefficient of n byte length arrays u and
 * v, whose popcounts are given in u_popc and v_popc respectively.
 *
 * Byte version
 */
static inline double
_dice_coeff_chars(
        const char *u, uint32_t u_popc,
        const char *v, uint32_t v_popc,
        char *andbuffer,
        int n) {
    uint64_t uv_popc = popcount_logand_chars(andbuffer, u, v, n);
    return (2 * uv_popc) / (double) (u_popc + v_popc);
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
    uint64_t uv_popc = c0 + c1 + c2 + c3;
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
        return a.score > b.score || (a.score == b.score && a.index < b.index);
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


typedef const uint64_t word_tp;
typedef std::function<void (word_tp *)> deleter_fn;
typedef std::unique_ptr<word_tp, deleter_fn> word_ptr;

/**
 * Given a char pointer ptr pointing to nbytes bytes, return a
 * std::unique_ptr to uint64_t containing those same byte values
 * (using the host's byte order, i.e. no byte reordering is done).
 *
 * The main purpose of this function is to fix pointer alignment
 * issues when converting from a char pointer to a uint64 pointer; the
 * issue being that a uint64 pointer has stricter alignment
 * requirements than a char pointer.
 *
 * We assume that releasing the memory associated with ptr is someone
 * else's problem. So, if ptr is already correctly aligned, we just
 * cast it to uint64 and return a unique_ptr whose deleter is
 * empty. If ptr is misaligned, then we copy the nbytes at ptr to a
 * location that is correctly aligned and then return a unique_ptr
 * whose deleter will delete that allocated space when the unique_ptr
 * goes out of scope.
 *
 * NB: ASSUMES nbytes is divisible by WORD_BYTES.
 *
 * TODO: On some architectures it might be advantageous to have
 * 16-byte aligned memory, even when the words used are only 8 bytes
 * (this is to do with cache line size). This function could be easily
 * modified to allow experimentation with different alignments.
 */
static word_ptr
adjust_ptr_alignment(const char *ptr, size_t nbytes) {
    static constexpr size_t wordbytes = sizeof(word_tp);
    size_t nwords = nbytes / wordbytes;
    uintptr_t addr = reinterpret_cast<uintptr_t>(ptr);
    // ptr is correctly aligned if addr is divisible by wordbytes
    if (addr % wordbytes != 0) {
        // ptr is NOT correctly aligned

        // copy_words has correct alignment
        uint64_t *copy_words = new uint64_t[nwords];
        // alias copy_words with a byte pointer; the cast safe because
        // uint8_t alignment is less restrictive than uint64_t
        uint8_t *copy_bytes = reinterpret_cast<uint8_t *>(copy_words);
        // copy everything across
        std::copy(ptr, ptr + nbytes, copy_bytes);
        // return a unique_ptr with array delete to delete copy_words
        auto array_delete = [] (word_tp *p) { delete[] p; };
        return word_ptr(copy_words, array_delete);
    } else {
        // ptr IS correctly aligned

        // safe cast because the address of ptr is wordbyte-aligned.
        word_tp *same = reinterpret_cast<word_tp *>(ptr);
        // don't delete backing array since we don't own it
        auto empty_delete = [] (word_tp *) { };
        return word_ptr(same, empty_delete);
    }
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
        clock_t t = clock();
        if (array_bytes >= WORD_BYTES && array_bytes % WORD_BYTES == 0) {
            // WORD_BYTES divides array_bytes
            int nwords = array_bytes / WORD_BYTES;
            // The static_cast is to avoid int overflow in the multiplication
            size_t total_bytes = static_cast<size_t>(narrays) * array_bytes;
            auto ptr = adjust_ptr_alignment(arrays, total_bytes);
            auto u = ptr.get();

            switch (nwords) {
            case 64: _popcount_arrays<64>(counts, u, narrays); break;
            case 32: _popcount_arrays<32>(counts, u, narrays); break;
            case 16: _popcount_arrays<16>(counts, u, narrays); break;
            case  8: _popcount_arrays< 8>(counts, u, narrays); break;
            default:
                for (int i = 0; i < narrays; ++i, u += nwords)
                    counts[i] = _popcount_array(u, nwords);
            }
        } else {
            // array_bytes not aligned with our word size
            for (int i = 0; i < narrays; ++i) {
                counts[i] = popcnt(&arrays[i], array_bytes);
            }
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
        uint32_t u_popc, v_popc;
        // assumes WORD_BYTES divides array_bytes
        int nwords = array_bytes / WORD_BYTES;

        auto ptr_u = adjust_ptr_alignment(array1, array_bytes);
        auto ptr_v = adjust_ptr_alignment(array2, array_bytes);
        auto u = ptr_u.get();
        auto v = ptr_v.get();

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
     * number matched above the given threshold
     */
    int match_one_against_many_dice_k_top(
            const char *one,
            const char *many,
            const uint32_t *counts_many,
            int n,
            int keybytes,
            uint32_t k,
            double threshold,
            unsigned int *indices,
            double *scores) {

        uint32_t count_one;

        // Here we create top_k_scores on the stack by providing it
        // with a vector in which to put its elements. We do this so
        // that we can reserve the amount of space needed for the
        // scores in advance and avoid potential memory reallocation
        // and copying. Note the data structure is a priority queue where
        // the **lowest** score has the highest priority. The item with
        // the lowest score is the first to be popped off the queue.
        typedef std::vector<Node> node_vector;
        typedef std::priority_queue<Node, std::vector<Node>, score_cmp> node_queue;
        node_vector vec;
        Node temp_node;
        vec.reserve(k + 1);
        node_queue top_k_scores(score_cmp(), vec);
        bool key_is_word_divisible = (keybytes > WORD_BYTES) && (keybytes % WORD_BYTES == 0);
        if (key_is_word_divisible) {
            // keybytes is divisible by WORD_BYTES
            int keywords = keybytes / WORD_BYTES;
            // The static_cast is to avoid int overflow in the multiplication
            size_t total_bytes = static_cast<size_t>(n) * keybytes;
            auto ptr_comp1 = adjust_ptr_alignment(one, total_bytes);
            auto ptr_comp2 = adjust_ptr_alignment(many, total_bytes);
            auto comp1 = ptr_comp1.get();
            auto comp2 = ptr_comp2.get();

            count_one = _popcount_array(comp1, keywords);

            if (count_one == 0) {
                if (threshold > 0) {
                    return 0;
                }

                for (uint32_t j = 0; j < k; ++j) {
                    scores[j] = 0.0;
                    indices[j] = j;
                }

                return static_cast<int>(k);
            }

            uint32_t max_popcnt_delta = keybytes * CHAR_BIT; // = bits per key
            if(threshold > 0) {
                max_popcnt_delta = calculate_max_difference(count_one, threshold);
            }

            double dynamic_threshold = threshold;
            auto push_score = [&](double score, int idx) {
                if (score >= dynamic_threshold) {
                    top_k_scores.push(Node(idx, score));
                    if (top_k_scores.size() > k) {
                        // Popping the top element is O(log(k))!
                        temp_node = top_k_scores.top();
                        top_k_scores.pop();
                        // threshold can now be raised
                        dynamic_threshold = temp_node.score;
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

        } else {
            // As the keybytes is not evenly divisible by WORD_BYTES we
            // process individual bytes instead of 64 bit words.
            count_one = popcnt(one, keybytes);

            // DUPLICATED FROM ABOVE
            if (count_one == 0) {
                if (threshold > 0) {
                    return 0;
                }

                for (uint32_t j = 0; j < k; ++j) {
                    scores[j] = 0.0;
                    indices[j] = j;
                }

                return static_cast<int>(k);
            }
            uint32_t max_popcnt_delta = keybytes * CHAR_BIT; // = bits per key
            if(threshold > 0) {
                max_popcnt_delta = calculate_max_difference(count_one, threshold);
            }
            double dynamic_threshold = threshold;
            auto push_score = [&](double score, int idx) {
                if (score >= dynamic_threshold) {
                    top_k_scores.push(Node(idx, score));
                    if (top_k_scores.size() > k) {
                        // Popping the top element is O(log(k))!
                        temp_node = top_k_scores.top();
                        top_k_scores.pop();
                        // threshold can now be raised
                        dynamic_threshold = temp_node.score;
                    }
                }
            };

            const char *current = many;
            char *andbuffer = new char[keybytes];

            for (int j = 0; j < n; j++, current += keybytes) {
                const uint32_t counts_many_j = counts_many[j];
                if (abs_diff(count_one, counts_many_j) <= max_popcnt_delta) {
                    double score = _dice_coeff_chars(one, count_one, current, counts_many_j, andbuffer, keybytes);
                    push_score(score, j);
                }
            }
            delete andbuffer;

        }

        // Copy the scores and indices in reverse order so that the
        // best match is at index 0 and the worst is at index
        // top_k_scores.size()-1.
        int nscores = top_k_scores.size();
        for (int i = top_k_scores.size() - 1; i >= 0; --i) {
           scores[i] = top_k_scores.top().score;
           indices[i] = top_k_scores.top().index;
           assert(indices[i] >= 0);
           assert(indices[i] <= k);
           // Popping the top element is O(log(k))!
           top_k_scores.pop();
        }
        assert(top_k_scores.empty());
        return nscores;
    }
}

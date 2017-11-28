#include <algorithm>
#include <vector>
#include <queue>
#include <cstdint>
#include <cstdlib>
#include <iostream>


#define WORDBYTES (sizeof(uint64_t))
#define WORDBITS (WORDBYTES * 8)
#define KEYBITS 1024
#define KEYBYTES (KEYBITS / 8)
// KEYWORDS must be divisible by 4. It is currently equal to 16.
#define KEYWORDS (KEYBYTES / WORDBYTES)

// Source: http://danluu.com/assembly-intrinsics/
// https://stackoverflow.com/questions/25078285/replacing-a-32-bit-loop-count-variable-with-64-bit-introduces-crazy-performance
//
// NB: Dan Luu's original assembly is incorrect because it
// clobbers registers marked as "input only" (see warning at
// https://gcc.gnu.org/onlinedocs/gcc/Extended-Asm.html#InputOperands
// -- this mistake does not materialise with GCC (4.9), but it
// does with Clang (3.6 and 3.8)).  We fix the mistake by
// explicitly loading the contents of buf into registers and using
// these same registers for the intermediate popcnts.
static inline uint32_t
builtin_popcnt_unrolled_errata_manual(const uint64_t* buf) {
  uint64_t b0, b1, b2, b3;
  uint64_t c0, c1, c2, c3;
  c0 = c1 = c2 = c3 = 0;

  // We unroll this manually because some versions of GCC don't do so
  // of their own volition.  Speedup from this in such cases is >20%.
#undef LOOP_BODY
#define LOOP_BODY(i) do {                                         \
  b0 = buf[i]; b1 = buf[i + 1]; b2 = buf[i + 2]; b3 = buf[i + 3]; \
  __asm__(                                                        \
    "popcnt %4, %4  \n\t"                                         \
    "add %4, %0     \n\t"                                         \
    "popcnt %5, %5  \n\t"                                         \
    "add %5, %1     \n\t"                                         \
    "popcnt %6, %6  \n\t"                                         \
    "add %6, %2     \n\t"                                         \
    "popcnt %7, %7  \n\t"                                         \
    "add %7, %3     \n\t"                                         \
    : "+r" (c0), "+r" (c1), "+r" (c2), "+r" (c3),                 \
      "+r" (b0), "+r" (b1), "+r" (b2), "+r" (b3));                \
  } while (0)

  LOOP_BODY(0);
  LOOP_BODY(4);
  LOOP_BODY(8);
  LOOP_BODY(12);

  return c0 + c1 + c2 + c3;
}

/**
 * Compute the Dice coefficient similarity measure of two bit patterns.
 */
static double
dice_coeff_1024(const char *e1, const char *e2) {
    const uint64_t *comp1 = (const uint64_t *) e1;
    const uint64_t *comp2 = (const uint64_t *) e2;

    uint32_t count_both = 0;

    count_both += builtin_popcnt_unrolled_errata_manual(comp1);
    count_both += builtin_popcnt_unrolled_errata_manual(comp2);
    if(count_both == 0) {
        return 0.0;
    }

    uint64_t combined[KEYWORDS];
    for (unsigned int i = 0 ; i < KEYWORDS; i++ ) {
        combined[i] = comp1[i] & comp2[i];
    }

    uint32_t count_and = builtin_popcnt_unrolled_errata_manual(combined);

    return 2 * count_and / (double)count_both;
}


class Node {

public:
    int index;
    double score;

    // Constructor with default
    Node( int n_index = -1, double n_score = -1.0 )
        :index(n_index), score( n_score )
        {
        }
};

struct score_cmp{
    bool operator()(const Node& a, const Node& b) const{
        return a.score > b.score;
    }
};


/**
 * Count lots of bits.
 */
static void popcount_1024_array(const char *many, int n, uint32_t *counts_many) {
    for (int i = 0; i < n; i++) {
        const uint64_t *sig = (const uint64_t *) many + i * KEYWORDS;
        counts_many[i] = builtin_popcnt_unrolled_errata_manual(sig);
    }
}

/**
 *
 */
static uint32_t calculate_max_difference(uint32_t popcnt_a, double threshold)
{
    return 2 * popcnt_a * (1/threshold - 1);
}

extern "C"
{
    /**
     * Calculate up to the top k indices and scores.
     * Returns the number matched above a threshold.
     */
    int match_one_against_many_dice_1024_k_top(
        const char *one,
        const char *many,
        const uint32_t *counts_many,
        int n,
        uint32_t k,
        double threshold,
        int *indices,
        double *scores) {

        const uint64_t *comp1 = (const uint64_t *) one;
        const uint64_t *comp2 = (const uint64_t *) many;

        std::priority_queue<Node, std::vector<Node>, score_cmp> max_k_scores;

        uint32_t count_one = builtin_popcnt_unrolled_errata_manual(comp1);

        uint64_t combined[KEYWORDS];

        double *all_scores = new double[n];

        uint32_t max_popcnt_delta = 1024;
        if(threshold > 0) {
            max_popcnt_delta = calculate_max_difference(count_one, threshold);
        }
        uint32_t current_delta;

        for (int j = 0; j < n; j++) {
            const uint64_t *current = comp2 + j * KEYWORDS;

            if(count_one > counts_many[j]){
                current_delta = count_one - counts_many[j];
            } else {
                current_delta = counts_many[j] - count_one;
            }

            if(current_delta <= max_popcnt_delta){
                for (unsigned int i = 0 ; i < KEYWORDS; i++ ) {
                    combined[i] = current[i] & comp1[i];
                }

                uint32_t count_curr = builtin_popcnt_unrolled_errata_manual(combined);

                double score = 2 * count_curr / (double) (count_one + counts_many[j]);
                all_scores[j] = score;
            } else {
                // Skipping because popcount difference too large
                all_scores[j] = -1;
            }
        }

        for (int j = 0; j < n; j++) {

            if(all_scores[j] >= threshold) {
                max_k_scores.push(Node(j, all_scores[j]));
            }

            if(max_k_scores.size() > k) max_k_scores.pop();
        }

        delete[] all_scores;

        int i = 0;
        while (!max_k_scores.empty()) {

           scores[i] = max_k_scores.top().score;
           indices[i] = max_k_scores.top().index;

           max_k_scores.pop();
           i+=1;
        }
        return i;
    }

    int match_one_against_many_dice(const char *one, const char *many, int n, double *score) {

        static const double threshold = 0.0;
        static const int k = 1;
        int idx_unused;
        uint32_t *counts_many = new uint32_t[n];
        popcount_1024_array(many, n, counts_many);
        int res = match_one_against_many_dice_1024_k_top(
            one, many, counts_many, n, k, threshold, &idx_unused, score);
        delete[] counts_many;

        return res;
    }
}


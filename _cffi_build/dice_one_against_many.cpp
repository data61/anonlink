#include <algorithm>
#include <vector>
#include <queue>
#include <cstdint>
#include <cstdlib>
#include <ctime>
#include <cassert>


template<int n>
uint32_t popcount(const uint64_t *buf) {
    return popcount<4>(buf) + popcount<n - 4>(buf + 4);
}

template<>
uint32_t popcount<4>(const uint64_t* buf) {
    uint64_t b0, b1, b2, b3;
    uint64_t c0, c1, c2, c3;
    c0 = c1 = c2 = c3 = 0;

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

    return c0 + c1 + c2 + c3;
}

static uint32_t
popcount_array(const uint64_t *buf, int n) {
    // WORDS_PER_POPCOUNT is how many elements of buf we process each
    // iteration. Currently 16, which corresponds to 16*64 = 1024 bits.
    static constexpr int WORDS_PER_POPCOUNT = 16;
    assert(n % WORDS_PER_POPCOUNT == 0);
    uint32_t pc = 0;
    for (int i = 0; i < n; i += WORDS_PER_POPCOUNT)
        pc += popcount<WORDS_PER_POPCOUNT>(buf + i);
    return pc;
}

static uint32_t
popcount_combined_array(const uint64_t *__restrict__ buf1, const uint64_t *__restrict__ buf2, int n) {
    // WORDS_PER_POPCOUNT is how many elements of buf we process each
    // iteration. Currently 16, which corresponds to 16*64 = 1024 bits.
    static constexpr int WORDS_PER_POPCOUNT = 16;
    assert(n % WORDS_PER_POPCOUNT == 0);
    uint32_t pc = 0;
    uint64_t combined[WORDS_PER_POPCOUNT];
    for (int i = 0; i < n; i += WORDS_PER_POPCOUNT) {
        for (int j = 0; j < WORDS_PER_POPCOUNT; ++j)
            combined[j] = buf1[i + j] & buf2[i + j];
        pc += popcount<WORDS_PER_POPCOUNT>(combined);
    }
    return pc;
}

/**
 * Compute the Dice coefficient similarity measure of two bit patterns.
 */
static double
dice_coeff_1024(const char *e1, const char *e2) {
    const uint64_t *comp1 = (const uint64_t *) e1;
    const uint64_t *comp2 = (const uint64_t *) e2;

    static constexpr int KEYWORDS = 16;
    uint32_t count_both = 0;

    count_both += popcount_array(comp1, KEYWORDS);
    count_both += popcount_array(comp2, KEYWORDS);
    if(count_both == 0) {
        return 0.0;
    }
    uint32_t count_and = popcount_combined_array(comp1, comp2, KEYWORDS);

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
 *
 */
static uint32_t calculate_max_difference(uint32_t popcnt_a, double threshold)
{
    return 2 * popcnt_a * (1/threshold - 1);
}

static double
dice_coeff(const uint64_t *u, uint32_t u_popc, const uint64_t *v, uint32_t v_popc, int n)
{
    uint32_t uv_popc = popcount_combined_array(u, v, n);
    return (2 * uv_popc) / (double) (u_popc + v_popc);
}

/**
 * Convert clock measurement t to milliseconds.
 *
 * t should have been obtained as the difference of calls to clock()
 * for this to make sense.
 */
static inline double to_millis(clock_t t)
{
    static constexpr double CPS = (double)CLOCKS_PER_SEC;
    return t * 1.0E3 / CPS;
}

extern "C"
{
    /**
     * Calculate population counts of an array of inputs; return how
     * long it took in milliseconds.
     *
     * 'many' must point to n*KEYWORDS*sizeof(uint64_t) (== 128*n) bytes
     * 'counts_many' must point to n*sizeof(uint32_t) bytes.
     * For i = 0 to n - 1, the population count of the 1024 bits
     *
     *   many[i * KEYWORDS] ... many[(i + 1) * KEYWORDS - 1]
     *
     * is put in counts_many[i].
     */
    double popcount_1024_array(const char *many, int n, uint32_t *counts_many) {
        static constexpr int KEYWORDS = 16;
        clock_t t = clock();
        for (int i = 0; i < n; i++) {
            const uint64_t *sig = (const uint64_t *) many + i * KEYWORDS;
            counts_many[i] = popcount_array(sig, KEYWORDS);
        }
        return to_millis(clock() - t);
    }

    /**
     * Calculate up to the top k indices and scores.  Returns the
     * number matched above a threshold or -1 if keybytes is not a
     * multiple of 32.
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

        const uint64_t *comp1 = (const uint64_t *) one;
        const uint64_t *comp2 = (const uint64_t *) many;

        // FIXME: This comment needs to be updated
        // keybytes must be divisible by 32, because keywords must be
        // divisible by 4 for the builtin popcount function to work
        // and keywords = keybytes / 8.
        static constexpr int WORDBYTES = sizeof(uint64_t);
        int keywords = keybytes / WORDBYTES;
        if (keywords % 16 != 0)
            return -1;

        std::priority_queue<Node, std::vector<Node>, score_cmp> max_k_scores;

        uint32_t count_one = popcount_array(comp1, keywords);
        uint32_t max_popcnt_delta = keywords * WORDBYTES * 8; // = bits per key
        if(threshold > 0) {
            max_popcnt_delta = calculate_max_difference(count_one, threshold);
        }

        for (int j = 0; j < n; j++) {
            const uint64_t *current = comp2 + j * keywords;
            const uint32_t counts_many_j = counts_many[j];
            uint32_t current_delta;

            if (count_one > counts_many_j) {
                current_delta = count_one - counts_many_j;
            } else {
                current_delta = counts_many_j - count_one;
            }

            if (current_delta <= max_popcnt_delta) {
                double score = dice_coeff(comp1, count_one, current, counts_many_j, keywords);
                if (score >= threshold) {
                    max_k_scores.push(Node(j, score));
                    if (max_k_scores.size() > k)
                        max_k_scores.pop();
                }
            }
        }

        int i = 0;
        while ( ! max_k_scores.empty()) {
           scores[i] = max_k_scores.top().score;
           indices[i] = max_k_scores.top().index;
           max_k_scores.pop();
           i += 1;
        }
        return i;
    }

    int match_one_against_many_dice(const char *one, const char *many, int n, double *score) {

        static const double threshold = 0.0;
        static const int k = 1;
        int idx_unused;
        uint32_t *counts_many = new uint32_t[n];
        popcount_1024_array(many, n, counts_many);
        int res = match_one_against_many_dice_k_top(
            one, many, counts_many, n, 128, k, threshold, &idx_unused, score);
        delete[] counts_many;

        return res;
    }
}

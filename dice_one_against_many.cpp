#include <immintrin.h>
#include <x86intrin.h>

#include <algorithm>
#include <vector>
#include <cstdint>
#include <cstdlib>
#include <cassert>
#include <bitset>
#include <iostream>

// From ChemFP library - MIT license
static uint64_t POPCNT64(uint64_t x) {
    /* GNU GCC >= 4.2 supports the POPCNT instruction */
#if !defined(__GNUC__) || (__GNUC__ >= 4 && __GNUC_MINOR__ >= 2)
    __asm__ ("popcnt %1, %0" : "=r" (x) : "0" (x));
#endif
    return x;
}



// Source: http://danluu.com/assembly-intrinsics/
// https://stackoverflow.com/questions/25078285/replacing-a-32-bit-loop-count-variable-with-64-bit-introduces-crazy-performance
uint32_t builtin_popcnt_unrolled_errata_manual(const uint64_t* buf, int len) {
  assert(len % 4 == 0);
  uint64_t cnt[4];
  for (int i = 0; i < 4; ++i) {
    cnt[i] = 0;
  }

  for (int i = 0; i < len; i+=4) {
    __asm__(
        "popcnt %4, %4  \n\t"
        "add %4, %0     \n\t"
        "popcnt %5, %5  \n\t"
        "add %5, %1     \n\t"
        "popcnt %6, %6  \n\t"
        "add %6, %2     \n\t"
        "popcnt %7, %7  \n\t"
        "add %7, %3     \n\t" // +r means input/output, r means intput
        : "+r" (cnt[0]), "+r" (cnt[1]), "+r" (cnt[2]), "+r" (cnt[3])
        : "r"  (buf[i]), "r"  (buf[i+1]), "r"  (buf[i+2]), "r"  (buf[i+3]));
  }
  return cnt[0] + cnt[1] + cnt[2] + cnt[3];
}


// length in bits of key
// n number of keys to compare against
int match_one_against_many_dice(const char *one, const char *many, int n, int l, double &score) {
    int nbyte = int(l / 8); // assume l is divisible by 8 - 1024 bit key, 128 bytes
    int nuint64 = int(nbyte / sizeof(uint64_t)); // assume l is divisible by 64

    //  std::cerr << nbyte << " " <<nuint64<<" "<<n<<" " <<l<<"\n";

    const uint64_t *comp1 = (const uint64_t *) one;
    const uint64_t *comp2 = (const uint64_t *) many;

    uint32_t count_one = 0;
    for (int i = 0; i < nuint64; i++) {
        count_one += POPCNT64(comp1[i]);
    }
    //  std::cerr << "count_one: " << count_one << "\n";


    uint32_t *counts_many = new uint32_t[n];
    for (int j = 0; j < n; j++) {
        counts_many[j] = 0;
        const uint64_t *sig = comp2 + j * nuint64;
        for (int i = 0; i < nuint64; i++) {
            counts_many[j] += POPCNT64(sig[i]);
        }
    }

    //  std::cerr << "count_many: " <<counts_many[2] << "\n";
    //  std::cerr << std::flush;
    double best_score = -1.0;
    int best_index = -1;

    for (int j = 0; j < n; j++) {
        int count_curr = 0;
        const uint64_t *current = comp2 + j * nuint64;
        for (int i = 0; i < nuint64; i++) {
            count_curr += POPCNT64(*(current + i) & *(comp1 + i));
        }
        double score = 2 * count_curr / (double) (count_one + counts_many[j]);
        if (score > best_score) {
            best_score = score;
            best_index = j;
        }
    }

    delete counts_many;

    score = best_score;
    return best_index;

}


void print_filter(const uint64_t *filter) {
    for (int i = 0; i < 16; i++) {
        std::cout << std::bitset<64>(*(filter + i));
    }

    std::cout << std::endl;
}

extern "C"
{
    int match_one_against_many_dice_c(const char *one, const char *many, int n, int l, double *score) {
        double sc = 0.0;
        int res = match_one_against_many_dice(one, many, n, l, sc);
        *score = sc;
        return res;
    }

    int match_one_against_many_dice_1024_c(const char *one, const char *many, int n, double *score) {

        //std::cerr << "Matching " << n << " entities" << "\n";

        const uint64_t *comp1 = (const uint64_t *) one;
        const uint64_t *comp2 = (const uint64_t *) many;

        //std::cout << "f ";
        //print_filter(comp1);

        uint32_t count_one = builtin_popcnt_unrolled_errata_manual(comp1, 16);

        //std::cout << count_one << std::endl;

        uint32_t *counts_many = new uint32_t[n];

        for (int j = 0; j < n; j++) {
            const uint64_t *sig = comp2 + j * 16;
            counts_many[j] = builtin_popcnt_unrolled_errata_manual(sig, 16);
        }

        double best_score = -1.0;
        int best_index = -1;

        for (int j = 0; j < n; j++) {
            const uint64_t *current = comp2 + j * 16;

            //std::cout << j << " "; //print_filter(comp2);

            uint64_t* combined = new uint64_t[16];
            for (int i=0 ; i < 16; i++ ) {
                combined[i] = current[i] & comp1[i];
            }

            uint32_t count_curr = builtin_popcnt_unrolled_errata_manual(combined, 16);

            double score = 2 * count_curr / (double) (count_one + counts_many[j]);

            //std::cout << "shared popcnt: " << count_curr << " count_j: " << counts_many[j] << " Score: " << score <<  std::endl;
            if (score > best_score) {
                best_score = score;
                best_index = j;
            }
            delete combined;
        }

        delete counts_many;


        //std::cerr << "Best score: " << best_score << " at index " << best_index << "\n";

        *score = best_score;
        return best_index;

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
     * Return the top k indices and scores.
     */
    void match_one_against_many_dice_1024_k_top(const char *one, const char *many, int n, int k, int *indices, double *scores) {

        //std::cerr << "Matching top " << k << " of " << n << " entities" << "\n";

        const uint64_t *comp1 = (const uint64_t *) one;
        const uint64_t *comp2 = (const uint64_t *) many;

        std::vector<Node> all_scores;

        uint32_t count_one = builtin_popcnt_unrolled_errata_manual(comp1, 16);

        //std::cout << count_one << std::endl;

        uint32_t *counts_many = new uint32_t[n];

        for (int j = 0; j < n; j++) {
            const uint64_t *sig = comp2 + j * 16;
            counts_many[j] = builtin_popcnt_unrolled_errata_manual(sig, 16);
        }

        double best_score = -1.0;
        int best_index = -1;

        for (int j = 0; j < n; j++) {
            const uint64_t *current = comp2 + j * 16;

            //std::cout << j << " "; //print_filter(comp2);

            uint64_t* combined = new uint64_t[16];
            for (int i=0 ; i < 16; i++ ) {
                combined[i] = current[i] & comp1[i];
            }

            uint32_t count_curr = builtin_popcnt_unrolled_errata_manual(combined, 16);

            double score = 2 * count_curr / (double) (count_one + counts_many[j]);
            all_scores.push_back(Node(j, score));

            //std::cout << "shared popcnt: " << count_curr << " count_j: " << counts_many[j] << " Score: " << score <<  std::endl;
            if (score > best_score) {
                best_score = score;
                best_index = j;
            }
            delete combined;
        }

        delete counts_many;

        //std::cerr << "Best score: " << best_score << " at index " << best_index << "\n";

        // Sort scores
        std::make_heap (all_scores.begin(), all_scores.end(), score_cmp());

        std::sort_heap (all_scores.begin(), all_scores.end(), score_cmp());

        //std::cout << "final sorted range :";
        for (int i=0; i < all_scores.size(); i++) {
            //std::cout << ' ' << all_scores[i].score;
            if(i < k) {
                scores[i] = all_scores[i].score;
                indices[i] = all_scores[i].index;
            }
        }

    }

}

#include <immintrin.h>
#include <x86intrin.h>

#include <cstdint>
#include <cstdlib>
#include <cassert>

#include <iostream>

// From ChemFP library - MIT license

static uint64_t POPCNT64(uint64_t x) {
  /* GNU GCC >= 4.2 supports the POPCNT instruction */
#if !defined(__GNUC__) || (__GNUC__ >= 4 && __GNUC_MINOR__ >= 2)
  __asm__ ("popcnt %1, %0" : "=r" (x) : "0" (x));
#endif
  return x;
}

// length in bits of key
// n number of keys to compare against
int match_one_against_many_dice(const char * one, const char * many, int n, int l, double & score)
{
  int nbyte = int(l/8); // assume l is divisible by 8 - 1024 bit key, 128 bytes
  int nuint64 = int(nbyte / sizeof(uint64_t)); // assume l is divisible by 64
  
  //  std::cerr << nbyte << " " <<nuint64<<" "<<n<<" " <<l<<"\n";

  const uint64_t * comp1 = (const uint64_t *)one;
  const uint64_t * comp2 = (const uint64_t *)many;

  uint32_t count_one = 0;
  for(int i =0; i < nuint64; i++)
  {
    count_one += POPCNT64(comp1[i]);
  }
  //  std::cerr << "count_one: " << count_one << "\n";


  uint32_t * counts_many = new uint32_t[n];
  for(int j = 0; j < n; j++)
  { 
    counts_many[j] = 0;
    const uint64_t *sig =  comp2 + j * nuint64;
    for(int i =0; i < nuint64; i++)
    {
      counts_many[j] += POPCNT64(sig[i]);
    }
  }

  //  std::cerr << "count_many: " <<counts_many[2] << "\n";
  //  std::cerr << std::flush;
  double best_score = -1.0;
  int best_index = -1;

  for(int j = 0; j < n; j++)
  {
    int count_curr = 0;
    const uint64_t * current = comp2 + j * nuint64;
    for(int i=0; i < nuint64; i++)
    {
      count_curr += POPCNT64(*(current+i) & *(comp1+i));
    }
    double score = 2*count_curr/(double)(count_one + counts_many[j]); 
    if(score > best_score)
      {
	best_score = score;
	best_index = j;
      }
  }

  delete counts_many;

  score = best_score;
  return best_index;

}




extern "C"
{
  int match_one_against_many_dice_c(const char * one, const char * many, int n, int l, double * score)
  {
    double sc = 0.0;
    int res = match_one_against_many_dice(one, many, n, l, sc);
    *score = sc;
    return res;
  }

  int match_one_against_many_dice_1024_c(const char * one, const char * many, int n, double * score)
  {
  
  //  std::cerr << nbyte << " " <<nuint64<<" "<<n<<" " <<l<<"\n";

  const uint64_t * comp1 = (const uint64_t *)one;
  const uint64_t * comp2 = (const uint64_t *)many;

  uint32_t count_one = POPCNT64(*(comp1));
  count_one += POPCNT64(*(comp1 + 1));
  count_one += POPCNT64(*(comp1 + 2));
  count_one += POPCNT64(*(comp1 + 3));
  count_one += POPCNT64(*(comp1 + 4));
  count_one += POPCNT64(*(comp1 + 5));
  count_one += POPCNT64(*(comp1 + 6));
  count_one += POPCNT64(*(comp1 + 7));
  count_one += POPCNT64(*(comp1 + 8));
  count_one += POPCNT64(*(comp1 + 9));
  count_one += POPCNT64(*(comp1 + 10));
  count_one += POPCNT64(*(comp1 + 11));
  count_one += POPCNT64(*(comp1 + 12));
  count_one += POPCNT64(*(comp1 + 13));
  count_one += POPCNT64(*(comp1 + 14));
  count_one += POPCNT64(*(comp1 + 15));

  uint32_t * counts_many = new uint32_t[n];
  for(int j = 0; j < n; j++)
  { 
    const uint64_t *sig =  comp2 + j * 16;
    counts_many[j] = POPCNT64(*(sig));
    counts_many[j] += POPCNT64(*(sig+1));
    counts_many[j] += POPCNT64(*(sig+2));
    counts_many[j] += POPCNT64(*(sig+3));
    counts_many[j] += POPCNT64(*(sig+4));
    counts_many[j] += POPCNT64(*(sig+5));
    counts_many[j] += POPCNT64(*(sig+6));
    counts_many[j] += POPCNT64(*(sig+7));
    counts_many[j] += POPCNT64(*(sig+8));
    counts_many[j] += POPCNT64(*(sig+9));
    counts_many[j] += POPCNT64(*(sig+10));
    counts_many[j] += POPCNT64(*(sig+11));
    counts_many[j] += POPCNT64(*(sig+12));
    counts_many[j] += POPCNT64(*(sig+13));
    counts_many[j] += POPCNT64(*(sig+14));
    counts_many[j] += POPCNT64(*(sig+15));
  }				       

  double best_score = -1.0;
  int best_index = -1;

  for(int j = 0; j < n; j++)
  {
    const uint64_t * current = comp2 + j * 16;
    int count_curr;
    count_curr = POPCNT64(*(current) & *(comp1));
    count_curr += POPCNT64(*(current+1) & *(comp1+1));
    count_curr += POPCNT64(*(current+2) & *(comp1+2));
    count_curr += POPCNT64(*(current+3) & *(comp1+3));
    count_curr += POPCNT64(*(current+4) & *(comp1+4));
    count_curr += POPCNT64(*(current+5) & *(comp1+5));
    count_curr += POPCNT64(*(current+6) & *(comp1+6));
    count_curr += POPCNT64(*(current+7) & *(comp1+7));
    count_curr += POPCNT64(*(current+8) & *(comp1+8));
    count_curr += POPCNT64(*(current+9) & *(comp1+9));
    count_curr += POPCNT64(*(current+10) & *(comp1+10));
    count_curr += POPCNT64(*(current+11) & *(comp1+11));
    count_curr += POPCNT64(*(current+12) & *(comp1+12));
    count_curr += POPCNT64(*(current+13) & *(comp1+13));
    count_curr += POPCNT64(*(current+14) & *(comp1+14));
    count_curr += POPCNT64(*(current+15) & *(comp1+15));

    double score = 2*count_curr/(double)(count_one + counts_many[j]); 
    if(score > best_score)
    {
	    best_score = score;
	    best_index = j;
    }
  }

  delete counts_many;

  *score = best_score;
  return best_index;

  }

}

#ifndef _multiparty_solving_inner_h
#define _multiparty_solving_inner_h

#include <unordered_set>

struct Record {
    unsigned int dset_i;
    unsigned int rec_i;
    
    Record() {}
    Record(unsigned int dset_i_, unsigned int rec_i_) : dset_i(dset_i_), rec_i(rec_i_) {}
    bool operator==(const Record &other) const {
        return dset_i == other.dset_i && rec_i == other.rec_i;
    }
};


// These are only ever made inside the GroupsStore class in _multiparty_solving_inner.
// They are always created with at least one element. Elements are never deleted. Thus, they are
// always nonempty.
typedef std::vector<Record> Group;


std::unordered_set<Group *>
greedy_solve_inner(
    unsigned int dset_is0[],
    unsigned int dset_is1[],
    unsigned int rec_is0[],
    unsigned int rec_is1[],
    size_t n,
    double merge_threshold,
    bool deduplicated);

#endif /* _multiparty_solving_inner_h */

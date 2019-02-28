#include <algorithm>
#include <cassert>
#include <unordered_map>
#include <vector>
#include "_multiparty_solving_inner.h"

namespace {

struct RecordHasher {
    std::hash<uint64_t> hasher;
    size_t operator()(const Record &record) const {
        return hasher(static_cast<uint64_t>(record.dset_i) << 32
                      ^ static_cast<uint64_t>(record.rec_i));
    }
};


class GroupsStore {
// A group is a set of records. GroupsStore stores all records as members of disjoint sets.

private:
    // Map from a record to the group containing it.
    std::unordered_map<Record, Group*, RecordHasher> record_group_map;
    
#ifndef NDEBUG
    bool in_group(Record record) const {
        // Check if the record belongs to some group.
        return record_group_map.count(record);
    }

    bool group_consistent(Group *group) {
        // Ensure that for all r in group, record_group_map[r] == group.
        return std::all_of(
            group->cbegin(), group->cend(),
            [this, group](Record r) {
                return record_group_map.at(r) == group;
            });
    }
#endif /* !NDEBUG */
    
public:
    Group *get_group(Record record) const {
        // Get the group that a record belongs to.
        // Return nullptr if it does not belong to any group.
        
        auto res_iterator = record_group_map.find(record);
        if (res_iterator == record_group_map.end()) {
            return nullptr;
        } else {
            Group *retval = res_iterator->second;
            assert(retval);
            assert(retval->size());
            return retval;
        }
    }
    
    Group *make_group(Record record) {
        // Makes a new group containing only one record. Stores it. Returns the group.
        
        assert(!in_group(record));
        
        Group *group = new Group {record};
        record_group_map[record] = group;
        return group;
    }
    
    Group *make_group(Record record0, Record record1) {
        // Makes a new group containing two records. Stores it. Returns the group.
        
        assert(!in_group(record0));
        assert(!in_group(record1));
        assert(record0 != record1);
        
        Group *group = new Group {record0, record1};
        record_group_map[record0] = group;
        record_group_map[record1] = group;
        return group;
    }

    Group *add_to_group(Group *group, Record record) {
        // Adds a record to an existing group. Stores the reference. Returns the group.
        
        assert(!in_group(record));
        assert(group);
        assert(group_consistent(group));
        assert(group->size());

        group->push_back(record);
        record_group_map[record] = group;
        return group;
    }
    
    Group *merge_into(Group * __restrict__ absorber, Group * __restrict__ absorbee) {
        // Merges two existing groups. The records in absorbee are moved into absorber.
        // The absorbee is freed and should no longer be dereferenced.
        // Returns the merged group (the absorber).

        assert(absorber);
        assert(absorbee);
        assert(absorbee != absorber);
        assert(group_consistent(absorber));
        assert(group_consistent(absorbee));
        assert(absorber->size());
        assert(absorbee->size());

        // Move records over.
        absorber->reserve(absorber->size() + absorbee->size());
        absorber->insert(absorber->end(), absorbee->cbegin(), absorbee->cend());

        // Ensure that all records point at the merged group.
        for (const auto &item : *absorbee) {
            record_group_map[item] = absorber;
        }

        delete absorbee;
        return absorber;
    }
    
    std::unordered_set<Group *> get_groups() {
        // Returns the set of unique groups.

        // Make set of all unique groups.
        std::unordered_set<Group *> unique_groups;
        for (const auto &item : record_group_map) {
            Group * const group = item.second;
            assert(group->size());
            unique_groups.insert(group);
        }

        return unique_groups;
    }
};

template <class T>
class EdgesMatrix {
// Recall that two groups are merged iff every pair of records has been encountered as a candidate
// pair. This data structure is a symmetric sparse matrix that stores the number of edges
// encountered between two groups. It supports two operations:
// 1. increment the number of edges between two groups by one and return the new number
// 2. merge a column into another column (and also merge the corresponding rows); this is used when
//    we are merging two groups together.

private:
    typedef unsigned long long CountType;

    typedef std::unordered_map<T, CountType> Column;
    typedef std::unordered_map<T, Column> SparseMatrix;
    
    SparseMatrix sparse_matrix;
    
    CountType set_or_increment(T key0, T key1, CountType n) {
        // Increment entry at column key0, row key1 by n if it exists. Set to n if it doesn't.
        
        // This makes a new object at sparse_matrix[key0] if one doesn't already exist.
        Column &column = sparse_matrix[key0];
        return set_or_increment(column, key1, n);
    }
    
    CountType set_or_increment(Column &key0_column, T key1, CountType n) {
        // Increment entry at key0_column, row key1 by n if it exists. Set to n if it doesn't.

        // Set entry to 0 if it doesn't exist and get the reference.
        std::pair<typename Column::iterator, bool> emplace_res
            = key0_column.emplace(key1, 0);
        typename Column::iterator &count_iterator = emplace_res.first;
        CountType &entry_ref = count_iterator->second;

        // Increment the entry by n in place.
        entry_ref += n;
        
        return entry_ref;
    }
    
public:
    CountType increment(T key0, T key1) {
        // Call set_or_increment twice for symmetry.
        CountType retval0 = set_or_increment(key0, key1, 1);
        CountType retval1[[maybe_unused]] = set_or_increment(key1, key0, 1);
        
        assert(retval0 == retval1); // Assert symmetric.
        
        return retval0;
    }
    
    void merge_into(T absorber_key, T absorbee_key) {
        assert(absorber_key != absorbee_key);
        Column &absorber_store = sparse_matrix[absorber_key];
        Column &absorbee_store = sparse_matrix[absorbee_key];
        
        // Merging two groups.
        // matrix[absorbee][absorber] and matrix[absorbee][absorber] are no longer needed.
        absorber_store.erase(absorbee_key);
        absorbee_store.erase(absorber_key);

        // Move all the edges from absorbee to absorber. Same with edges referencing absorbee.
        for (const auto &edge_count : absorbee_store) {
            T edge = edge_count.first;
            assert(edge);
            CountType count = edge_count.second;
            assert(count);
            
            // Move edge count from absorbee to absorber.
            set_or_increment(absorber_key, edge, count);
            
            // Edge count (from some third group) referencing absorbee will now reference absorber.
            Column &mp_match = sparse_matrix[edge];
            set_or_increment(mp_match, absorber_key, count);
            mp_match.erase(absorbee_key);
        }

        // Column no longer needed.
        sparse_matrix.erase(absorbee_key);

        // Possible cleanup.
        if (absorber_store.empty()) {
            sparse_matrix.erase(absorber_key);
        }
    }
    
};


// Check if there exists a datset that has more than one element in the two groups.
// If so, and if we assume that the two datasets are deduplicated, then we cannot merge the groups.
bool check_no_duplicates(Record i0, Record i1) {
    return i0.dset_i != i1.dset_i;
}
bool check_no_duplicates(Record i0, Group *group1) {
    return std::all_of(group1->cbegin(), group1->cend(),
                       [i0](Record r) {
                           return check_no_duplicates(i0, r);
                       });
}
bool check_no_duplicates(Group *group0, Group *group1) {
    return std::all_of(group0->cbegin(), group0->cend(),
                       [group1](Record r) {
                           return check_no_duplicates(r, group1);
                       });
}


void none_grouped(GroupsStore &groups_store, Record i0, Record i1, bool deduplicated) {
    if (!deduplicated || check_no_duplicates(i0, i1)) {
        // Neither is in a group, so let's make one.
        groups_store.make_group(i0, i1);
    }
    // If they are duplicates from the same datasets, then they will never be in the same group, so
    // there is no point making singleton groups for them.
}

void one_grouped(GroupsStore &groups_store,
                 EdgesMatrix<Group *> &edges_store,
                 Group *group,
                 Record i,
                 double merge_threshold,
                 bool deduplicated) {
    if (1.0 >= merge_threshold * group->size()) {
        if (!deduplicated || check_no_duplicates(i, group)) {
            // We have two singletons (one has a group of itself, one doesn't), so we can merge.
            groups_store.add_to_group(group, i);
        }
    } else {
        // The group has at least 2 elements. We've only matched with one so far (or else we'd
        // already have a group of size at least one), so we can't merge.
        Group *group_i = groups_store.make_group(i);
        edges_store.increment(group, group_i);
    }
}

void two_grouped_merge(GroupsStore &groups_store,
                       EdgesMatrix<Group *> &edges_store,
                       Group *absorber,
                       Group *absorbee) {
    // Merge the two groups.
    // Merge the two sets of records.
    groups_store.merge_into(absorber, absorbee);
    // Merge the relevant columns/rows of the sparse edges matrix.
    edges_store.merge_into(absorber, absorbee);
}

void two_grouped(GroupsStore &groups_store,
                 EdgesMatrix<Group *> &edges_store,
                 Group *group0,
                 Group *group1,
                 double merge_threshold,
                 bool deduplicated) {
    if (group0 == group1) {
        return; // Already grouped together. Nothing to do.
    }

    double overlap = edges_store.increment(group0, group1);
    auto group_0_size = group0->size();
    auto group_1_size = group1->size();
    // The below is equivalent to: for every pair of records in the Cartesian product of group 0 and
    // group 1, we've encountered an edge.
    if (overlap >= merge_threshold * group_0_size * group_1_size) {
        if (!deduplicated || check_no_duplicates(group0, group1)) {
            // Optimise by enlarging the bigger group.
            if (group_0_size < group_1_size) {
                two_grouped_merge(groups_store, edges_store, group1, group0);
            } else {
                two_grouped_merge(groups_store, edges_store, group0, group1);
            }
        }
    }
}

} /* namespace */

std::unordered_set<Group *>
greedy_solve_inner(unsigned int dset_is0[],
                   unsigned int dset_is1[],
                   unsigned int rec_is0[],
                   unsigned int rec_is1[],
                   size_t n,
                   double merge_threshold,
                   bool deduplicated) {
    // Keep track of groups that have already been formed.
    GroupsStore groups_store;

    // Keep track of edges between records that we've encountered. We only merge two groups if
    // we've encountered edges between all their records.
    EdgesMatrix<Group *> edges_store;

    for (size_t i = 0; i < n; ++i) {
        Record i0(dset_is0[i], rec_is0[i]);
        Record i1(dset_is1[i], rec_is1[i]);

        if (i0 == i1) {
            continue; // Record trivially grouped with itself. Nothing to do.
        }

        // These will be nullptr if the corresponding records don't already belong do a group.
        Group *group_i0 = groups_store.get_group(i0);
        Group *group_i1 = groups_store.get_group(i1);
        
        if (group_i0) {
            assert(group_i0->size());
            if (group_i1) {
                assert(group_i1->size());
                two_grouped(groups_store, edges_store,
                            group_i0, group_i1,
                            merge_threshold, deduplicated);
            } else {
                one_grouped(groups_store, edges_store,
                            group_i0, i1,
                            merge_threshold, deduplicated);
            }
        } else {
            if (group_i1) {
                assert(group_i1->size());
                one_grouped(groups_store, edges_store,
                            group_i1, i0,
                            merge_threshold, deduplicated);
            } else {
                none_grouped(groups_store, i0, i1, deduplicated);
            }
        }
    }

    return groups_store.get_groups();
}

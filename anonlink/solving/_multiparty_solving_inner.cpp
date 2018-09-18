#include <unordered_map>
#include <unordered_set>
#include "_multiparty_solving_inner.h"

struct RecordHasher {
    size_t operator()(const Record &record) const {
        return (std::hash<int>()(record.dset_i) << 1) ^ std::hash<int>()(record.rec_i);
    }
};



class GroupsStore {
private:
    typedef std::unordered_map<Record, Group*, RecordHasher> InnerStore;
    InnerStore inner_store;
    
#ifndef NDEBUG
    bool in_group(Record record) const {
        return this->inner_store.count(record);
    }
#endif /* NDEBUG */
    
public:
    Group *get_group(Record record) const {
        auto res_iterator = this->inner_store.find(record);
        if (res_iterator == this->inner_store.end()) {
            return nullptr;
        } else {
            Group *retval = res_iterator->second;
            assert(retval);
            return retval;
        }
    }
    
    Group *make_group(Record record) {
        assert(!this->in_group(record));
        Group *group = new Group {record};
        this->inner_store[record] = group;
        return group;
    }
    
    Group *make_group(Record record0, Record record1) {
        assert(!this->in_group(record0));
        assert(!this->in_group(record1));
        Group *group = new Group {record0, record1};
        this->inner_store[record0] = group;
        this->inner_store[record1] = group;
        return group;
    }
    
    Group *add_to_group(Group *group, Record record) {
        assert(!this->in_group(record));
        assert(group);
        assert(std::all_of(group->cbegin(),
                           group->cend(),
                           [this, group](Record r) { return this->inner_store.at(r) == group; }));
        group->push_back(record);
        this->inner_store[record] = group;
        return group;
    }
    
    Group *merge_into(Group * __restrict__ absorber, Group * __restrict__ absorbee) {
        assert(absorber);
        assert(absorbee);
        assert(std::all_of(absorber->cbegin(),
                           absorber->cend(),
                           [this, absorber](Record r) {
                               return this->inner_store.at(r) == absorber;
                           }));
        assert(std::all_of(absorbee->cbegin(),
                           absorbee->cend(),
                           [this, absorbee](Record r) {
                               return this->inner_store.at(r) == absorbee;
                           }));
        absorber->reserve(absorber->size() + absorbee->size());
        absorber->insert(absorber->end(), absorbee->cbegin(), absorbee->cend());
        for (const auto &item : *absorbee) {
            this->inner_store[item] = absorber;
        }
        delete absorbee;
        return absorber;
    }
    
    std::vector<Group *> retrieve_nontrivial_groups() {
        std::unordered_set<Group *> all_groups;
        for (const auto &item : this->inner_store) {
            all_groups.insert(item.second);
        }
        
        std::vector<Group *> retval;
        for (const auto &group : all_groups) {
            if (group->size() > 1) {
                retval.push_back(group);
            } else {
                delete group;
            }
        }
        
        return retval;
    }
};

class LinksStore {
private:
    typedef std::unordered_map<Group*, size_t> LinksStoreInnerInner;
    typedef std::unordered_map<Group*, LinksStoreInnerInner> LinksStoreInner;
    
    LinksStoreInner links_store_inner;
    
    size_t links_noassert(Group *group0, Group *group1) const {
        auto outer_iterator = this->links_store_inner.find(group0);
        if (outer_iterator == this->links_store_inner.end()) {
            return 0;
        } else {
            auto inner_iterator = outer_iterator->second.find(group1);
            if (inner_iterator == outer_iterator->second.end()) {
                return 0;
            } else {
                return inner_iterator->second;
            }
        }
    }
    
    inline size_t set_or_increment(Group *group0, Group *group1, size_t n) {
        return this->links_store_inner[group0].try_emplace(group1, 0).first->second += n;
    }
    
    inline size_t set_or_increment(LinksStoreInnerInner &group0_store, Group *group1, size_t n) {
        return group0_store.try_emplace(group1, 0).first->second += n;
    }
    
public:
    size_t increment(Group *group0, Group *group1) {
        assert(group0);
        assert(group1);
        size_t retval1 = this->set_or_increment(group0, group1, 1);
        size_t retval2 = this->set_or_increment(group1, group0, 1);
        assert(retval1 == retval2);
        return retval1;
    }
    
    void merge_into(Group *absorber, Group *absorbee) {
        assert(absorber);
        assert(absorbee);
        LinksStoreInnerInner &absorber_store = this->links_store_inner[absorber];
        LinksStoreInnerInner &absorbee_store = this->links_store_inner[absorbee];
        
        absorber_store.erase(absorbee);
        absorbee_store.erase(absorber);
        for (const auto &link_count : absorbee_store) {
            Group *link = link_count.first;
            assert (link);
            size_t count = link_count.second;
            assert (count);
            
            this->set_or_increment(absorber, link, count);
            
            LinksStoreInnerInner &mp_match = this->links_store_inner[link];
            set_or_increment(mp_match, absorber, count);
            mp_match.erase(absorbee);
        }
        this->links_store_inner.erase(absorbee);
        if (absorber_store.empty()) {
            this->links_store_inner.erase(absorber);
        }
    }
    
};


void none_grouped(GroupsStore &groups_store, Record i0, Record i1) {
    groups_store.make_group(i0, i1);
}

void one_grouped(GroupsStore &groups_store, LinksStore &links_store, Group *group, Record i) {
    if (group->size() == 1) {
        groups_store.add_to_group(group, i);
    } else {
        Group *group_i = groups_store.make_group(i);
        links_store.increment(group, group_i);
    }
}

void two_grouped_merge(GroupsStore &groups_store,
                       LinksStore &links_store,
                       Group *absorber,
                       Group *absorbee) {
    groups_store.merge_into(absorber, absorbee);
    links_store.merge_into(absorber, absorbee);
}

void two_grouped(GroupsStore &groups_store, LinksStore &links_store, Group *group0, Group *group1) {
    size_t overlap = links_store.increment(group0, group1);
    size_t group_0_size = group0->size();
    size_t group_1_size = group1->size();
    if (overlap == group_0_size * group_1_size) {
        if (group_0_size < group_1_size) {
            two_grouped_merge(groups_store, links_store, group1, group0);
        } else {
            two_grouped_merge(groups_store, links_store, group0, group1);
        }
    }
}

std::vector<Group *>
greedy_solve_inner(
                   unsigned int dset_is0[],
                   unsigned int dset_is1[],
                   unsigned int rec_is0[],
                   unsigned int rec_is1[],
                   size_t n
                   ) {
    GroupsStore groups_store;
    LinksStore links_store;

    for (size_t i = 0; i < n; ++i) {
        Record i0(dset_is0[i], rec_is0[i]);
        Record i1(dset_is1[i], rec_is1[i]);

        Group *group_i0 = groups_store.get_group(i0);
        Group *group_i1 = groups_store.get_group(i1);
        
        if (group_i0) {
            if (group_i1) {
                two_grouped(groups_store, links_store, group_i0, group_i1);
            } else {
                one_grouped(groups_store, links_store, group_i0, i1);
            }
        } else {
            if (group_i1) {
                one_grouped(groups_store, links_store, group_i1, i0);
            } else {
                none_grouped(groups_store, i0, i1);
            }
        }
    }

    return groups_store.retrieve_nontrivial_groups();
}

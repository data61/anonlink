Proposal: 1
Title: Proposal Process
Author: Brian Thorne
Status: Draft
Created: 2019-11-4

## Abstract

Proposals for major features and changes to the anonlink library shall be written before implementation. This 
facilitates better communication of the proposal, as well as the potential to improved designs due to earlier 
feedback.

We intend proposals to be the primary mechanism for proposing major new features, for collecting team and community 
input on an issue, and for documenting the design decisions that have gone into anonlink. The author is responsible 
for building consensus and documenting dissenting opinions.

Proposals are maintained as text files in the versioned repository, their revision history is the historical record
of the feature proposal.

## Details

### Motivation 

The audience of these proposals are developers of anonlink.
A proposals should contain a single key feature or new idea. Small enhancements or patches don't need a proposal.

### Technical Specifications

#### Document

Proposal documents live in the `docs/proposals` folder of the `anonlink` library. Proposals are written
in Markdown (or RST?)

Proposal documents will be named `prop-{n}-{short-name}.md`.
 
This meta proposal is therefore found in the file: `prop-1-proposals.md`.

#### Auxiliary Files

Additional files (such as diagrams or scripts) should be placed in a folder with the name `prop-n`.

#### Proposal Contents

At a minimum a proposal needs to have:

- Abstract - a short (~200 word) abstract.
- Preamble (Title, List of authors, Proposal Number)
- Proposal Details

The proposal details will usually include:  

- motivation - Clearly explain why the proposal is being made. 
- rational - why particular design decisions were made. It should describe alternate designs that were considered and related work
- technical specification - This should be detailed enough to write an implementation from.
- rejected ideas - Often various ideas will be proposed that are rejected for some reason. Ideally these ideas should be 
  recorded along with the reasoning as to why they were rejected.
- Open Issues
- Backwards Compatibility
- references

#### Preamble

Each proposal must begin with an RFC 822 style header preamble. The headers must appear in the following order. 
Headers marked with "*" are optional and are described below.

```
Proposal: <proposal number>
Title: <proposal title>
Author: <list of authors real names>
Status: <Draft | Active | Accepted | Provisional | Deferred | Rejected |
         Withdrawn | Final | Superseded>
Created: <date first written, in yyyy-mm-dd format>
```



### References

- The python enhancement proposal process https://www.python.org/dev/peps/pep-0001/
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
input on an issue, and for documenting the design decisions that have gone into anonlink. A proposal should provide
a concise technical specification of the feature or change and the rationale behind it.

The author is responsible for building consensus and documenting dissenting opinions.

The audience of these proposals are developers of anonlink itself. Proposals are maintained as text files in the
versioned repository, their revision history is the historical record of the feature proposal. 

## Motivation 


## Workflow

The more focused the proposal, the more successful it tends to be. If in doubt, split into several well-focused ones.

Each proposal must have a champion — someone who writes the proposal using the style and format described below, 
shepherds the discussions in the appropriate forums, and attempts to build community consensus around the idea. 

The proposal should be submitted as a draft proposal via a GitHub pull request to the `docs/proposals` directory with 
the name prop-<n>-<short-title>.md where <n> is an appropriately assigned 4 digit number 
(e.g., prop-0000-fooDescription.rst). The draft must comply with the technical specifications outlined below.

Once the PR for the proposal is in place, a post should be made to the mailing list containing the abstract and a link
to the PR, with the purpose of starting discussion on usage and impact. Discussion on the pull request will have a 
broader scope, also including details of implementation.

At the earliest convenience, the PR should be merged (regardless of whether it is accepted during discussion). 
Additional PRs may be made by the Author/s to update or expand the proposal, or by maintainers to set its status, and 
links to discussion URLs, etc.

It is generally recommended that a *prototype* implementation be co-developed with the proposal, as ideas that sound 
good in principle sometimes turn out to be impractical when subjected to the test of implementation. Often it 
makes sense for the prototype implementation to be made available as a separate PR to the repo (making sure to 
appropriately mark the PR as a WIP). Another option is to include a prototype as an auxiliary file along with the 
proposal. 

## Review and Resolution

Proposals are discussed on the anonlink mailing list. The possible paths of the status of a proposal are:

![](prop-0001/resolution-process.png)

Eventually, after discussion, there may be a consensus that the proposal should be accepted – see the next section 
for details. At this point the status becomes `Accepted`.

Once a Proposal has been `Accepted`, the implementation or change must be completed (incorporated into the main source 
code repository) before updating the status of the proposal to `Final`.

To allow gathering of additional design and interface feedback before committing to long term stability for a 
feature or standard library API, a Proposal may also be marked as `Provisional`. This is short for "Provisionally
Accepted", and indicates that the proposal has been accepted for inclusion, but additional user feedback is needed
before the full design can be considered `Final`. Unlike regular accepted proposals, provisionally accepted
proposals may still be `Rejected` or `Withdrawn` even after the related changes have been included in a release.

Wherever possible, it is preferable to reduce the scope of a proposal to avoid the need to rely on the `Provisional`
status (e.g. by deferring some features to later).

A Proposal can also be assigned status `Deferred`. The author or any core developer can assign this status
when no progress is being made on a Proposal.

A Proposal can also be `Rejected`. Perhaps after all is said and done it was not a good idea. It is still important to
have a record of this fact. The `Withdrawn` status is similar — it means that the author themselves has decided that
the Proposal is actually a bad idea, or has accepted that a competing proposal is a better alternative.

When a Proposal is `Accepted`, `Rejected`, or `Withdrawn`, the status should be updated accordingly. In addition to
updating the status field, the Resolution header should be added with a link to the relevant PR or thread in the mailing
list archives.

Proposals can also be superseded by a different Proposal, rendering the original obsolete. The status should be updated
to `Replaced` and the `Replaced-By` and `Replaces` headers should be added to the original and new Proposals 
respectively.

Process proposals may have a status of `Active` if they are never meant to be completed, e.g. this proposal.

## Maintenance

In general, proposals are no longer modified after they have reached the `Final` state. The code and project 
documentation are considered the ultimate reference for implemented features. However, `Active` proposals
may be updated over time to reflect changes to development practices and other details. The precise process followed in
these cases will depend on the nature and purpose of the update.


## Technical Specifications

### Document

Proposal documents live in the `docs/proposals` folder of the `anonlink` library. Proposals are written
in Markdown.

Proposal documents will be named `prop-{n}-{short-name}.md`.
 
This meta proposal is therefore found in the file: `prop-1-proposals.md`.

### Auxiliary Files

Additional files (such as diagrams or scripts) should be placed in a folder with the name `prop-n`.

### Proposal Contents

A proposals should contain a single key feature or new idea. Small enhancements or patches don't need a proposal.

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

### Preamble

Each proposal must begin with an [RFC 822](https://tools.ietf.org/html/rfc822.html) style header preamble. The headers
must appear in the following order. Headers marked with "*" are optional and are described below.

```
Proposal: <proposal number>
Title: <proposal title>
Author: <list of authors real names>
Status: <Draft | Active | Accepted | Provisional | Deferred | Rejected |
         Withdrawn | Final | Superseded>
Created: <date first written, in yyyy-mm-dd format>
* Replaces: <Proposal number>
* Replaced By: <Proposal number>
```

All proposals should begin with a status of `Draft`.

## Open Issues

- Should proposals just apply to the anonlink library, or anything related to the project.
- Where should proposals live - here in the anonlink library docs or a new repository?
- The process for accepting/rejecting/adopting a proposal
- Proposals are discussed on the anonlink mailing list and/or GitHub PR?
- Should this document mandate an _index_ of proposals?
- Markdown versus reStructuredText

## References

- The python enhancement proposal process https://www.python.org/dev/peps/pep-0001/
- Numpy enhancement proposals https://numpy.org/neps/nep-0000
- Anonlink mailing list https://groups.google.com/forum/#!forum/anonlink

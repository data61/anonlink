Proposal: 1
Title: Releasing Anonlink
Author: Brian Thorne
Status: Draft
Created: 2019-11-5

## Abstract

This proposal outlines a design for automated packaging and releasing of anonlink using our primary CI/CD system - 
Microsoft's Azure DevOps [^1].

## Motivation 

An automated process for releasing Anonlink allows for more frequent releases and ensures that releases are
packaged, reviewed and communicated consistently.

### Current Manual Process

The process that team members carry out before adoption of this proposal is as follows:

 - Update the version in `setup.py`. Use semantic versions.
 - Update the `CHANGELOG.rst`
 - Create a `release-{version}` branch from an up to date master branch and request a code review.
 - Tag the commit with the version by creating a GitHub release https://github.com/data61/anonlink/releases, include the changelog.
 - This triggers the CI systems (Travis and Azure) to build and upload artifacts to PyPi.
 - check on [pypi](https://pypi.org/project/anonlink/#history) that release appears and then check that it is indeed pip installable.
 - Manually upload release artifacts (such as binary wheels and the tar.gz file) to the GitHub release page.
 - proudly announce the new release on the anonlink google group https://groups.google.com/forum/#!forum/anonlink

## Technical Specifications

The proposed release process is to create a new "release pipeline" in Azure DevOps that is triggered on a tagged
commit. It is expected the tag is added using GitHub's release interface.

The release pipeline will:
- (If necessary) extract the version from `setup.py`,
- pull the artifacts from the [CI feed](https://dev.azure.com/data61/Anonlink/_packaging?_a=feed&feed=anonlink),
- automatically upload release artifacts to PyPi, and
- upload release artifacts to GitHub.

The full release process is then:

- Update the version in `setup.py` using a semantic version.
- Update the `CHANGELOG.rst`
- Create a `release-{version}` branch from an up to date master branch and request a code review.
- Tag the commit with the version by creating a GitHub release https://github.com/data61/anonlink/releases, include the changelog.
- This triggers the CI system to build and upload artifacts to PyPi and GitHub
- proudly announce the new release on the anonlink google group https://groups.google.com/forum/#!forum/anonlink
 

## Rejected Ideas

Creating a new release every merge into master was one idea that was explored. This idea was rejected as we wanted
to retain more control of when a release is made and how many changes are bundled into a single release.

Having the CI/CD system create the git tag was explored, where the CI/CD system could have a manual trigger acting as
a _Release_ button that could create the tag and GitHub release entirely. This was rejected as we believe having a
human in the loop sanity checking and editing the changelog is required. 

## Open Issues

There is the possibility of version discrepancy between what is used by `setup.py` when building and installing
the library and the git tag marking a release. In the author's view the git tag should be the source of truth for
a release - a modification to how the version is computed could mean various release candidates could be created
without changing the codebase simply by tagging a commit with e.g. `release-1.0.0.rc1`. Currently the version is
stored as a string literal in `setup.py`, however this could first check for an environment variable, or read the
version from a text file.


## References

[^1]: [Azure DevOps landing page for Anonlink](https://dev.azure.com/data61/Anonlink)
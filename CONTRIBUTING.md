# Contributing to PCR-GLOBWB
Thanks for your time and willingness to contribute to PCR-GLOBWB! This page gives a few guidelines on how to report on findings or requests and provide improvements.

## Reporting findings and requests
If you have found a bug or unexpected behavior in PCR-GLOBWB or you have a feature or enhancement request you can create a [GitHub issue](https://github.com/UU-Hydro/PCR-GLOBWB_model/issues). When submitting an issue, use the appropriate label (e.g. bug, unexpected, feature or enhancement) for your issue. Please do not use issues for support questions.

**Bug findings** report on cases where PCR-GLOBWB actually fails whereas **unexpected behavior findings** report on cases where PCR-GLOBWB does not fail but behaves unexpectedly. To allow us to develop upon the finding please provide:

- The PCR-GLOBWB and Python version used
- A clear and detailed description of the bug or unexpected behavior, including
    - The PCR-GLOBWB log
- A clear and detailed description of the expected outcome
- *If possible*, a minimal and reproducible working example (including all data and scripts)
- *If possible*, suggested changes to fix the issue

**Feature requests** report on cases where new functionality is introduced into PCR-GLOBWB whereas **enhancements requests** report on cases where PCR-GLOBWB functionality is (slightly) altered or improved. To allow us to develop upon the request please provide:

- The PCR-GLOBWB version used
- A clear and detailed description of the feature or enhancement, including
    - The problem the feature or enhancement aims to resolve
- Suggested changes to develop the feature or enhancement, including
    - Potential downsides of the suggested changes

## Providing improvements
To provide improvements to PCR-GLOBWB, such as bug fixes or feature implementations, please submit a [GitHub pull request](https://github.com/UU-Hydro/PCR-GLOBWB_model/pulls). Any pull request should conform to the PCR-GLOBWB branching strategy. The PCR-GLOBWB repository contains 5 different types of branches (see figure below):

- The **main** branch; contains production-ready code that can be released
- The **develop** branch; contains pre-production code with newly developed features that are in *the* process of being tested
- **feature/[name]** branches; used when adding new features to your code
- **release/[name]** branches; used when preparing new production releases
- **hotfix/[name]** branches; used to quickly address necessary changes in your main branch

Therefore, the following steps should be taken for any pull request:

1. Create an issue reporting on the changes you intend to make (see section above)
2. Create your own fork of the PCR-GLOBWB repository
3. Create your own "feature/[name]" or "hotfix/[name]" branch (depending on the issue) with a clear and concise name
5. Apply your modifications to your own branch
6. Submit a GitHub pull request to the develop branch of the PCR-GLOBWB repository

![Git-flow branching strategy](img/git-model@2x.png "Git-flow branching strategy")
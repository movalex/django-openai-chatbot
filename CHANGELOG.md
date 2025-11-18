# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project adheres to Semantic Versioning (SemVer).

## [0.2.0] - 2025-11-14

SemVer rationale: Minor version bump. Since the last recorded changes include adding a new OpenAI model (feature) and adjustments to the supported model list, we treat this as a backward-compatible feature release. A removal of `gpt3-turbo` is noted below; if your deployment depended on that specific model, treat this as a breaking change in your environment.

### Added
- Add `4o-mini` OpenAI model support ([e02503d](https://github.com/movalex/django-openai-chatbot/commit/e02503d4093aab219ac24d860bfc5b70eaf1d287)).
- Add application screenshot to repository/docs ([f177407](https://github.com/movalex/django-openai-chatbot/commit/f1774078f4279ed6de2d70b900b7c6d581e3b883)).

### Changed
- Update models list to reflect current supported models ([f2a558f](https://github.com/movalex/django-openai-chatbot/commit/f2a558f8088aaca0642ad807fe6e8956f283c1c1)).

### Removed
- Remove deprecated `gpt3-turbo` model from defaults/config ([e02503d](https://github.com/movalex/django-openai-chatbot/commit/e02503d4093aab219ac24d860bfc5b70eaf1d287)).

### Chore
- Update `.gitignore` rules ([927e1a1](https://github.com/movalex/django-openai-chatbot/commit/927e1a1f9f26e24ba49c4acb6363bb1c8ac3292a)).

---

### Notes
- Default branch history considered: last 5 commits as of 2025-11-14.
- If you have a previously tagged version prior to these changes, you may wish to re-tag based on your own compatibility assessment.

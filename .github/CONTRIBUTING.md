# Contributing Guidelines

We welcome contributions! Before adding new functionality, open an issue first. Bug reports, fixes, and feedback are always appreciated.

Please take the time to review the [Code of Conduct](CODE_OF_CONDUCT.md), which all contributors are subject to on this project.

## Prerequisites

**Backend (Python):**
- Python 3.9+

**Frontend:**
- Node.js 24.0.0
- pnpm 10.0.0 (required)

**Installation:**
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies and build
cd frontend
pnpm install
pnpm run build
cd ..
```

**Note:** All Python dependencies are pinned to exact versions in `requirements.txt`. We recommend using a virtual environment (venv, virtualenv, conda, etc.) but leave the choice to you.

### Frontend Development

For active frontend development with hot reload:

```bash
cd frontend
pnpm run dev
```

This starts a Vite dev server on port 8081 with instant updates when you modify frontend files.

## Reporting Bugs

Before submitting a bug report:
- Search existing issues and comment if one exists instead of creating a duplicate.

When submitting a bug report:
- Use a clear title
- List exact steps to reproduce the issue
- Provide examples, links, or code snippets
- Describe observed vs. expected behavior
- Include screenshots or GIFs
  - For macOS and Windows: [LICEcap](https://www.cockos.com/licecap/)
  - For Linux: [Silentcast](https://github.com/colinkeenan/silentcast)
- Mention if the issue is consistent or intermittent and share environment details

## Suggesting Enhancements

Before submitting an enhancement:
- Search existing suggestions and comment on one instead of creating a duplicate.

When submitting an enhancement:
- Use a clear title
- Describe the enhancement step-by-step
- Provide examples or code snippets
- Explain current vs. expected behavior and its benefits

## First Time Contributors

Check `beginner` and `help-wanted` issues to get started.

## Pull Requests

Please follow these steps:
1. Use the Pull Request template
2. Follow the [Code of Conduct](CODE_OF_CONDUCT.md)
3. Test both backend and frontend changes:
   ```bash
   # Test backend
   python app.py

   # Rebuild frontend if modified
   cd frontend && pnpm run build && cd ..
   ```
4. Ensure all [status checks](https://help.github.com/articles/about-status-checks/) pass before review
   - All dependencies should be pinned to exact versions
   - Test the `/stt/transcribe` endpoint matches the API contract

Note: Reviewers may request additional changes before merging.

## Code Style

**Python:**
- Follow PEP 8 guidelines
- Use meaningful variable names
- Add docstrings to functions
- Keep functions focused and modular

**Frontend:**
- Follow the existing code structure from `@deepgram/starter-uis`
- Don't create custom components - use what's provided in the design system
- Keep JavaScript clean and well-commented

## Security

Review the [Security Policy](SECURITY.md) for:
- Reporting security vulnerabilities
- Dependency management
- API key handling best practices

**Important:** Never commit `.env` files or API keys to the repository.

## Questions?

Connect with us through any of these channels:
- [GitHub Discussions](https://github.com/orgs/deepgram/discussions)
- [Discord](https://discord.gg/deepgram)
- [Bluesky](https://bsky.app/profile/deepgram.com)

For additional guidance, check out [GitHub Flow](https://guides.github.com/introduction/flow/index.html).

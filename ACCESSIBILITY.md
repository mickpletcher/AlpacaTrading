<!-- markdownlint-disable MD013 -->
# Accessibility

## Goal and scope

AlpacaTrading aims to make its documentation, contribution process, local journal, and generated reports usable by people with different abilities and assistive technologies. WCAG 2.2 Level AA is a design and review target for the repository-owned web surfaces, not a certification or a claim that every criterion has been met.

This repository is a collection of Python and PowerShell tools. GitHub, browsers, operating systems, terminals, Alpaca, and other external services have their own accessibility behavior. This statement covers the material maintained here, not those services.

## Current status and limitations

The journal and generated reports are reviewed under [specification 007](specs/007-community-accessibility/spec.md). Repeatable validation procedures live in [Tests/README.md](Tests/README.md). Per-change evidence and limitations belong in the pull request.

- Markdown source and plain-text instructions are available alongside screenshots and HTML reports.
- The journal uses labeled controls, keyboard-operable navigation, visible focus, text feedback, and reduced-motion behavior. Review and test these features whenever the UI changes.
- Reports provide text values and table structure rather than relying only on visual charts or colors. Wide data tables may require horizontal scrolling.
- A complete screen-reader, voice-control, cross-browser, PDF, or repository-wide WCAG conformance assessment has not been completed. Automated checks cannot establish full accessibility.
- Third-party generated backtesting charts, legacy learning materials, and terminal/PowerShell host behavior need separate evaluation. No compatibility promise is made for a specific assistive technology.
- The journal's existing security and data-handling limitations remain in [ISSUES.md](ISSUES.md). Accessibility work does not remove those restrictions.

## Contributor checklist

- Write in plain language with descriptive headings, meaningful links, and short ordered steps.
- Provide useful alt text and nearby text explanations for screenshots and diagrams. Do not put essential instructions only in images, color, position, or emoji.
- Prefer simple tables with headers and a caption or clear introduction. Offer text or CSV alternatives for complex visual output, without exposing private trading data.
- Use native controls with programmatic labels. Make every action reachable and usable with a keyboard. Keep focus visible and predictable after navigation, errors, updates, and cancellation.
- Use text as well as color for status. Aim for at least 4.5:1 contrast for ordinary text and 3:1 for large text and meaningful controls.
- Check text resizing, narrow-screen reflow, reduced-motion preferences, and keyboard access to scrollable data. Avoid flashing, forced animation, and unnecessary time limits.
- Announce meaningful dynamic feedback without making the whole page a noisy live region. Identify errors in text and preserve entered values when a request fails.
- For audio or video contributions, provide captions or a transcript as appropriate.
- Test actual generated output and success, failure, repeated, and cancelled UI flows. Record the browser, operating system, tools, and untested behavior honestly.

See [W3C's accessibility introduction](https://www.w3.org/WAI/fundamentals/accessibility-intro/) and [WCAG 2.2](https://www.w3.org/TR/WCAG22/) for more guidance.

## Report a barrier or request an alternative

Use the [accessibility form](https://github.com/mickpletcher/AlpacaTrading/issues/new?template=accessibility.yml), or a [blank issue](https://github.com/mickpletcher/AlpacaTrading/issues/new) if the form itself is a barrier. A text-only report is enough. Describe the file or page, intended task, barrier, expected experience, and an alternative that would help. Browser, operating system, assistive technology, and zoom level are optional.

Do not provide a diagnosis, medical information, credentials, account identifiers, or private journal records. Reports are public. For a sensitive security issue, use [SECURITY.md](SECURITY.md) instead.

The repository owner, [@mickpletcher](https://github.com/mickpletcher), reviews accessibility reports alongside other project work. No response deadline or audited conformance level is promised. Revisit this statement when relevant behavior, validation, or known barriers change.
<!-- markdownlint-enable MD013 -->

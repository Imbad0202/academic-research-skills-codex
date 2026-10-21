# Native Windows marketplace regression

This workflow runs the reviewed Codex source patch on a disposable GitHub-hosted Windows Server 2022 x64 VM. It does not install or publish a Codex application.

The patch is pinned to upstream commit `430a16799d90e296fb27b1e94f206023902b7e56`. The manifest checks the patch and all four resulting source files before compilation. Rust is pinned to 1.99.1; external actions are pinned to commit IDs.

It first runs the exact Windows-only directory-sharing-lock regression. This must execute and pass one test; an empty or ignored test set fails validation. It then runs the `marketplace_` filtered tests in `codex-core-plugins`, requiring successful execution of at least 100 tests. This minimum is an accidental-filter guard, not a statement that every crate test has run.

The native test locks the installed marketplace directory against sharing, triggers an update, checks that the installed copy survives and staging is empty, verifies that the next automatic attempt is suppressed, then releases the handle and checks manual recovery. The wider test set covers persistent retry state, repeated triggers, process locking, clock correction, failed-clone cleanup and cleanup during backoff.

The test temporary directory must be on NTFS. Test logs and a receipt containing OS, toolchain, source identity and executed test counts are uploaded for seven days, including ordinary test failures. A failure before the Python harness starts may produce no artifact; consult the Actions step logs in that case. The test step has a 75-minute limit inside a 90-minute job limit, leaving budget for artifact upload. A forced timeout or cancellation can still prevent receipt creation or upload; partial step logs may be the only evidence.

These are native Windows filesystem tests, not verification on the reporter's exact Windows 10 machine or backup software. The test uses a share-mode-0 directory handle; the resulting Win32 error code is not recorded. It does not prove reproduction of every access-denied (OS error 5) scenario. The original issue cannot be declared resolved solely from this VM run. There is no full unfiltered crate test run or desktop application end-to-end test here.

Publishing the five files in this package to branch `validation/codex-marketplace-windows` of the public `Imbad0202/academic-research-skills-codex` repository triggers the workflow. No release, merge, issue comment or application installation is part of this workflow.

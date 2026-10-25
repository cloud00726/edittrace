# Independent regression consumer

Copy workflow.yml into your project's `.github/workflows/edittrace.yml` and suite.json into `regressions/suite.json`. Replace the example's explicit expectations with reviewed cases from your own task.

The template downloads the published Linux x64 0.2.0 preview ZIP, validates its pinned SHA256, then runs only the consuming project's fixture. It requires neither this repository's scripts nor its toolchain. It emits JSON because 0.3.0/JUnit is still a local candidate. The output upload runs on failure as well; full input/source is not uploaded by default.

After 0.3.0 is actually published, pin its verified URL/hash and change the run step to `suite run regressions/suite.json --format junit --out result.xml`. Do not invent a release URL. The template has not been dispatched as an external project's CI; its fixture is locally exercised through the core.

# Planning Evidence — 2026-10-09

**Feature**: `C:\code\ama\specs\001-proxy-dependency-upgrades`  
**Repository/branch**: `johnbilliris/ama`, `001-proxy-dependency-upgrades`  
**Decision record**: `research.md`; record design: `data-model.md`

These observations prove only the identities, retrievals and comparisons described. They do **not** prove successful installation, full dependency closure, absence of vulnerabilities or application compatibility. No installation, project test, security scan, commit, push or remote mutation was performed.

All times in the tables are **UTC on 2026-10-08**; local observation date was 2026-10-09 in Australia/Sydney. Requests used fresh HTTP retrieval rather than local package caches. Downloaded archives were inspected, not executed.

## E0 — Baseline identity and protected inputs

Repository HEAD: `62d249dc1205644fed934ea167df56695e92b3d2`. The initial worktree contained only the untracked feature specification directory. Paths below are relative to `C:\code\ama`.

| Input | SHA-256 |
| --- | --- |
| `package.json` | `5eb6d50a7c6faf9d0ccba7a644f1524bc9e7a1bb9733bfc8145ed82b0148de17` |
| `apps\web\package.json` | `6e36c4424448030ee238d54044ef3399d17d8776ee4b13e0a5e377b7f6e86db0` |
| `packages\ui\package.json` | `4c9a1965b5583f9d4a7687c6fa1bb7e1cf7a470665f8db1001156842e55cd275` |
| `pyproject.toml` | `db8c0d71e077248bb38796121133842bf0801aa26edaea2243bfe598d657a03a` |
| `apps\agents\pyproject.toml` | `e24ad41cc8c11d2f0b9bb5bf10b23a221fb5884deca99b1586cd07ba6240a4a6` |
| `apps\api\pyproject.toml` | `baad8872399c46cf7edb257e65ae6b3367632cb03a39306ac1a9a9ae325cee63` |
| `pnpm-lock.yaml` | `a7faae5796f708f8c1dff2b95bc0fbb3bcd3bac598af7cfda8a641864dcb75e4` |
| `uv.lock` | `5d6c10e42cfed38ce9d2a065e0cc2bc3bb5bffbb11bfb63a1d1a03e434fb0b00` |
| `apps\agents\uv.lock` | `1452d8f9f692411a9dd32ec4cb3135b38090cd0bba083dd75422c603f90efa77` |
| `apps\api\uv.lock` | `748bfa0f0c991bc1d5d85ff9b9220e5cda6dc722b6226d9ef750975ec3efe3fc` |
| `tools\specify-cli\uv.lock` | `56b333409ddcbda721045331cb54dcc629b13a2e4a001128376aedb94fd43edf` |
| Feature `spec.md` | `fa8d3b615693624afd9d8874a77ad7874703121bec7cd1624878beb66a5f1034` |
| Feature `checklists\requirements.md` | `2ead948df3298c8346fa5d5baa9c61fe8831df7ba279b7e3da43bef2ca035027` |
| `.specify\memory\constitution.md` | `5bd445a37ab0f0c323b7544b004e6775777572870fb9aa3ee50a4e014865866b` |
| `.github\agents\copilot-instructions.md` | `de79d0536c70e23f6846f5a5344dc27d0a1452fc725472ebcda6e212ccb90c0e` |

Lock inspection used existing Python `tomllib` and PyYAML 6.0.3, not installed package metadata. Counts: root uv 309 package entries; agents 251; API 135; specify-cli 53. These include marker alternatives, not a claim that all entries install in one environment. pnpm lock format is 9.0 with root/web/domain/UI importers.

Selected retained comparison points outside the matrix:

| Package | Root uv | Agents uv | API uv | specify-cli uv |
| --- | --- | --- | --- | --- |
| cryptography | 50.0.1 | 50.0.1 | 50.0.1 | 50.0.1 |
| idna | 3.11 | 3.11 | 3.20 | 3.19 |
| PyJWT | 2.15.0 | 2.15.0 | 2.15.0 | 2.15.0 |
| h2 / hpack | 4.4.1 / 4.2.0 | 4.3.0 / 4.1.0 | not present | not present |
| FastAPI | 0.138.0 | 0.141.1 | 0.141.1 | not present |
| Pydantic / settings | 2.13.5 / 2.15.0 | 2.12.5 / 2.14.1 | 2.13.5 / 2.15.0 | not present |
| setuptools | 84.0.0 | 82.0.1 | not present | not a targeted entry |
| mem0ai | 2.0.20 | 2.0.2 | not present | not present |

All registry sources in the four uv locks were the approved Python proxy. Root npm overrides include sharp 0.35.5, source-map-js 1.2.2, PostCSS >=8.5.18 and the other existing security constraints; none was changed.

## E1 — Supplied PR snapshot, not a new inventory

Read-only requests: `gh api repos/johnbilliris/ama/pulls/<number>` and `gh api repos/johnbilliris/ama/pulls/<number>/files?per_page=100`. Only the 33 supplied numbers were queried. All 33 were open when observed, between **23:03:14 and 23:03:47 UTC**. No broad PR listing or PR lifecycle operation was performed.

Observed base pointers were `cebd9064cb534e78b96ea719caec4e35ad6e705f` (five), `5c0dab3195ba12e0af20a3ae67b75d117ced7c99` (20), and current baseline `62d249dc1205644fed934ea167df56695e92b3d2` (eight). Their old proposal baselines are not substituted for current resolved locks.

- `cebd9064…`: #102, #103, #105, #111, #112.
- `5c0dab31…`: #115, #116, #117, #120, #121, #122, #123, #124, #125, #126, #127, #128, #129, #130, #132, #133, #134, #135, #136, #137.
- `62d249dc…`: #143, #144, #145, #146, #147, #148, #149, #150.

Every PR URL is `https://github.com/johnbilliris/ama/pull/<number>`. Original targets and current decisions remain individually linked in `research.md`.

| PR | Observed head SHA | Changed proposal surfaces |
| --- | --- | --- |
| #149 | `88374e88219178caa2e962b3fac8f2ee791cdae8` | `apps\web\package.json` |
| #150 | `d1971c19598bf880cafbfd0e9a48f7dc3ca8a930` | `apps\web\package.json` |
| #148 | `709b50a94a065869ae28920857b64814382eff90` | `apps\web\package.json` |
| #147 | `cc686cb730b8be99ea7834f2e2692c5a551d3a57` | `apps\web\package.json` |
| #146 | `b2238f8fc57f89635ca10d2790a044a2555f9ffa` | `apps\web\package.json` |
| #144 | `ab07c81f375e752fe78328144d9062900bb699ab` | `apps\web\package.json` |
| #133 | `0108cd0185694308dd124f432804d0bad0dcbf47` | web manifest + root pnpm lock |
| #137 | `07f744c5a70210cdde91f777cfe0b3204647e0c8` | web manifest + root pnpm lock |
| #132 | `5652c57402f1077485b715d4238049e81ac2ce6d` | web manifest |
| #130 | `3ce8337f68350df9a4f99e8fc3f5fe91f0a7acfa` | `packages\ui\package.json` |
| #135 | `4adb252cb0d5dc1831daf787cb403fc2398f90a1` | root `pyproject.toml` + `uv.lock` |
| #136 | `fa398a9451890e15900a26269d4a60ff47fcf9e7` | `apps\agents\uv.lock` |
| #111 | `ac341efdcc950ad9571fecc81d093226819e0694` | root `uv.lock` |
| #134 | `2248d1fd3df3dc721b5377ca91e4879cfc95a3a0` | agents manifest + agents lock |
| #121 | `564bcba2068f7822c6cf308a602d8cc647dab8a5` | root `uv.lock` |
| #116 | `49555b31a1dbd43da2e148a669ea38e8c0c0aaec` | root `uv.lock` |
| #124 | `4cb797e3cb9f4894142f0fdbb119bb8b0cab5689` | root `uv.lock` |
| #123 | `4d8a1ae984b15fd390fe263d09de93a0e98ee3dc` | root `uv.lock` |
| #129 | `c887681fdcb8026be0af8395ec8cbf710d7c4ecd` | `apps\agents\uv.lock` |
| #128 | `3c493bbef1dd554d725b1e007859a4b1351c97ad` | `apps\agents\uv.lock` |
| #127 | `80a12a3cecac8b66ec5776b04765466e4b3ed157` | agents manifest + agents lock |
| #126 | `8bf1b9d636aad74341580decea8eea004169cfe6` | `apps\agents\uv.lock` |
| #125 | `f73415295c9e5f9edfbdc49d0fce75375fd2fcc3` | `apps\agents\uv.lock` |
| #112 | `a5d5b3a6bddea09283da28c8731525ecff8a7ce7` | `apps\agents\uv.lock` |
| #120 | `ff3b73a1eeb1fc188a6bc1043af010da15550add` | `apps\agents\uv.lock` |
| #115 | `c98d5143644529072d44a8eca920243f59920aac` | `apps\agents\uv.lock` |
| #122 | `648ee7b0891da1995166d8364e16db5bde86b162` | `apps\agents\uv.lock` |
| #117 | `548fb83494fe13e97fbfde52665f7347b9b4797c` | `apps\agents\uv.lock` |
| #145 | `2f9a951c194105ec207be1608180c09ebbe21afb` | 19 workflow files; current active scope is larger, below |
| #143 | `577e36ce45e91635b81d8ebb759e767beb285764` | `ci.yml`, `corpus-ingest.yml` |
| #105 | `f6bb036b9ef93e631fab91511f516ef3a136b051` | `security-scan.yml` |
| #103 | `7b7587310c82ab24365277d274e6f2331ba592cd` | `prompts-publish.yml` |
| #102 | `55ec28b873133f54b4d10ed72e97a7b2ba6521bd` | `foundry-carveout-review.yml` |

The existing 25 checkout-containing workflows were parsed as YAML to exclude commented-out steps. In addition to #145's 19 files, active references occur in `amend-loop-coupling.yml`, `foundry-carveout-review-6mo.yml`, `foundry-carveout-review.yml`, `help-gates.yml`, `simulation-load-test.yml` and `simulation-stub-sweep.yml`. Those are related consistency surfaces, not six new PRs.

Upload-artifact occurs in seven workflows: `ci.yml`, `corpus-ingest.yml`, `dr-drill.yml`, `eval-publish-dataset.yml`, `nightly-load.yml`, `simulation-load-test.yml`, `spec-036-50-agent-load.yml`. There are ten active uses: six target SHA, three old full SHA, one v4 tag. All Action files are under `C:\code\ama\.github\workflows`.

## E2 — npm artifact retrievals

Metadata was obtained from the approved npm proxy. The artifact URLs came from its `dist.tarball` entries under:

`https://ms-feed-25.pkgs.visualstudio.com/1es-public/_packaging/npm-public/npm/registry/`

Unscoped suffixes are `<package>/-/<package>-<version>.tgz`; scoped suffixes are `@<scope>/<package>/-/<package>-<version>.tgz`. These are **proxy-provided Microsoft artifact locations**, not public registry bypass. Package JSON identity/version was checked inside every archive listed.

**16 distinct npm package/version archives retrieved and matched the supplied checksum.** This includes research-only companions, retained baseline samples and the rejected ESLint candidate; it is not a count of approved upgrades. `sha512-…` values are publisher/proxy SRI; a bare 40-hex value below is the weaker published SHA-1 shasum. The SHA-256 column is the locally computed digest of the fresh bytes.

| ID | Package/version | UTC request | Actual SHA-256 | Expected published checksum, matched |
| --- | --- | --- | --- | --- |
| N01 | `@azure/msal-browser@5.24.0` | `23:09:21` | `ee4b1ac1dd31b333616f4f3fd731dd13b8ee8f6de7c6014308866335f16f1609` | `sha512-jS1stt81tslcVZi7fqVD+g6vr8w/IWqFl/vAB2dx/6EOroQDuCR4+z0o3C+d6a/GpLATvdoO+kwnDcYzsBXKQA==` |
| N02 | `@azure/msal-browser@5.9.0` | `23:06:29` | `9226413150df089b694e0b5ff0c12e425e3108864927b27f6126d9873c17b255` | `22b0853e70f26e63862ad7ef686ffa4b4eebe4a3` |
| N03 | `@azure/msal-react@5.7.2` | `23:06:23` | `ca7cc13809abb515fe64c29568da4afa79f97f50a33dda2a32d06fb08ad67a66` | `sha512-xxwNH2dp77ACHuPFG+a9LTPinz7s+Xoh66Vvz/pWeyPMSXT0p+I4p9UXWpLWzY8qKBxJWbhyLwAtoaqVFiakHQ==` |
| N04 | `@playwright/test@1.63.0` | `23:06:26` | `fc594f36b7b4aafece614ec6852ad728423215a76edd0a2a1821bb0c49539c4e` | `808020c46e8b6b91f9d628cd0ebcbb32bdfd8b6c` |
| N05 | `@types/node@26.6.4` | `23:06:33` | `bf2dbf11cfccd34681fc4d5e4d150afce77fd6610224757dbe6c92c8e5149700` | `sha512-ldVPDCzj7fsaGZrLB0NuHuTvJcsNasysBAqMolr/cgxrLd1xbqxIr3XJiPnHHJUCxj5sNF1vnRj9aWnrVh5Jcg==` |
| N06 | `eslint@10.11.0` | `23:09:23` | `2c1c9adad9ba0d7c8b885216a920a46eb4c1d400d04f8baafe2b281aaea945f0` | `sha512-P7a6UEEqb9G95MYAtqkmsTbVXIYyzIfl6NGOIJk162PaahFxFyeGcrlXYFSiagECg4sEm8IseJdZBKR3rx6MsQ==` |
| N07 | `eslint-config-next@16.2.6` | `23:09:23` | `a426657d5d0239fa0a476598515b2112109253a4ca855b9cfa94a3e213e53582` | `1a04578efe6fde5cdb6265e98e88c9f61927e2c7` |
| N08 | `eslint-config-next@16.3.8` | `23:09:22` | `7c56bb144a853c3b2b9011a753f8a390c68ccf1157176e21a3193b8a0399d799` | `sha512-81vovwMe6NGnoFsl0KUJWzlS+y239i3fdsxs49gSEX3pDQW2cuKy+fxUPXNkQqqx6OCPheYPtBlSufc9aZ0k+w==` |
| N09 | `js-yaml@4.3.1` | `23:06:22` | `08d6282b77a3e7242061f6dd5516c019b25c53041ad267bca3b790d79ddd5f34` | `01216c001d67f48e2cd560d708c7af21090a3848` |
| N10 | `jsdom@30.1.1` | `23:09:21` | `ce6675111b9fd03e754e98505433c98b05a7ac5a36e2a533165df5481946a749` | `sha512-FahmoPK5vbPc+jxV1iErMHmAZypCZ942NHF4+qqaWAuvaKKTBZxawnmAtrbGWLU7MtlxfqIP0qw6aSI+aWGtLg==` |
| N11 | `next@15.5.21` | `23:06:53` | `ffc133c1448abb813f09df98dbdc6b8e58dfcd90a0088193ac67d6a1d506d13b` | `43355e37f9d1ed8cf96018aa57f84ea2ec213f7b` |
| N12 | `next@16.3.8` | `23:06:39` | `f6f312a6f62b3addcf3dbf10a5d908940bd9d772c59561341d8ac134fd077ff6` | `sha512-U7QEZaTini6wKrb8A8hqLLqYQyCetegKjCpJOyxk642vWoMoU1x5PyZCJFvgYgiptA8xc5j/9xYlZFO7w9Sjmw==` |
| N13 | `playwright@1.63.0` | `23:14:26` | `195a5ee9bfed7c6e9c03965950e32e5e4dbedaa02e740e5a530eb4b87dae050c` | `99b56f9f69b1b70c44f00bf84b2fe52348ae2511` |
| N14 | `playwright-core@1.63.0` | `23:14:27` | `208593d4e1bcd8f8fe5f869cad1cc332dc7f1d70dc1d58c102dc3ac36e30f26c` | `e57665bc32846c213ac39a1e4d5bc6228e76b376` |
| N15 | `sharp@0.35.5` | `23:06:26` | `3b6bbbe6b308f5c383938ca4a31926cd5d79c4651ed8c5fda16a97da2014a9ac` | `sha512-Ywn4OnzGukp7CDMrp08RQ50YKmuwG47brZgIVPTvBaaAfQlRlygrRqSrxdCiL9M+LlzLBiJ68IR1QqvzHyjC7g==` |
| N16 | `source-map-js@1.2.2` | `23:06:25` | `05c8cf8e7c3a6b56cada7668fe9342b10f4b625efc92aba9ba05b9e8fe4d71a3` | `sha512-KGj/8Y43x35aZVDtt+J4mK1hoLGHULMYfSkODJNQjNDC3oW1PqPoxMwo0pLUsWM/UEGzON/NxeHywEfNXNP3Vw==` |

**Limitations**: Next/SWC/sharp platform variants, all transitive tarballs and Playwright browser files were not retrieved. No peer-resolving installation or runtime/security check ran. A locally computed stronger digest does not by itself upgrade the strength of a SHA-1-only publisher assertion.

### Absence, access and compatibility observations

| Observation | Evidence | Classification |
| --- | --- | --- |
| ESLint 10.12.0 | Successful catalogue omitted it; `https://packagefeedproxy.microsoft.io/npm/eslint/10.12.0` returned 404 at 23:07:57. | Target absent at observation time; N06 is not automatically eligible. |
| jsdom 30.1.2 | Successful catalogue omitted it; `https://packagefeedproxy.microsoft.io/npm/jsdom/30.1.2` returned 404 at 23:07:58. | Target absent; N10 is a tentative fallback, not a validated install. |
| config-next initial request | Connection reset at 23:06:26; later successful metadata and N07/N08 retrievals. | Transient access failure, subsequently recovered. |
| MSAL common 16.14.2 | Catalogue requests failed with socket error 10054; last recorded retry 23:16:51. Exact `%40azure%2Fmsal-common/16.14.2` endpoint returned 404 at 23:16:19. | Unverified source chain; no trustworthy eligible set, no fallback chosen. |
| ESLint plugin compatibility | Successful catalogues at 23:10:39 found no ESLint-10 peers in config-next 16.3.8's required react/import/jsx-a11y ranges. | Compatibility rejection, distinct from artifact absence. |

Peer catalogue SHA-256 values: react `4d76f67d45a7e424209972f62153e98b7e7c434388312685fd127a3574e7fc40`; import `ba26ba7ff8233f74b72bb13a01cc4cb569dbf7bd2ad6ea9f2a2e067f3bf8ee4e`; jsx-a11y `13f24df5aa7a9d4b2064700d2c62d3eaccbacdc1f09dd55d42ca7710e5de4d34`. Their exact ranges/highest releases and the SemVer fallback ordering are recorded in research R3.

## E3 — Python wheel retrievals

Metadata came from `https://packagefeedproxy.microsoft.io/pypi/simple/<normalised-name>/`. Downloads used its Microsoft links under:

`https://ms-feed-25.pkgs.visualstudio.com/6f084628-a36d-42cb-934d-057357e379dc/_packaging/49d7402f-07bb-4b18-a9ce-086e6e98a554/pypi/download/`

The relative download path is the package/feed-version/filename returned by that metadata; do not invent public PyPI URLs. For example h2 is `h2/4.4.1/h2-4.4.1-py3-none-any.whl`, while engineio uses `python-engineio/4.14/python_engineio-4.14.0-py3-none-any.whl`.

**24 wheels across 18 versions** were freshly retrieved, matched their metadata SHA-256, had matching wheel METADATA name/version, were not yanked, and declared Python 3.12-compatible Requires-Python. For the retained versions, corresponding recorded lock hashes were also compared where present and matched.

Universal wheels are artifact coverage for the recorded Python 3.12 platforms, not full environment installations. The three native libraries have separate Linux x64, Linux arm64 and Windows x64 samples; ABI3 cryptography wheels permit Python 3.12. Other native/build dependencies and runtime tests remain unverified.

In every row, actual SHA-256 **equals** the expected hash in proxy metadata:

| Filename | UTC request | Expected and actual SHA-256 |
| --- | --- | --- |
| `aiohttp-3.14.3-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl` | `23:09:19` | `543906c127fb1d929b95076db19b83fa2d46751006ff1e23b093aa5ac4d8db42` |
| `aiohttp-3.14.3-cp312-cp312-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl` | `23:09:21` | `f631fe87a6f30df5fbe6d79640b25e4cffb38c31c7fb6f10871517b84b0f8c1a` |
| `aiohttp-3.14.3-cp312-cp312-win_amd64.whl` | `23:09:21` | `33a2d7c28d33797a2e99923dffa63f83d908a19b6bf26cfe80fa790aa5e1a75a` |
| `cryptography-50.0.1-cp311-abi3-manylinux2014_x86_64.manylinux_2_17_x86_64.whl` | `23:09:19` | `ff838d62ec1bfce4f9ba7fa16f4a7b554cd8d0c299e6be37502161a660c84eef` |
| `cryptography-50.0.1-cp311-abi3-manylinux2014_aarch64.manylinux_2_17_aarch64.whl` | `23:09:19` | `53e279950892dc102c6b4e52af03ae5ea92fac572a1ddab78ca73a997f62b69f` |
| `cryptography-50.0.1-cp311-abi3-win_amd64.whl` | `23:09:22` | `aed8db4f6d71c51efb89530e12d9464e7bf2923d46c3205dc794a2a93f8c0648` |
| `fastapi-0.138.0-py3-none-any.whl` | `23:14:23` | `b6f54fd1bd72c80b0f899f172c61a600f6f7af9b43d4d772a018f35624048cb0` |
| `fastapi-0.141.1-py3-none-any.whl` | `23:14:25` | `bfb91aa2d334c61cb35ba9a116fc123b3d3df31640b801cf57a7a78ec3f603b3` |
| `h2-4.4.1-py3-none-any.whl` | `23:09:19` | `0e25f1462b23c9cb82d9eb02e28bc706dac2a68cb457c6a0d74d63c8a2a5d0e6` |
| `hpack-4.2.0-py3-none-any.whl` | `23:14:27` | `858ac0b02280fa582b5080d68db0899c62a80375e0e5413a74970c5e518b6986` |
| `idna-3.15-py3-none-any.whl` | `23:09:19` | `048adeaf8c2d788c40fee287673ccaa74c24ffd8dcf09ffa555a2fbb59f10ac8` |
| `mcp-1.30.0-py3-none-any.whl` | `23:09:22` | `666edb5009503e1047c9d60346a756f94b261f05cc2625f23d41c728ffc484d0` |
| `msgpack-1.2.2-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl` | `23:09:19` | `77c2e018417dc1d66f235e383877ee885b60ade9d29e494dd581e08af2cb1923` |
| `msgpack-1.2.2-cp312-cp312-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl` | `23:09:21` | `90986cc9aab9d7d1d8f38bcbf65d3f7ac83bdd90c35765db7d691b4829698cba` |
| `msgpack-1.2.2-cp312-cp312-win_amd64.whl` | `23:09:23` | `b68614fba0570349833b7dd999ff0aed4e5cc8d9eb6e3a7d4527be33c65e33d3` |
| `pyasn1-0.6.4-py3-none-any.whl` | `23:09:22` | `deda9277cfd454080ec40b207fb6df82206a3a2688735233cdcd8d3d565f088b` |
| `pydantic_settings-2.14.2-py3-none-any.whl` | `23:09:22` | `a20c97b37910b6550d5ea50fbcc2d4187defe58cd57070b73863d069419c9440` |
| `pydantic_settings-2.15.0-py3-none-any.whl` | `23:09:23` | `0ba092c291c94baceb5eff768aa0d56400a457585bc0175925a5a5510303da42` |
| `pyjwt-2.15.0-py3-none-any.whl` | `23:09:19` | `7a3742debf6b879e912dbb9819ceec1594be812452b78c5f2e2dfc56564954f8` |
| `python_engineio-4.14.0-py3-none-any.whl` | `23:17:50` | `9f0fe275fb7d67bfc1a632421adf22949fd4843bd9c458c004b0a89cede302a2` |
| `python_multipart-0.0.32-py3-none-any.whl` | `23:09:23` | `ff6d3f776f16878c894e52e107296ffc890e913c611b1a4ec6c44e2821fe2e23` |
| `python_socketio-5.17.0-py3-none-any.whl` | `23:09:19` | `b5826fd2f8aa02e11347816349b74ac6b53e8a4f4e4b1cf1388e1aff19b7f3f4` |
| `setuptools-83.0.0-py3-none-any.whl` | `23:09:20` | `29b23c360f22f414dc7336bb39178cc7bcbf6021ed2733cde173f09dba19abb3` |
| `starlette-1.7.0-py3-none-any.whl` | `23:09:22` | `67f8e99895493dd2911a03f11314af6ceebeae4e704bb9f43dfc6a9db151c93e` |

Engineio's first attempt at 23:09:19 failed with socket error 10054. The last row for that package records the successful retry, not a reinterpretation of the initial failure as absence.

## E4 — Official Action source and asset evidence

API provenance: `gh api repos/<official-repository>/git/commits/<full-sha>`, `git/trees/<tree-sha>?recursive=1`, tag refs and, where needed, official releases/compare endpoints.

Source archives: `https://codeload.github.com/<official-repository>/tar.gz/<full-sha>`. For each complete tree, archive files were checked against the corresponding Git blob SHA-1 (`blob <length>\0<bytes>`). All five had no missing blobs or mismatches. This verifies source identity against the pinned official commit in addition to recording archive SHA-256.

| PR / official repository | Full proposed SHA | UTC request | Archive SHA-256 | Verified blobs |
| --- | --- | --- | --- | --- |
| #145 `actions/checkout` | `3d3c42e5aac5ba805825da76410c181273ba90b1` | `23:09:26` | `b59292069298c7be5ffd9c636431a229faff70ece00e0c24fd31baeb7b309fa3` | 101 |
| #143 `actions/upload-artifact` | `b7c566a772e6b6bfb58ed0dc250532a479d7789f` | `23:09:27` | `ac4d02cada05aaf668c77eb6770b6d9cd037277da84bf0ad4b2846b5124a47b0` | 208 |
| #105 `gitleaks/gitleaks-action` | `ff98106e4c7b2bc287b24eaf42907196329070c7` | `23:09:24` | `3f88235e0914861be223a8584e376ab9c686f41bd77655852c4c12cbc71f73fa` | 17 |
| #103 `sigstore/cosign-installer` | `398d4b0eeef1380460a10c8013a76f728fb906ac` | `23:09:24` | `5fd270b570f7ac92a4065186c997d3ac0b7351c7c36a7defd85cd109bd93dd3f` | 6 |
| #102 `peter-evans/create-or-update-comment` | `e8674b075228eee787fea43ef493e45ece1004c9` | `23:09:33` | `4a652e05b844b8be883938916496d26bc5e22528bc1c0f87ad7198cbab22eed7` | 27 |

Pinned source trees, in the same order: `150e70ecad5ebf06a559a01ea3a56d9a3236d2b1`, `bb934e399202b45ca0a0ebc508adefb58bb2ae3b`, `50087d01bbbe89f68a29e3e53220f419c44eb3ee`, `c13729074d183d43da2e2165e5c8800f5373eba1`, `a6727213ab218c2973cc12c8d2b35bb7f5c72911`.

### Ordering is not inferred from hashes or timestamps

- At 23:13, official checkout tags/releases mapped the proposed SHA to **v7.0.1**, current pinned baseline to **v5.0.1**, and current v4 tag to **v4.4.0** (`11d5960a326750d5838078e36cf38b85af677262`). Releases were neither draft nor prerelease. Sources: [v7.0.1](https://github.com/actions/checkout/releases/tag/v7.0.1), [v5.0.1](https://github.com/actions/checkout/releases/tag/v5.0.1), [v4.4.0](https://github.com/actions/checkout/releases/tag/v4.4.0). The compare API reported divergence, so an ancestry claim would be wrong; stable release ordering supplies version ordering, with security/behaviour checks still outstanding.
- Upload-artifact's v4 commit `ea165f8d65b6e75b540449e92b4886f43607fa02` is an ancestor of the proposed v6 SHA: compare returned `ahead`, 43 ahead / zero behind.
- Comment action v4 `71345be0265236311c031f5c7866368bd1eff043` to v5 returned `ahead`, 112 ahead / zero behind.
- Gitleaks baseline `dcedce43c6f43de0b836d1fe38946645c9c638dc` and cosign-installer baseline `f713795cb21599bc4e5c4b58cbad1da852d7eeb9` could not be resolved: compare and Git commit API 404, REST commit API 422 “No commit found for SHA”, confirmed at 23:13. GitHub read authentication worked for the other queries. These baseline provenance gaps remain blockers.

### Required release assets

Gitleaks target source defaults to **8.24.3**; it was not assumed to follow latest. At 23:16:19–23:16:22:

| Official URL | Actual SHA-256 | Result |
| --- | --- | --- |
| `https://github.com/gitleaks/gitleaks/releases/download/v8.24.3/gitleaks_8.24.3_checksums.txt` | `eefa9ab1ee69571248a6fa070a2a7de0837dd9eb72745d131f8766206aac8ac2` | Retrieved official checksum file. |
| `https://github.com/gitleaks/gitleaks/releases/download/v8.24.3/gitleaks_8.24.3_linux_x64.tar.gz` | `9991e0b2903da4c8f6122b5c3186448b927a5da4deef1fe45271c3793f4ee29c` | 5,796,002 bytes retrieved; SHA-256 matched official checksum. Not executed. |

Redirects stayed on GitHub's `release-assets.githubusercontent.com`; signed query strings are intentionally omitted.

Cosign required assets were **not retrieved or signature-verified**. The inspected proposed action pins bootstrap v2.5.2; its Linux amd64 binary expected SHA-256 is `bcfeae05557a9f313ee4392d2f335d0ff69ebbfd232019e3736fb04999fe1734`. The repository's explicit `cosign-release: v2.4.1` also requires that release's `cosign-linux-amd64`, `.sig` and `release/release-cosign.pub`. The source pins public-key SHA-256 `f4cea466e5e887a45da5031757fa1d32655d83420639dc1758749b744179f126`. These are future verification inputs, **not successful asset results**.

## E5 — Reproduction, limits and planning boundary

Session scratch location:

`C:\Users\prbillir\AppData\Local\Temp\ama-plan-001-proxy-20261009`

It contains temporary request records, metadata, probe scripts and downloaded archives. It is not a repository dependency, permanent evidence service or prerequisite for another maintainer: immutable identities, source locations, digests and reproduction methods are recorded above. Re-fetch and revalidate at final installation time; do not count the scratch cache as fresh final evidence. No signed URL credentials were copied into this document.

Planning-only operations:

- Standard `setup-plan.ps1 -Json` produced the expected feature/plan paths and branch. Its feature-scoped specification-hardening guard succeeded.
- The standard `update-agent-context.ps1 -AgentType copilot` was run on a disposable mirror. It completed; no substantive context additions were needed. The real project guidance and manual additions remained byte-for-byte unchanged.
- Manifests, four uv locks, pnpm lock, active workflows, test configurations, Docker/development install recipes and the existing source-policy helper were inspected. Their commands were not executed as installs/tests.
- Planning-document validation passed: 33 unique matrix PRs, 31 work-item identities, P/F/R/H counts 12/1/15/5, all recorded PR heads and npm/wheel/Action artifact digests matched the collected observations, no unresolved template markers or later-phase artifacts, and protected inputs were unchanged. This was document/evidence validation, not an application test run.
- All 33 source PRs remain included. No whole-batch upgrade readiness, final security clearance or application-validation pass is asserted.

**Still unverified**: complete native/transitive/build artifact closure; MSAL common 16.14.2; full supported-environment installs; stronger provenance where npm metadata supplies only SHA-1; cosign assets/signatures; affected independently resolved pip baselines; runner versions and live credentials; all applicable quality/security gates.

The raw observations support a human Plan review with explicit holds, not an implementation or merge approval.

## E6 — Phase-8 execution-start snapshot and T001 recheck

**Observation window**: local worktree/source-input hash capture at `2026-10-09T01:59:16Z`; fixed-scope PR recheck `2026-10-09T02:02:05.5166436Z`–`2026-10-09T02:02:09.5658075Z` (UTC).
**Execution-start HEAD**: `f825197e1113437c96d56c0b621fef4ed5d329f0`; expected planning baseline: `62d249dc1205644fed934ea167df56695e92b3d2` (**different**).
**HEAD difference assessment**: `git diff --name-status 62d249dc1205644fed934ea167df56695e92b3d2...HEAD` showed only feature documentation/checklist files added; no application, dependency, workflow, or package-source-policy input changed since the recorded baseline. Each dependency manifest/lock hash in E0 was re-computed and matched exactly. Therefore the HEAD discrepancy is recorded, but no dependency/source input drift requiring a scope decision was found.

The pre-edit worktree was `M specs/001-proxy-dependency-upgrades/tasks.md`, untracked `specs/001-proxy-dependency-upgrades/.analyze-done` and `specs/001-proxy-dependency-upgrades/review.md`, with no staged changes. These user/prior-phase artifacts are preserved. No source, policy, workflow, manifest, or lock file had been edited when these hashes were captured.

### E0 dependency-input hash recheck

Each value below was recalculated with SHA-256 and matches the corresponding E0 value above:

| Input | Rechecked SHA-256 | Result |
| --- | --- | --- |
| Feature `spec.md` | `fa8d3b615693624afd9d8874a77ad7874703121bec7cd1624878beb66a5f1034` | match |
| `checklists\requirements.md` | `2ead948df3298c8346fa5d5baa9c61fe8831df7ba279b7e3da43bef2ca035027` | match |
| `.specify\memory\constitution.md` | `5bd445a37ab0f0c323b7544b004e6775777572870fb9aa3ee50a4e014865866b` | match |
| `.github\agents\copilot-instructions.md` | `de79d0536c70e23f6846f5a5344dc27d0a1452fc725472ebcda6e212ccb90c0e` | match |

| Input | Rechecked SHA-256 | Result |
| --- | --- | --- |
| `package.json` | `5eb6d50a7c6faf9d0ccba7a644f1524bc9e7a1bb9733bfc8145ed82b0148de17` | match |
| `apps\web\package.json` | `6e36c4424448030ee238d54044ef3399d17d8776ee4b13e0a5e377b7f6e86db0` | match |
| `packages\ui\package.json` | `4c9a1965b5583f9d4a7687c6fa1bb7e1cf7a470665f8db1001156842e55cd275` | match |
| `pyproject.toml` | `db8c0d71e077248bb38796121133842bf0801aa26edaea2243bfe598d657a03a` | match |
| `apps\agents\pyproject.toml` | `e24ad41cc8c11d2f0b9bb5bf10b23a221fb5884deca99b1586cd07ba6240a4a6` | match |
| `apps\api\pyproject.toml` | `baad8872399c46cf7edb257e65ae6b3367632cb03a39306ac1a9a9ae325cee63` | match |
| `pnpm-lock.yaml` | `a7faae5796f708f8c1dff2b95bc0fbb3bcd3bac598af7cfda8a641864dcb75e4` | match |
| `uv.lock` | `5d6c10e42cfed38ce9d2a065e0cc2bc3bb5bffbb11bfb63a1d1a03e434fb0b00` | match |
| `apps\agents\uv.lock` | `1452d8f9f692411a9dd32ec4cb3135b38090cd0bba083dd75422c603f90efa77` | match |
| `apps\api\uv.lock` | `748bfa0f0c991bc1d5d85ff9b9220e5cda6dc722b6226d9ef750975ec3efe3fc` | match |
| `tools\specify-cli\uv.lock` | `56b333409ddcbda721045331cb54dcc629b13a2e4a001128376aedb94fd43edf` | match |

### Pre-edit package-source-policy and recipe inputs

The repository has no `.npmrc`, `.pnpmfile.cjs`, or `uv.toml` at execution start. `npm config get registry` returned `https://packagefeedproxy.microsoft.io/npm/`; this reflects the current effective user configuration, not a checked-in repository policy. No credentials or credential-bearing config were read or recorded. Existing Python proxy declarations and lock sources remain as recorded in E0. The following additional source-setting/consumer boundary inputs were hashed before any permitted edits:

| Input | SHA-256 |
| --- | --- |
| `pnpm-workspace.yaml` | `c39825523db53e12c96cda70f7073c837a642d5aafd376d573c0e9b51c79e539` |
| `scripts\verify_python_package_sources.py` | `8f9418048d69a6624eecd2666e1f17f8eb1a89431b363e75f100f94c08f4f7f7` |
| `.devcontainer\devcontainer.json` | `a2e05109f89df89e1110878a5c035161ad87071ab9edfc07daca72c28b9b8140` |
| `.devcontainer\Dockerfile` | `6afa9189cfe8ab77bb702c28c126b6291892f686a817a3294f4c49180ed77180` |
| `.devcontainer\install-python-dependencies.py` | `885a129909dcb2f569851504ab377a43f2b0f0d5bbbe4515ffb2ac9d6ab3549d` |
| `compose.yaml` | `e5359893df070606964004534512fcbf08d9485d0c5c9c23768b4ed953cafda1` |
| `apps\web\Dockerfile` | `146f66a05a8e6c6415dd44ca947a931c5c7a0b0627a3bfefbcc000d3439920e8` |
| `apps\api\Dockerfile` | `29afddc5814bd331907f1df917313a7a82073efda7dfc143de497b7e512ad67a` |
| `apps\agents\Dockerfile` | `6fd895cbcad6cf50309046a9ed0d55b0408094256cde0db9beb1bf1c99f2affa` |
| `apps\ingestion\Dockerfile` | `30b947ad6fad2bef75e71a775d76f99b9778ecb101d96e67fd84dfa234bd423a` |
| `apps\ingest-runner\Dockerfile` | `02e99699f3df2137df60e20c9bdc8e9370aa952a5d7a1a7467eb03db9477f740` |
| `apps\eval-runner\Dockerfile` | `48324b9b42614337a9381aa0c5696b406373ced4a289601b1f14264f2fd61e76` |
| `scripts\install_pyproject_dependencies.py` | `682d5a4545f8ca151efe05175b42aaf90d5ac80891723e5543f45d60c8ad6f57` |
| `.npmrc`, `.pnpmfile.cjs`, `uv.toml` | absent at execution start |

### Pre-edit workflow SHA-256 inventory

All workflow files in this table were hashed before T004. This is the protected pre-edit baseline for the entire current workflow directory, not only the three T004 files.

| Workflow | SHA-256 |
| --- | --- |
| `.github\workflows\amend-loop-coupling.yml` | `88817f36ce830fe9bc6f5b0ef24b02217552a3eb9a613876e9f0f731e06c626a` |
| `.github\workflows\cd.yml` | `bd0c5bf23da18d1d62b0a1bdcd49bcb949ab87c10024767659faa46ea4db781a` |
| `.github\workflows\chaos-quarterly.yml` | `be842a3f011aa38a52d045de8b1f7e440298c97da145128c663b4056e2f23c32` |
| `.github\workflows\ci.yml` | `08e82c721590a47b7c9fe8193702b49eca80aeec074750cac90ebd2d7b259dd3` |
| `.github\workflows\codeql.yml` | `be5ce7e848a4f588d54649e2fbc8df9295b4a04e67573c69064fa1cd994df9d3` |
| `.github\workflows\corpus-ingest.yml` | `a237d894ec56b35b797beb0f3ac09fdbcf03f53e945a0372db00373e2aa44182` |
| `.github\workflows\dora-metrics.yml` | `731b03559c6054d14ccc2402d646bd6373d0b0ba2ab44c00bb3265881142c803` |
| `.github\workflows\dr-drill.yml` | `e60bf4113d9631b55ee92d21df540316c0c88cc2b9e98e044a06925255679d15` |
| `.github\workflows\drift-detection.yml` | `424d86f182d7086707a73dcbe97b370120bab26ea2604cc1eabaf9f2f9a24b50` |
| `.github\workflows\eval-pr-gate.yml` | `424fa2e7836ce438451d558d3597ec7e174c617154f0bb5d2353bb13904a0758` |
| `.github\workflows\eval-publish-dataset.yml` | `fc81cb502ce3e0bf1b1cbcb1093d63b8679a1b5eb2aa2108353bc7c89741a8ec` |
| `.github\workflows\foundry-carveout-review-6mo.yml` | `f04c605a66c5fb06335ab70ac86696290fc2153e71dabd5d6b0de167c772bab7` |
| `.github\workflows\foundry-carveout-review.yml` | `29d4c3397d12f02a156e543111e4d0cf03250dae8a9849da5ab372e3c267e771` |
| `.github\workflows\help-gates.yml` | `d4bdda588ffb57821c027a5f5ef12e471a154741d4d2be2b8b719464a5a544cd` |
| `.github\workflows\help-snapshot.yml` | `9b8ad0a368f75a67127f4e7b89e8248381ff16e6e9bf4ad95e664a32a0a729d0` |
| `.github\workflows\nightly-load.yml` | `16f4709e73415d16b79026704fcc19e9ce6cb6db4155c333c5e0ac7551c95bf0` |
| `.github\workflows\prompts-publish.yml` | `a2d28059950eeceecdeb367b00f969b8d5c57dc27450aff49c1b79db39d92263` |
| `.github\workflows\security-scan.yml` | `bec69dce9e2819f57c69a884b0f555594b2b70bc556d78c549bd0b9f2acd2152` |
| `.github\workflows\simulation-load-test.yml` | `e4e4341f4186eaee1994930995cb0ab3139fdcf0105432c4b38faf9cc2fa04a7` |
| `.github\workflows\simulation-stub-sweep.yml` | `9ed8a47010876fd04bd6b860a6ae9d30271eabed9470150f1c66cec96a652585` |
| `.github\workflows\spec-035-gate.yml` | `734d38cb452f9b6c0236957e00417d1eec3d2e0e083fce603c3219c7bbe0ce35` |
| `.github\workflows\spec-036-50-agent-load.yml` | `5dd80dfa74784059eb335061ab59b9f23e3fa7cf5db2f8a3e977f07908ac8e9c` |
| `.github\workflows\spec-036-blue-green-e2e.yml` | `889dd54e0c23585dc7d72711fa1d18162f4181e69e54ec3ca71a68d3f9117f6c` |
| `.github\workflows\staging-promotion.yml` | `ed251762275b52c64def6c7ce00c60b74e341768398bc58fd7cc9a7c6cf9177f` |
| `.github\workflows\web-coverage-iteration.yml` | `223702b43facc93faca58493cfe389c34a6b6c1079a7be5edabf1590e2f51a80` |

### E1 fixed-scope PR recheck

Read-only GitHub GraphQL query targeted **only** the 33 PR numbers in the frozen register; it did not enumerate other PRs or perform a GitHub write. Result: 33/33 open, no file list exceeded 100 entries, and every observed head/base and changed-file set matched E1's recorded heads, base groups, and proposal surfaces. No PR drift was found.

| PR | State | Head SHA | Base SHA | Current changed files |
| --- | --- | --- | --- | --- |
| #149 | OPEN | `88374e88219178caa2e962b3fac8f2ee791cdae8` | `62d249dc1205644fed934ea167df56695e92b3d2` | `apps/web/package.json` |
| #150 | OPEN | `d1971c19598bf880cafbfd0e9a48f7dc3ca8a930` | `62d249dc1205644fed934ea167df56695e92b3d2` | `apps/web/package.json` |
| #148 | OPEN | `709b50a94a065869ae28920857b64814382eff90` | `62d249dc1205644fed934ea167df56695e92b3d2` | `apps/web/package.json` |
| #147 | OPEN | `cc686cb730b8be99ea7834f2e2692c5a551d3a57` | `62d249dc1205644fed934ea167df56695e92b3d2` | `apps/web/package.json` |
| #146 | OPEN | `b2238f8fc57f89635ca10d2790a044a2555f9ffa` | `62d249dc1205644fed934ea167df56695e92b3d2` | `apps/web/package.json` |
| #144 | OPEN | `ab07c81f375e752fe78328144d9062900bb699ab` | `62d249dc1205644fed934ea167df56695e92b3d2` | `apps/web/package.json` |
| #133 | OPEN | `0108cd0185694308dd124f432804d0bad0dcbf47` | `5c0dab3195ba12e0af20a3ae67b75d117ced7c99` | `apps/web/package.json`, `pnpm-lock.yaml` |
| #137 | OPEN | `07f744c5a70210cdde91f777cfe0b3204647e0c8` | `5c0dab3195ba12e0af20a3ae67b75d117ced7c99` | `apps/web/package.json`, `pnpm-lock.yaml` |
| #132 | OPEN | `5652c57402f1077485b715d4238049e81ac2ce6d` | `5c0dab3195ba12e0af20a3ae67b75d117ced7c99` | `apps/web/package.json` |
| #130 | OPEN | `3ce8337f68350df9a4f99e8fc3f5fe91f0a7acfa` | `5c0dab3195ba12e0af20a3ae67b75d117ced7c99` | `packages/ui/package.json` |
| #135 | OPEN | `4adb252cb0d5dc1831daf787cb403fc2398f90a1` | `5c0dab3195ba12e0af20a3ae67b75d117ced7c99` | `pyproject.toml`, `uv.lock` |
| #136 | OPEN | `fa398a9451890e15900a26269d4a60ff47fcf9e7` | `5c0dab3195ba12e0af20a3ae67b75d117ced7c99` | `apps/agents/uv.lock` |
| #111 | OPEN | `ac341efdcc950ad9571fecc81d093226819e0694` | `cebd9064cb534e78b96ea719caec4e35ad6e705f` | `uv.lock` |
| #134 | OPEN | `2248d1fd3df3dc721b5377ca91e4879cfc95a3a0` | `5c0dab3195ba12e0af20a3ae67b75d117ced7c99` | `apps/agents/pyproject.toml`, `apps/agents/uv.lock` |
| #121 | OPEN | `564bcba2068f7822c6cf308a602d8cc647dab8a5` | `5c0dab3195ba12e0af20a3ae67b75d117ced7c99` | `uv.lock` |
| #116 | OPEN | `49555b31a1dbd43da2e148a669ea38e8c0c0aaec` | `5c0dab3195ba12e0af20a3ae67b75d117ced7c99` | `uv.lock` |
| #124 | OPEN | `4cb797e3cb9f4894142f0fdbb119bb8b0cab5689` | `5c0dab3195ba12e0af20a3ae67b75d117ced7c99` | `uv.lock` |
| #123 | OPEN | `4d8a1ae984b15fd390fe263d09de93a0e98ee3dc` | `5c0dab3195ba12e0af20a3ae67b75d117ced7c99` | `uv.lock` |
| #129 | OPEN | `c887681fdcb8026be0af8395ec8cbf710d7c4ecd` | `5c0dab3195ba12e0af20a3ae67b75d117ced7c99` | `apps/agents/uv.lock` |
| #128 | OPEN | `3c493bbef1dd554d725b1e007859a4b1351c97ad` | `5c0dab3195ba12e0af20a3ae67b75d117ced7c99` | `apps/agents/uv.lock` |
| #127 | OPEN | `80a12a3cecac8b66ec5776b04765466e4b3ed157` | `5c0dab3195ba12e0af20a3ae67b75d117ced7c99` | `apps/agents/pyproject.toml`, `apps/agents/uv.lock` |
| #126 | OPEN | `8bf1b9d636aad74341580decea8eea004169cfe6` | `5c0dab3195ba12e0af20a3ae67b75d117ced7c99` | `apps/agents/uv.lock` |
| #125 | OPEN | `f73415295c9e5f9edfbdc49d0fce75375fd2fcc3` | `5c0dab3195ba12e0af20a3ae67b75d117ced7c99` | `apps/agents/uv.lock` |
| #112 | OPEN | `a5d5b3a6bddea09283da28c8731525ecff8a7ce7` | `cebd9064cb534e78b96ea719caec4e35ad6e705f` | `apps/agents/uv.lock` |
| #120 | OPEN | `ff3b73a1eeb1fc188a6bc1043af010da15550add` | `5c0dab3195ba12e0af20a3ae67b75d117ced7c99` | `apps/agents/uv.lock` |
| #115 | OPEN | `c98d5143644529072d44a8eca920243f59920aac` | `5c0dab3195ba12e0af20a3ae67b75d117ced7c99` | `apps/agents/uv.lock` |
| #122 | OPEN | `648ee7b0891da1995166d8364e16db5bde86b162` | `5c0dab3195ba12e0af20a3ae67b75d117ced7c99` | `apps/agents/pyproject.toml`, `apps/agents/uv.lock` |
| #117 | OPEN | `548fb83494fe13e97fbfde52665f7347b9b4797c` | `5c0dab3195ba12e0af20a3ae67b75d117ced7c99` | `apps/agents/uv.lock` |
| #145 | OPEN | `2f9a951c194105ec207be1608180c09ebbe21afb` | `62d249dc1205644fed934ea167df56695e92b3d2` | 19 workflow files; same set as E1 |
| #143 | OPEN | `577e36ce45e91635b81d8ebb759e767beb285764` | `62d249dc1205644fed934ea167df56695e92b3d2` | `.github/workflows/ci.yml`, `.github/workflows/corpus-ingest.yml` |
| #105 | OPEN | `f6bb036b9ef93e631fab91511f516ef3a136b051` | `cebd9064cb534e78b96ea719caec4e35ad6e705f` | `.github/workflows/security-scan.yml` |
| #103 | OPEN | `7b7587310c82ab24365277d274e6f2331ba592cd` | `cebd9064cb534e78b96ea719caec4e35ad6e705f` | `.github/workflows/prompts-publish.yml` |
| #102 | OPEN | `55ec28b873133f54b4d10ed72e97a7b2ba6521bd` | `cebd9064cb534e78b96ea719caec4e35ad6e705f` | `.github/workflows/foundry-carveout-review.yml` |

**T001 result**: complete for the frozen scope: recorded the different execution HEAD, verified E0 input hashes unchanged, hashed workflow/source-policy baselines before edits, and verified the exact 33 PR heads/bases/files without scope expansion. No scope decision is currently needed.

## E7 — Supported-environment matrix and exactness holds (T002)

The matrix below was built from `plan.md`, `quickstart.md`, checked-in workflows, Dockerfiles, helper scripts and source settings. Rows are intentionally separate by importer, install recipe, container or Action runner; no result is aggregated across independent consumers. Versions and platforms shown are repository declarations/targets, not observations from a completed CI/container run.

Common exactness rule: `ubuntu-latest`, `windows-latest`, `node:24-alpine`, `node:24-bookworm-slim`, `python:3.12-slim`, `python:3.13-slim`, and `mcr.microsoft.com/devcontainers/python:1-3.12-bookworm` are mutable labels with no digest recorded in the checked-in recipes. The workflows pin Node/Python majors, not runtime patches. The exact hosted runner image/build, actual architecture/libc build, installed runtime patch and GitHub Actions runner version therefore remain **unknown until an authorized matching run**; none is inferred from the current Windows ARM64/Python 3.14 host. Docker builds have no recorded base-image digest or explicit target platform in the affected Dockerfiles. These are concrete per-row holds, not substituted evidence.

### Locked/importer and aggregate environments

| Environment ID | Independent scope / checked-in recipe | Declared runtime and tools | OS / architecture / libc / digest | Effective source and markers | Status / concrete gap |
| --- | --- | --- | --- | --- | --- |
| `NW-PNPM-UBUNTU` | `apps\web` importer; root `pnpm-lock.yaml`; CI `quality` install and quickstart root workspace | Node `24`; pnpm `10.6.3` | `ubuntu-latest`; required x64 target; exact hosted image, Node patch, libc and runner version unobserved | Python env is proxy-only; `NPM_CONFIG_REGISTRY` was absent from the job at baseline; importer remains independent | Matrix recorded; exact runner/runtime and CI npm source evidence blocked |
| `NU-PNPM-UBUNTU` | `packages\ui` importer; same root lock and shared workspace install | Node `24`; pnpm `10.6.3` | Same declared runner target as NW; exact image/patch/libc/runner version unobserved | Same npm boundary as NW; retain Next 15 importer separately | Matrix recorded; same environment hold; no collapse into NW |
| `NW-ALPINE-WEB` | `apps\web\Dockerfile`, builder and runtime; root pnpm lock, web importer | `node:24-alpine`; global pnpm `10.6.3` | Alpine/musl by tag; exact Alpine/Node patch, architecture, libc revision and image digest unrecorded | Dockerfile `ARG` default is the Microsoft npm proxy; `compose.yaml` passes that build argument | Blocked for exact digest/architecture and musl artifact validation |
| `DEV-PY-HELPER` | `.devcontainer\devcontainer.json` post-create helper; `.devcontainer\install-python-dependencies.py` aggregates root dev/load, API, agents and other pyprojects without uv locks | Python `3.12` image; uv `0.11.21`; pip/uv resolver | Debian Bookworm/glibc tags; actual container architecture, image digest and Python patch unobserved | Helper forces Microsoft PyPI proxy and clears secondary indexes; `devcontainer.json` mounts persistent caches by default | Blocked for exact image/architecture and clean baseline; local host is not evidence |
| `DEV-PNPM` | Same devcontainer post-create `CI=true pnpm install --frozen-lockfile`; shared root lock, web and UI importers | Node `24`; pnpm `10.6.3` | `node:24-bookworm-slim` stage plus devcontainer Bookworm; digest/architecture/patch unobserved | Dockerfile sets npm proxy; baseline `devcontainer.json` had no `NPM_CONFIG_REGISTRY` in `containerEnv`; persistent pnpm/node_modules volumes are not clean caches | Matrix recorded; clean runs and explicit container boundary required |
| `PR-ROOT-LINUX-UV` | Root `uv.lock`; quickstart `uv sync --locked --extra dev --extra load --no-cache --python 3.12 --no-python-downloads` | Python `3.12`; documented uv `0.11.21` | Linux / `ubuntu-latest` target; patch, image, architecture, libc and runner build not captured | Microsoft PyPI proxy; `dev` and `load` extras; marker-specific branches retained | Blocked for exact runner/runtime and baseline installs |
| `PR-ROOT-WINDOWS-CI` | Root `uv.lock`; `ci.yml` `quality-windows`, `windows-ci`, `--no-install-project`; separate eval-runner `--no-deps` step | Python `3.12`; uv installed as `0.11.21` | `windows-latest`, required x64 target; exact Windows build, architecture observation, Python patch and runner version unobserved | Microsoft PyPI proxy; `windows-ci` extra and Windows markers | Blocked for matching Windows x64 runner and two baseline installs |
| `PA-AGENTS-LINUX-UV` | `apps\agents\uv.lock`; standalone agents `uv sync --project ... --locked --no-cache --python 3.12 --no-python-downloads` | Python `3.12`; documented uv `0.11.21` | Linux target; no pinned runner/image/digest, architecture, libc or Python patch captured | Microsoft PyPI proxy; agents lock/markers only, independent of root | Blocked for exact environment and two baseline installs |

### Separate Linux pip/helper/container recipes

Each row has its own resolution ID and baseline status, even where it installs the same local project or uses the same runner label. At baseline, workflow Python settings name only the approved proxy; there is no actual installed map recorded for these recipes.

| Environment ID | Exact consumer / recipe | Declared environment and resolution boundary | Source / status |
| --- | --- | --- | --- |
| `CI-PIP-SOURCE-POLICY` | `.github\workflows\ci.yml` `python-package-source-policy`; `pip install pytest`, then `tests/policy` | `ubuntu-latest`, setup Python `3.12`; unlocked pip recipe | Microsoft PyPI proxy declared; runtime patch/runner build and installed map unobserved; baseline blocked |
| `CI-PIP-QUALITY` | `ci.yml` `quality`; pip installs tooling plus editable root, API and agents projects | `ubuntu-latest`, Python `3.12`; independent pip resolution, not root/agents uv-lock proof | Microsoft PyPI proxy declared; exact runner and installed baseline map unobserved; blocked |
| `CI-PIP-ISOLATION` | `ci.yml` `simulation-tenant-isolation`; pip installs pytest/pytest-asyncio and editable `apps/api` | `ubuntu-latest`, Python `3.12`; unlocked recipe | Microsoft PyPI proxy declared; exact runner and installed map unobserved; blocked |
| `CI-PIP-STORY` | `ci.yml` `story-acceptance`; pip installs editable API and agents alongside a separate pnpm install | `ubuntu-latest`, Python `3.12`, Node `24`, pnpm `10.6.3`; two separate source boundaries | Microsoft Python proxy declared; npm registry unset at baseline; both exact runner and installed maps unobserved; blocked |
| `CI-PIP-EVIDENCE-PACK` | `ci.yml` `evidence-pack-publication-gate`; pip installs `jsonschema`, `pyyaml`, `referencing` | `ubuntu-latest`, Python `3.12`; unlocked recipe | Microsoft PyPI proxy declared; exact runner/installed map unobserved; blocked |
| `EVAL-PR-PIP` | `eval-pr-gate.yml` `eval-gate`; editable eval-core, eval-dataset, eval-runner, API, then pytest/ruff | `ubuntu-latest`, Python `3.12`; independent pip recipe | Microsoft PyPI proxy declared; exact runner/installed map unobserved; blocked |
| `SPEC-035-PIP` | `spec-035-gate.yml` `invariants`; tooling and editable API | `ubuntu-latest`, Python `3.12`; independent pip recipe; separate from its pnpm install | Microsoft PyPI proxy declared; exact runner/installed map unobserved; blocked |
| `SPEC-036-50-PIP` | `spec-036-50-agent-load.yml`; editable root `.[load]` recipe | `ubuntu-latest`, Python `3.12`; root optional `load` dependencies resolved by pip | Microsoft PyPI proxy declared; exact runner/installed map unobserved; blocked |
| `SPEC-036-BLUEGREEN-PIP` | `spec-036-blue-green-e2e.yml`; pytest/pytest-asyncio and editable API/agents | `ubuntu-latest`, Python `3.12`; independent pip recipe | Microsoft PyPI proxy declared; exact runner/installed map unobserved; blocked |
| `CD-DEPLOY-PIP` | `cd.yml` `deploy`; editable API/seed-loader and `jsonschema` helper step | `ubuntu-latest`, Python `3.12`; deployment workflow recipe; not authorized to execute | Microsoft PyPI proxy declared; no deployment or live run; exact runner/installed map unobserved; blocked |
| `DOCKER-API-PIP` | `apps\api\Dockerfile`; Python dependency helper, eval-core/API installs | `python:3.12-slim`, mutable tag; no uv lock drives helper resolution | Microsoft PyPI proxy environment in Dockerfile; image digest/arch/libc and installed map unobserved; blocked |
| `DOCKER-AGENTS-PIP` | `apps\agents\Dockerfile`; Python helper plus no-deps local project install | `python:3.12-slim`, mutable tag; independent from standalone agents uv lock | Microsoft PyPI proxy environment in Dockerfile; image digest/arch/libc and installed map unobserved; blocked |
| `DOCKER-INGESTION-PIP` | `apps\ingestion\Dockerfile`; direct pip install eval-core/API/ingestion | `python:3.12-slim`, mutable tag | Microsoft PyPI proxy environment in Dockerfile; image digest/arch/libc and installed map unobserved; blocked |
| `DOCKER-INGEST-RUNNER-PIP` | `apps\ingest-runner\Dockerfile`; Python 3.13 pip recipe with uv `0.5.14` | `python:3.13-slim`, mutable tag; distinct from the Python 3.12 target matrix | Microsoft PyPI proxy environment in Dockerfile; exact Python/build digest and resolution not captured; blocked, no 3.12 substitution |
| `DOCKER-EVAL-RUNNER-PIP` | `apps\eval-runner\Dockerfile`; direct pip install eval-core/eval-runner | `python:3.12-slim`, mutable tag | Microsoft PyPI proxy environment in Dockerfile; image digest/arch/libc and installed map unobserved; blocked |
| `DEVCONTAINER-HELPER-PIP` | `.devcontainer\install-python-dependencies.py --mode editables` | Python `3.12`, uv `0.11.21`; helper reads many pyprojects and resolves ranges without locks | Helper enforces Microsoft PyPI proxy; this helper resolution remains separate from each Docker and CI recipe; blocked pending two clean runs |

### Active Action runner environments

`runs-on` labels below are known from the current YAML; exact host OS image/build, actual runner version, runtime patch and attested architecture remain unobserved. Runner minimums from the approved plan remain mandatory: `2.327.1`, and `2.329.0` for checkout's authenticated Docker-action Git use.

| Environment ID | Active reference population | Declared runner / runtime | Exactness/source status |
| --- | --- | --- | --- |
| `ACTION-UBUNTU-CHECKOUT` | 40 active checkout uses | `ubuntu-latest`; checkout Node runtime | Runner image/version and checkout behavior unobserved; official source retrieval is separate; blocked |
| `ACTION-WINDOWS-CHECKOUT` | One active checkout use (`quality-windows`) | `windows-latest`; checkout Node runtime | Windows image/build and runner version unobserved; blocked |
| `ACTION-SOVEREIGN-CHECKOUT` | One active checkout use (`specify-cli-quality`) | `[self-hosted, ama-au-sovereign, azure-au, linux, x64]` | Labels specify Linux/x64; actual version, image, sovereign identity and required minimum unverified; blocked |
| `ACTION-UBUNTU-UPLOAD` | Ten active upload-artifact uses | `ubuntu-latest`; official Action runtime | Actual runner image/version and retrieval evidence unobserved; blocked |
| `ACTION-UBUNTU-GITLEAKS` | One active gitleaks use | `ubuntu-latest`; target Action uses Node 20 | Existing baseline provenance remains B-ACTION-BASE; runner and target asset revalidation outstanding |
| `ACTION-UBUNTU-COSIGN` | One active cosign-installer use | `ubuntu-latest`; composite action | Existing baseline provenance and required assets/signature remain unresolved; runner evidence absent |
| `ACTION-UBUNTU-COMMENT` | One active create-or-update-comment use | `ubuntu-latest`; official Action runtime | No live comment authorized; runner/functional evidence absent |

**T002 result: BLOCKED**. The matrix and per-consumer environment IDs are recorded, but the actual devcontainer architecture cannot be established: Docker Desktop's Linux daemon is unavailable (`docker info` and the filtered devcontainer query both failed to connect to `dockerDesktopLinuxEngine`), no devcontainer is running, and the `devcontainer` CLI is absent. Mutable/unpinned hosted runner, runtime patch, libc and base-image digest fields also remain unavailable and are not inferred. These gaps block the affected environment evidence in T006, T007, T013 and final validation. The inspected local host is Windows ARM64/Python 3.14.7/Node 24.16.0/uv 0.11.21 and is diagnostic only; it is not evidence for any GitHub-hosted, Linux, Windows x64, Alpine or devcontainer run. T003–T005 source-policy settings can be scoped to already inventoried boundaries; none of those edits will claim that the unavailable environment has been verified.

Local diagnostic versions rechecked separately: Node `v24.16.0`, Python `3.14.7`, uv `0.11.21`, pnpm `10.6.3`, npm `11.13.0`, Windows NT `10.0.26300.0`, ARM64. These host values do not replace any platform/runtime row above.

## E8 — Root npm proxy policy (T003)

After the E6 pre-edit hash inventory, created only the credential-free root `.npmrc` line `registry=https://packagefeedproxy.microsoft.io/npm/`. It contains no credentials, public fallback or unrelated settings. SHA-256: `f7c36b5e6d696c92992ba4d5b59ebf93d94953f2003dcad4ac2c83f31e4a1bb2`. Verification confirmed exactly one non-empty setting and `npm config get registry` returned the approved Microsoft npm proxy. This is configuration evidence only: no artifact retrieval/install was performed and B-SOURCE-ENV remains open pending every boundary and artifact-host validation.

### T004 — Workflow npm retrieval/install/bootstrap boundaries

Before editing, a read-only scan of all 25 workflow YAML files found active npm/pnpm/npx/bootstrap boundaries only in the three task-authorized files; commented/dormant CI lines were excluded. Job-level `NPM_CONFIG_REGISTRY=https://packagefeedproxy.microsoft.io/npm/` now covers every active boundary while avoiding a no-op setting on Python-only jobs:

| Workflow | Exact affected jobs | Boundary covered |
| --- | --- | --- |
| `.github\workflows\ci.yml` | `quality`, `accessibility-citation-card`, `story-acceptance`, `docs-arch` | `pnpm/action-setup`, `setup-node`, frozen workspace installs and pnpm commands; `docs-arch`'s `npx markdownlint-cli2` |
| `.github\workflows\spec-035-gate.yml` | `invariants` | `pnpm/action-setup`, setup-node, frozen workspace install, pnpm and `npx ajv-cli` |
| `.github\workflows\cd.yml` | `deploy` | pnpm package-manager bootstrap and azd pre-provision/post-deploy hooks that package the web app |

No setting was added to `cd.yml`'s rollback job or any other workflow without an npm boundary. Existing Python proxy environment, workflow triggers, permissions, runner labels, Action refs and all other workflow content were retained. PyYAML `BaseLoader` parsed all three edited workflows; an assertion verified the exact environment variable only on the six inventoried jobs; a diff-content check found no trailing spaces on added lines.

Post-edit SHA-256: `ci.yml` `00bd6c235e41915558622a311f12fa583a2533e9b041e5703669a1bd82ccfa2c`; `spec-035-gate.yml` `7bfe504eaf4625716d2e0ed4e45691c9c72475b2b589e926a09944249ad7cb6d`; `cd.yml` `44f93f936e27f8121b9706855692640def1d9d1f0e66fefe47e81d79aa1a5e0f`. `git diff --check` returned exit 2 because Git flags the repository's CRLF terminators on newly added lines as trailing whitespace; the custom check after removing line terminators confirmed no actual trailing spaces. B-SOURCE-ENV remains open until retrieval/host evidence is verified for each relevant environment.

### T005 — Devcontainer npm boundary

Added only `NPM_CONFIG_REGISTRY=https://packagefeedproxy.microsoft.io/npm/` to `.devcontainer/devcontainer.json` `containerEnv`, covering its checked-in `CI=true pnpm install --frozen-lockfile` post-create command. JSON parsing and assertions verified the exact variable/value and frozen-install command. The existing `.devcontainer\Dockerfile` SHA-256 remains `6afa9189cfe8ab77bb702c28c126b6291892f686a817a3294f4c49180ed77180`; `compose.yaml` remains `e5359893df070606964004534512fcbf08d9485d0c5c9c23768b4ed953cafda1`; both retain their existing Microsoft proxy settings. Post-edit `devcontainer.json` SHA-256 is `b055e9b14fa32b970c6055d0d928905be0a5cf6384945e670de26d46d72b5285`. The repository npm config resolves to the approved proxy. The in-container runtime check could not be run because the Docker Desktop Linux daemon is unavailable; actual package artifact host and clean-cache retrieval are not verified. B-SOURCE-ENV therefore remains open.

## E9 — Unchanged-baseline consumer and quality gates (T006–T007)

No dependency version, lock, Action pin or application source was changed before this checkpoint. No baseline install or quality suite was attempted on the Windows ARM64/Python 3.14 host because it is not one of the supported environments; GitHub Actions were not dispatched and Docker could not connect to its Linux daemon. `NOT COLLECTED` below means no installed map was obtained; it is not an empty map, lock-derived map, or pass.

### T006 — Independent consumer baseline status

| Environment ID | Checked-in baseline recipe / independent consumer | Status | Installed map | Exact hold |
| --- | --- | --- | --- | --- |
| `CI-PIP-SOURCE-POLICY` | `ci.yml#python-package-source-policy`; `pip install pytest` | blocked | NOT COLLECTED | Requires the actual Ubuntu Python 3.12 runner; local Python 3.14 is not a substitute |
| `CI-PIP-QUALITY` | `ci.yml#quality`; pip tooling plus editable root, API and agents projects | blocked | NOT COLLECTED | Independent pip graph; exact Ubuntu/Python 3.12 environment unavailable |
| `CI-PIP-ISOLATION` | `ci.yml#simulation-tenant-isolation`; pip test dependencies plus editable API | blocked | NOT COLLECTED | Exact Ubuntu/Python 3.12 environment unavailable |
| `CI-PIP-STORY` | `ci.yml#story-acceptance`; editable API and agents alongside independent pnpm install | blocked | NOT COLLECTED | Exact Ubuntu/Node 24/Python 3.12 environment unavailable |
| `CI-PIP-EVIDENCE-PACK` | `ci.yml#evidence-pack-publication-gate`; pip `jsonschema`, `pyyaml`, `referencing` | blocked | NOT COLLECTED | Exact Ubuntu/Python 3.12 environment unavailable |
| `CI-UV-WINDOWS` | `ci.yml#quality-windows`; root `uv sync --locked --extra windows-ci --no-install-project`, then eval-runner `--no-deps` install | blocked | NOT COLLECTED | No Windows x64 `windows-latest` runner; the local ARM64 host is not equivalent |
| `CI-UV-SPECIFY-CLI` | `ci.yml#specify-cli-quality`; separate `tools/specify-cli/uv.lock`, locked/offline | not-applicable to the 31 work items | NOT COLLECTED | Protected independent lock; none of the 33 PRs targets this scope; retain its E0 hash and version map as protected |
| `EVAL-PR-PIP` | `eval-pr-gate.yml#eval-gate`; editable eval-core, eval-dataset, eval-runner, API, pytest and ruff | blocked | NOT COLLECTED | Exact Ubuntu/Python 3.12 runner unavailable |
| `SPEC-035-PIP` | `spec-035-gate.yml#invariants`; tooling plus editable API | blocked | NOT COLLECTED | Exact Ubuntu/Python 3.12 runner unavailable |
| `SPEC-036-50-PIP` | `spec-036-50-agent-load.yml#retrieval-50-agent`; root editable `.[load]` | blocked | NOT COLLECTED | Exact Ubuntu/Python 3.12 runner unavailable |
| `SPEC-036-BLUEGREEN-PIP` | `spec-036-blue-green-e2e.yml#blue-green-e2e`; pytest/pytest-asyncio plus editable API/agents | blocked | NOT COLLECTED | Exact Ubuntu/Python 3.12 runner unavailable |
| `CD-DEPLOY-PIP` | `cd.yml#deploy`; editable API/seed-loader and `jsonschema` helper | blocked / not-run | NOT COLLECTED | Deployment workflow execution is not authorized; no deployment/dispatch performed; matching runner unavailable |
| `SCRIPT-API-PIP` | `apps\api\Dockerfile`; `scripts\install_pyproject_dependencies.py` then local packages | blocked | NOT COLLECTED | Docker daemon unavailable; Python base tag has no captured digest |
| `SCRIPT-AGENTS-PIP` | `apps\agents\Dockerfile`; helper plus no-deps local install | blocked | NOT COLLECTED | Docker daemon unavailable; this pip graph is independent of the agents uv lock |
| `DOCKER-INGESTION-PIP` | `apps\ingestion\Dockerfile`; direct pip install of eval-core/API/ingestion | blocked | NOT COLLECTED | Docker daemon unavailable; Python base tag has no captured digest |
| `DOCKER-INGEST-RUNNER-PIP` | `apps\ingest-runner\Dockerfile`; Python 3.13, uv 0.5.14 and its own install sequence | blocked | NOT COLLECTED | Docker daemon unavailable; do not substitute Python 3.12 evidence |
| `DOCKER-EVAL-RUNNER-PIP` | `apps\eval-runner\Dockerfile`; direct pip install eval-core/eval-runner | blocked | NOT COLLECTED | Docker daemon unavailable; Python base tag has no captured digest |
| `DEVCONTAINER-HELPER-PIP` | `.devcontainer\install-python-dependencies.py --mode editables` | blocked | NOT COLLECTED | Docker daemon and devcontainer CLI unavailable; no supported architecture could be verified |

**T006 status: BLOCKED**. Every affected independently resolving pip/helper/container recipe has its own row and a concrete environment hold; no `uv.lock` was used as a substitute for an unlocked installed map. `B-CONSUMER-BASE` remains open and blocks all dependent pip/helper/container selection and any claim of a reproduced baseline. No public feed or alternate environment was used.

### T007 — Frozen-baseline quality checks

| Baseline environment / selector | Required command/check family from `quickstart.md` §4 | Status | Reason / failure fingerprint |
| --- | --- | --- | --- |
| `PYTHON-LINUX-3.12` | `verify_python_package_sources.py`; `pytest tests/policy -q`; ruff check/format; mypy; lint-imports; `pytest tests/equivalence`; unit/contract/integration/simulation selection with the specified marker exclusions; benchmark; overlay taxonomy `--check`; coverage ratchet | blocked / not-run | Matching Ubuntu/Python 3.12 runner unavailable; no commands executed; fingerprint `not-run: unsupported local OS/runtime` |
| `PYTHON-LINUX-ISOLATION` | `spec007_isolation --strict-markers`; minimum 113 collected cases; checked-in simulation-tenant-isolation selector | blocked / not-run | Matching Ubuntu/Python 3.12 runner unavailable; no collection count claimed |
| `PYTHON-WINDOWS-X64` | `uv sync --locked --extra windows-ci --no-install-project`; eval-runner no-deps install; Windows contract/integration selector | blocked / not-run | No Windows x64 runner; local Windows ARM64/Python 3.14 excluded |
| `WEB-NODE24-UBUNTU` | domain typecheck/build; web lint; `tsc --noEmit`; web unit/integration/a11y tests; production build/postbuild | blocked / not-run | No matching Ubuntu/Node 24 runner; exact Node patch unavailable |
| `WEB-PLAYWRIGHT` | browser install, evidence test collection/execution, story acceptance collection/execution | blocked / not-run | Docker unavailable locally; browser/OS artifact source not established; no cache treated as proof |
| `WORKFLOW-CONTRACTS` | `python -m pytest tests/devops -q`; spec-035/eval-PR gates | blocked / not-run | Matching baseline runner unavailable; no workflow dispatch or live deployment authorized |
| `SECURITY-SCANS` | CodeQL, gitleaks, PSRule, Trivy and baseline/candidate finding comparison | blocked / not-run | No exact Actions runner/scan run was available; existing thresholds/allowlists not changed |

No baseline check is represented as passed, waived, or pre-existing-failure evidence. **T007 status: BLOCKED** pending the actual supported environments and exact frozen-baseline runs.

## E10 — Traceability, lock baseline and active Action inventory (T008–T010)

### T008 — Frozen 33-PR / 31-work-item reconciliation

Read-only audit compared the frozen register in `tasks.md` to R1 in `research.md` and “Supplied PR Baseline” in `spec.md`: 33 distinct PR identifiers appear in all three; the task register has 31 distinct work-item rows; there are no missing or extra identifiers. Counts reconcile as separate units:

| Unit | P | F | R | H | Total |
| --- | ---: | ---: | ---: | ---: | ---: |
| Source PR directions | 12 | 1 | 15 | 5 | 33 |
| Work-item directions | 12 | 1 | 13 | 5 | 31 |

The denominator difference is NW-next: work-item direction remains provisional P (`16.3.8`); source PRs remain individually #149 P (`16.3.6 → 16.3.8`), #133 R (`16.2.6 → 16.2.11`) and #132 R (`16.2.6 → 16.2.11`). Their original targets and supplied scopes remain intact. These are provisional planning directions only, not delivery outcomes.

### T009 — Revalidated lock/importer baselines

The current package manifests/locks still match E0's recorded SHA-256 values. The versions below were read from the current pnpm importers/package keys and current TOML `uv.lock` package entries; they are lock resolutions, **not** evidence of installed baseline maps for independent pip/helper/container recipes. Python lock source entries resolve to the approved Microsoft PyPI proxy.

| Work item | Revalidated independent scope | Current locked resolution |
| --- | --- | --- |
| `NW-next` | `apps\web` importer in root `pnpm-lock.yaml` | Next `16.3.6` |
| `NW-eslint` | `apps\web` importer / root pnpm lock | ESLint `9.39.4` |
| `NW-jsdom` | `apps\web` importer / root pnpm lock | jsdom `25.0.1` |
| `NW-playwright` | `apps\web` importer / root pnpm lock | `@playwright/test`, `playwright`, `playwright-core` all `1.59.1` |
| `NW-node-types` | `apps\web` importer / root pnpm lock | `@types/node` `22.13.10` |
| `NW-msal-react` | `apps\web` importer / root pnpm lock | `@azure/msal-react` `5.3.2`; browser `5.9.0`; common instances `16.5.2` and `16.14.1` |
| `NW-js-yaml` | `apps\web` importer / root pnpm lock | js-yaml `4.1.1` |
| `NU-next` | `packages\ui` importer / root pnpm lock | Next `15.5.18`, distinct from web Next 16 |
| `PR-cryptography` | Root Python `uv.lock` | cryptography `50.0.1`; root declaration floor `>=50.0.0,<51` |
| `PA-h2` | `apps\agents\uv.lock` | h2 `4.3.0`, hpack `4.1.0`; root lock independently has h2 `4.4.1`, hpack `4.2.0` |
| `PR-idna` | Root Python `uv.lock` | idna `3.11` |
| `PA-aiohttp` | `apps\agents\uv.lock` | aiohttp `3.14.3` |
| `PR-msgpack` | Root Python `uv.lock` | msgpack `1.2.2` |
| `PR-pyjwt` | Root Python `uv.lock` | PyJWT `2.15.0`; keep `>=2.14.0,<3` protection |
| `PR-engineio` | Root Python `uv.lock` | python-engineio `4.14.0` |
| `PR-socketio` | Root Python `uv.lock` | python-socketio `5.17.0` |
| `PA-setuptools` | `apps\agents\uv.lock` | setuptools `82.0.1`; root separately has `84.0.0` |
| `PA-pyasn1` | `apps\agents\uv.lock` | pyasn1 `0.6.4` |
| `PA-mcp` | `apps\agents\uv.lock` | mcp `1.30.0` |
| `PA-socketio` | `apps\agents\uv.lock` | python-socketio `5.17.0`, distinct from root scope |
| `PA-engineio` | `apps\agents\uv.lock` | python-engineio `4.14.0`, distinct from root scope |
| `PA-idna` | `apps\agents\uv.lock` | idna `3.11`, distinct from root scope |
| `PA-starlette` | `apps\agents\uv.lock` | Starlette `1.7.0` |
| `PA-pyjwt` | `apps\agents\uv.lock` | PyJWT `2.15.0`; keep `PyJWT[crypto]>=2.14.0,<3` |
| `PA-settings` | `apps\agents\uv.lock` | pydantic-settings `2.14.1`; root separately has `2.15.0` |
| `PA-multipart` | `apps\agents\uv.lock` | python-multipart `0.0.32` |

Protected/current lock comparisons: `apps\api\uv.lock` idna `3.20`, `tools\specify-cli\uv.lock` idna `3.19`; neither is normalized to root `3.11`. API and specify-cli lock inputs remain at their E0 hashes. Preserve root and agents cryptography `50.0.1`, both PyJWT `>=2.14.0,<3` constraints, root redis-entraid/mem0ai protections, and root npm overrides for sharp `0.35.5`, source-map-js `1.2.2`, and PostCSS. No manifest/lock edit or installed-version claim was made. All P/F/R/H and retain/supersede directions remain provisional.

### T010 — Current active Action occurrence inventory

The inventory was parsed from all 25 current `.github/workflows/*.yml` files using PyYAML `BaseLoader`, traversing `jobs.*.steps[].uses`; YAML comments are not parsed, and there were zero matching explicitly dormant (`if: false`) steps. It yields 55 active target Action occurrences: 42 checkout, ten upload-artifact, one gitleaks, one cosign-installer and one comment. Of the ten upload references, six already use the proposed v6 full SHA. An unnamed/un-IDed step is labelled `step-N` below by its one-based YAML step position.

| Workflow | Job | Step | Runner | Baseline reference | Work item |
| --- | --- | --- | --- | --- | --- |
| `amend-loop-coupling.yml` | `coupling-check` | `Checkout` | `ubuntu-latest` | `actions/checkout@v4` | AC-checkout (#145) |
| `cd.yml` | `deploy` | `Checkout validated commit` | `ubuntu-latest` | `actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd` | AC-checkout (#145) |
| `cd.yml` | `rollback` | `step-1` | `ubuntu-latest` | `actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd` | AC-checkout (#145) |
| `chaos-quarterly.yml` | `gameday` | `step-1` | `ubuntu-latest` | `actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd` | AC-checkout (#145) |
| `ci.yml` | `python-package-source-policy` | `step-1` | `ubuntu-latest` | `actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd` | AC-checkout (#145) |
| `ci.yml` | `simulation-tenant-isolation` | `step-1` | `ubuntu-latest` | `actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd` | AC-checkout (#145) |
| `ci.yml` | `quality` | `step-1` | `ubuntu-latest` | `actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd` | AC-checkout (#145) |
| `ci.yml` | `quality` | `upload-benchmark-results` | `ubuntu-latest` | `actions/upload-artifact@b7c566a772e6b6bfb58ed0dc250532a479d7789f` | AC-upload (#143) |
| `ci.yml` | `quality` | `upload-coverage-results` | `ubuntu-latest` | `actions/upload-artifact@b7c566a772e6b6bfb58ed0dc250532a479d7789f` | AC-upload (#143) |
| `ci.yml` | `specify-cli-quality` | `step-1` | `[self-hosted, ama-au-sovereign, azure-au, linux, x64]` | `actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd` | AC-checkout (#145) |
| `ci.yml` | `quality-windows` | `step-1` | `windows-latest` | `actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd` | AC-checkout (#145) |
| `ci.yml` | `golden-set-canonical` | `step-1` | `ubuntu-latest` | `actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd` | AC-checkout (#145) |
| `ci.yml` | `accessibility-citation-card` | `step-1` | `ubuntu-latest` | `actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd` | AC-checkout (#145) |
| `ci.yml` | `accessibility-citation-card` | `Upload junit report` | `ubuntu-latest` | `actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02` | AC-upload (#143) |
| `ci.yml` | `story-acceptance` | `step-1` | `ubuntu-latest` | `actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd` | AC-checkout (#145) |
| `ci.yml` | `evidence-pack-publication-gate` | `step-1` | `ubuntu-latest` | `actions/checkout@v4` | AC-checkout (#145) |
| `ci.yml` | `docs-arch` | `step-1` | `ubuntu-latest` | `actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd` | AC-checkout (#145) |
| `codeql.yml` | `analyze` | `Checkout` | `ubuntu-latest` | `actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd` | AC-checkout (#145) |
| `corpus-ingest.yml` | `ingest` | `Checkout` | `ubuntu-latest` | `actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd` | AC-checkout (#145) |
| `corpus-ingest.yml` | `ingest` | `Upload corpus_build_sha artefact` | `ubuntu-latest` | `actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02` | AC-upload (#143) |
| `corpus-ingest.yml` | `ingest` | `Upload offline-cache bundle artefact` | `ubuntu-latest` | `actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02` | AC-upload (#143) |
| `dora-metrics.yml` | `publish` | `step-1` | `ubuntu-latest` | `actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd` | AC-checkout (#145) |
| `dr-drill.yml` | `failover` | `step-1` | `ubuntu-latest` | `actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd` | AC-checkout (#145) |
| `dr-drill.yml` | `failover` | `Upload drill artefacts` | `ubuntu-latest` | `actions/upload-artifact@b7c566a772e6b6bfb58ed0dc250532a479d7789f` | AC-upload (#143) |
| `drift-detection.yml` | `detect-drift` | `Checkout repository` | `ubuntu-latest` | `actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd` | AC-checkout (#145) |
| `eval-pr-gate.yml` | `eval-gate` | `Checkout` | `ubuntu-latest` | `actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd` | AC-checkout (#145) |
| `eval-publish-dataset.yml` | `validate-and-publish` | `Checkout` | `ubuntu-latest` | `actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd` | AC-checkout (#145) |
| `eval-publish-dataset.yml` | `validate-and-publish` | `Upload cases + manifest as artifact` | `ubuntu-latest` | `actions/upload-artifact@b7c566a772e6b6bfb58ed0dc250532a479d7789f` | AC-upload (#143) |
| `foundry-carveout-review-6mo.yml` | `review-window` | `step-1` | `ubuntu-latest` | `actions/checkout@v4` | AC-checkout (#145) |
| `foundry-carveout-review.yml` | `review-cadence-gate` | `step-1` | `ubuntu-latest` | `actions/checkout@v4` | AC-checkout (#145) |
| `foundry-carveout-review.yml` | `prompt-hash-diff-comment` | `step-1` | `ubuntu-latest` | `actions/checkout@v4` | AC-checkout (#145) |
| `foundry-carveout-review.yml` | `prompt-hash-diff-comment` | `Post comment on PR` | `ubuntu-latest` | `peter-evans/create-or-update-comment@v4` | AC-comment (#102) |
| `help-gates.yml` | `help-gates` | `step-1` | `ubuntu-latest` | `actions/checkout@v4` | AC-checkout (#145) |
| `help-snapshot.yml` | `publish` | `step-1` | `ubuntu-latest` | `actions/checkout@v4` | AC-checkout (#145) |
| `help-snapshot.yml` | `rollback` | `step-1` | `ubuntu-latest` | `actions/checkout@v4` | AC-checkout (#145) |
| `nightly-load.yml` | `load` | `step-1` | `ubuntu-latest` | `actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd` | AC-checkout (#145) |
| `nightly-load.yml` | `load` | `Upload load test artefacts` | `ubuntu-latest` | `actions/upload-artifact@b7c566a772e6b6bfb58ed0dc250532a479d7789f` | AC-upload (#143) |
| `prompts-publish.yml` | `sign` | `step-1` | `ubuntu-latest` | `actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd` | AC-checkout (#145) |
| `prompts-publish.yml` | `sign` | `Install cosign` | `ubuntu-latest` | `sigstore/cosign-installer@f713795cb21599bc4e5c4b58cbad1da852d7eeb9` | AC-cosign (#103) |
| `security-scan.yml` | `gitleaks` | `step-1` | `ubuntu-latest` | `actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd` | AC-checkout (#145) |
| `security-scan.yml` | `gitleaks` | `gitleaks` | `ubuntu-latest` | `gitleaks/gitleaks-action@dcedce43c6f43de0b836d1fe38946645c9c638dc` | AC-gitleaks (#105) |
| `security-scan.yml` | `psrule-bicep` | `step-1` | `ubuntu-latest` | `actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd` | AC-checkout (#145) |
| `security-scan.yml` | `trivy-fs` | `step-1` | `ubuntu-latest` | `actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd` | AC-checkout (#145) |
| `simulation-load-test.yml` | `locust-load-test` | `Checkout` | `ubuntu-latest` | `actions/checkout@v4` | AC-checkout (#145) |
| `simulation-load-test.yml` | `locust-load-test` | `Archive Locust HTML report` | `ubuntu-latest` | `actions/upload-artifact@v4` | AC-upload (#143) |
| `simulation-stub-sweep.yml` | `sweep` | `step-1` | `ubuntu-latest` | `actions/checkout@v4` | AC-checkout (#145) |
| `spec-035-gate.yml` | `invariants` | `step-1` | `ubuntu-latest` | `actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd` | AC-checkout (#145) |
| `spec-036-50-agent-load.yml` | `retrieval-50-agent` | `step-1` | `ubuntu-latest` | `actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd` | AC-checkout (#145) |
| `spec-036-50-agent-load.yml` | `retrieval-50-agent` | `Upload load artefacts` | `ubuntu-latest` | `actions/upload-artifact@b7c566a772e6b6bfb58ed0dc250532a479d7789f` | AC-upload (#143) |
| `spec-036-blue-green-e2e.yml` | `blue-green-e2e` | `step-1` | `ubuntu-latest` | `actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd` | AC-checkout (#145) |
| `staging-promotion.yml` | `static-gate` | `step-1` | `ubuntu-latest` | `actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd` | AC-checkout (#145) |
| `staging-promotion.yml` | `runtime-gate` | `step-1` | `ubuntu-latest` | `actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd` | AC-checkout (#145) |
| `staging-promotion.yml` | `smoke-injection` | `step-1` | `ubuntu-latest` | `actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd` | AC-checkout (#145) |
| `staging-promotion.yml` | `promote` | `step-1` | `ubuntu-latest` | `actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd` | AC-checkout (#145) |
| `web-coverage-iteration.yml` | `iterate` | `step-1` | `ubuntu-latest` | `actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd` | AC-checkout (#145) |

**T010 result**: 55/55 current active occurrences captured across 25 workflows with exact baseline refs and runner labels. All upload uses already matching target and all remaining old refs remain independently recorded; no action edit or dispatch occurred.

## E11 — Current approved-source artifact rechecks (T011–T012)

No package was installed, no manifest/lock was edited, and no public npm/PyPI registry was queried. npm metadata and tarballs were requested from `https://packagefeedproxy.microsoft.io/npm/`; its metadata supplied `https://ms-feed-25.pkgs.visualstudio.com/1es-public/_packaging/npm-public/npm/registry/...` tarball paths. Redirects for the npm tarballs ended at the per-artifact `*.vsblob.vsassets.io` hosts listed below; redirect query strings were not retained. Their approval as the proxy's artifact backend is not separately attested here, so B-SOURCE-ENV remains open. Python wheel indexes were queried only at `https://packagefeedproxy.microsoft.io/pypi/simple/`; their file links were returned from `ms-feed-25.pkgs.visualstudio.com`. Downloads used isolated empty scratch destinations, `--no-cache-dir`, and no install.

### T011 — npm metadata and direct-artifact results

Successful fresh proxy catalogues contained 430 ESLint versions and 287 jsdom versions. `eslint@10.12.0` and `jsdom@30.1.2` were absent from those catalogues and their exact version lookups returned E404. Retrieved direct tarballs for the candidates/companions below have matching registry `dist.integrity` where it is SHA-512; where the proxy supplied only `dist.shasum`, only that SHA-1 is publisher/proxy provenance. Locally computed SHA-256 is recorded for identity but is not upgraded into publisher provenance.

| Package/version | Tarball filename | Registry checksum result | Computed SHA-256 | Final redirect host |
| --- | --- | --- | --- | --- |
| `next@16.3.8` | `next-16.3.8.tgz` | SHA-512 SRI matched | `f6f312a6f62b3addcf3dbf10a5d908940bd9d772c59561341d8ac134fd077ff6` | `bsovsblobprodcus457.vsblob.vsassets.io` |
| `next@15.5.21` | `next-15.5.21.tgz` | SHA-1 shasum matched; no SHA-512 SRI | `ffc133c1448abb813f09df98dbdc6b8e58dfcd90a0088193ac67d6a1d506d13b` | `jzpvsblobprodcus470.vsblob.vsassets.io` |
| `@next/env@16.3.8` | `env-16.3.8.tgz` | SHA-512 SRI matched | `e7a57b40302e5834051ce474b23195d78027e5ce3938e43aaf144b538c2534b9` | `2lbvsblobprodcus415.vsblob.vsassets.io` |
| `@next/env@15.5.21` | `env-15.5.21.tgz` | SHA-1 shasum matched; no SHA-512 SRI | `e8e0cb59ab1a828f74fd9876ab845ba5cb04cbcdba1f74c28c6a1b30e60dc75a` | `2k1vsblobprodcus453.vsblob.vsassets.io` |
| `@swc/helpers@0.5.23` | `helpers-0.5.23.tgz` | SHA-1 shasum matched; no SHA-512 SRI | `3de0ff851b7c1d1c7d79655750b18a3b48cf59f56c8fec7bf8a29b250405b945` | `ej8vsblobprodcus489.vsblob.vsassets.io` |
| `@swc/helpers@0.5.15` | `helpers-0.5.15.tgz` | SHA-1 shasum matched; no SHA-512 SRI | `97e22cf245b7f60a14f14305e07211b459321cef2c3349f33df8adcd58396456` | `pivvsblobprodcus434.vsblob.vsassets.io` |
| `@next/swc-linux-x64-gnu@16.3.8` | `swc-linux-x64-gnu-16.3.8.tgz` | SHA-512 SRI matched | `1edacab83f15c56f4059b17adc37155248e3f273a1cbc6a2e1cd3020368a786f` | `mgpvsblobprodcus428.vsblob.vsassets.io` |
| `@next/swc-linux-x64-musl@16.3.8` | `swc-linux-x64-musl-16.3.8.tgz` | SHA-512 SRI matched | `197315b0727ad600ed6672532eb421366de2baa592ffee2aaaa0b709a28ecf7e` | `79pvsblobprodcus44.vsblob.vsassets.io` |
| `@next/swc-linux-x64-gnu@15.5.21` | `swc-linux-x64-gnu-15.5.21.tgz` | SHA-1 shasum matched; no SHA-512 SRI | `7e68c89633c6d42f9feaebd59b8b7ebf9764e578691f97d2e4c5b92d81954ec1` | `4gpvsblobprodcus446.vsblob.vsassets.io` |
| `@next/swc-linux-x64-musl@15.5.21` | `swc-linux-x64-musl-15.5.21.tgz` | SHA-1 shasum matched; no SHA-512 SRI | `ebeb094ea13d170bf85e067fba9cefcfe3ba0d9461ab80c95b5b56173dd207e9` | `v1dvsblobprodcus482.vsblob.vsassets.io` |
| `eslint@10.11.0` | `eslint-10.11.0.tgz` | SHA-512 SRI matched | `2c1c9adad9ba0d7c8b885216a920a46eb4c1d400d04f8baafe2b281aaea945f0` | `k9bvsblobprodcus452.vsblob.vsassets.io` |
| `jsdom@30.1.1` | `jsdom-30.1.1.tgz` | SHA-512 SRI matched | `ce6675111b9fd03e754e98505433c98b05a7ac5a36e2a533165df5481946a749` | `6puvsblobprodcus437.vsblob.vsassets.io` |
| `@playwright/test@1.63.0` | `test-1.63.0.tgz` | SHA-1 shasum matched; no SHA-512 SRI | `fc594f36b7b4aafece614ec6852ad728423215a76edd0a2a1821bb0c49539c4e` | `8wivsblobprodcus487.vsblob.vsassets.io` |
| `playwright@1.63.0` | `playwright-1.63.0.tgz` | SHA-1 shasum matched; no SHA-512 SRI | `195a5ee9bfed7c6e9c03965950e32e5e4dbedaa02e740e5a530eb4b87dae050c` | `q8avsblobprodcus427.vsblob.vsassets.io` |
| `playwright-core@1.63.0` | `playwright-core-1.63.0.tgz` | SHA-1 shasum matched; no SHA-512 SRI | `208593d4e1bcd8f8fe5f869cad1cc332dc7f1d70dc1d58c102dc3ac36e30f26c` | `tqtvsblobprodcus420.vsblob.vsassets.io` |
| `@types/node@26.6.4` | `node-26.6.4.tgz` | SHA-512 SRI matched; `node/package.json` identity/version verified | `bf2dbf11cfccd34681fc4d5e4d150afce77fd6610224757dbe6c92c8e5149700` | `m4wvsblobprodcus459.vsblob.vsassets.io` |
| `@azure/msal-react@5.7.2` | `msal-react-5.7.2.tgz` | SHA-512 SRI matched | `ca7cc13809abb515fe64c29568da4afa79f97f50a33dda2a32d06fb08ad67a66` | `6bavsblobprodcus442.vsblob.vsassets.io` |
| `@azure/msal-browser@5.24.0` | `msal-browser-5.24.0.tgz` | SHA-512 SRI matched | `ee4b1ac1dd31b333616f4f3fd731dd13b8ee8f6de7c6014308866335f16f1609` | `w3xvsblobprodcus414.vsblob.vsassets.io` |
| `@azure/msal-common@16.14.2` | `msal-common-16.14.2.tgz` | SHA-512 SRI matched | `f8fd433f9da534a8d9ffc62cbe36a4c35399503ec53c2e6f33e09c1aef58ab48` | `7kwvsblobprodcus429.vsblob.vsassets.io` |
| `js-yaml@4.3.1` | `js-yaml-4.3.1.tgz` | SHA-1 shasum matched; no SHA-512 SRI | `08d6282b77a3e7242061f6dd5516c019b25c53041ad267bca3b790d79ddd5f34` | `ckfvsblobprodcus45.vsblob.vsassets.io` |
| `sharp@0.35.5` | `sharp-0.35.5.tgz` | SHA-512 SRI matched | `3b6bbbe6b308f5c383938ca4a31926cd5d79c4651ed8c5fda16a97da2014a9ac` | `ej8vsblobprodcus489.vsblob.vsassets.io` |
| `@img/sharp-linux-x64@0.35.5` | `sharp-linux-x64-0.35.5.tgz` | SHA-512 SRI matched | `556787285d3244c07686a355de5b5a4c4d0019a12785bf24764e756a96ea3334` | `85evsblobprodcus416.vsblob.vsassets.io` |
| `@img/sharp-linuxmusl-x64@0.35.5` | `sharp-linuxmusl-x64-0.35.5.tgz` | SHA-512 SRI matched | `577bca1fabb66b2d8d89fc203851280d2bf604130803382d229544f75bab2ea0` | `g4avsblobprodcus42.vsblob.vsassets.io` |
| `@img/sharp-libvips-linux-x64@1.3.4` | `sharp-libvips-linux-x64-1.3.4.tgz` | SHA-512 SRI matched | `e371cb713fc8822c96a0d3fb60a3d092799d0aefab6d7f1fb3b72d8d75f1d109` | `jzpvsblobprodcus470.vsblob.vsassets.io` |
| `@img/sharp-libvips-linuxmusl-x64@1.3.4` | `sharp-libvips-linuxmusl-x64-1.3.4.tgz` | SHA-512 SRI matched | `c6312802c16511458a1cf3d990c3e2b9dba555932caf297025ba0bec34ee5cbe` | `r30vsblobprodcus451.vsblob.vsassets.io` |
| `postcss@8.5.28` | `postcss-8.5.28.tgz` | SHA-1 shasum matched; no SHA-512 SRI | `f63d6d9bce28989cd083add85af717c0264e44323d35c909ae99ac934e9641a6` | `m4wvsblobprodcus459.vsblob.vsassets.io` |

The exact weaker registry SHA-1 values for tarballs without `dist.integrity` are retained here (a local SHA-256 is not publisher provenance):

| Package/version | Proxy `dist.shasum` (SHA-1) |
| --- | --- |
| `next@15.5.21` | `43355e37f9d1ed8cf96018aa57f84ea2ec213f7b` |
| `@next/env@15.5.21` | `782aa4d6b08ddfd12ac7e17ca85b7ee1b61c500b` |
| `@swc/helpers@0.5.23` | `19287d0d86d962b111376039a50c792902c9a86a` |
| `@swc/helpers@0.5.15` | `79efab344c5819ecf83a43f3f9f811fc84b516d7` |
| `@next/swc-linux-x64-gnu@15.5.21` | `8df24c447815a9d7c71c86209607fb2340275837` |
| `@next/swc-linux-x64-musl@15.5.21` | `eec68325de1fa0c708c031754bd0310d145d9424` |
| `@playwright/test@1.63.0` | `808020c46e8b6b91f9d628cd0ebcbb32bdfd8b6c` |
| `playwright@1.63.0` | `99b56f9f69b1b70c44f00bf84b2fe52348ae2511` |
| `playwright-core@1.63.0` | `e57665bc32846c213ac39a1e4d5bc6228e76b376` |
| `js-yaml@4.3.1` | `01216c001d67f48e2cd560d708c7af21090a3848` |
| `postcss@8.5.28` | `da4563a99a06e62d6c1cd1acae363224bcaed6e9` |

For the exact proxy-returned `dist.tarball` URLs, concatenate the following suffix with `https://ms-feed-25.pkgs.visualstudio.com/1es-public/_packaging/npm-public/npm/registry/`. Capture times are file-byte write times in UTC from the fresh isolated artifact directory during `2026-10-09T02:20:29Z`–`02:23:45Z`; the Next 16.3.8 archive was independently re-fetched at `02:31:11Z`. Final hosts correspond to the redirects observed during each byte fetch. No signed redirect query strings are recorded.

| Package/version | Exact tarball URL suffix | Captured UTC | Final host |
| --- | --- | --- | --- |
| `next@16.3.8` | `next/-/next-16.3.8.tgz` | `2026-10-09T02:31:11.5762542Z` | `bsovsblobprodcus457.vsblob.vsassets.io` |
| `next@15.5.21` | `next/-/next-15.5.21.tgz` | `2026-10-09T02:20:52.7611894Z` | `jzpvsblobprodcus470.vsblob.vsassets.io` |
| `@next/env@16.3.8` | `@next/env/-/env-16.3.8.tgz` | `2026-10-09T02:20:59.6829506Z` | `2lbvsblobprodcus415.vsblob.vsassets.io` |
| `@next/env@15.5.21` | `@next/env/-/env-15.5.21.tgz` | `2026-10-09T02:21:04.7462775Z` | `2k1vsblobprodcus453.vsblob.vsassets.io` |
| `@swc/helpers@0.5.23` | `@swc/helpers/-/helpers-0.5.23.tgz` | `2026-10-09T02:21:07.7176392Z` | `ej8vsblobprodcus489.vsblob.vsassets.io` |
| `@swc/helpers@0.5.15` | `@swc/helpers/-/helpers-0.5.15.tgz` | `2026-10-09T02:21:11.9365870Z` | `pivvsblobprodcus434.vsblob.vsassets.io` |
| `@next/swc-linux-x64-gnu@16.3.8` | `@next/swc-linux-x64-gnu/-/swc-linux-x64-gnu-16.3.8.tgz` | `2026-10-09T02:21:26.1291929Z` | `mgpvsblobprodcus428.vsblob.vsassets.io` |
| `@next/swc-linux-x64-musl@16.3.8` | `@next/swc-linux-x64-musl/-/swc-linux-x64-musl-16.3.8.tgz` | `2026-10-09T02:21:44.2409493Z` | `79pvsblobprodcus44.vsblob.vsassets.io` |
| `@next/swc-linux-x64-gnu@15.5.21` | `@next/swc-linux-x64-gnu/-/swc-linux-x64-gnu-15.5.21.tgz` | `2026-10-09T02:22:03.4887520Z` | `4gpvsblobprodcus446.vsblob.vsassets.io` |
| `@next/swc-linux-x64-musl@15.5.21` | `@next/swc-linux-x64-musl/-/swc-linux-x64-musl-15.5.21.tgz` | `2026-10-09T02:22:25.4170388Z` | `v1dvsblobprodcus482.vsblob.vsassets.io` |
| `eslint@10.11.0` | `eslint/-/eslint-10.11.0.tgz` | `2026-10-09T02:22:30.0685119Z` | `k9bvsblobprodcus452.vsblob.vsassets.io` |
| `jsdom@30.1.1` | `jsdom/-/jsdom-30.1.1.tgz` | `2026-10-09T02:22:34.4271862Z` | `6puvsblobprodcus437.vsblob.vsassets.io` |
| `@playwright/test@1.63.0` | `@playwright/test/-/test-1.63.0.tgz` | `2026-10-09T02:22:38.8490323Z` | `8wivsblobprodcus487.vsblob.vsassets.io` |
| `playwright@1.63.0` | `playwright/-/playwright-1.63.0.tgz` | `2026-10-09T02:22:44.6549474Z` | `q8avsblobprodcus427.vsblob.vsassets.io` |
| `playwright-core@1.63.0` | `playwright-core/-/playwright-core-1.63.0.tgz` | `2026-10-09T02:22:50.2927979Z` | `tqtvsblobprodcus420.vsblob.vsassets.io` |
| `@types/node@26.6.4` | `@types/node/-/node-26.6.4.tgz` | `2026-10-09T02:22:56.7185883Z` | `m4wvsblobprodcus459.vsblob.vsassets.io` |
| `@azure/msal-react@5.7.2` | `@azure/msal-react/-/msal-react-5.7.2.tgz` | `2026-10-09T02:23:00.8056031Z` | `6bavsblobprodcus442.vsblob.vsassets.io` |
| `@azure/msal-browser@5.24.0` | `@azure/msal-browser/-/msal-browser-5.24.0.tgz` | `2026-10-09T02:23:05.8807527Z` | `w3xvsblobprodcus414.vsblob.vsassets.io` |
| `@azure/msal-common@16.14.2` | `@azure/msal-common/-/msal-common-16.14.2.tgz` | `2026-10-09T02:23:09.6386607Z` | `7kwvsblobprodcus429.vsblob.vsassets.io` |
| `js-yaml@4.3.1` | `js-yaml/-/js-yaml-4.3.1.tgz` | `2026-10-09T02:23:13.2808179Z` | `ckfvsblobprodcus45.vsblob.vsassets.io` |
| `sharp@0.35.5` | `sharp/-/sharp-0.35.5.tgz` | `2026-10-09T02:23:18.4202761Z` | `ej8vsblobprodcus489.vsblob.vsassets.io` |
| `@img/sharp-linux-x64@0.35.5` | `@img/sharp-linux-x64/-/sharp-linux-x64-0.35.5.tgz` | `2026-10-09T02:23:23.5260556Z` | `85evsblobprodcus416.vsblob.vsassets.io` |
| `@img/sharp-linuxmusl-x64@0.35.5` | `@img/sharp-linuxmusl-x64/-/sharp-linuxmusl-x64-0.35.5.tgz` | `2026-10-09T02:23:28.1517074Z` | `g4avsblobprodcus42.vsblob.vsassets.io` |
| `@img/sharp-libvips-linux-x64@1.3.4` | `@img/sharp-libvips-linux-x64/-/sharp-libvips-linux-x64-1.3.4.tgz` | `2026-10-09T02:23:34.3202973Z` | `jzpvsblobprodcus470.vsblob.vsassets.io` |
| `@img/sharp-libvips-linuxmusl-x64@1.3.4` | `@img/sharp-libvips-linuxmusl-x64/-/sharp-libvips-linuxmusl-x64-1.3.4.tgz` | `2026-10-09T02:23:41.1924300Z` | `r30vsblobprodcus451.vsblob.vsassets.io` |
| `postcss@8.5.28` | `postcss/-/postcss-8.5.28.tgz` | `2026-10-09T02:23:45.6198304Z` | `m4wvsblobprodcus459.vsblob.vsassets.io` |

The exact current `eslint`/`jsdom` catalogues and target endpoint recheck ran at `2026-10-09T02:47:12.6609498Z`–`02:47:26.2669322Z`: 430 and 287 versions respectively, neither target present; exact target lookups failed with E404 (`No match found for version 10.12.0` / `30.1.2`; the earlier E404 responses are retained in command output). Proxy `dist.tarball` URLs were re-queried at `02:44:12.9192098Z`–`02:46:37.8250260Z`; the feed host and path are preserved above.

Metadata recheck also confirmed: Next `16.3.8` requires Node `>=20.9.0`, `@next/env@16.3.8`, `@swc/helpers@0.5.23`, exact PostCSS `8.5.23`, optional `sharp ^0.35.4` and eight platform SWC packages; the checked-in PostCSS `8.5.28` protection remains higher. Next `15.5.21` requires `@next/env@15.5.21`, `@swc/helpers@0.5.15`, PostCSS `8.4.31`, and its own SWC companions; the existing PostCSS floor must not be weakened. Retrieved SWC evidence covers only Linux x64 GNU/musl; devcontainer architecture and other native variants remain open.

For jsdom, target `30.1.2` is absent; `30.1.1` is the highest lower stable same-major candidate found by the successful proxy catalogue, above locked `25.0.1`, but it requires Node `^22.22.2 || ^24.15.0 || >=26.0.0`. Its direct tarball is verified; its transitive graph and the actual Node 24 patch remain unverified. Playwright `1.63.0` package metadata requires Node `>=20`; the three direct archives were retrieved, but Chromium/browser and OS dependency sources were not approved or fetched. No cached browser was used.

For ESLint, target `10.12.0` is absent. `10.11.0` is a retrieved same-major lower candidate but remains ineligible: current `eslint-plugin-react@7.37.5`, `eslint-plugin-import@2.32.0`, and `eslint-plugin-jsx-a11y@6.10.2` peers exclude ESLint 10, despite `eslint-config-next@16.3.8` itself declaring ESLint `>=9.0.0`. Keep #150 held at the verified `9.39.4` baseline. Node types `26.6.4` is retrievable, but no Node-24 surface/runtime compatibility evidence exists.

For MSAL, metadata/archives now establish the direct `@azure/msal-react@5.7.2` → `@azure/msal-browser@5.24.0` → `@azure/msal-common@16.14.2` graph; React `19.2.6` satisfies the React peer. These are source observations only. No install/test ran, no final host policy approval was recorded for the `vsblob.vsassets.io` redirects, and the existing #144 work item remains unchanged/incomplete pending the complete source/consumer gates.

**T011 status: BLOCKED / incomplete.** Direct target/candidate/companion artifacts and some native files were re-fetched, but not every transitive or supported-architecture artifact was closed; npm proxy SHA-1-only records are not stronger publisher provenance; browser payload source is not approved; and the Microsoft feed's `vsblob.vsassets.io` final redirect host is recorded but not independently policy-attested. No source fallback or lock integrity downgrade was used.

### T012 — Python wheel retrieval and integrity

From `2026-10-09T02:25:00.2701324Z` through `2026-10-09T02:28:28.6211286Z`, direct wheel files were downloaded with `pip download --no-cache-dir --no-deps --only-binary=:all:` and an explicit Microsoft proxy index; Python proxy simple pages were then re-fetched from their exact `packagefeedproxy.microsoft.io` host. All 28 downloaded wheels match their current proxy simple-page `#sha256` values. For versions already present in root/agents/API locks, downloaded hashes also match the corresponding lock hashes. Candidate versions absent from current locks are verified against the current proxy page only. `Requires-Python`, wheel tags and package `METADATA` were read from the wheel archives; no wheel was installed or executed.

| Wheel file | `Requires-Python` | SHA-256 (proxy simple hash = actual) |
| --- | --- | --- |
| `aiohttp-3.14.3-cp312-cp312-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl` | `>=3.10` | `f631fe87a6f30df5fbe6d79640b25e4cffb38c31c7fb6f10871517b84b0f8c1a` |
| `aiohttp-3.14.3-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl` | `>=3.10` | `543906c127fb1d929b95076db19b83fa2d46751006ff1e23b093aa5ac4d8db42` |
| `aiohttp-3.14.3-cp312-cp312-win_amd64.whl` | `>=3.10` | `33a2d7c28d33797a2e99923dffa63f83d908a19b6bf26cfe80fa790aa5e1a75a` |
| `cryptography-50.0.1-cp311-abi3-manylinux2014_aarch64.manylinux_2_17_aarch64.whl` | `>=3.9, !=3.9.0, !=3.9.1` | `53e279950892dc102c6b4e52af03ae5ea92fac572a1ddab78ca73a997f62b69f` |
| `cryptography-50.0.1-cp311-abi3-manylinux2014_x86_64.manylinux_2_17_x86_64.whl` | `>=3.9, !=3.9.0, !=3.9.1` | `ff838d62ec1bfce4f9ba7fa16f4a7b554cd8d0c299e6be37502161a660c84eef` |
| `cryptography-50.0.1-cp311-abi3-win_amd64.whl` | `>=3.9, !=3.9.0, !=3.9.1` | `aed8db4f6d71c51efb89530e12d9464e7bf2923d46c3205dc794a2a93f8c0648` |
| `h2-4.4.1-py3-none-any.whl` | `>=3.10` | `0e25f1462b23c9cb82d9eb02e28bc706dac2a68cb457c6a0d74d63c8a2a5d0e6` |
| `hpack-4.2.0-py3-none-any.whl` | `>=3.10` | `858ac0b02280fa582b5080d68db0899c62a80375e0e5413a74970c5e518b6986` |
| `hyperframe-6.1.0-py3-none-any.whl` | `>=3.9` | `b03380493a519fce58ea5af42e4a42317bf9bd425596f7a0835ffce80f1a42e5` |
| `idna-3.15-py3-none-any.whl` | `>=3.8` | `048adeaf8c2d788c40fee287673ccaa74c24ffd8dcf09ffa555a2fbb59f10ac8` |
| `mcp-1.30.0-py3-none-any.whl` | `>=3.10` | `666edb5009503e1047c9d60346a756f94b261f05cc2625f23d41c728ffc484d0` |
| `msgpack-1.2.2-cp312-cp312-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl` | `>=3.10` | `90986cc9aab9d7d1d8f38bcbf65d3f7ac83bdd90c35765db7d691b4829698cba` |
| `msgpack-1.2.2-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl` | `>=3.10` | `77c2e018417dc1d66f235e383877ee885b60ade9d29e494dd581e08af2cb1923` |
| `msgpack-1.2.2-cp312-cp312-win_amd64.whl` | `>=3.10` | `b68614fba0570349833b7dd999ff0aed4e5cc8d9eb6e3a7d4527be33c65e33d3` |
| `pyasn1-0.6.4-py3-none-any.whl` | `>=3.8` | `deda9277cfd454080ec40b207fb6df82206a3a2688735233cdcd8d3d565f088b` |
| `pydantic-2.12.5-py3-none-any.whl` | `>=3.9` | `e561593fccf61e8a20fc46dfc2dfe075b8be7d0188df33f221ad1f0139180f9d` |
| `pydantic_core-2.41.5-cp312-cp312-manylinux_2_17_aarch64.manylinux2014_aarch64.whl` | `>=3.9` | `e96cea19e34778f8d59fe40775a7a574d95816eb150850a85a7a4c8f4b94ac69` |
| `pydantic_core-2.41.5-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl` | `>=3.9` | `eceb81a8d74f9267ef4081e246ffd6d129da5d87e37a77c9bde550cb04870c1c` |
| `pydantic_core-2.41.5-cp312-cp312-win_amd64.whl` | `>=3.9` | `1962293292865bca8e54702b08a4f26da73adc83dd1fcf26fbc875b35d81c815` |
| `pydantic-settings-2.14.2-py3-none-any.whl` | `>=3.10` | `a20c97b37910b6550d5ea50fbcc2d4187defe58cd57070b73863d069419c9440` |
| `PyJWT-2.15.0-py3-none-any.whl` | `>=3.9` | `7a3742debf6b879e912dbb9819ceec1594be812452b78c5f2e2dfc56564954f8` |
| `python_dotenv-1.2.2-py3-none-any.whl` | `>=3.10` | `1d8214789a24de455a8b8bd8ae6fe3c6b69a5e3d64aa8a8e5d68e694bbcb285a` |
| `python_engineio-4.14.0-py3-none-any.whl` | `>=3.8` | `9f0fe275fb7d67bfc1a632421adf22949fd4843bd9c458c004b0a89cede302a2` |
| `python_multipart-0.0.32-py3-none-any.whl` | `>=3.10` | `ff6d3f776f16878c894e52e107296ffc890e913c611b1a4ec6c44e2821fe2e23` |
| `python_socketio-5.17.0-py3-none-any.whl` | `>=3.8` | `b5826fd2f8aa02e11347816349b74ac6b53e8a4f4e4b1cf1388e1aff19b7f3f4` |
| `setuptools-83.0.0-py3-none-any.whl` | `>=3.10` | `29b23c360f22f414dc7336bb39178cc7bcbf6021ed2733cde173f09dba19abb3` |
| `starlette-1.7.0-py3-none-any.whl` | `>=3.10` | `67f8e99895493dd2911a03f11314af6ceebeae4e704bb9f43dfc6a9db151c93e` |
| `typing_inspection-0.4.2-py3-none-any.whl` | `>=3.9` | `4ed1cacbdc298c220f1bd249ed5287caa16f34d44ef4e9c3d0cbad5b521545e7` |

Scope mapping remains separate: root PR work items `PR-cryptography`, `PR-idna`, `PR-msgpack`, `PR-pyjwt`, `PR-engineio`, `PR-socketio` use `uv.lock` and root extras/markers; agents work items `PA-h2`, `PA-aiohttp`, `PA-setuptools`, `PA-pyasn1`, `PA-mcp`, `PA-socketio`, `PA-engineio`, `PA-idna`, `PA-starlette`, `PA-pyjwt`, `PA-settings`, `PA-multipart` use `apps\agents\uv.lock` independently. The same `idna==3.15` wheel is source evidence for both PR #111 and #112, not a merged lock scope. Root and agents keep their own already-newer resolutions, including root `h2 4.4.1`/`hpack 4.2.0`, root `setuptools 84.0.0`, root settings `2.15.0`, and agents settings `2.14.1` until an authorized candidate edit. Root `cryptography>=50.0.0,<51`, both PyJWT `>=2.14.0,<3` floors, root `redis-entraid 1.2.1`, root `mem0ai 2.0.20`, and agents `mem0ai 2.0.2` remain unchanged.

Compatibility metadata confirms `h2 4.4.1` requires `hpack>=4.2,<5` and `hyperframe>=6.1,<7`; downloaded `hpack 4.2.0` and current `hyperframe 6.1.0` satisfy those declared ranges. `pydantic-settings 2.14.2` base dependencies include `pydantic>=2.7.0`, `python-dotenv>=0.21.0`, and `typing-inspection>=0.4.0`; current agents resolutions `pydantic 2.12.5`, `python-dotenv 1.2.2`, `typing-inspection 0.4.2`, and `pydantic-core 2.41.5` meet those declared floors. Optional pydantic-settings extras are not selected by the standalone agents recipe. These are metadata/wheel observations, not a resolver or `pip check` result.

### Lock marker/extra context for those artifact rows

Every recorded Python artifact came from the proxy index `https://packagefeedproxy.microsoft.io/pypi/simple/`; the root/agents/API lock entries inspected for retained files also use that proxy. The selected top-level package records have no `resolution-markers` field, so Python 3.12 Linux/Windows/ARM64 applicability is determined by wheel tags and the requested runtime, not an invented lock marker. Lock metadata with material marked/extra relationships was checked separately:

| Lock scope | Recorded marker/extra relationship relevant to these work items |
| --- | --- |
| Root `uv.lock` | `cryptography`'s `cffi` dependency is marked `platform_python_implementation != 'PyPy'`; `aiohttp`/`starlette` use `typing-extensions` under `python_full_version < '3.13'`; MCP/Starlette have `anyio` marker alternatives for `<3.15` / `>=3.15`; MCP `pywin32` is `sys_platform == 'win32'`; `python-socketio` has optional `client` extra (`requests`, `websocket-client`) |
| Agents `apps\agents\uv.lock` | `cryptography` has the same non-PyPy `cffi` marker; `aiohttp` and Starlette include the Python `<3.13` `typing-extensions` marker; `mcp` includes the `pyjwt` `crypto` extra reference and a Windows-only `pywin32` marker; `pyjwt`'s `crypto` extra includes cryptography; `python-socketio` has optional `client` extra |
| API `apps\api\uv.lock` (protected) | Current retained comparison entries use the same proxy; its `aiohttp`, `cryptography`, `pydantic-settings`, PyJWT, socketio and Starlette marker/extra branches remain protected and were not changed |

The actual root/agents install recipes and selected extras remain distinct: root Linux development uses `dev` plus `load`, Windows CI uses `windows-ci`, and standalone agents uses its own project/lock without assuming root extras. Lock inspection only documents current branches; it does not assert an installed marker map for any consumer.

**T012 result: complete for the requested direct artifact retrieval/integrity record.** All listed root/agents candidate and retained direct wheel files were freshly retrieved via the sole approved PyPI proxy, with native CPython 3.12 Linux x64, Linux ARM64 and Windows x64 variants for cryptography, msgpack, aiohttp and pydantic-core; all proxy simple hashes matched. This does **not** establish a full dependency closure, two clean installs, runtime compatibility, or a passing test. `B-CONSUMER-BASE` and B-VALIDATION remain open from T006/T007.

## E12 — Action provenance/assets and explicit work-item holds (T013–T018)

### T013 — Official Action source recheck

Read-only GitHub API recheck ran `2026-10-09T02:33:43.4090631Z`–`2026-10-09T02:34:17.6918801Z` against only the five official upstream repositories and exact proposed full SHAs. Each commit resolved to its expected full SHA; its recursive tree was not truncated and its `action.yml` blob SHA was read at that commit:

| Official repository | Proposed SHA | Tree SHA | Tree entries | `action.yml` blob SHA |
| --- | --- | --- | ---: | --- |
| `actions/checkout` | `3d3c42e5aac5ba805825da76410c181273ba90b1` | `150e70ecad5ebf06a559a01ea3a56d9a3236d2b1` | 113 | `5b0524f730db83f9513c18ab31a6c086c7239076` |
| `actions/upload-artifact` | `b7c566a772e6b6bfb58ed0dc250532a479d7789f` | `bb934e399202b45ca0a0ebc508adefb58bb2ae3b` | 235 | `28f04cc696830ad0609506e0888d8b3b83d5d616` |
| `gitleaks/gitleaks-action` | `ff98106e4c7b2bc287b24eaf42907196329070c7` | `50087d01bbbe89f68a29e3e53220f419c44eb3ee` | 21 | `6ad15a7e076d4a6c34980a00985c1dd9e9bba5fc` |
| `sigstore/cosign-installer` | `398d4b0eeef1380460a10c8013a76f728fb906ac` | `c13729074d183d43da2e2165e5c8800f5373eba1` | 8 | `e3f111772a13d7f261725bbcc44f3a9f58e4f6fa` |
| `peter-evans/create-or-update-comment` | `e8674b075228eee787fea43ef493e45ece1004c9` | `a6727213ab218c2973cc12c8d2b35bb7f5c72911` | 31 | `076a27b7df5121b7c036e865acabbec478dfef0a` |

Official ref/compare rechecks: checkout v7.0.1 resolves to the proposed SHA and v5.0.1 to current full-SHA baseline `93cb6efe18208431cddfb8368fd83d5badbf9bfd`; compare remains `diverged` (34 ahead / 1 behind), so do not claim ancestry and use only the official stable release ordering. Upload v6 resolves to the proposed SHA and its v4.6.2 baseline compare remains `ahead` (43/0). Comment v5/v4 refs resolve to `e867...`/`71345...`; compare remains `ahead` (112/0). No hash lexical ordering or timestamps were used.

For a fresh source-blob check, the official codeload archive for each exact SHA was retrieved and every file was compared against the corresponding Git `blob <length>\0<bytes>` SHA-1 in its complete, non-truncated official recursive tree. Verification ran `2026-10-09T02:41:32.0493586Z`–`2026-10-09T02:42:00.0634984Z`; each row had zero missing blobs and zero mismatches:

| Repository | Full SHA | codeload archive SHA-256 | Git blobs verified |
| --- | --- | --- | ---: |
| `actions/checkout` | `3d3c42e5aac5ba805825da76410c181273ba90b1` | `b59292069298c7be5ffd9c636431a229faff70ece00e0c24fd31baeb7b309fa3` | 101/101 |
| `actions/upload-artifact` | `b7c566a772e6b6bfb58ed0dc250532a479d7789f` | `ac4d02cada05aaf668c77eb6770b6d9cd037277da84bf0ad4b2846b5124a47b0` | 208/208 |
| `gitleaks/gitleaks-action` | `ff98106e4c7b2bc287b24eaf42907196329070c7` | `3f88235e0914861be223a8584e376ab9c686f41bd77655852c4c12cbc71f73fa` | 17/17 |
| `sigstore/cosign-installer` | `398d4b0eeef1380460a10c8013a76f728fb906ac` | `5fd270b570f7ac92a4065186c997d3ac0b7351c7c36a7defd85cd109bd93dd3f` | 6/6 |
| `peter-evans/create-or-update-comment` | `e8674b075228eee787fea43ef493e45ece1004c9` | `4a652e05b844b8be883938916496d26bc5e22528bc1c0f87ad7198cbab22eed7` | 27/27 |

The gitleaks baseline `dcedce43c6f43de0b836d1fe38946645c9c638dc` and cosign-installer baseline `f713795cb21599bc4e5c4b58cbad1da852d7eeb9` still return official GitHub API 422 “No commit found for SHA”. This keeps B-ACTION-BASE open for #105/#103. Actual hosted and sovereign runner versions/minimums and checkout fork/credential behavior were not exercised; T002 records those runner-version gaps. Thus T013 remains **blocked/incomplete** despite revalidated proposed source identities.

### T017 — Gitleaks target asset; baseline hold retained

At `2026-10-09T02:35:13.8888978Z`–`2026-10-09T02:35:32.1228181Z`, fetched the official v8.24.3 checksum file and `gitleaks_8.24.3_linux_x64.tar.gz` through GitHub release URLs. Both followed to `release-assets.githubusercontent.com`; no signed query string was retained. The checksum file SHA-256 is `eefa9ab1ee69571248a6fa070a2a7de0837dd9eb72745d131f8766206aac8ac2`; the downloaded archive SHA-256 is `9991e0b2903da4c8f6122b5c3186448b927a5da4deef1fe45271c3793f4ee29c`, matching the exact `gitleaks_8.24.3_linux_x64.tar.gz` checksum line. The binary was not executed.

The current baseline still cannot be resolved from the official upstream repository (GitHub commit API returned 422 for the recorded SHA). Therefore monotonicity/no-downgrade cannot be proved; `security-scan.yml` remains unchanged and AC-gitleaks remains **blocked/incomplete**. Owner/next action: repository/security maintainer to provide authoritative baseline provenance or an explicitly approved policy resolution; then recheck the exact action/asset and runner. **T017 hold-record task completed; B-ACTION-BASE not cleared.**

### T018 — Cosign required assets/signature; baseline hold retained

At the E12 observation window, retrieved the official pinned bootstrap and requested release files. Bootstrap `v2.5.2` `cosign-linux-amd64` was 132,561,156 bytes and SHA-256 `bcfeae05557a9f313ee4392d2f335d0ff69ebbfd232019e3736fb04999fe1734`, matching the specified value. The requested `v2.4.1` Linux amd64 binary SHA-256 is `8b24b946dd5809c6bd93de08033bcf6bc0ed7d336b7785787c080f574b89249b`; its `.sig` SHA-256 is `2cd598f53ffff67995a6354efdaa07ce4c88bd2da03f742ab2e257e3ecf3a186`; `release/release-cosign.pub` SHA-256 is `f4cea466e5e887a45da5031757fa1d32655d83420639dc1758749b744179f126`, matching the recorded key hash. Release assets resolved to `release-assets.githubusercontent.com`; the key came from `raw.githubusercontent.com`. No redirect query string was retained.

The detached signature decoded as a 71-byte ECDSA signature. Verification with the downloaded official P-256 release key over the exact v2.4.1 binary using ECDSA/SHA-256 returned `VERIFIED` (the existing local `cryptography 50.0.1` verifier; no package install or signing action was run). The asset/signature sub-gate is evidenced; no release was published or signed.

The prior active full-SHA baseline remains unresolvable at GitHub API (422), so AC-cosign still cannot pass its no-downgrade gate; `.github\workflows\prompts-publish.yml` remains unchanged. Owner/next action: repository/security maintainer to supply authoritative baseline provenance or an explicit policy resolution; retain the pin until then. **T018 hold-record task completed; B-ACTION-BASE remains open.** Checklist files were not edited; T050 must assess CHK027/CHK028 against this evidence.

### T014–T016 — Library holds rechecked, no version-file changes

| Task / PR | New or confirmed evidence | Hold and next action |
| --- | --- | --- |
| T014 / #150 ESLint | Proxy catalogue and exact lookup both exclude target `10.12.0`; direct `10.11.0` artifact has verified SHA-512; current Next lint plugin peers remain limited to ESLint 9 (`react ^9.7`, `import ^9`, `jsx-a11y ^9`) while config-next 16.3.8 depends on those families | B-ESLINT remains open; retain baseline `9.39.4`; frontend maintainer to wait for an eligible compatible plugin graph or request a separately approved bounded scope change. No major-9 fallback or rule weakening |
| T015 / #146 Node types | `@types/node@26.6.4` direct archive identity/version and SHA-512 were verified from the Microsoft proxy | B-TYPES remains open; retain `22.13.10`; frontend maintainer to demonstrate Node-24 API-surface compatibility plus type/build/test evidence. Do not migrate runtime or invent a major-24 fallback |
| T016 / #144 MSAL | Direct React `5.7.2`, browser `5.24.0`, and common `16.14.2` archives have verified SHA-512; metadata confirms React requires browser `^5.24.0`, browser requires common `16.14.2`, and the current React `19.2.6` meets its peer | Keep baseline unchanged and B-MSAL open pending approved final-host/source boundary and supported clean install/auth regression evidence; owner dependency/feed maintainer. No public npm or React downgrade |

**MSAL sub-hold update**: the specifically missing `@azure/msal-common@16.14.2` bytes are now retrievable from the approved proxy tarball URL; the exact archive identity and proxy SHA-512 match, and the React/browser/common metadata edges were observed. Preserve the original failed/unknown planning observation in E2. This resolves the earlier MSAL-common artifact-access uncertainty, but does not certify overall B-MSAL: complete source-host boundary, other npm artifact closure, clean installs and auth regression evidence remain unmet under T011/T036/T046. The NW-msal-react baseline remains unchanged; it is not in T020's edit allowlist.

T014–T018 are **completed as explicit hold/verification-record tasks only**; #150, #146, #105, and #103 remain blocked, and #144's common-artifact access sub-hold is cleared while its work item remains incomplete for the broader gates above. No candidate was selected, no dependency declaration/lock/action pin changed, and no policy hold was silently waived.

## E13 — T019 provisional ledger and T020 edit allowlist gate

### T019 — Provisional inventory reconciliation

The per-PR and per-work-item ledgers are recorded in `research.md` “Phase 8 provisional PR/work-item decision ledger”; the inventory check also confirms 33 PRs map to 31 distinct work items, with the three NW-next source directions preserved. Count units are `12/1/15/5` over 33 PRs and `12/1/13/5` over 31 work items. No direction is final; the original planning matrix and E1 snapshot are retained. Provisional evidence gaps and current hold states are explicit. T019 **complete as provisional inventory only**; it does not itself authorize an edit or close any blocker.

### T020 — Pre-edit allowlist result

Evaluated only the candidate package/Action edits in T021–T023, using T003–T018 status and the T019 inventory. T003–T005 configuration tasks are complete, but `B-SOURCE-ENV` remains open because registry configuration alone does not prove every artifact path/host and every clean consumer boundary. T006 (`B-CONSUMER-BASE`) and T007 frozen-baseline quality checks are **blocked**: no matching supported GitHub runner/container environment was available, and Docker's Linux daemon was unavailable. T011 is **blocked/incomplete** for full npm native/transitive/browser coverage and approved source/integrity closure; T013 is **blocked/incomplete** for runner-minimum/runtime/behavior evidence and #105/#103 baseline provenance. T012 contains direct proxy wheel evidence only, not a clean install. T014–T018 hold records remain, with only the #144 missing-common-artifact sub-hold and #103 cosign asset/signature sub-gate now evidenced as described in E12.

| Work item | Scope-specific pre-edit gate result | T020 disposition |
| --- | --- | --- |
| `NW-next` | B-SOURCE-ENV remains open; T011 has only selected native files and not the complete supported artifact/integrity closure; T007 baseline checks unavailable | exclude; no version edit authorized |
| `NW-eslint` | B-ESLINT peer conflict and absent `10.12.0` | hold; exclude |
| `NW-jsdom` | T011 direct fallback archive only; Node 24 patch, full transitive graph and baseline test evidence unavailable | exclude |
| `NW-playwright` | T011 trio direct archives only; browser/OS payload source not approved; T007 unavailable | exclude |
| `NW-node-types` | B-TYPES; Node 24 type-surface/runtime compatibility evidence absent | hold; exclude |
| `NW-msal-react` | Common/browser/react direct artifact sub-hold cleared in E12; T011 full source/environment gate and T007 auth/install validation still incomplete | exclude; no version edit authorized |
| `NW-js-yaml` | Target archive uses SHA-1-only proxy provenance; direct/regression tests and T007 unavailable | exclude |
| `NU-next` | Target/companion records incomplete for all required source/integrity/platform conditions; T007 unavailable | exclude |
| `PR-cryptography` | R direction is newer `50.0.1`; direct wheels only, no clean root installs or final security/quality evidence | no edit; retain direction provisional |
| `PA-h2` | Candidate/hpack direct wheels and dependency metadata verified; T006 independent consumer baseline and T007 environment checks unavailable | exclude |
| `PR-idna` | Candidate wheel verified; T007 root Linux/Windows baseline checks blocked and B-VALIDATION open | exclude |
| `PA-aiohttp` | R direction already at `3.14.3`; wheels verified, but no standalone agents clean install or tests | no edit; retain direction provisional |
| `PR-msgpack` | R direction already at `1.2.2`; platform files verified, but no root installation or quality/security pass | no edit; retain direction provisional |
| `PR-pyjwt` | R direction already at `2.15.0`; preserve `>=2.14.0,<3`; installation/security/quality gates unavailable | no edit; retain direction provisional |
| `PR-engineio` | R direction already at `4.14.0`; direct wheel only; installation/quality gates unavailable | no edit; retain direction provisional |
| `PR-socketio` | R direction already at `5.17.0`; direct wheel only; installation/quality gates unavailable | no edit; retain direction provisional |
| `PA-setuptools` | Candidate wheel verified; agents lock install and unchanged-baseline quality gates unavailable | exclude |
| `PA-pyasn1` | R direction already at `0.6.4`; direct wheel only; standalone agents installation/tests unavailable | no edit; retain direction provisional |
| `PA-mcp` | R direction already at `1.30.0`; direct wheel only; standalone agents installation/tests unavailable | no edit; retain direction provisional |
| `PA-socketio` | R direction already at `5.17.0`; direct wheel only; standalone agents installation/tests unavailable | no edit; retain direction provisional |
| `PA-engineio` | R direction already at `4.14.0`; direct wheel only; standalone agents installation/tests unavailable | no edit; retain direction provisional |
| `PA-idna` | Candidate wheel verified; agents lock install, consumer baseline and T007 gates unavailable | exclude |
| `PA-starlette` | R direction already at `1.7.0`; direct wheel only; standalone agents tests unavailable | no edit; retain direction provisional |
| `PA-pyjwt` | R direction already at `2.15.0`; preserve `PyJWT[crypto]>=2.14.0,<3`; installation/security checks unavailable | no edit; retain direction provisional |
| `PA-settings` | Candidate wheel plus direct dependency floors verified; complete resolution/install and agents validation unavailable | exclude |
| `PA-multipart` | R direction already at `0.0.32`; direct wheel only; agents installation/tests unavailable | no edit; retain direction provisional |
| `AC-checkout` | Proposed official source/tree/blob is reverified; Ubuntu, Windows and sovereign runner version/minimum, fork/credential behavior and baseline gates unavailable | exclude |
| `AC-upload` | Proposed official source/tree/blob is reverified; actual runner, artifact behavior and baseline quality gates unavailable | exclude |
| `AC-gitleaks` | B-ACTION-BASE: current baseline SHA unresolved, so ordering/no-downgrade unproved | hold; exclude |
| `AC-cosign` | B-ACTION-BASE: current baseline SHA unresolved; asset/signature sub-gate alone cannot establish ordering | hold; exclude |
| `AC-comment` | Proposed source/order is verified; runner behavior and baseline quality evidence unavailable; live comment explicitly unauthorized | exclude |

**T020 result: complete gate evaluation; execution allowlist is empty (`∅`).** No dependency manifest, lockfile, or Action pin is authorized for modification in this phase. No version file was edited. The empty allowlist does not remove any hold and is not a final candidate/outcome claim. T021, T022, and T023 are **not ready**: T021 remains blocked on npm source/artifact/baseline gates; T022 on T007 and root-install/security evidence; T023 on T007 and the independent agents baseline/install evidence. Re-evaluate T020 only after its named prerequisites have new, scope-specific evidence.

## E14 — Phase-8 continuation observations (T002/T006/T007/T011/T013; T020 disposition)

This addendum records the user's approved resume, preserving E6–E13 as historical observations. It supersedes only the earlier local Docker/devcontainer availability statement and updates the dependent gate dispositions. No dependency manifest, lockfile, Action pin, spec, plan, checklist, review, or `.analyze-done` file was edited. T002, T006, T007, T011, and T013 remain incomplete; T020 remains checked from its prior completed allowlist evaluation and is not counted as a second task completion.

### T002 — Linux/ARM64 devcontainer build attempt

| Probe | Result |
| --- | --- |
| Ephemeral CLI | `npm exec --yes --package=@devcontainers/cli --registry=https://packagefeedproxy.microsoft.io/npm/ -- devcontainer --version` returned `@devcontainers/cli 0.89.0`, host Node.js `v24.16.0`, `win32 10.0.26300 arm64`. No manifest/global install was used. |
| Docker engine | Docker client `29.8.2 windows/arm64`; server `29.8.2 linux/arm64` (`docker info` reported `linux/aarch64`, kernel `6.18.33.1-microsoft-standard-WSL2`). The configured build had no `--platform` override, so this attempt targeted the engine's Linux/ARM64 platform. |
| Python base | Build trace resolved `mcr.microsoft.com/devcontainers/python:1-3.12-bookworm@sha256:7876580dc67fd460fd962f004cbeb480027e9bbc0657096f1087db11f9eaff39`; image inspection reported Linux/ARM64. Both the image probe and the build step observed Python `3.12.11`. |
| Node base | Build trace resolved `docker.io/library/node:24-bookworm-slim@sha256:d6aa754f16b3197301076f047b5def2f02ea1dbbc2ca920407d46d7ec7f87b20`. A separate no-network probe of the locally cached ARM64 `node:24-bookworm-slim` tag returned Node `v24.21.0` and npm `11.19.0` (local image ID/RepoDigest `sha256:0e0ff40c39bc087845bfb27465a0df4ea419520094bc35842ff83dd8cbe6f9b6`). Because the devcontainer image did not finish building and the tag is mutable, this local base-tag probe is not represented as a runtime probe of a successfully built devcontainer. |
| Build tools/source | The Dockerfile's uv installation completed as `uv-0.11.21`, retrieving `uv-0.11.21-py3-none-manylinux_2_28_aarch64.whl` through `packagefeedproxy.microsoft.io/pypi/simple` (Microsoft artifact host). Its pinned `pnpm@10.6.3` npm-install step completed; the later `pnpm --version` post-create print was not reached. `.devcontainer/devcontainer.json` resolved `NPM_CONFIG_REGISTRY=https://packagefeedproxy.microsoft.io/npm/`; the Dockerfile sets the approved Python proxy and clears secondary indexes. |

`devcontainer up --workspace-folder C:\code\ama` ran from `2026-10-09T03:03:35.879Z` and failed at `2026-10-09T03:05:19.607Z` (BuildKit record `owx5yg39oondph5nnnpzdzdxj`, exit 1). It stopped at Dockerfile step `#35 [development 20/23]`, while running the configured Python dependency helper in `--mode dependencies`, before the image completed or any container/post-create command ran. uv reported the unchanged recipe's resolution is unsatisfiable: `redis-entraid==1.2.1` requires `pyjwt>=2.13.0,<2.14.dev0`, while the collected requirements also require `PyJWT[crypto]>=2.14.0,<3`. No dependency was installed from that failed resolution and no installed map was collected. Do not lower the PyJWT security floor or remove the redis-entraid exception to force a build.

The later `pnpm install --frozen-lockfile`, `playwright install chromium`, `playwright install-deps chromium`, and post-create commands were not reached; no browser-CDN, apt, or Playwright OS/browser retrieval was performed by this attempt. A filtered Docker check found no created project devcontainer. The actual local build target is established as Linux/ARM64, but a successfully built/running devcontainer and its complete runtime/tool set are **not** established. The hosted Ubuntu/Windows x64, Alpine, standalone agents, and other Docker recipe rows remain unobserved; no Linux/amd64 or Windows/x64 result is inferred from this ARM64 engine.

**T002 status: BLOCKED/incomplete.** The local architecture, Python base version, uv install, and build failure are now observed. The task requires the complete supported-environment matrix; exact hosted runner/image/runtime versions, Windows x64, Alpine/musl and other per-recipe details remain unavailable, and this devcontainer did not finish building. Leave T002 unchecked.

### T006 — Consumer-baseline rows and installed-map status

No `uv.lock` or declaration was used as installed evidence. The build attempt above produced no project installed map; the configured post-create Python editables and frozen pnpm install were not reached. The following per-consumer rows remain separate; `NOT COLLECTED` is not an empty map or a pass.

| Environment ID | Continuation result | Installed map | Current disposition |
| --- | --- | --- | --- |
| `CI-PIP-SOURCE-POLICY` | Not run | NOT COLLECTED | Blocked; matching Ubuntu/Python 3.12 hosted runner unavailable. |
| `CI-PIP-QUALITY` | Not run | NOT COLLECTED | Blocked; independent Ubuntu pip graph and matching runner unavailable. |
| `CI-PIP-ISOLATION` | Not run | NOT COLLECTED | Blocked; matching Ubuntu/Python 3.12 recipe unavailable. |
| `CI-PIP-STORY` | Not run | NOT COLLECTED | Blocked; neither its independent pip graph nor pnpm workspace map was obtained on the matching runner. |
| `CI-PIP-EVIDENCE-PACK` | Not run | NOT COLLECTED | Blocked; matching Ubuntu/Python 3.12 recipe unavailable. |
| `CI-UV-WINDOWS` | Not run | NOT COLLECTED | Blocked; no Windows x64 `windows-latest` runner. Windows ARM64/Python 3.14 is not a substitute. |
| `CI-UV-SPECIFY-CLI` | Not run | NOT COLLECTED | Not applicable to these 31 work items; its separate protected lock remains unchanged. |
| `EVAL-PR-PIP` | Not run | NOT COLLECTED | Blocked; matching Ubuntu/Python 3.12 recipe unavailable. |
| `SPEC-035-PIP` | Not run | NOT COLLECTED | Blocked; matching Ubuntu/Python 3.12 recipe unavailable. |
| `SPEC-036-50-PIP` | Not run | NOT COLLECTED | Blocked; matching Ubuntu/Python 3.12 recipe unavailable. |
| `SPEC-036-BLUEGREEN-PIP` | Not run | NOT COLLECTED | Blocked; matching Ubuntu/Python 3.12 recipe unavailable. |
| `CD-DEPLOY-PIP` | Not run | NOT COLLECTED | Blocked/not-run; deployment or workflow dispatch is not authorized. |
| `SCRIPT-API-PIP` | Not run | NOT COLLECTED | Blocked for the supported container target; only a Linux/ARM64 engine was available, and no x64 result is inferred. |
| `SCRIPT-AGENTS-PIP` | Not run | NOT COLLECTED | Blocked for the supported container target; only a Linux/ARM64 engine was available, and no x64 result is inferred. |
| `DOCKER-INGESTION-PIP` | Not run | NOT COLLECTED | Blocked for the supported container target; only a Linux/ARM64 engine was available, and no x64 result is inferred. |
| `DOCKER-INGEST-RUNNER-PIP` | Not run | NOT COLLECTED | Blocked; Python 3.13/uv 0.5.14 remains a separate recipe and was not substituted with the Python 3.12 devcontainer attempt. |
| `DOCKER-EVAL-RUNNER-PIP` | Not run | NOT COLLECTED | Blocked for the supported container target; only a Linux/ARM64 engine was available, and no x64 result is inferred. |
| `DEVCONTAINER-HELPER-PIP` | Build-time `--mode dependencies` attempted and failed resolution before installation; post-create `--mode editables` not reached | NOT COLLECTED | Blocked; conflict and exact ARM64 base/tool evidence are recorded above; no clean pair or installed map. |
| `DEV-PNPM` | Post-create frozen install not reached | NOT COLLECTED | Blocked by the devcontainer build failure; no workspace install map. |

Read-only GitHub Actions inspection found baseline-commit run `37731039293` (`ci.yml`, head `62d249dc1205644fed934ea167df56695e92b3d2`, conclusion `failure`). The Actions API returned zero jobs and the run-log endpoint returned 404, so it provides no usable job, installed-map, runtime, or test evidence. No workflow was dispatched. `B-CONSUMER-BASE` remains open and T006 remains **BLOCKED**.

### T007 — Frozen-baseline quality checks

| Baseline check group | Status | Result |
| --- | --- | --- |
| Python Linux 3.12 quality/policy/equivalence/unit/integration/simulation/benchmark/coverage/taxonomy | blocked / not-run | No matching Ubuntu x64/Python 3.12 baseline run; no commands executed. |
| Python Linux isolation selector and minimum collection count | blocked / not-run | No matching runner; no collection count claimed. |
| Python Windows x64 quality/eval-runner checks | blocked / not-run | No Windows x64 runner; ARM64/Python 3.14 excluded. |
| Web Node 24 Ubuntu lint/type/unit/a11y/build checks | blocked / not-run | No matching Ubuntu x64 runner. The local cached Node base probe is not CI test evidence. |
| Playwright/browser and story acceptance | blocked / not-run | The devcontainer failed before browser install; browser/OS source gate remains open. |
| Workflow contract tests and spec-035/eval-PR gates | blocked / not-run | No matching baseline runner or accessible hosted job logs; no dispatch. |
| CodeQL, gitleaks, PSRule, Trivy and finding comparison | blocked / not-run | No matching scan run or baseline/candidate comparison. |

The devcontainer resolver failure is an install/build failure relevant to T002/T006, not a passing or failing T007 quality test. No quickstart §4 test command ran. **T007 remains BLOCKED**; no baseline check is represented as passed or waived.

### T011/T013 — Outstanding-completeness recheck

No T011 candidate npm archive or Action source was re-fetched in this continuation. The devcontainer build separately installed the pinned uv tool wheel through the approved Python proxy and ran its pinned pnpm tool-install step through the configured npm proxy; neither tool install is counted among the candidate-artifact totals. Reuse the historical E11/E12 records: 26 npm archive downloads (some with only proxy SHA-1 provenance), 28 Python wheels checked against approved-proxy SHA-256 values, and five official GitHub Action source archives/tree-blob sets verified. These remain selected retrieval observations, not complete environment closure.

**T011 remains BLOCKED/incomplete.** Required npm native/transitive closure and supported-platform coverage remain incomplete; some npm records remain SHA-1-only; full MSAL source/final-host approval and the complete companion graph remain open; Playwright browser/OS artifacts have not been retrieved from an approved source; and no clean consumer install or relevant quality test was completed. The devcontainer build stopped before the frozen pnpm/browser steps and adds no npm closure evidence. The uv wheel used for the devcontainer toolchain is not evidence of the 28 candidate/retained Python wheel set or a consumer install.

**T013 remains BLOCKED/incomplete.** The five proposed official source/tree/blob verifications remain historical evidence; the gitleaks asset checksum and cosign asset/signature sub-gate remain evidenced. Actual hosted/sovereign runner versions and minimums, Action runtime compatibility, checkout fork/credential behavior, and any functional runner execution remain unverified. Existing #105/#103 baseline SHAs remain unresolved upstream, so `B-ACTION-BASE` remains open. No Action was executed and no workflow was dispatched.

### T020 — Existing empty-allowlist disposition reaffirmed

This is a scope-bounded disposition check against the new T002/T006/T007 observations, not a second inventory or a duplicate task completion. `B-SOURCE-ENV` remains open; `B-CONSUMER-BASE` remains open with no installed maps and the devcontainer resolution failure; `B-VALIDATION` remains open; T011/T013 remain incomplete; and the existing #150, #146, #144, #105, and #103 holds are preserved. The #144 common-artifact sub-hold and #103 asset/signature sub-gate remain sub-gate evidence only and do not clear their broader holds.

**T020 allowlist remains empty (`∅`). T021, T022, and T023 are not eligible.** No dependency declaration, lockfile, or Action pin was changed. T020 remains checked only for its original complete gate evaluation; T002/T006/T007/T011/T013 remain unchecked until their acceptance conditions have evidence-backed completion.

## E15 — Phase-8 successful devcontainer, installed maps, baseline checks, and T020 refresh

Observed 2026-10-09. This addendum preserves E0–E14 as historical evidence and supersedes only the failed-build/devcontainer rows and `not-run` local-check statements in E14. The successful local ARM64 build and checks below do not stand in for hosted Linux/AMD64, Alpine/musl, Windows x64, sovereign-runner, or remote workflow evidence.

### T002 — Successful Linux/ARM64 devcontainer and authorized installer fix

| Probe | Successful observation |
| --- | --- |
| Build | `devcontainer up` completed successfully with devcontainer CLI `0.89.0`. The source and post-create steps ran for `/workspace`; container user is `vscode`. |
| Host/engine | CLI host: Node `v24.16.0`, Windows ARM64. Docker client: `29.8.2 windows/arm64`; Docker server/build target: `29.8.2 linux/arm64`, reported as `aarch64`. No `--platform` override was used. |
| Pinned Python base | `mcr.microsoft.com/devcontainers/python:1-3.12-bookworm@sha256:7876580dc67fd460fd962f004cbeb480027e9bbc0657096f1087db11f9eaff39`; built-container Python `3.12.11`. |
| Built-container tools | Python `3.12.11`; uv `0.11.21 (aarch64-unknown-linux-gnu)`; Node `v24.21.0`; npm `11.19.0`; pnpm `10.6.3`; Azure CLI `2.91.0`. |
| Registry settings | `npm config get registry` returned `https://packagefeedproxy.microsoft.io/npm/`; `PIP_INDEX_URL` and `UV_DEFAULT_INDEX` were `https://packagefeedproxy.microsoft.io/pypi/simple`; `PIP_EXTRA_INDEX_URL`, `PIP_FIND_LINKS`, `UV_INDEX`, `UV_INDEX_URL`, `UV_EXTRA_INDEX_URL`, and `UV_FIND_LINKS` were empty. |
| Active container | ID `564f578d408ed2617e5c3f2e39d3e71b55fdd3e77a6aa25b267f88e476e0dde6`; `uname -sm` reported `Linux aarch64`; Python path `/opt/venv/bin/python`. |
| Post-create | Python editable setup and `pnpm install --frozen-lockfile` completed. The pnpm output warned that build scripts for `protobufjs`, `sharp`, and `unrs-resolver` were ignored; no script approval was granted. |

The build-time resolver conflict was resolved only by the user-approved, policy-preserving change to `.devcontainer/install-python-dependencies.py` and `tests/policy/test_install_python_dependencies.py`. The helper now reads the existing root `[tool.uv].override-dependencies` and passes those entries to the aggregate uv install through a short-lived `--overrides` file. This preserves the existing `PyJWT[crypto]>=2.14.0,<3` security floor when `redis-entraid==1.2.1` constrains PyJWT below `2.14`; no manifest, lock, or security floor was changed. The parent-verified focused regression command

```text
uv run --no-project --with pytest --with ruff --index-url https://packagefeedproxy.microsoft.io/pypi/simple python -m pytest tests/policy/test_install_python_dependencies.py -q
```

passed **2 tests**; Ruff passed in that same ephemeral environment. The full `tests/policy` run in T007 below also passed. A transient approved-proxy `ECONNRESET` while fetching the locked `next@15.5.18` was retried successfully; this is an access interruption followed by retrieval, not package absence. No public npm or PyPI feed was used.

**T002 remains incomplete/blocked.** The built image and its actual Linux/ARM64 architecture/runtime are now evidenced, but this does not establish the complete supported matrix. Linux/AMD64 runner and container builds, Alpine/musl, Windows x64, hosted/sovereign runner versions, and the other recipe-specific base-image digests remain unavailable. Do not infer them from this build or the Windows ARM64 host.

### T006 — Distinct installed baseline maps and remaining consumer holds

All uv installs below used explicitly isolated `/tmp` environments, the existing locks with `--locked`, `--no-cache`, Python `3.12`, and `--no-python-downloads`. The source settings were explicitly set to the approved PyPI proxy with secondary indexes and find-links empty. The active shell inherited `VIRTUAL_ENV=/opt/venv`; uv warned that this differed from each `UV_PROJECT_ENVIRONMENT`, ignored the active environment, created the stated `/tmp` environment, and installed there. The map queries below name each target interpreter explicitly, so the `/opt/venv` package set is not accidentally counted as a root or agents lock map.

| Environment ID | Actual provisioned recipe/map | Installed map summary | Status |
| --- | --- | --- | --- |
| `DEVCONTAINER-HELPER-PIP` | Successful build/post-create aggregate in the single shared `/opt/venv`; `uv pip list --python /opt/venv/bin/python --format=freeze`, sorted with `LC_ALL=C sort -f` | **300** `name==version` rows; map SHA-256 `069150ec6fdb069400f85c73b214c3bf1ff737fe174162b7302c8b04bccb5401`. Work-item-relevant versions include `aiohttp 3.14.4`, `cryptography 50.0.2`, `h2/hpack 4.4.1/4.2.0`, `idna 3.20`, `mem0ai 2.2.1`, `msgpack 1.2.3`, `PyJWT 2.15.1`, `pydantic-settings 2.15.0`, `redis-entraid 1.2.1`, `setuptools 84.0.0`, `python-engineio 4.14.0`, `python-socketio 5.17.0`, `starlette 1.7.0`, and `python-multipart 0.0.32`. | One shared aggregate only; it is not three lock maps and is not a repeatability pair. |
| `ROOT-UV-LINUX-ARM64` | From `/workspace`: `UV_PROJECT_ENVIRONMENT=/tmp/phase8-root-uv uv sync --locked --extra dev --extra load --no-cache --python 3.12 --no-python-downloads`; map from `uv pip list --python /tmp/phase8-root-uv/bin/python --format=freeze` | **298** installed rows; map SHA-256 `ccac93bbf845646cc1d53d98767991f57726bba45e39db245abf4750129f487d`. Relevant versions include `cryptography 50.0.1`, `idna 3.11`, `msgpack 1.2.2`, `PyJWT 2.15.0`, `redis-entraid 1.2.1`, `h2/hpack 4.4.1/4.2.0`, `aiohttp 3.14.3`, `setuptools 84.0.0`, `mcp 1.30.0`, `mem0ai 2.0.20`, `pydantic-settings 2.15.0`, `fastapi 0.138.0`, `python-engineio 4.14.0`, `python-socketio 5.17.0`, `starlette 1.7.0`, and `python-multipart 0.0.32`. | One successful locked/no-cache Linux/ARM64 install of the root lock. |
| `AGENTS-UV-LINUX-ARM64` | From `/workspace/apps/agents`: `UV_PROJECT_ENVIRONMENT=/tmp/phase8-agents-uv uv sync --project /workspace/apps/agents --locked --no-cache --python 3.12 --no-python-downloads`; map from `uv pip list --python /tmp/phase8-agents-uv/bin/python --format=freeze` | **244** installed rows; map SHA-256 `bd22e259f6bb3e6b06a7508c7ea1fadadf5b9a3d626a2e57d4b3b254fda81f98`. Relevant versions include `cryptography 50.0.1`, `idna 3.11`, `msgpack 1.2.2`, `PyJWT 2.15.0`, `h2/hpack 4.3.0/4.1.0`, `aiohttp 3.14.3`, `setuptools 82.0.1`, `mcp 1.30.0`, `mem0ai 2.0.2`, `pydantic-settings 2.14.1`, `fastapi 0.141.1`, `python-engineio 4.14.0`, `python-socketio 5.17.0`, `starlette 1.7.0`, and `python-multipart 0.0.32`. | One successful locked/no-cache Linux/ARM64 install of the independent agents lock. |

The installed pnpm workspace was enumerated after the frozen post-create install with `pnpm --recursive list --depth Infinity --json`. For each importer, the map digest below is over sorted, unique lower-case `name==version` entries recursively flattened from dependencies, devDependencies, and optionalDependencies, with a final newline; these hashes are map fingerprints, not artifact hashes.

| pnpm importer/environment | Unique map entries | Map SHA-256 | Relevant resolved baseline versions |
| --- | ---: | --- | --- |
| `/workspace/apps/web` (`NW` importer) | 799 | `2453624dc3a5cfdef8942d811b244a44639192947db4db3d26fe28dbb2e85aa7` | Next and `@next/env` `16.3.6`; ARM64 SWC GNU/musl `16.3.6`; jsdom `25.0.1`; Playwright trio `1.59.1`; ESLint `9.39.4`; `@types/node 22.13.10`; js-yaml `4.1.1`; MSAL React `5.3.2`; sharp `0.35.5`; PostCSS `8.5.28`. |
| `/workspace/packages/ui` (`NU` importer) | 114 | `4dc8e3ef829f81bf97a580abb1ac31274298113a74b825ed22f627e621e5fcd9` | Next and `@next/env` `15.5.18`; ARM64 SWC GNU/musl `15.5.18`; Playwright trio `1.59.1`; sharp `0.35.5`; PostCSS `8.5.28`. |
| `/workspace/packages/domain` | 10 | `45eb4b4e852c3cda61c570d3cf15950c4e6cb63ada2a4bc4af673e5c877511d7` | Workspace-local domain importer; no targeted package upgrade. |
| `/workspace` root importer | 0 | `01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b` | No root package dependency entries in the recursive listing. |

The current devcontainer helper aggregate is observably different from the independent lock maps (for example, aggregate `idna 3.20` versus root/agents locked `3.11`, and aggregate `mem0ai 2.2.1` versus root `2.0.20` / agents `2.0.2`). It therefore remains one shared pip resolution context; it is not evidence for the locked root or agents contexts.

The other E14 consumer rows remain individually blocked/not-run: Ubuntu/Python 3.12 CI pip jobs, Windows x64 `quality-windows`, eval-PR and spec-035/spec-036 pip recipes, the API/agents/ingestion/ingest-runner/eval-runner Docker recipes, and the deployment job were not independently provisioned here. The available Docker engine was Linux/ARM64, so no Linux/AMD64 image or Windows x64 runner result is inferred. No hosted workflow, deployment, or live Azure step was dispatched. API and specify-cli locks remain protected, unaffected comparison scopes and were not installed. **B-CONSUMER-BASE remains open; T006 is incomplete.**

### T007 — Frozen-baseline checks executed in the available environment

Every local result below is limited to the Linux/ARM64 devcontainer. The root-lock checks used `/tmp/phase8-root-uv`; the shared repository/CI-style checks used `/opt/venv` where noted. These do not replace the Ubuntu/Linux/AMD64 or Windows x64 baselines.

| Environment/check | Exact command(s) | Result |
| --- | --- | --- |
| `ROOT-UV-LINUX-ARM64` source-policy check | `python /workspace/scripts/verify_python_package_sources.py` | **PASS** — approved Python proxy reported. |
| `ROOT-UV-LINUX-ARM64` policy tests | `python -m pytest /workspace/tests/policy -q` | **PASS** — 12 passed. Includes the authorized installer regression test. |
| `ROOT-UV-LINUX-ARM64` lint/type/import/codegen | `ruff check apps tests packages`; `ruff format --check apps tests packages`; `mypy apps packages`; `lint-imports`; `python /workspace/scripts/codegen/generate_map_overlay_taxonomy_ts.py --check` | **PASS** — Ruff clean; 1,537 files already formatted; mypy reported no issues in 790 files; import contracts 5 kept/0 broken after analyzing 611 files and 548 dependencies; taxonomy check exited 0. |
| `ROOT-UV-LINUX-ARM64` equivalence | `pytest tests/equivalence -q --tb=short` | **PASS** — 6 passed. |
| `DEVCONTAINER-LINUX-ARM64-PY312` quality test selection | With `AMA_ENVIRONMENT=test` and `AMA_TRUST_FORWARDED_PRINCIPAL=1`: `pytest tests/unit tests/contract tests/integration tests/simulation -m "not azure_staging and not azure_foundry_staging and not azure_cosmos_staging and not azure_speech_staging and not azure_blob_worm_staging and not measurement_staging and not e2e and not load and not locust" --cov=apps --cov=packages --cov-report=xml --cov-report=term` | **FAIL** — 5,820 passed, 2 failed, 19 skipped, 14 deselected, 32 warnings; exit 1 after 1,336.35 s. Failures: `tests/integration/test_indexing_licence_inventory_lint.py::test_lint_detects_inventory_row_missing` and `::test_lint_detects_orphan_inventory_row`; both raised `PermissionError [Errno 1] Operation not permitted` from `shutil.copymode` for `/workspace/docs/corpus/INDEXING-LICENCE-INVENTORY.md` on the mounted workspace. Recorded as a baseline failure; not fixed or waived. |
| `DEVCONTAINER-LINUX-ARM64-PY312` simulation isolation | Ran the exact 18-file `SELECTION` and env from `.github/workflows/ci.yml#simulation-tenant-isolation`: `pytest $SELECTION -m spec007_isolation --strict-markers --collect-only -q`, then `pytest $SELECTION -m spec007_isolation --strict-markers -q --tb=short`; `SPEC007_MIN_CASES=113`, `AMA_ENVIRONMENT=test`, `AMA_TRUST_FORWARDED_PRINCIPAL=1`, `AMA_TEST_SUPPORT=1` | **PASS locally** — 113 collected (minimum 113); 112 passed, 1 skipped. Still ARM64-only. |
| `DEVCONTAINER-LINUX-ARM64-PY312` DevOps contracts | `python -m pytest /workspace/tests/devops -q` | **FAIL** — 211 passed, 1 skipped, 7 failed. Failures: Azure Maps wiring, CD reusable eval-gate inputs, KEDA replica text, Foundry workflow trigger, CI P1 release-gate wiring, soft-delete Bicep wiring, and spec-005 audit lint. No unrelated fixes applied. |
| `DEVCONTAINER-LINUX-ARM64-PY312` spec-035 local test shard | `python -m pytest apps/api/tests/contract/spec_035 apps/api/tests/unit/spec_035 -q --tb=short` | **FAIL** — 84 passed, 5 failed, 4 errors. The four production-reach setup errors reported `ModuleNotFoundError: ama_domain`; five auth tests received 401 because `AMA_ENTRA_TEST_PRINCIPAL` was ignored while live Entra authentication was enabled. No Azure credentials or live endpoint was used. |
| `DEVCONTAINER-LINUX-ARM64-PY312` eval-PR local checks | `ruff check packages/eval-core/ packages/eval-dataset/ apps/eval-runner/ tests/unit/eval/`; `python -m pytest packages/eval-core/tests/ packages/eval-dataset/tests/ tests/unit/eval/ -q` | Ruff **PASS**. Pytest **FAIL** — 84 passed, 5 failed, 4 errors; failures were 401s with the test principal ignored in live Entra mode, and setup errors reported `ModuleNotFoundError: ama_domain`. No workflow dispatch or Azure step was run. |
| `DEVCONTAINER-LINUX-ARM64-PY312` benchmark | `pytest tests/benchmark/ --benchmark-json=.benchmarks/current.json -q` | **FAIL** — 27 passed, 6 failed; benchmark regression report failed one SLO (`test_api_dashboard_p95_concurrent`, recorded `0.0 ms` against SLO `2 s`). Other failures included `test_aiims_assignment_under_5s`, `test_pprr_transition_under_5s`, `test_recovery_dashboard_under_10s`, `test_concurrent_recovery_operations`, and `test_pipeline_evacuation`; traces included missing `/app/var` and `PermissionError: /app`. The tool also warned the environment differed from the stored benchmark baseline and enforced SLOs without relative comparison. |
| `DEV-PNPM-LINUX-ARM64-NODE24` domain/web | `pnpm --filter @ama/domain run typecheck`; `pnpm --filter @ama/domain build`; `pnpm --filter @ama/web lint`; `pnpm --filter @ama/web exec tsc --noEmit`; `pnpm --filter @ama/web test`; `pnpm --filter @ama/web test:a11y`; `pnpm --filter @ama/web build` | **PASS** — domain typecheck/build; web lint/typecheck; web Vitest 36 files/174 tests; a11y 2 files/15 tests; Next.js build exited 0. Build emitted a webpack “Critical dependency: require function … cannot be statically extracted” warning; not changed. |
| `DEV-PNPM-LINUX-ARM64-NODE24` Playwright collection/browser | `pnpm --filter @ama/web exec playwright --version`; `pnpm --filter @ama/web exec playwright install --list`; both quickstart `--list` commands for `evidence` and `chromium`/`mobile` | **PASS for collection only** — Playwright `1.59.1`; local browser inventory reports Chromium revision `1217` under `/opt/ms-playwright`; evidence collected 5 tests, story collection 6 tests. This is the existing baseline browser, not the proposed `1.63.0` browser payload. |
| `DEV-PNPM-LINUX-ARM64-NODE24` evidence Playwright tests | With `PYTHONPATH=/workspace/packages/domain/src`, `AMA_TEST_MODE=1`, `AMA_TEST_SUPPORT=1`, `AMA_ENVIRONMENT=dev`: `pnpm --filter @ama/web exec playwright test --project=evidence` | **PASS locally** — 5 passed in 42.7 s. |
| `DEV-PNPM-LINUX-ARM64-NODE24` story acceptance | With `PYTHONPATH=/workspace/packages/domain/src`, `AMA_TEST_SUPPORT=1`, `AMA_ENVIRONMENT=dev`: `pnpm --filter @ama/web exec playwright test --project=chromium --project=mobile /workspace/tests/e2e/test_incident_commander_dashboard.spec.ts /workspace/tests/e2e/test_persona_workspace.spec.ts /workspace/tests/e2e/test_dashboard_decision_support.spec.ts` | **FAIL** — 6 failed. Assertions could not find expected `NSW Flood Response` / `Operations Officer` headings; browser logs included `Cannot read properties of undefined (reading 'length')`. This remains an unwaived baseline failure. |

For Playwright only, the test process received per-command `GIT_CONFIG_COUNT=1`, `GIT_CONFIG_KEY_0=safe.directory`, `GIT_CONFIG_VALUE_0=/workspace` after listing had emitted a non-fatal Git “dubious ownership” message. No global Git configuration was changed.

Not run/blocked: the coverage-ratchet and spec-035 PowerShell invariant scripts because `pwsh` is absent; the spec-035 `npx ajv-cli@5.0.0` schema step because `ajv-cli` is not installed and no on-the-fly package installation was added; Windows x64, hosted Linux/AMD64, Alpine/musl, CodeQL/gitleaks/PSRule/Trivy, sovereign-runner, deployment, live Azure, and remote Action execution. The coverage-ratchet CI condition also requires the Python quality step to succeed, which it did not here. No hosted workflow was dispatched.

All eleven baseline manifest/lock hashes for `package.json`, the web/UI manifests, root/agents/API Python manifests, the pnpm lock, and root/agents/API/specify-cli uv locks still match their E0 values. `pnpm install --frozen-lockfile` and all locked uv installs left those files unchanged. Generated coverage/test/build outputs from this run were restored where they touched tracked files; no implementation, dependency, lock, or Action-pin edits were made.

**T007 remains incomplete/blocked.** Some Linux/ARM64 checks passed, but required checks failed or were not run and no equivalent Ubuntu/Linux/AMD64 or Windows x64 result exists. Failures are preserved as baseline evidence; none was treated as a pass or repaired as unrelated work.

### T011 — Current retrieval observations (not artifact closure)

The successful Linux/ARM64 devcontainer is current evidence that the configured npm/Python sources could provision the installed baseline tool/dependency sets described above. The frozen pnpm install used the approved npm registry; the root and agents uv installs used the approved Python proxy with `--no-cache` and `--locked`. They establish installed baseline maps for those specific contexts only. They do not establish candidate artifact identities/checksums, all transitive artifacts, all final redirect hosts, or two clean candidate installs. No new per-wheel SHA-256 values or per-npm-archive hashes were calculated for these installed maps; map hashes above are not artifact hashes.

The installed Playwright `1.59.1` Chromium inventory and current locked package maps do not validate the proposed Playwright `1.63.0` browser/OS payload. A successful baseline fetch after the transient `next@15.5.18` proxy retry does not establish candidate absence or candidate source closure. The historical E11/E12 direct artifact hashes, source-archive/tree/blob verifications, and the #103 Cosign sub-gate remain unchanged and retain their original provenance labels.

**T011 remains incomplete.** Candidate native/transitive closure and platform coverage, source-host/integrity gaps (including SHA-1-only npm metadata), full MSAL graph/final-host approval, Playwright `1.63.0` browser/OS artifacts, and Linux/AMD64/Alpine evidence remain open. `B-SOURCE-ENV` is not closed by configuration or by the baseline build.

### T013 — Action evidence retained; runner/baseline gates still open

No proposed Action source archives, tree/blob sets, release assets, or Cosign signatures were re-fetched in this continuation. Retain E12's five proposed official source/tree/blob verifications and the recorded gitleaks/Cosign asset evidence, including the #103 Cosign asset/signature sub-gate. No conclusive supported-runner minimum/version or checkout fork/credential behavior evidence was obtained, no Action was functionally executed, and no workflow was dispatched. The old #105/#103 full-SHA baselines remain unresolved upstream; `B-ACTION-BASE` is open.

**T013 remains incomplete/blocked.** Proposed-source verification and #103 asset/signature evidence do not clear the runner compatibility or old-baseline provenance requirements.

### T020 — Recalculated pre-edit execution allowlist

This is a fresh gate evaluation after the new T002/T006/T007/T011/T013 evidence. It does not repeat T019, change a candidate, clear a hold, or authorize work beyond T020. W-01/W-02 were treated as gates: E0 retains the pre-edit workflow/source-policy hash inventory captured before T003–T005 (do not overwrite it with current hashes); T006 now has per-consumer/map checkpoints, but the missing hosted and recipe-specific rows keep W-02 active. No review/checklist marker was changed.

| Candidate edit scope | Refreshed disposition | Gate still preventing an edit |
| --- | --- | --- |
| T021 npm: `NW-next`, `NU-next`, `NW-jsdom`, `NW-playwright`, `NW-js-yaml`, and the other web/UI package candidates | **Exclude** | The new install/map evidence is only for the current locked versions on the ARM64 devcontainer. T011's full candidate native/transitive/platform/source/integrity closure is still missing; some candidate metadata has only SHA-1 where stronger lock integrity must be preserved; the proposed Playwright browser assets are not verified. The story acceptance baseline also failed. `B-SOURCE-ENV` and `B-VALIDATION` remain open. |
| `NW-jsdom` fallback `30.1.1` | **No fallback selected** | It remains a tentative same-major candidate between baseline `25.0.1` and target `30.1.2`; the Node `24.21.0` devcontainer observation is not the complete supported runner/platform compatibility proof, and full candidate transitive/source/test gates remain unmet. |
| T022 root `PR-idna` | **Exclude** | The root locked baseline map is one Linux/ARM64 install; Windows x64 and Ubuntu/Linux/AMD64 consumer baselines remain unavailable. T007's full Python quality selection failed in this environment and is not a passing supported-runner baseline. |
| T023 agents `PA-h2`, `PA-idna`, `PA-setuptools`, `PA-settings` | **Exclude** | The independent agents lock map is one Linux/ARM64 install. Standalone supported x64 and affected pip/Docker consumer maps and matching validation remain unavailable; no security/validation gate is waived. |
| Action candidates (`AC-checkout`, `AC-upload`, `AC-comment`) | **Exclude** | T013 lacks conclusive supported-runner minimum/behavior evidence and functional runner checks. |
| `AC-gitleaks`, `AC-cosign` | **Hold; exclude** | `B-ACTION-BASE` remains open because the old full-SHA baselines are unresolved. The Cosign asset/signature sub-gate does not prove baseline ordering. |
| Existing retain/supersede directions | **No version edit** | These are provisional outcomes, not authority for cosmetic edits or downgrades; final outcomes remain for T052. |

**T020 result: the refreshed execution allowlist is empty (`∅`).** No dependency manifest, lockfile, or Action pin was changed. `B-SOURCE-ENV`, `B-CONSUMER-BASE`, `B-VALIDATION`, the affected work-item holds, and W-02 remain active. T020 remains complete as a gate evaluation (`[X]`); T002, T006, T007, T011, and T013 remain unchecked/incomplete. Stop here: T021–T023 were not started. Resume at **T006** for the missing supported consumer/runner maps, then **T007** for required matching baseline checks; close only the remaining T011/T013 source/runner gaps with authorized evidence, and reevaluate **T020** before the parent considers the sole T021–T023 parallel group.

## E16 — Linux/AMD64 emulation attempt (T002)

Observed 2026-10-09. Docker Buildx advertised `linux/amd64` support on the Windows/ARM64 host. A no-push Dev Container build was attempted with:

```text
npm exec --yes --package=@devcontainers/cli --registry=https://packagefeedproxy.microsoft.io/npm/ -- devcontainer build --workspace-folder C:\code\ama --platform linux/amd64 --image-name ama-proxy-upgrade:phase8-amd64
```

The build failed during Dockerfile step 20/23, while the Python dependency resolver was running under QEMU: `qemu: uncaught target signal 11 (Segmentation fault)`. `uv` exited with `SIGSEGV`; the final image was not produced, and no AMD64 container or installed map was obtained. This is a local emulation/tool failure, not evidence that any package version is absent from the proxy. It does not establish a Linux/AMD64 baseline or clear `B-CONSUMER-BASE`. No workflow was dispatched or remote resource changed.

## E17 — Node 24 Alpine web baseline builds (T006/T011)

Observed 2026-10-09 using the existing `apps/web/Dockerfile`, clean `docker buildx` invocations, and the approved npm proxy passed as `NPM_CONFIG_REGISTRY`.

| Target | Result | Evidence |
|---|---|---|
| Linux/ARM64 Alpine | **Build passed.** `docker buildx build --platform linux/arm64 --load --no-cache --tag ama-web-baseline:phase8-alpine-arm64 --build-arg NPM_CONFIG_REGISTRY=https://packagefeedproxy.microsoft.io/npm/ --file apps/web/Dockerfile .` | Base `node:24-alpine@sha256:ebfe2f90462722a7a4de65e91990e97fe0d401c70e0e762c5b53302f905ec1c1`; final image platform `linux/arm64`, image ID `sha256:2d9391b5225182f3c9ae97b3af481f9ca5ad74f319f61bbfcac39274d1a34167`. Running the image's Node binary reported `v24.21.0`. Frozen pnpm install completed with pnpm 10.6.3; Next.js 16.3.6 production build exited successfully with the existing webpack critical-dependency warning. The install warned that the `unrs-resolver` build script was ignored; no approval was granted. Transient proxy `ECONNRESET` requests were retried successfully. |
| Linux/AMD64 under local QEMU | **Incomplete.** A no-cache `docker buildx build --platform linux/amd64` of the same Dockerfile completed `pnpm install --frozen-lockfile`, but the Next.js build emitted repeated QEMU signal-11 segmentation faults. The command remained hung without progress and was stopped after more than 15 minutes; no final image was created. | This demonstrates only an emulated package-install attempt; it is not a native Linux/AMD64 runtime or successful web-build result. The failure is an emulation/tool failure, not evidence that a package version is missing from the proxy. |

These builds establish the current locked Next.js/Node baseline for ARM64 Alpine and a partial, emulated AMD64 install only. They do not validate candidate versions, repeated clean-install pairs, or browser payloads, and they do not clear the supported Linux/AMD64, Windows x64, or source/integrity gates. T002/T006/T011 remain incomplete; no dependency, lockfile, or Action pin was changed.

## E18 — Authorized draft-PR hosted checks

Observed 2026-10-09 after the user authorized checkpoint `67c79626328f30ff476f379dd38cfbf6f8969227` and draft PR [#152](https://github.com/johnbilliris/ama/pull/152) solely to collect existing CI evidence. The PR remains draft and was not merged; none of the 33 existing chore PRs was modified.

| Run | Environment | Result |
|---|---|---|
| [eval-pr-gate `37885912203`](https://github.com/johnbilliris/ama/actions/runs/37885912203) | Hosted Ubuntu 24.04 image `20261004.327.1`; Python 3.12.15 x64. The workflow's global `PIP_INDEX_URL` and `UV_DEFAULT_INDEX` are the approved Microsoft proxy, with secondary indexes disabled. | **PASS** — Ruff passed; eval unit suite 164 passed, 1 skipped, 1 warning; scorecard gate passed with 25 samples. The existing eval workflow posted one automated scorecard comment on new draft PR #152 using its configured `pull-requests: write` permission. |
| [security-scan `37885912169`](https://github.com/johnbilliris/ama/actions/runs/37885912169) | Hosted security workflow on the same draft PR. | Gitleaks and PSRule passed. Trivy failed with **one HIGH, zero CRITICAL**: Next.js `16.3.6`, CVE-2026-94483 (SSRF in Image Optimization), fixed in `16.3.8`. This is evidence of a finding in the unchanged baseline and supports evaluating PR #149; it does not establish proxy retrieval, compatibility, or candidate validation for `16.3.8`. |
| [push-triggered ci.yml `37885889980`](https://github.com/johnbilliris/ama/actions/runs/37885889980) | Commit `67c79626328f30ff476f379dd38cfbf6f8969227`. | **No matrix evidence** — run failed in 0 seconds with no jobs/logs; GitHub CLI reported a likely workflow-file issue. The recorded E0 baseline run [37731039293](https://github.com/johnbilliris/ama/actions/runs/37731039293) on `62d249dc1205644fed934ea167df56695e92b3d2` likewise failed in 0 seconds with no jobs/logs. No supported CI matrix result can be inferred from either run. |

The only hosted Linux/x64 baseline obtained is the eval-pr-gate recipe above; it does not cover the Python/Windows x64 quality matrix, all project CI jobs, Alpine, or Action runtime/checkout behavior. The Trivy finding was already present in the unchanged version files and no severity threshold was altered. The automated comment was confined to newly authorized draft PR #152. The remaining workflow matrix, source, compatibility, and validation holds remain open; T002/T006/T007/T011/T013 are not all cleared and T020 must be reassessed before any dependency edit.

## E19 — Hosted baseline matrix after CI repair; T020 re-evaluation

Observed 2026-10-09. This addendum preserves E0–E18 as historical evidence and supersedes only E18's statement that the hosted Linux/Windows quality matrix was still unavailable and its instruction to reassess T020. The configured `ci.yml` matrix has now run on the explicitly approved draft PR [#152](https://github.com/johnbilliris/ama/pull/152); it contains both passing and failing/skipped jobs below. PR #152 remains draft and unmerged, and none of the 33 existing chore PRs was modified. Run [37887899653, attempt 2](https://github.com/johnbilliris/ama/actions/runs/37887899653) ran `ci.yml` for commit [`d812f688db5ccd32c31f8e9b4708fe458d8906ce`](https://github.com/johnbilliris/ama/commit/d812f688db5ccd32c31f8e9b4708fe458d8906ce).

### CI no-job defect and approved repair

The no-job issue was traced to `UV_CACHE_DIR: ${{ runner.temp }}\uv-cache` at `quality-windows` job-level `env`, where the runner context is not allowed. The approved minimal fix in `d812f688` moved that setting to the cache and uv-consuming step-level environments; it did not change dependency declarations/locks, Action pins, permissions, triggers, or test selectors. Official actionlint v1.7.12 for Windows/ARM64 was release-checksum-verified from `rhysd/actionlint`; `ci.yml` passed with only the two documented custom self-hosted-runner-label warnings ignored. `python -m pytest tests/devops/test_ci_workflow_structure.py -q` passed **14 tests**. `git -c core.whitespace=cr-at-eol diff --check` passed.

### `ci.yml` baseline matrix results

Python package-install boundaries in the hosted Python jobs used `PIP_INDEX_URL` and `UV_DEFAULT_INDEX` set to `https://packagefeedproxy.microsoft.io/pypi/simple`; secondary indexes and find-links were empty. These are baseline results on `d812f688`, not candidate-upgrade runs.

| Job | Environment / recipe evidence | Result |
|---|---|---|
| [quality](https://github.com/johnbilliris/ama/actions/runs/37887899653/job/113687177030) | Hosted Ubuntu 24.04, image `20261004.327.1`, Python `3.12.15/x64`. Used the checked-in Linux pip recipe: install `pytest pytest-cov pytest-asyncio pytest-benchmark hypothesis ruff mypy==2.0.0 import-linter pyyaml`, then editable `apps/api`, `apps/agents`, `packages/eval-core`, and `apps/eval-runner`. | **PASS** — Ruff passed; `pytest tests/equivalence -q --tb=short`: 6 passed; CI quality selection `pytest tests/unit tests/contract tests/integration tests/simulation -m "not azure_staging and not azure_foundry_staging and not azure_cosmos_staging and not azure_speech_staging and not azure_blob_worm_staging and not measurement_staging and not e2e and not load and not locust" --cov=apps --cov=packages --cov-report=xml --cov-report=term`: **5,829 passed, 12 skipped, 14 deselected, 31 warnings**. This is the pip recipe, not a Linux/x64 install map for the root `uv.lock`; no installed-version map/digest was emitted or inferred. |
| [quality-windows](https://github.com/johnbilliris/ama/actions/runs/37887899653/job/113687141919) | Hosted `windows-2025-vs2026`, image `20260925.250.1`, Python `3.12.10/x64`. Approved Python proxy env; uv cache action reported a **miss**. `uv sync --locked --extra windows-ci --no-install-project` resolved **309** and installed **267** packages; the log directly shows `idna==3.11`. The existing no-deps editable eval-runner install followed. | **PASS** — `uv run --no-sync ruff check apps tests packages`; `uv run --no-sync pytest tests/contract tests/integration -q --tb=line --maxfail=10`: **2,498 passed, 27 skipped**. No complete installed-version map or map checksum was emitted; no digest is claimed. |
| [python-package-source-policy](https://github.com/johnbilliris/ama/actions/runs/37887899653/job/113687141088) | Hosted Ubuntu 24.04 / Python 3.12.15 x64. | **PASS** — source-policy job. This does not prove every artifact redirect host is policy-attested. |
| [simulation-tenant-isolation](https://github.com/johnbilliris/ama/actions/runs/37887899653/job/113687141346) | Hosted Linux x64 baseline. | **PASS**. |
| [docs-arch](https://github.com/johnbilliris/ama/actions/runs/37887899653/job/113687140567), [golden-set-canonical](https://github.com/johnbilliris/ama/actions/runs/37887899653/job/113687141749), [accessibility-citation-card](https://github.com/johnbilliris/ama/actions/runs/37887899653/job/113687142007), [evidence-pack-publication-gate](https://github.com/johnbilliris/ama/actions/runs/37887899653/job/113687141783) | Hosted `ci.yml` jobs. | **PASS**. |
| [specify-cli-quality](https://github.com/johnbilliris/ama/actions/runs/37887899653/job/113687141556) | No change detected for its selector. | **SKIPPED**; not a passing test result. |
| [story-acceptance](https://github.com/johnbilliris/ama/actions/runs/37887899653/job/113687140392) | Hosted Ubuntu 24.04 image `20261004.327.1`, Python 3.12.15 x64, Node 24; approved npm/Python proxy settings. A transient `IncompleteRead` occurred while installing `apps/api`, then the retry succeeded. Spec 040 evidence Playwright selection passed **5 tests**. | **FAIL** — the story selector `pnpm --filter @ama/web exec playwright test --project=chromium --project=mobile` with the three configured story specs exited 1: `Error: No tests found.` This is a baseline selector/test-wiring failure, not evidence of dependency incompatibility. Preserve it; no selector fix was made. |

### Separate draft-PR gate and security evidence

| Run / job | Result |
|---|---|
| [eval-pr-gate run 37885912203](https://github.com/johnbilliris/ama/actions/runs/37885912203), [eval-gate job](https://github.com/johnbilliris/ama/actions/runs/37885912203/job/113675761525) | Hosted Ubuntu 24.04 image `20261004.327.1`, Python 3.12.15 x64, approved Python proxy with secondary indexes disabled. Ruff passed; eval tests **164 passed, 1 skipped, 1 warning**; the scorecard passed with **25 samples**. The existing workflow posted one automated scorecard comment on newly authorized draft PR #152 through its configured `pull-requests: write` permission. No comment was posted to any of the 33 chore PRs. |
| [security-scan run 37885912169](https://github.com/johnbilliris/ama/actions/runs/37885912169), [gitleaks](https://github.com/johnbilliris/ama/actions/runs/37885912169/job/113675761940), [PSRule](https://github.com/johnbilliris/ama/actions/runs/37885912169/job/113675762215), [Trivy](https://github.com/johnbilliris/ama/actions/runs/37885912169/job/113675761743) | Gitleaks and PSRule **PASS**. Trivy **FAIL**: one HIGH, zero CRITICAL; unchanged Next.js `16.3.6`, `CVE-2026-94483` (SSRF in Image Optimization), fixed in `16.3.8`. This makes #149 security-relevant but is not evidence of `16.3.8` compatibility, full approved-source closure, or candidate validation, and does not waive T011. No threshold or allowlist was changed. |

The earlier job-less runs `37885889980` (checkpoint commit `67c79626328f30ff476f379dd38cfbf6f8969227`) and `37731039293` (E0/main baseline) remain historical observations only; the full configured CI matrix result is now available from run `37887899653`. W-02 remains active. E0's pre-edit input hashes were not overwritten by the later CI workflow fix.

### Candidate source observations relevant to T020

The approved npm proxy freshly served `next@16.3.8`, `@next/env@16.3.8`, and `@next/swc-linux-x64-gnu@16.3.8` / `@next/swc-linux-x64-musl@16.3.8`; the package SHA-512 SRI values matched the retrieved files. This is artifact-level evidence only. The required `@next/swc-linux-arm64-*` candidate variant and the full companion/transitive closure are still missing. Some other companion records are SHA-1-only. The observed final `vsblob.vsassets.io` redirect hosts are not independently policy-attested. Playwright `1.63.0` browser/OS payloads and the full browser revision set remain unresolved. `B-SOURCE-ENV` and T011 remain open; the Trivy fixed-version result does not close either.

### T002/T006/T007/T011/T013 status update

- **T002 remains incomplete (`[ ]`).** E19 directly records hosted Ubuntu/Python Linux x64 and Windows x64 runner images/runtimes and their respective CI recipes. It does not complete the exact matrix: no native Linux/AMD64 root-uv/container baseline was obtained; local QEMU Linux/AMD64 attempts still SIGSEGV as recorded in E16/E17; Alpine/musl candidate coverage, standalone agents, the other affected helper/container recipes, and Action-runner minimum/behavior rows remain open.
- **T006 remains incomplete (`[ ]`, B-CONSUMER-BASE open).** The Linux x64 quality job is the pip/editable-install recipe and emitted no full installed map. Windows x64 is a fresh cache-miss root `windows-ci` locked install with 309 resolved / 267 installed packages and logged `idna==3.11`, but no complete map checksum. Other spec/workflow, standalone-agents, helper, and API/agents/ingestion/ingest-runner/eval-runner container recipes remain unmeasured as independent consumers.
- **T007 is complete as baseline outcome capture (`[X]`), not as an all-green gate.** E14/E15 local baseline outcomes and E19 hosted outcomes are recorded with failures/skips preserved. The story selector failed, the baseline Trivy scan found one HIGH, and previously recorded DevOps/spec-035/benchmark failures and blocked/not-run checks remain failures or holds; none was waived or relabeled pass.
- **T011 remains incomplete (`[ ]`).** Next native/transitive/platform coverage, artifact/redirect-host policy and integrity gaps, Playwright browser/OS payloads, and the full candidate closures remain open.
- **T013 remains incomplete (`[ ]`).** The matrix exercised existing Action pins only; supported runner minimums, proposed-SHA/source/asset validation, checkout fork/credential behavior, and #105/#103 baseline provenance are not cleared.

### T020 — scope-by-scope pre-edit allowlist

Re-evaluated T020 after E19 against T003–T007 and T011–T018. A hosted job pass is counted only for the recipe/scope it actually exercised; the evaluation does not treat the CI workflow correction, job-less historical runs, a failed baseline check, W-02, or the Trivy finding as a pass or policy waiver.

| Edit scope / work item | T020 disposition | Exact remaining gate |
|---|---|---|
| `NW-next` (#149/#133/#132), target Next `16.3.8` | **Exclude** | Trivy confirms the target is the recorded CVE fix, and the approved proxy's x64 GNU/musl artifacts have matching SHA-512 SRI. The ARM64 SWC candidate and full companion/transitive closure are still missing; redirect-host policy is not attested; the baseline story selector failed. No T011 or candidate-runtime gate is waived. |
| `NU-next`, target `15.5.21` | **Exclude** | T011 still lacks complete scope-specific candidate/native/transitive source-integrity closure and the required baseline/compatibility evidence. Do not conflate its Next 15 importer with `NW-next`. |
| `NW-jsdom`, target `30.1.2` / possible `30.1.1` fallback | **Exclude** | The target remains absent; the fallback still lacks complete transitive/source and supported Node 24 runtime compatibility evidence. |
| `NW-playwright`, coupled `@playwright/test` / `playwright` / `playwright-core` `1.63.0` | **Exclude** | Browser/OS download sources and the full browser revision set remain unresolved; direct npm package artifacts do not close that gate. |
| `NW-js-yaml`, target `4.3.1` | **Exclude** | Existing proxy metadata is SHA-1-only and no stronger publisher/lock-integrity evidence plus scope regression gate is recorded. |
| `NW-eslint` (#150), `NW-node-types` (#146), `NW-msal-react` (#144) | **Hold / exclude** | Existing B-ESLINT peer conflict, B-TYPES Node-24 compatibility hold, and B-MSAL full companion/source/consumer hold remain open (T014–T016). |
| Root `PR-idna` (#111), `idna 3.11 → 3.15` in `C:\code\ama\uv.lock` | **Exclude** | T012's approved-proxy universal wheel and integrity/`Requires-Python >=3.8` record remain valid; Windows x64 `windows-ci` now freshly installs the locked `idna==3.11` and its quality job passes. However, the Linux x64 `quality` run used pip editable installs, not a root `uv.lock` sync/map; the only Linux root locked map remains the Linux/ARM64 devcontainer in E15. T006 therefore does not establish the supported Linux x64 root-lock baseline needed for this edit. The security scan is a baseline scan with a Next finding and supplies no candidate-idna clearance. |
| Agents `PA-h2` (`h2 4.4.1` + `hpack 4.2.0`), `PA-idna` (`3.15`), `PA-setuptools` (`83.0.0`), `PA-settings` (`2.14.2`) | **Exclude** | T012 direct wheel evidence does not substitute for a standalone `apps/agents/uv.lock` supported-x64 consumer baseline. E15 has one Linux/ARM64 agents lock map; E19's Linux pip `-e apps/agents` recipe and Windows root lock are not that independent agents lock context. Its matching baseline checks remain unavailable (T006/T007). |
| Action edits (`AC-checkout`, `AC-upload`, `AC-gitleaks`, `AC-cosign`, `AC-comment`; T025–T033) | **Hold / exclude** | T013 remains incomplete for runner/source/behavior evidence; B-ACTION-BASE still blocks gitleaks/cosign ordering; the CI run used existing pins, not proposed SHAs. No live Action side effect is authorized. |
| Root/agents retain or supersede directions with no required version change | **No edit** | Provisional retain/supersede labels are not authority for cosmetic changes or normalization. |

**T020 result: execution allowlist remains empty (`∅`); no T021–T023 scope is eligible.** The new x64 baseline evidence improves T002/T006/T007 but does not clear every scope's exact pre-edit gates. `B-SOURCE-ENV`, `B-CONSUMER-BASE`, `B-ACTION-BASE`, W-02, and batch-wide `B-VALIDATION` remain open; no candidate two-clean-install evidence was generated. No manifest, lockfile, or Action pin was changed in this re-evaluation; T021–T023 remain not started. No workflow was dispatched and no PR/comment operation was performed for E19.

## E20 — Isolated Linux x64 uv-lock baselines and scoped T020 allowlist

Observed 2026-10-09 in the feature-scoped [`phase8-python-baseline-maps` job](https://github.com/johnbilliris/ama/actions/runs/37891855096/job/113694467512), run `37891855096` on commit [`d01cf1ed683e84ed2f837f54e5b6550da323c96e`](https://github.com/johnbilliris/ama/commit/d01cf1ed683e84ed2f837f54e5b6550da323c96e), draft PR [#152](https://github.com/johnbilliris/ama/pull/152). The feature-specific job was restricted to this branch. It ran on Ubuntu 24.04 image `20261004.327.1`, Python 3.12.15 x64, using the approved Microsoft PyPI proxy. Each lock was installed into a separate fresh runner-temp environment with `uv sync --locked --no-cache --python 3.12 --no-python-downloads`; each installed `name==version` map was sorted, hashed, and uploaded in the seven-day `phase8-python-baseline-maps` artifact. No repository dependency file was edited by the capture job.

| Consumer / map | Installed rows | SHA-256 of downloaded CI artifact | Relevant installed versions |
|---|---:|---|---|
| Root uv lock — Linux x64, `dev` + `load` | 302 | `7f19fa2efef48334ea6d18e2203a98fa6b282dfbd245499a77255c8ced0bf217` | `idna==3.11`, `cryptography==50.0.1`, `h2==4.4.1`, `hpack==4.2.0`, `msgpack==1.2.2`, `pyjwt==2.15.0`, `pydantic-settings==2.15.0`, `redis-entraid==1.2.1`, `setuptools==84.0.0`, `python-engineio==4.14.0`, `python-socketio==5.17.0`, `starlette==1.7.0`, `python-multipart==0.0.32`. |
| Agents uv lock — Linux x64, independent project lock | 248 | `254e4bbcf53de3afe38a6920bb9c3635e027ad16c2522b0d58eb933a6561541d` | `idna==3.11`, `h2==4.3.0`, `hpack==4.1.0`, `cryptography==50.0.1`, `msgpack==1.2.2`, `pyjwt==2.15.0`, `pydantic-settings==2.14.1`, `setuptools==82.0.1`, `python-engineio==4.14.0`, `python-socketio==5.17.0`, `starlette==1.7.0`, `python-multipart==0.0.32`. |

Both hashes above were recomputed over the two downloaded artifact files and match the `sha256sum` lines in the completed CI job. They fingerprint complete installed maps, not package archives. The Windows x64 `quality-windows` job in E19 separately had a uv cache miss and ran the root `windows-ci` locked install on Python 3.12.10 (309 resolved, 267 installed; `idna==3.11` appeared in the log), followed by passing Ruff and 2,498 contract/integration tests. That Windows job did not emit a full map hash and is not represented as an independent agents-lock map.

### Completed baseline matrix for this revision

Run [`ci.yml` 37891855096](https://github.com/johnbilliris/ama/actions/runs/37891855096) completed with overall failure due to the web story selector. The new lock-map job, Linux `quality`, Windows `quality-windows`, source-policy, simulation-isolation, docs, accessibility, golden-set, and evidence-publication checks passed; `specify-cli-quality` was skipped by its change detector. Linux `quality` ran on Ubuntu 24.04/Python 3.12.15 x64 and reported 5,829 passed, 12 skipped, and 14 deselected; Windows `quality-windows` ran on `windows-2025-vs2026` image `20260925.250.1`, Python 3.12.10 x64, and reported 2,498 passed, 27 skipped. The story acceptance job failed with `Error: No tests found` for its configured Chromium/mobile selector after the transient API-package `IncompleteRead` was retried successfully and five Spec 040 evidence tests passed. Preserve the selector failure. The separate security scan still reports one HIGH/zero CRITICAL on unchanged Next.js 16.3.6 (CVE-2026-94483, fixed in 16.3.8); this does not implicate the Python lock scopes.

### T020 — scope-by-scope pre-edit allowlist after E20

The new fresh Linux x64 maps close the exact baseline gap for the root and agents **uv.lock** resolution contexts. E15 retains the separate Linux/ARM64 lock maps; E19 retains the Windows root `windows-ci` locked install and test evidence. E12/R4 record exact approved-proxy candidate wheel, integrity, compatibility-range, and supported-Python metadata for the Python targets below. The new baseline-map evidence does not establish every CI pip/helper/container recipe. T006 remains incomplete globally; only the lock contexts actually captured are eligible for consideration. No `pyproject.toml`, pip-helper, Dockerfile, other lock, or non-Python scope is in this allowlist.

| Authorized lock-only edit scope | Work item / PR | Approved target | Baseline/source evidence and boundary |
|---|---|---|---|
| Root `uv.lock` | `PR-idna`, #111 | `idna 3.15` | Fresh root Linux x64 `dev` + `load` map and Windows x64 root `windows-ci` lock sync both show `idna==3.11`; E12 records the proxy universal wheel, checksum and Python metadata. Only root `uv.lock` is authorized; API `idna==3.20` and specify-cli `idna==3.19` remain unchanged. |
| `apps/agents/uv.lock` | `PA-h2`, #136 | `h2 4.4.1` plus required `hpack 4.2.0` | Fresh independent agents Linux x64 map shows `h2==4.3.0`, `hpack==4.1.0`; E12 verifies both approved-proxy wheels; R4 records h2's `hpack>=4.2,<5` and `hyperframe>=6.1,<7` requirements. Root `h2/hpack` are already 4.4.1/4.2.0 and remain untouched. |
| `apps/agents/uv.lock` | `PA-idna`, #112 | `idna 3.15` | Fresh independent agents Linux x64 map shows `idna==3.11`; E12 records the exact proxy wheel/integrity and Python metadata. Keep separate from root/API/specify-cli resolutions. |
| `apps/agents/uv.lock` | `PA-setuptools`, #129 | `setuptools 83.0.0` | Fresh independent agents Linux x64 map shows `82.0.1`; E12 records the proxy wheel/integrity. Root `84.0.0` remains unchanged. |
| `apps/agents/uv.lock` | `PA-settings`, #122 | `pydantic-settings 2.14.2` | Fresh independent agents Linux x64 map shows `2.14.1`; E12/R4 record the proxy wheel/integrity and declared dependency floors compatible with the current agents Pydantic, dotenv, and typing-inspection versions. Root `2.15.0` remains unchanged. |
| Other `uv.lock`, npm, pip/container consumers, Actions | All other work items | None | No scope change is authorized. Unmeasured independent pip/helper/container recipes remain blocked; npm candidate closure/host evidence, browser artifacts, Action runner/provenance and the story selector remain open. |

**T020 result after E20: non-empty allowlist for exactly five Python uv-lock work items.** T022 may update only root `uv.lock` for #111; T023 may update only `apps/agents/uv.lock` for #112, #136 (including hpack), #129, and #122. Do not edit declarations as a convenience; the approved targets are transitive resolutions in these lock contexts. No PR direction is final until T052's post-edit install, quality, security, and integrity checks pass. `T006` remains unchecked and `B-CONSUMER-BASE` remains open for independent pip/helper/container recipes; `T007` is complete as baseline result capture, not an all-green result. `T011` remains incomplete for npm/browser/redirect-host closure, `T013` remains incomplete for Actions, and the baseline story-selector failure and Next CVE remain recorded. T021 is excluded from this allowlist; only the Python lock scopes in T022–T023 may start.

## E21 — Python lock candidates: ARM64 repeatability, x64 maps, and quality checks

Observed 2026-10-09 on branch `001-proxy-dependency-upgrades`, HEAD `d01cf1ed683e84ed2f837f54e5b6550da323c96e`, before publishing the candidate locks. The installed environments ran inside the existing Linux/ARM64 devcontainer: Linux `aarch64`, CPython 3.12.11, uv 0.11.21. The configured source was `https://packagefeedproxy.microsoft.io/pypi/simple`; `scripts/verify_python_package_sources.py` passed and confirmed that approved source. These runs supplement, but do not replace, the Linux x64 baseline maps in E20 or establish Windows x64 results.

Each candidate pair used separate `UV_PROJECT_ENVIRONMENT` directories and `--no-cache`. Root A/B ran from `/workspace` with `uv sync --locked --extra dev --extra load --no-cache --python 3.12 --no-python-downloads`; standalone agents A/B ran from `/workspace/apps/agents` with `uv sync --project /workspace/apps/agents --locked --no-cache --python 3.12 --no-python-downloads`. Each installed map was generated with `uv pip list --python <run-env>/bin/python --format=freeze | LC_ALL=C sort -f`. `cmp` and SHA-256 confirmed that A and B were identical for each lock.

| Candidate lock context | Installed rows per run | A/B installed-map SHA-256 | Full map |
| --- | ---: | --- | --- |
| Root, `dev` + `load`, Linux/ARM64 | 298 | `f7cb6864d61cf76042d427d42f4705b4fe8b4b37b574522d4ed6da8ee4df7d58` | [`e21-root-linux-arm64.txt`](./candidate-maps/e21-root-linux-arm64.txt) |
| Standalone agents, Linux/ARM64 | 244 | `8cec5212cf59f90c3ccc8c373c58ac3862a62a09d707953abbcfde996b419ab5` | [`e21-agents-linux-arm64.txt`](./candidate-maps/e21-agents-linux-arm64.txt) |

The candidate map hashes also match the persisted map-file hashes. `uv lock --check --no-cache` passed for both lockfiles (309 root and 251 agents locked packages resolved). Full sorted baseline-to-candidate installed-map comparison on the same ARM64 runtime found no unapproved changes:

The feature-scoped `phase8-python-baseline-maps` job completed successfully twice on separate Ubuntu x64 runner executions using the approved proxy and explicit `--no-cache` installs. Run A was CI run [`37903502768`](https://github.com/johnbilliris/ama/actions/runs/37903502768), head `150f9ad3`. Run B was attempt 2 of CI run [`37913845624`](https://github.com/johnbilliris/ama/actions/runs/37913845624), head `8c285dd2`; the intervening head changed only evidence/task documentation, and both candidate lock hashes remained unchanged. Each run used Ubuntu 24.04, CPython 3.12.15 x64 and uv 0.11.21, with separate runner-temp environments for root (`dev` + `load`) and standalone agents. Run B repeated the exact checked-in commands from `.github/workflows/ci.yml`: root `uv sync --locked --extra dev --extra load --no-cache --python 3.12 --no-python-downloads`; agents `uv sync --project apps/agents --locked --no-cache --python 3.12 --no-python-downloads`. Both A/B installed maps compared byte-for-byte equal per lock; their SHA-256 values and row counts match the persisted full-map files below. Each candidate x64 map has the same number of rows as its E20 x64 baseline map; sorted comparison found only the authorized changes.

| Candidate lock context | Installed rows per run | A/B map SHA-256 | Full map |
| --- | ---: | --- | --- |
| Root, Linux x64; runs A `37903502768` / B `37913845624` attempt 2 | 302 | `1dc8fef140566f9b5e15cc7669de0f5e2de3de9e3775a6054abbef3144316441` | [`e21-root-linux-x64.txt`](./candidate-maps/e21-root-linux-x64.txt) |
| Standalone agents, Linux x64; runs A `37903502768` / B `37913845624` attempt 2 | 248 | `f2821283d8f081b91cff306a45080e87b1fba55bdedd5b4a2f5384683cdebce9` | [`e21-agents-linux-x64.txt`](./candidate-maps/e21-agents-linux-x64.txt) |

The exact x64 root delta against E20 is `idna 3.11 → 3.15`. The exact agents delta is `h2 4.3.0 → 4.4.1`, `hpack 4.1.0 → 4.2.0`, `idna 3.11 → 3.15`, `pydantic-settings 2.14.1 → 2.14.2`, and `setuptools 82.0.1 → 83.0.0`; no other installed-map entry changed. E20 baseline and E21 candidate map hashes fingerprint complete installed-version maps, not package archives.

| Lock scope | Exact installed-map delta | Protected versions unchanged |
| --- | --- | --- |
| Root `uv.lock` | `idna 3.11 → 3.15` | `cryptography 50.0.1`, `msgpack 1.2.2`, `PyJWT 2.15.0`, `h2/hpack 4.4.1/4.2.0`, `pydantic-settings 2.15.0`, and `setuptools 84.0.0`. |
| `apps/agents/uv.lock` | `h2 4.3.0 → 4.4.1`, `hpack 4.1.0 → 4.2.0`, `idna 3.11 → 3.15`, `pydantic-settings 2.14.1 → 2.14.2`, `setuptools 82.0.1 → 83.0.0`. | `cryptography 50.0.1`, `msgpack 1.2.2`, `PyJWT 2.15.0`, `aiohttp 3.14.3`, `pyasn1 0.6.4`, `mcp 1.30.0`, `python-engineio 4.14.0`, `python-socketio 5.17.0`, `starlette 1.7.0`, and `python-multipart 0.0.32`. |

Post-edit SHA-256: root `uv.lock` `402417e4a32c94235801644b63ee4ea174376fd6c4468bb7eb3d1458188d3868`; agents `uv.lock` `3391269344807df9ad63b629394a27c029f704172337002662ddebc58cd70c29`. No dependency declaration, API/specify-cli lock, pip/helper/container recipe, npm manifest/lock, Action pin, or security override changed in this candidate edit.

### Candidate checks

| Candidate environment / check | Result |
| --- | --- |
| Root source policy, `python /workspace/scripts/verify_python_package_sources.py` | **PASS** — approved Microsoft Python proxy confirmed. |
| Root lock validity, `uv lock --check --no-cache`; agents equivalent | **PASS** — both existing lock graphs resolve without rewriting. |
| Root candidate policy/equivalence tests, `pytest tests/policy tests/equivalence` | **PASS** — 18 passed. |
| Agents candidate configuration/runtime subset (`tests/unit/test_communication_config.py`, `test_evacuation_config.py`, `test_resource_allocation_config.py`, `test_risk_assessment_config.py`, `test_maf_runtime_errors.py`, `test_maf_runtime_error_imports.py`) | **PASS** — 198 passed; one non-fatal `PytestConfigWarning` for `asyncio_mode`. |
| Root candidate Ruff, format, mypy, import-linter, taxonomy | **PASS** — Ruff clean; 1,537 files already formatted; mypy no issues in 790 source files; import contracts 5 kept/0 broken after analyzing 611 files and 548 dependencies; taxonomy `--check` exited 0. Import-linter emitted a non-fatal warning that its existing cache file was corrupt. |
| Root candidate simulation tenant-isolation selector from `ci.yml#simulation-tenant-isolation` | **PASS locally** — 113 collected (required minimum 113), 112 passed, 1 skipped. ARM64 only. |
| Root candidate full Linux quality selection from Quickstart §4 | **FAIL, same baseline failures** — 5,820 passed, 2 failed, 19 skipped, 14 deselected, 32 warnings; exit 1 after 1,339.64 s. The two failures are `tests/integration/test_indexing_licence_inventory_lint.py::test_lint_detects_inventory_row_missing` and `::test_lint_detects_orphan_inventory_row`, both `PermissionError [Errno 1] Operation not permitted` from `shutil.copymode` on `/workspace/docs/corpus/INDEXING-LICENCE-INVENTORY.md`. E15's unchanged ARM64 baseline records the same two failures and counts; no failure was waived or fixed. |
| Root candidate benchmark selection | **FAIL, same baseline failures** — 27 passed, 6 failed, 2 warnings. The same six tests also fail in the unchanged `/tmp/phase8-root-uv` baseline: `test_aiims_assignment_under_5s`, `test_pprr_transition_under_5s`, `test_recovery_dashboard_under_10s`, `test_concurrent_recovery_operations`, `test_api_dashboard_p95_concurrent`, and `test_pipeline_evacuation`. |
| `uv pip check` against old and candidate root/agents environments | **FAIL, unchanged baseline metadata conflicts** — root: `redis-entraid 1.2.1` declares `PyJWT~=2.13.0` while the preserved security override installs `PyJWT 2.15.0`; agents: `agent-framework-mem0` declares `mem0ai<2` while the preserved patched-version override installs `mem0ai 2.0.2`. Both exact findings also occur in the respective pre-edit ARM64 environments. The overrides and installed protected versions were not weakened. |
| Candidate GitHub Actions Linux x64 quality (`ci.yml` run `37913845624`, attempt 2) | **PASS** — quality job completed: 5,829 passed, 12 skipped, 14 deselected; Ruff, format, mypy, import boundaries, codegen, equivalence (6 passed), Python coverage-ratchet phase A (78.58%, floor 0%, no prior artifact), and benchmark (33 passed, 1 warning) passed. Source-policy, docs, and simulation-isolation jobs also passed. This is the existing CI pip/editable-install recipe; the separate no-cache uv-lock maps are recorded above. |
| Candidate GitHub Actions Windows x64 `quality-windows` (`ci.yml` run `37913845624`, attempt 2) | **PASS, one cold candidate install** — `windows-latest`, Python 3.12.10 x64; `uv` 0.11.21; `uv` cache action reported a miss for the candidate-lock key, `uv sync --locked --extra windows-ci --no-install-project` resolved 309 and installed 267 packages, including `idna==3.15`. Ruff passed, the existing no-deps eval-runner package install completed, and contract/integration tests reported 2,498 passed, 27 skipped, 4 warnings. This is a fresh cache-miss Windows result, but not the required pair of explicit `--no-cache` installs or a full installed map. |
| Candidate accessibility, golden-set and evidence publication (`ci.yml` run `37913845624`, attempt 2) | **PASS** — accessibility citation-card 8 tests passed; golden-set and evidence-pack publication jobs passed. `specify-cli-quality` was skipped by its change detector. |
| Candidate story acceptance (`ci.yml` run `37913845624`, attempt 2) | **FAIL, same baseline selector failure** — the five Spec 040 evidence tests passed; the configured Chromium/mobile story selection then exited `Error: No tests found` for the three configured story specs. This reproduces the E20 baseline failure; no selector was changed. |
| Candidate security scan, run `37913845559` | **FAIL, unchanged baseline finding** — gitleaks and PSRule passed; Trivy found only `next 16.3.6`, HIGH `CVE-2026-94483`, fixed in `16.3.8`. No Next.js or npm files were changed in this Python-only candidate. |
| Candidate eval PR gate, run `37913845567` | **PASS** — eval-gate job completed successfully. |
| Initial candidate workflow attempt on head `150f9ad3` and documentation-only attempt on `eff69962` | **BLOCKED before start** — GitHub reported account-payment/spending-limit restrictions. They yielded no candidate result; the later attempt 2 above ran after billing was restored. |
| Markdownlint of `tasks.md` and `evidence.md` via the approved npm proxy | **INCOMPLETE** — 52 pre-existing MD060 table-spacing diagnostics remain in earlier tables; no diagnostics were emitted for the new E21–E23 sections. |

E21 now has two identical no-cache candidate map installs for each Linux x64 and ARM64 uv lock; E23 adds two identical no-cache Windows x64 root `windows-ci` maps. The prior Windows `quality-windows` job passed after a cold cache-miss candidate sync, and E23 separately completed the no-deps eval-runner installation in both no-cache environments. Independent pip/helper/container recipes and remaining npm/Action scopes remain unmeasured or blocked. T006/B-CONSUMER-BASE, T024, T045, and final T052 remain incomplete; T039–T041 are recorded complete in `tasks.md`. No PR outcome is final.

## E22 — Next 16.3.8 ARM64 SWC artifact recheck

Observed 2026-10-09 at 08:35 UTC from PowerShell on Windows using Node `v24.16.0` / npm `11.13.0`. Re-fetched only through `https://packagefeedproxy.microsoft.io/npm/` with `npm pack --json --prefer-online --registry=https://packagefeedproxy.microsoft.io/npm/`; separately queried each `dist.tarball` metadata URL through the same registry. Npm's verbose logs show a successful registry packument response, then the artifact request followed to the final blob host listed below. The final signed query strings are intentionally not retained.

| Package | `dist.tarball` host/path returned from proxy | Final artifact host observed in npm log | Tarball bytes | Proxy `dist.integrity`, matched against downloaded bytes | Proxy `dist.shasum` |
| --- | --- | --- | ---: | --- | --- |
| `@next/swc-linux-arm64-gnu@16.3.8` | `ms-feed-25.pkgs.visualstudio.com/1es-public/_packaging/npm-public/npm/registry/@next/swc-linux-arm64-gnu/-/swc-linux-arm64-gnu-16.3.8.tgz` | `yrxvsblobprodcus449.vsblob.vsassets.io` | 32,025,992 | `sha512-O659ygeQYqneJ1fBKMpFxIFqYkYswu8IAS1OCKK/4f3ZgJJm1dRz4fVJZRi/kLLWjnBKnebOePA4WNv+sV1pVA==` | `fe6704a2061f6141096dea2c44de21b2b279ae5a` |
| `@next/swc-linux-arm64-musl@16.3.8` | `ms-feed-25.pkgs.visualstudio.com/1es-public/_packaging/npm-public/npm/registry/@next/swc-linux-arm64-musl/-/swc-linux-arm64-musl-16.3.8.tgz` | `lngvsblobprodcus421.vsblob.vsassets.io` | 31,371,815 | `sha512-dSjKSyWpzxoO1d3DIZZcP4XJcNaKeLmxQMFOiYl5vuBRMmweIqnAhty8tAmRsvTss779cK1FtYnDMj40e4TQlg==` | `c36276d658b928685d7868977c997399d62487f4` |

For both archives, `npm pack` identified the expected package name/version and contained the corresponding ARM64 GNU or musl `.node` file. The locally computed SHA-512 over each downloaded archive exactly matched the proxy-provided SRI. This supersedes only E20's observation that the Next 16.3.8 ARM64 SWC files were missing at that observation time; it does not establish full Next companion/transitive closure or a supported-runtime build.

Each extracted native binding was then loaded with `require()` on Linux/ARM64 Node `v24.21.0`: the GNU binary loaded and exposed 60 exports in Debian 12 / glibc 2.36 using local image `node:24-bookworm` (`sha256:64af3819f9275802414d7cdc38c27e9d82bd564dec4d4da87d008255d36c63b4`); the musl binary loaded and exposed 60 exports in Alpine `3.24.2` / musl libc using local image `ama-web-baseline:phase8-alpine-arm64` (`sha256:2d9391b5225182f3c9ae97b3af481f9ca5ad74f319f61bbfcac39274d1a34167`). This was a native binding-load check only, not a Next.js application build or candidate lock integration test.

The evidence-only commit `eff69962` triggered `ci.yml` run `37905767531`, security-scan run `37905767506`, and eval-pr-gate run `37905767485`. Every scheduled job failed before start with GitHub's account-payment/spending-limit message; no additional install or test ran. That commit did not change either candidate lock, so run `37903502768` on code commit `150f9ad3` remains the only executed hosted candidate CI result.

The two final `*.vsblob.vsassets.io` hosts are recorded as observations, not approved-source attestations. The proxy-fed artifact retrieval succeeded, but policy evidence has not independently attested those final blob hosts. No npm manifest or lock was changed and no package was installed into the application; only the isolated native binding-load check was executed. `T011` and `B-SOURCE-ENV` remain open for redirect-host policy, complete npm graphs, Playwright browser/OS payloads, MSAL companions, and the other npm candidates. The T020 execution allowlist remains limited to the five Python uv-lock scopes; NW-next remains excluded pending those source, full-closure, and compatibility gates.

## E23 — Branch-scoped Windows x64 candidate map job

Added `phase8-python-windows-candidate-maps` to `.github/workflows/ci.yml`, gated to pull requests whose head branch is `001-proxy-dependency-upgrades` and dependent only on the Python source-policy job. On `windows-latest` with Python 3.12, it installs uv from the approved Python proxy, then runs the root `windows-ci` locked sync twice in distinct runner-temp `UV_PROJECT_ENVIRONMENT` directories with `--no-cache --no-python-downloads`. Each isolated environment also receives the existing `apps/eval-runner` editable installation with `--no-deps --no-cache`; the complete installed `uv pip list --format=freeze` maps are sorted, SHA-256 hashed, compared byte-for-byte, and uploaded as `phase8-python-windows-candidate-maps`. The job asserts that both maps retain the authorized `idna==3.15` and protected root dependency versions. It intentionally has no dependency cache action.

The job passed on the first feature-branch run: [`ci.yml` run `38006394482`](https://github.com/johnbilliris/ama/actions/runs/38006394482), head `5cf33e42`, job `114076167947`, artifact `11651796211`. It ran on `windows-latest` / Microsoft Windows Server 2025 with Python 3.12.10 x64 and uv 0.11.21. Both A and B were separate runner-temp environments; each fresh `uv sync --locked --extra windows-ci --no-install-project --no-cache --python 3.12 --no-python-downloads` resolved 309 and installed 267 packages, then ran the no-deps editable eval-runner install. Each complete map contained 268 rows, the two maps compared equal, and both SHA-256 hashes were `54b55be9e0fccb86f51b729cc7c49ae1e9cd7a16da1556586a9aa9459195f667`. The identical full maps are preserved as [`e23-windows-root-a.txt`](./candidate-maps/e23-windows-root-a.txt) and [`e23-windows-root-b.txt`](./candidate-maps/e23-windows-root-b.txt); both contain `idna==3.15`, `cryptography==50.0.1`, `msgpack==1.2.2`, `PyJWT==2.15.0`, `h2/hpack==4.4.1/4.2.0`, `pydantic-settings==2.15.0`, and `setuptools==84.0.0`.

**T040 is complete for the root Windows x64 `windows-ci` lock context.** The earlier successful `quality-windows` job in run `37913845624` separately ran Ruff and the Windows contract/integration suite (2,498 passed, 27 skipped); this new job adds the two explicit no-cache install maps and repeated no-deps eval-runner install. Neither result is a full marker-complete Windows map for other independent consumers.

The same workflow run's general `quality` job stopped at `ruff format --check`: it found only the newly added `tests/devops/test_ci_workflow_structure.py` assertion at line 83 needed Ruff's one-line formatting. That exact formatting was corrected locally; `uv tool run --no-cache --from ruff==0.15.12 ruff format --check tests/devops/test_ci_workflow_structure.py` reported the file already formatted. The quality job must be rerun on the corrected commit before T045 is considered complete again. Windows `quality-windows` and its dependent downstream matrix jobs were skipped because `quality` failed; the independent Windows map job passed.

The same commit's security workflow again passed gitleaks/PSRule and failed Trivy only on the known unchanged Next.js 16.3.6 HIGH CVE-2026-94483. The eval PR gate completed its evaluation but failed the scorecard threshold: 25 samples, `gpt-5.4-mini@2026-03-17` must-include `0.857 < 0.900`. No thresholds or dependency scopes were changed. Local workflow validation: `python -m pytest tests/devops/test_ci_workflow_structure.py -q --tb=short` — **15 passed**; Ruff format check reported the Python test file already formatted; PyYAML `BaseLoader` parsed the workflow; the embedded Windows PowerShell script parsed cleanly; CRLF-aware `git diff --check` passed.

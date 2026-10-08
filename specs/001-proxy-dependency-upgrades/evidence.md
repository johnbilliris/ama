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

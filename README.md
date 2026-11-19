# M3.5 demo: quality gates in front of a deployment

A small project for Azure Repos and Azure Pipelines. Nothing is deployed to Azure App Service. The "app" is a mock, and the "deployment" is a mock that copies a folder and writes a record. What is real is the part you are teaching: two quality gates (Promptfoo and RAGAS) that decide whether the deployment stage runs.

## What is in the folder

| Path | What it is |
|---|---|
| `app/px_mock.py` | Mock PX Service Assistant. Returns an answer and the retrieved text for four questions. |
| `app/release.json` | The one file you edit during the demo. `mode` is `good`, `wrong_fact` or `unsupported_claim`. |
| `tests/golden.json` | The four golden questions with the text each answer must and must not contain. |
| `promptfoo/promptfooconfig.yaml` and `px_provider.py` | Promptfoo gate: plain right or wrong checks. No judge model, no key. |
| `gates/ragas_gate.py` | RAGAS gate: faithfulness, averaged over the four questions, minimum 0.80. Needs the Azure judge. |
| `gates/deploy_mock.py` | Mock deploy: copies `app/` to a staging folder and writes `deployment.json`. |
| `azure-pipelines.yml` | Build, then Quality gate (two jobs side by side), then Deploy to staging (mock). |
| `requirements.txt` | Packages for the RAGAS job. |

## The three modes

| `mode` in `release.json` | What the app does | Promptfoo gate | RAGAS gate | Deploy |
|---|---|---|---|---|
| `good` | Answers straight from the retrieved text | passes | passes | runs |
| `wrong_fact` | States a wrong number (16 bar, 12 months) | **fails** | usually fails too | skipped |
| `unsupported_claim` | Right answer plus extra claims that are not in the retrieved text | passes (the facts are right) | **fails** | skipped |

The third row is the teaching moment: the right/wrong checks all pass and the app is still not safe to release. Only the faithfulness check sees it. That is why you want more than one kind of gate.

## One-time setup in Azure DevOps

### 1. Put the code in Azure Repos
1. Azure DevOps > your project > **Repos** > **Files**.
2. If the repo is empty, click **Initialize** (keep "Add a README" ticked) > **Initialize**.
3. Click the **...** (three dots) at the top right of the file list > **Upload file(s)**. Upload the folders and files of this project so the repo root contains `app`, `gates`, `promptfoo`, `tests`, `azure-pipelines.yml` and `requirements.txt`. (Easier: clone the repo on your computer with **Clone** > **Clone in VS Code** or the git URL, copy the files in, then `git add .`, `git commit -m "gate demo"`, `git push`.)
4. The branch must be named `main`.

### 2. Create the variable group with the judge settings
1. **Pipelines** > **Library** > **+ Variable group**.
2. Variable group name: `px-eval-secrets`.
3. Click **+ Add** four times and enter:
   - `AZURE_OPENAI_ENDPOINT` = `https://bosch-ai-foundry.services.ai.azure.com/` (your endpoint)
   - `AZURE_OPENAI_API_KEY` = your key, then click the **lock icon** at the end of that row to make it secret
   - `AZURE_OPENAI_CHAT_DEPLOYMENT` = `gpt-5.4-mini` (your deployment name)
   - `AZURE_OPENAI_API_VERSION` = `2025-04-01-preview`
4. Click **Save**.

If you already created `px-eval-secrets` for the earlier M3.5 pipeline, add these four variables to it. The earlier `PX_URL` and `PX_KEY` variables are not used here.

### 3. Create the environment
1. **Pipelines** > **Environments** > **New environment**.
2. Name: `px-staging`. Resource: **None**. Click **Create**.
3. Optional, makes a good talking point: open `px-staging` > **...** (top right) > **Approvals and checks** > **+** > **Approvals** > add yourself under Approvers > **Create**. The deploy will then wait for a click.

### 4. Create the pipeline
1. **Pipelines** > **Pipelines** > **New pipeline**.
2. **Azure Repos Git** > select your repo.
3. **Existing Azure Pipelines YAML file** > Branch `main` > Path `/azure-pipelines.yml` > **Continue**.
4. Click **Run**. If it says the pipeline needs permission to use `px-eval-secrets` or `px-staging`, open the run and click **View** > **Permit** (twice, once for each).

### 5. Make the gate blocking on pull requests (for the "stops a merge" point)
1. **Repos** > **Branches** > **...** next to `main` > **Branch policies**.
2. Under **Build Validation** click **+** > pick this pipeline > Policy requirement **Required** > **Save**.
3. Azure Repos ignores the `pr:` block in the YAML. This branch policy is what runs the pipeline on every pull request.

## The demo, step by step

### Run 1: everything passes
1. Leave `mode` as `good`. Run the pipeline (or push any small change).
2. Show the three stages: Build, Quality gate (Promptfoo and Ragas jobs), Deploy to staging (mock). All green.
3. Click the finished run > **Tests** tab: four Promptfoo tests passed.
4. Click the run > **Extensions** tab (or the summary): the RAGAS faithfulness table.
5. Open the **Published** artifacts > `px-staging` > `deployment.json`: the record of what "went out", with the build number, the commit and the gates that passed.

### Run 2: a plain wrong answer is caught
1. **Repos** > **Files** > `app/release.json` > **Edit**. Change `"mode": "good"` to `"mode": "wrong_fact"` > **Commit**.
2. The pipeline starts by itself (trigger on `main`).
3. The **Promptfoo** job goes red. Open it: the log says the pass rate is below the threshold of 100%. The **Deploy to staging** stage shows as skipped.
4. Talking point: nothing was deployed, and nobody had to remember to check.

### Run 3: the answers look right but the gate still stops it
1. Edit `app/release.json` again, set `"mode": "unsupported_claim"` > **Commit**.
2. Promptfoo goes **green** (the facts are right). The **Ragas** job goes **red**: faithfulness is about 0.5, below the 0.80 minimum. Deploy is skipped.
3. Talking point: the answer is correct and also contains things the knowledge base never said. A right/wrong check cannot see that. A faithfulness score can.

### Run 4: fix it
1. Set `"mode": "good"` again > **Commit**. All stages go green and the deploy runs.

### Optional: show it on a pull request
Create a branch, change `mode` to `unsupported_claim`, open a pull request into `main`. The build validation policy runs Build and the gates, the PR shows the failed check, and **Complete** is blocked. The Deploy stage does not run on a PR (it only runs on `main`).

## What to say about the thresholds
- Promptfoo uses `PROMPTFOO_PASS_RATE_THRESHOLD: "100"` in the YAML. Any wrong answer fails the gate.
- RAGAS uses `RAGAS_FAITHFULNESS_MIN: "0.80"` in the YAML. The average faithfulness has to be at least 0.80.
- Both numbers are a decision for the team, not a law. Change them in the YAML and run again to show how the gate reacts.

## Running it on your computer first (optional)
Promptfoo gate (needs Node, no key):
```
cd promptfoo
npm.cmd install promptfoo
$env:PROMPTFOO_PYTHON = "py"
$env:PROMPTFOO_PASS_RATE_THRESHOLD = "100"
npx.cmd promptfoo eval -c promptfooconfig.yaml --no-cache
```
RAGAS gate (needs the four `AZURE_OPENAI_*` variables set in the window):
```
py -m pip install -r requirements.txt
cd gates
py ragas_gate.py
```
Mock deploy: `cd gates` then `py deploy_mock.py`. It writes to the `out` folder.

## What has and has not been tested
- Tested: the Promptfoo gate in all three modes (passes in `good` and `unsupported_claim`, fails with exit code 100 in `wrong_fact`), the mock deploy, and the YAML parses.
- Tested with a stand-in judge only: the RAGAS gate's wiring, the average, the minimum and the exit code. The stand-in is a crude word-matching check, not a model, so the real faithfulness numbers will differ. Expect `good` to be near 1.0 and `unsupported_claim` to be clearly lower. If a real score surprises you, change `RAGAS_FAITHFULNESS_MIN` or the mock answers.
- Not tested: the pipeline inside Azure DevOps, the environment approval, and the RAGAS gate against your Azure deployment. Do one run before the session.

# ARS-Codex

[![Version](https://img.shields.io/badge/version-v0.1.21-blue)](VERSION)
[![License: CC BY-NC 4.0](https://img.shields.io/badge/license-CC%20BY--NC%204.0-lightgrey)](https://creativecommons.org/licenses/by-nc/4.0/)
[![Sponsor](https://img.shields.io/badge/sponsor-Buy%20Me%20a%20Coffee-orange?logo=buy-me-a-coffee)](https://buymeacoffee.com/crucify020v)

ARS-Codex は、[Academic Research Skills（ARS）Claude Code 版](https://github.com/Imbad0202/academic-research-skills) の Codex ネイティブな sibling ディストリビューションです。独自の plugin ID、パッケージング、バージョン、および runtime adapter を持ちます。

このリポジトリは、ARS ワークフローの内容を単一の Codex スキルとして同梱（ベンダリング）しています。

```text
skills/academic-research-suite/
  SKILL.md
  manifest.json
  agents/openai.yaml
  ars/
    deep-research/
    academic-paper/
    academic-paper-reviewer/
    academic-pipeline/
    experiment-agent/
    commands/
    hooks/
    docs/
    tests/
    shared/
```

元の Claude Code ARS チェックアウトは変更されません。アップストリームの内容は GitHub の新規クローンからコピーされ、`skills/academic-research-suite/SKILL.md` の Codex ルータを通じて適合されます。

## Claude Code ARS との関係

このリポジトリは ARS-Codex です。元の Claude Code ARS ディストリビューションを利用する場合は、[Imbad0202/academic-research-skills](https://github.com/Imbad0202/academic-research-skills) をご使用ください。

Claude Code ネイティブのスキルレイアウト、Claude 固有の agent-team 動作、または元の ARS 開発履歴が必要な場合は Claude Code リポジトリを、Codex ネイティブの単一スイートスキルが必要な場合はこのリポジトリを使用してください。

## バージョニング

この ARS-Codex パッケージのバージョンは `0.1.21` です。リポジトリルートの `VERSION` ファイル、`skills/academic-research-suite/SKILL.md` のメタデータバージョン、および `skills/academic-research-suite/manifest.json` の `adapter_version` は、ベンダリングされた ARS スイートとは独立して Codex パッケージのバージョンを管理します。ベンダリングされたアップストリームのバージョンは `manifest.source_repositories[]` にコミット単位で記録されています。

パッケージレベルの変更内容は [`CHANGELOG.md`](CHANGELOG.md) にまとめられています。

現在ベンダリングされている ARS ソースは `Imbad0202/academic-research-skills@bbc0659272a511b422f6856cd6f44b6ccb2ac213`（`v3.18.0`）を追跡しています。固定席の cross-model Reviewer 2 と re-review Judge Record、引用キャッシュの stale advisory と任意のライブ再検証、高影響 claim 優先サンプリング、scope-conformance／search-bounded novelty advisory、held-out pipeline robustness セットが追加され、v3.17 の dispatcher・最小権限・integrity contract も維持されています。

## ARS-Codex Plugin のインストール

Codex CLI で GitHub marketplace を追加し、ARS-Codex をインストールします。

```bash
codex plugin marketplace add Imbad0202/academic-research-skills-codex --ref main
codex plugin add ars-codex@ars-codex
```

後で plugin を更新する場合：

```bash
codex plugin marketplace upgrade ars-codex
codex plugin add ars-codex@ars-codex
```

Codex Desktop では、**Plugins** からこのリポジトリを追加し、
**ARS-Codex** をインストールすることもできます。

```text
Marketplace source: https://github.com/Imbad0202/academic-research-skills-codex.git
Branch/ref: main
Plugin: ars-codex
```

Plugin ルートは `plugins/ars-codex/` です。`skills/` にはシンボリックリンクではなく
`academic-research-suite` の実体コピーが含まれるため、Windows の Codex Desktop
plugin キャッシュでも bundled skill を正しく登録できます。

インストール後は新しい Codex セッションを開き、`$academic-research-suite` を呼び出すか、
同梱 workflow に該当する学術研究タスクを直接記述してください。

## Skill の直接インストールと更新

Plugin を使わず、このリポジトリパスからスキルを直接インストールすることもできます。公開および認証付き GitHub アクセスの両方で一貫して動作するよう、`--method git` を使用します。

```bash
python "$HOME/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py" \
  --repo Imbad0202/academic-research-skills-codex \
  --ref main \
  --path skills/academic-research-suite \
  --method git
```

既存のインストールを更新する場合:

```bash
rm -rf "$HOME/.codex/skills/academic-research-suite"
python "$HOME/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py" \
  --repo Imbad0202/academic-research-skills-codex \
  --ref main \
  --path skills/academic-research-suite \
  --method git
```

インストール後に新しい Codex セッションを開いてください。既存の Codex セッションは古いスキルキャッシュを保持している場合がありますが、他の Claude や Codex のセッションを閉じる必要はありません。

`/skills` で確認してください。ARS-Codex エントリが1つ（`academic-research-suite` または `ARS-Codex`）表示されるはずです。このパッケージから `academic-paper`、`academic-pipeline`、`deep-research`、`academic-paper-reviewer` が個別のスキルとして表示されては**いけません**。表示される場合は、上記の更新コマンドで再インストールし、新しい Codex セッションを開いてください。

## Codex ドキュメント

- [Codex セットアップ](skills/academic-research-suite/ars/docs/SETUP.md) - インストール、`ars-*` エイリアス、オプションツール、Material Passport アダプター、および未対応の Claude プラグイン機能について説明しています。
- [Codex アーキテクチャ](skills/academic-research-suite/ars/docs/ARCHITECTURE.md) - Codex ランタイムオーバーレイを含む ARS パイプラインの論理構成を説明しています。

## 使い方

`$academic-research-suite`（単数形）で明示的に呼び出し、研究タスクの説明とともにソースファイル、メモ、草稿テキスト、レビュアーコメント、または出力の制約条件を提供してください。

```text
Use $academic-research-suite to help me plan a systematic literature review on
AI adoption in higher education quality assurance.
```

Codex アダプターはリクエストを以下の5つの ARS ワークフローのいずれかにルーティングします。

| ワークフロー | 用途 | プロンプト例 |
|---|---|---|
| `deep-research` | 研究質問の精緻化、文献レビュー、システマティックレビュー、メタ分析、ファクトチェック | `Use $academic-research-suite to build a systematic review protocol for AI in higher education QA.` |
| `academic-paper` | 論文のアウトライン、執筆、アブストラクト、リビジョン、引用フォーマット、AI 開示 | `Use $academic-research-suite to turn these notes into an IMRaD paper outline and drafting plan.` |
| `academic-paper-reviewer` | 原稿レビュー、模擬ピアレビュー、編集判断、再レビュー | `Use $academic-research-suite to review this manuscript and produce a journal-style decision letter.` |
| `academic-pipeline` | 整合性ゲート、レビュー、リビジョン、最終チェックを含むエンドツーエンドの研究→論文ワークフロー | `Use $academic-research-suite to run an end-to-end research-to-paper pipeline from topic to revised manuscript.` |
| `experiment-agent` | コード実験の計画、ヒューマンスタディプロトコル、統計的解釈、再現性検証 | `Use $academic-research-suite to plan a code experiment and define reproducibility checks.` |

### Claude スタイルのエイリアス

Claude Code v3.7 では `/ars-*` スラッシュコマンドがインストールされます。Codex には同等のプラグインコマンドレジストリがないため、このパッケージは単一の `$academic-research-suite` スキル内でコマンドの目的をエミュレートします。どちらの形式でも使用可能です。

```text
Use $academic-research-suite: ars-plan my paper on AI governance in universities.
```

または、Codex クライアントがスラッシュ付きテキストを通常のユーザーメッセージとして渡す場合:

```text
/ars-plan my paper on AI governance in universities.
```

スラッシュ入力がクライアント側でインターセプトされる場合は、プレーンなエイリアス形式を使用してください:

```text
ars-plan my paper on AI governance in universities.
```

| Claude コマンド | Codex エイリアス | ルーティング先ワークフロー |
|---|---|---|
| `/ars-plan` | `ars-plan` | `academic-paper` `plan` モード |
| `/ars-outline` | `ars-outline` | `academic-paper` `outline-only` モード |
| `/ars-abstract` | `ars-abstract` | `academic-paper` `abstract-only` モード |
| `/ars-lit-review` | `ars-lit-review` | `academic-paper` `lit-review` モード |
| `/ars-citation-check` | `ars-citation-check` | `academic-paper` `citation-check` モード |
| `/ars-disclosure` | `ars-disclosure` | `academic-paper` `disclosure` モード |
| `/ars-format-convert` | `ars-format-convert` | `academic-paper` `format-convert` モード |
| `/ars-revision-coach` | `ars-revision-coach` | `academic-paper` `revision-coach` モード |
| `/ars-revision` | `ars-revision` | `academic-paper` `revision` モード |
| `/ars-full` | `ars-full` | `academic-pipeline` フルワークフロー |

### 作業パターン

最良の結果を得るには、ワークフローの目標と現在の資料の状況を伝えてください:

```text
Use $academic-research-suite.

Goal: write a journal article.
Current materials: I have a literature matrix and rough findings, but no outline.
Output needed now: paper architecture and missing-evidence checklist.
Constraints: English, APA 7, higher education policy audience.
```

論文のトピックや大まかな研究方向しかなく、明確な研究質問がまだない場合は、Codex ルータが ARS のソクラテス式スコーピングから開始するようにしてください:

```text
Use $academic-research-suite.

I want to write a paper on AI adoption in higher education quality assurance.
I do not yet have a clear research question.
Please use SCR / Socratic dialogue to help me narrow the question first; do not write an outline yet.
```

想定ルート: まず `deep-research` の `socratic` モードにルーティングされます。ARS は絞り込みのための質問を行い、研究質問が収束するまでアウトラインや草稿の作成は行いません。

レビュータスクの場合、原稿または原稿へのパスと、希望するレビューモードを指定してください:

```text
Use $academic-research-suite to review this paper.
Mode: full review.
Focus: methodology, contribution, citation integrity, and likely desk-reject risks.
Output: reviewer reports plus editorial decision letter.
```

段階的パイプラインの場合、Codex に全過程をサイレントに実行させるのではなく、チェックポイントを要求してください:

```text
Use $academic-research-suite to start an academic-pipeline run.
Begin with Stage 0 intake and stop after producing the pipeline dashboard.
```

### スモークテスト

新しい Codex セッションで以下を実行します:

```text
/skills
```

期待される結果: ARS エントリは1つのみ。

続いてソクラテスルーティングをテストします:

```text
Use $academic-research-suite.
I want to write a paper on AI adoption in higher education quality assurance.
I do not yet have a clear research question.
```

期待される結果: `deep-research` の `socratic` モードにルーティングされ、絞り込みの質問が行われます。

CLI スモークテスト:

```bash
codex exec --ephemeral --sandbox read-only \
  -C /path/to/academic-research-skills-codex \
  'Use $academic-research-suite. Router smoke test only. User request to classify: I want to write a paper on AI adoption in higher education quality assurance, but I do not yet have a clear research question. According to the academic-research-suite router, classify the workflow and mode.'
```

### 非ブロッキング Codex 警告

以下の Codex メッセージは、ARS のインストール失敗を意味するものではありません:

- `[features].codex_hooks is deprecated` - 便利なタイミングで Codex 設定を更新してください。ARS-Codex は通常の使用において hooks を必要としません。
- `hooks need review before they can run` - hooks を使用する場合は個別にレビューしてください。ARS-Codex はベンダリングされた Claude hooks をトレーサビリティメタデータとして扱い、それらを必要としません。

### Codex アダプターの動作

ARS は元々 Claude Code 向けに作成されました。この Codex パッケージでは以下の通りです:

- ベンダリングされた `agents/*.md` ファイルはロールおよびフェーズプロンプトとして使用されます。
- ベンダリングされた `commands/ars-*.md` ファイルはプロンプトレシピのみとして機能します。Codex はこれらをスラッシュコマンドとして登録しません。
- ベンダリングされた `hooks/hooks.json` ファイルはアップストリームのトレーサビリティのためのみ保持されています。Codex はこのパッケージから Claude Code hooks をインストールしません。
- ユーザーが明示的に委譲または並列 agent の作業を要求しない限り、Codex は自動的にバックグラウンド agent を起動しません。
- Web/ソース検証には Codex のブラウジング機能を使用し、現在の事実や外部情報が関係する場合はソースを引用する必要があります。
- クロスモデル検証はデフォルトで無効です。この Codex パッケージで明示的に要求された場合は、`ars/shared/cross_model_verification.md` に従って provider を設定し、provider、model、送信される内容の種類を示したうえで、外部送信前にユーザーの明示的な同意を得てください。外部レビュアーは設定済み provider API を通じて呼び出され、現在の Codex model で代替実行されることはありません。
- アップストリームの「fresh Claude Code session」という記述は、このパッケージでは新しい Codex セッションを意味します。Material Passport のリセットセマンティクスは引き続き適用されます。
- 引用、ソース、統計、またはジャーナルポリシーが検証できない場合、Codex は根拠を捏生するのではなく、未検証としてマークする必要があります。

### ARS v3.18 Release パリティ

このパッケージは、Codex に同等の概念が存在する範囲で、アップストリーム ARS `v3.18.0` と同等のユーザー向けワークフロー内容を目指しています。

| アップストリーム ARS 機能 | Codex パッケージの動作 |
|---|---|
| インストール可能な単一プラグイン | 単一の `academic-research-suite` skill を同梱するネイティブ Codex plugin `ars-codex` |
| `/ars-*` スラッシュコマンド | スキルルータ経由で `ars-*` エイリアスとしてエミュレート。ネイティブのスラッシュコマンドではありません |
| `skills/` シンボリックリンクから自動検出される4つのアップストリームスキル | 単一の Codex ルータスキルがワークフローを選択し、ベンダリングされたワークフロー `WORKFLOW.md` ファイルを読み込みます |
| プラグイン同梱の agent | agent ファイルはロール/フェーズプロンプトです。ユーザーが明示的に委譲サブ agent を要求しない限り、Codex はインラインで実行します |
| `model: opus` / `model: sonnet` コマンドルーティング | Claude メタデータとして扱われます。Codex はアクティブなモデルを使用します |
| 保護対象 agent の `tools:` allowlist | 最小権限のロール境界として保持され、委譲された owner に Bash やネットワーク transport は付与されません |
| Canonical cross-model handoff envelope | Dispatcher が envelope を検証し、同意後は payload のみを送信して、閉じた結果ルーティング contract に従います |
| Cross-model Reviewer 2 と re-review judge | provider 設定と送信内容への同意がある場合のみ有効。固定席、Judge Record、単一モデル family／fallback の開示を保持します |
| キャッシュ stale advisory とライブ再検証 | ローカルキャッシュが既定。stale 行は advisory のみで、`ARS_CACHE_REVALIDATE=1` がライブ書誌再検証を有効にします |
| リスク層別 claim・scope・novelty チェック | 高影響 claim 優先サンプリングと、gate を阻害しない scope／search-bounded novelty advisory を保持します |
| Panel／degradation／pipeline-boundary の実行可能チェック | hermetic テストとともにベンダリングされ、オプションの full-runtime manifest から公開されます |
| SessionStart および SubagentStop hooks（更新通知を含む） | トレーサビリティのためのみベンダリングされています。Codex は Claude hooks をインストールまたは実行しません |
| Plugin marketplace の更新 | `codex plugin marketplace upgrade ars-codex` の後に `ars-codex@ars-codex` を再追加します。Skill の直接インストールは引き続き再インストールまたは pull で更新します |
| Claude Code Agent Team | 自動ではありません。Codex サブ agent には委譲または並列 agent の明示的なユーザー要求が必要です |
| アップストリームドキュメントのクロスモデル provider ディスパッチ | デフォルトでは無効。provider 設定とユーザー同意が明示された場合のみ使用できます |

### オプション: 外部クロスモデルレビュアー API

レビュアーのキャリブレーションやクロスモデルの悪魔の代弁者（devil's advocate）チェックには、
`ars/shared/cross_model_verification.md` に記載された provider tuple のいずれかを設定してください。例:

```bash
export OPENAI_API_KEY="<your-openai-api-key>"
export ARS_CROSS_MODEL="gpt-5.5"
```

その後、プロンプトでクロスモデル検証を明示的に要求してください。provider が設定されていない場合、または送信内容の種類に対する明示的な同意がない場合、ARS-Codex はシングルランタイムレビューにフォールバックし、クロスモデル検証が利用不可であったことを報告します。

## サポートとスポンサーシップ

ARS-Codex があなたの研究ワークフローに役立った場合、[Buy Me a Coffee](https://buymeacoffee.com/crucify020v) からメンテナンスをサポートいただけます。

## セキュリティ

脆弱性については公開 issue を開かないでください。非公開報告の手順は [`SECURITY.md`](SECURITY.md) に従い、最新のローカル検証サマリーは[リリース準備およびセキュリティレポート](security_best_practices_report.md)を参照してください。

### 高度な利用のためのファイルレイアウト

エントリポイントは以下の通りです:

```text
skills/academic-research-suite/SKILL.md
```

ワークフローの内容は以下に配置されています:

```text
skills/academic-research-suite/ars/<workflow>/
```

共有スキーマ、コンプライアンスルール、およびクロスワークフローのコントラクトは以下に配置されています:

```text
skills/academic-research-suite/ars/shared/
```

パッケージのデバッグや更新を行う際は、これらのパスを維持してください。多くの ARS ワークフローファイルが `shared/`、`scripts/`、`examples/`、および他のワークフローディレクトリを相互参照しています。

## 更新ポリシー

更新は、選択されたアップストリーム ARS コンテンツを `skills/academic-research-suite/ars/` に同期します。Claude Code リポジトリを無差別にミラーしないでください。`.claude/`、`.claude-plugin/`、ソースの `.gitignore`、および Codex で不要なシンボリックリンクのみのエイリアスディレクトリなど、Claude/プラグインローダーファイルは除外してください。ネストされたアップストリーム `.github/` workflow は、非アクティブな traceability と self-test fixture として保持できます。

### 非アクティブなアップストリームスクリプト

一部のアップストリームメンテナンススクリプトはベンダリングされていますが、`.claude/CLAUDE.md` のようなベンダリングされていない Claude Code 入力を必要とするため、この Codex パッケージでは意図的に非アクティブになっています。アップストリームスクリプトを Codex CI に組み込む前に、`skills/academic-research-suite/manifest.json` の `inactive_upstream_scripts` を確認してください。

## 貢献者と謝辞

**Cheng-I Wu** - ARS スイートおよびこの Codex ディストリビューションのメンテナー。

**Codex** - メンテナーの指示のもと、Codex アダプターのパッケージング、ルータポリシーの強化、テスト修正、およびリリース準備レビューを支援。

ベンダリングされたアップストリーム ARS の貢献者は、[`skills/academic-research-suite/ars/README.md`](skills/academic-research-suite/ars/README.md#contributors) に記載されています。

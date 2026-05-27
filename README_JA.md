# Academic Research Skills for Codex

[![Version](https://img.shields.io/badge/version-v0.1.8-blue)](VERSION)
[![License: CC BY-NC 4.0](https://img.shields.io/badge/license-CC%20BY--NC%204.0-lightgrey)](https://creativecommons.org/licenses/by-nc/4.0/)
[![Sponsor](https://img.shields.io/badge/sponsor-Buy%20Me%20a%20Coffee-orange?logo=buy-me-a-coffee)](https://buymeacoffee.com/crucify020v)

Academic Research Skills スイートの Codex ネイティブパッケージです。本リポジトリは
[Academic Research Skills for Claude Code](https://github.com/Imbad0202/academic-research-skills)
の兄弟 Codex ディストリビューションにあたります。

本リポジトリは ARS ワークフローコンテンツを単一の Codex スキルとしてベンダリングしています。

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

元の Claude Code ARS チェックアウトは変更されません。アップストリームのコンテンツは
GitHub からの新規クローンを通じてコピーされ、
`skills/academic-research-suite/SKILL.md` の Codex ルータ経由で適用されます。

## Claude Code 版

本リポジトリは Codex パッケージです。Academic Research Skills のオリジナル Claude Code 版は
[Imbad0202/academic-research-skills](https://github.com/Imbad0202/academic-research-skills)
をご利用ください。

ネイティブの Claude Code スキルレイアウト、Claude 固有のエージェントチーム動作、
またはオリジナルの ARS 開発履歴が必要な場合は Claude Code リポジトリを使用してください。
Codex ネイティブの単一スイートスキルが必要な場合は本リポジトリを使用してください。

## バージョニング

本 Codex パッケージのバージョンは `0.1.8` です。リポジトリルートの `VERSION` ファイル、
`skills/academic-research-suite/SKILL.md` のメタデータバージョン、および
`skills/academic-research-suite/manifest.json` の `adapter_version` は、
ベンダリングされた ARS スイートとは独立して Codex パッケージバージョンを追跡します。
ベンダリングされたアップストリームバージョンはコミット単位で
`manifest.source_repositories[]` に記録されます。

パッケージレベルの変更内容は [`CHANGELOG.md`](CHANGELOG.md) にまとめられています。

現在ベンダリングされている ARS ソースは
`Imbad0202/academic-research-skills@96b82e82142dc95f117595c207d3e150b078e411`
(`v3.9.4.2`) を追跡しています。v3.9.4.2 のアップストリーム差分は
`.github/` 配下の CI/リリースゲートのみであり、本 Codex パッケージでは意図的に除外しています。
ベンダリングされたランタイムコンテンツには、ARS v3.9.4.1 の一時的検証ホットフィックスと
v3.9.1 から v3.9.4 までのワークフロー更新が含まれています。

## インストールと更新

本リポジトリパスからスキルをインストールしてください。パブリックアクセスと
クレデンシャル付き GitHub アクセスの両方で一貫して動作するよう `--method git` を使用します。

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

インストール後に新しい Codex の会話を開いてください。既存の Codex セッションは
古いスキルキャッシュを保持している場合があります。関連のない Claude や Codex のセッションを
閉じる必要はありません。

`/skills` で確認してください。ARS エントリが1つ (`academic-research-suite` または
`Academic Research ...`) 表示されるはずです。本パッケージから個別の `academic-paper`、
`academic-pipeline`、`deep-research`、`academic-paper-reviewer` スキルが
表示されては**いけません**。表示される場合は、上記の更新コマンドで再インストールし、
新しい Codex の会話を開いてください。

## Codex ドキュメント

- [Codex セットアップ](skills/academic-research-suite/ars/docs/SETUP.md) — インストール、
  `ars-*` エイリアス、オプションツール、Material Passport アダプタ、
  および未対応の Claude プラグイン機能について説明しています。
- [Codex アーキテクチャ](skills/academic-research-suite/ars/docs/ARCHITECTURE.md) —
  Codex ランタイムオーバーレイを使用した ARS パイプラインの論理構成を説明しています。

## 使い方

`$academic-research-suite`（単数形）で明示的にスイートを呼び出し、
研究タスクの説明と共にソースファイル、メモ、ドラフトテキスト、
レビューコメント、または出力の制約条件を提供してください。

```text
Use $academic-research-suite to help me plan a systematic literature review on
AI adoption in higher education quality assurance.
```

Codex アダプタはリクエストを5つの ARS ワークフローのいずれかにルーティングします。

| ワークフロー | 用途 | プロンプト例 |
|---|---|---|
| `deep-research` | 研究質問の精緻化、文献レビュー、システマティックレビュー、メタ分析、ファクトチェック | `Use $academic-research-suite to build a systematic review protocol for AI in higher education QA.` |
| `academic-paper` | 論文のアウトライン、執筆、要旨、改訂、引用フォーマット、AI 開示 | `Use $academic-research-suite to turn these notes into an IMRaD paper outline and drafting plan.` |
| `academic-paper-reviewer` | 原稿レビュー、シミュレートされたピアレビュー、編集判定、再レビュー | `Use $academic-research-suite to review this manuscript and produce a journal-style decision letter.` |
| `academic-pipeline` | インテグリティゲート、レビュー、改訂、最終チェックを含む研究から論文までのエンドツーエンドワークフロー | `Use $academic-research-suite to run an end-to-end research-to-paper pipeline from topic to revised manuscript.` |
| `experiment-agent` | コード実験の計画、ヒューマンスタディプロトコル、統計的解釈、再現性検証 | `Use $academic-research-suite to plan a code experiment and define reproducibility checks.` |

### Claude スタイルのエイリアス

Claude Code v3.7 では `/ars-*` スラッシュコマンドがインストールされます。
Codex には同等のプラグインコマンドレジストリがないため、本パッケージは
単一の `$academic-research-suite` スキル内でコマンドの意図をエミュレートします。
どちらの形式でも使用可能です:

```text
Use $academic-research-suite: ars-plan my paper on AI governance in universities.
```

または、Codex クライアントがスラッシュ付きテキストを通常のユーザーメッセージとして
渡す場合:

```text
/ars-plan my paper on AI governance in universities.
```

スラッシュ入力がクライアント側でインターセプトされる場合は、プレーンなエイリアス形式を
使用してください:

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

### 推奨ワークフロー

最良の結果を得るために、ワークフローの目標と素材の現在の状態から始めてください:

```text
Use $academic-research-suite.

Goal: write a journal article.
Current materials: I have a literature matrix and rough findings, but no outline.
Output needed now: paper architecture and missing-evidence checklist.
Constraints: English, APA 7, higher education policy audience.
```

論文のトピックや大まかな研究方向しかなく、明確な研究質問がまだない場合は、
Codex ルータがまず ARS のソクラテス的スコーピングを開始するようにしてください:

```text
Use $academic-research-suite.

I want to write a paper on AI adoption in higher education quality assurance.
I do not yet have a clear research question.
Please use SCR / Socratic dialogue to help me narrow the question first; do not write an outline yet.
```

想定ルート: まず `deep-research` の `socratic` モードにルーティングされます。
ARS は絞り込みの質問を行い、研究質問が収束するまでアウトラインやドラフトを生成してはいけません。

レビュータスクの場合、原稿または原稿へのパスと、希望するレビューモードを提供してください:

```text
Use $academic-research-suite to review this paper.
Mode: full review.
Focus: methodology, contribution, citation integrity, and likely desk-reject risks.
Output: reviewer reports plus editorial decision letter.
```

段階的パイプラインの場合、Codex に全プロセスを黙って実行させるのではなく、
チェックポイントを要求してください:

```text
Use $academic-research-suite to start an academic-pipeline run.
Begin with Stage 0 intake and stop after producing the pipeline dashboard.
```

### スモークテスト

新しい Codex の会話で以下を実行:

```text
/skills
```

期待される結果: ARS エントリが1つのみ。

続いてソクラテス的ルーティングをテスト:

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

以下の Codex メッセージは ARS のインストール失敗を意味するものではありません:

- `[features].codex_hooks is deprecated` — 都合の良い時に Codex の設定を更新してください。
  ARS Codex は通常の使用においてフックを必要としません。
- `hooks need review before they can run` — フックを使用する場合は個別に確認してください。
  ARS Codex はベンダリングされた Claude フックをトレーサビリティメタデータとして扱い、
  これらを必要としません。

### Codex アダプタの動作

ARS は元々 Claude Code 向けに作成されました。本 Codex パッケージでは以下の通りです:

- ベンダリングされた `agents/*.md` ファイルはロールおよびフェーズプロンプトとして使用されます。
- ベンダリングされた `commands/ars-*.md` ファイルはプロンプトレシピとしてのみ機能します。
  Codex はこれらをスラッシュコマンドとして登録しません。
- ベンダリングされた `hooks/hooks.json` ファイルはアップストリームのトレーサビリティのためのみ
  保持されています。Codex は本パッケージから Claude Code フックをインストールしません。
- ユーザーが明示的に委譲または並列エージェント処理を要求しない限り、
  Codex は自動的にバックグラウンドエージェントを生成しません。
- Web/ソース検証には Codex のブラウジング機能を使用し、現在の事実や外部情報が
  関わる場合は必ずソースを引用してください。
- クロスモデル検証はデフォルトで無効です。本 Codex パッケージで明示的に要求された場合、
  `ARS_CROSS_MODEL=claude-opus-4.7` と `ANTHROPIC_API_KEY` を設定してください。
  外部レビューアーは Anthropic Claude Opus 4.7 API を使用し、Codex/OpenAI API は使用しません。
  この明示的な Anthropic 設定がない場合、アップストリームの GPT/Gemini セカンダリディスパッチ
  命令は無視されます。
- アップストリームにおける "fresh Claude Code session" への言及は、本パッケージでは
  新しい Codex の会話を意味します。Material Passport のリセットセマンティクスは引き続き適用されます。
- 引用、ソース、統計、またはジャーナルポリシーが検証できない場合、Codex は裏付けを
  捏造するのではなく、未検証としてマークしてください。

### ARS v3.9.4.2 パリティ

本パッケージは、Codex に同等の概念が存在する範囲で、アップストリーム ARS v3.9.4.2 と
同じユーザー向けワークフローコンテンツを提供することを目指しています。

| アップストリーム ARS 機能 | Codex パッケージの動作 |
|---|---|
| インストール可能なプラグイン1つ | `skills/academic-research-suite` にインストール可能な単一 Codex スキル |
| `/ars-*` スラッシュコマンド | スキルルータ経由で `ars-*` エイリアスとしてエミュレート。ネイティブのスラッシュコマンドではない |
| `skills/` シンボリックリンクから自動検出される4つのアップストリームスキル | 単一の Codex ルータースキルがワークフローを選択し、ベンダリングされた `WORKFLOW.md` ファイルを読み込む |
| プラグイン同梱のエージェント | エージェントファイルはロール/フェーズプロンプトとして機能。ユーザーが明示的に委譲サブエージェントを要求しない限り、Codex はインラインで実行 |
| `model: opus` / `model: sonnet` コマンドルーティング | Claude メタデータとして扱われ、Codex はアクティブモデルを使用 |
| SessionStart および SubagentStop フック | トレーサビリティのためのみベンダリング。Codex は Claude フックをインストールまたは実行しない |
| プラグインマーケットプレースの更新 / 自動更新 | 本パッケージでは利用不可。再インストールまたは本 Codex リポジトリの pull で更新 |
| Claude Code エージェントチーム | 自動ではなし。Codex サブエージェントには委譲または並列エージェントの明示的なユーザー要求が必要 |
| アップストリームドキュメントのクロスモデル GPT/Gemini ディスパッチ | 無効。Codex パッケージは明示的な設定時のみオプションの Anthropic Claude Opus 4.7 レビューをサポート |

### オプション: Claude Opus 4.7 レビューアー API

レビューアーのキャリブレーションやクロスモデルの Devil's Advocate チェック用:

```bash
export ANTHROPIC_API_KEY="<your-anthropic-api-key>"
export ARS_CROSS_MODEL="claude-opus-4.7"
```

その後、プロンプトでクロスモデル検証を明示的に要求してください。
両方の環境変数が設定されていない場合、ARS Codex はシングルランタイムレビューに
フォールバックし、Claude Opus 4.7 検証ツールが利用不可であったことを報告します。

## サポートとスポンサー

ARS Codex があなたの研究ワークフローに役立った場合は、
[Buy Me a Coffee](https://buymeacoffee.com/crucify020v) からメンテナンスを
サポートしていただけますと幸いです。

## セキュリティ

脆弱性については公開の issue を開かないでください。
[`SECURITY.md`](SECURITY.md) に従って非公開で報告してください。
最新のローカル検証サマリーについては
[リリース準備およびセキュリティレポート](security_best_practices_report.md) を
ご参照ください。

### 高度な利用のためのファイルレイアウト

エントリポイントは以下の通りです:

```text
skills/academic-research-suite/SKILL.md
```

ワークフローコンテンツは以下に配置されています:

```text
skills/academic-research-suite/ars/<workflow>/
```

共有スキーマ、コンプライアンスルール、およびワークフロー間の契約は以下に配置されています:

```text
skills/academic-research-suite/ars/shared/
```

パッケージのデバッグや更新を行う際は、これらのパスを維持してください。
多くの ARS ワークフローファイルは `shared/`、`scripts/`、`examples/`、および
他のワークフローディレクトリを相互参照しています。

## 更新ポリシー

更新は選択されたアップストリーム ARS コンテンツを
`skills/academic-research-suite/ars/` に同期します。
Claude Code リポジトリを盲目的にミラーしないでください。
Codex で不要な `.claude/`、`.claude-plugin/`、`.github/`、ソースの `.gitignore`、
およびシンボリックリンクのみのエイリアスディレクトリなどの
Claude/プラグインローダーファイルは除外してください。

### 非アクティブなアップストリームスクリプト

一部のアップストリームメンテナンススクリプトはベンダリングされていますが、
`.claude/CLAUDE.md` のようなベンダリングされていない Claude Code 入力を必要とするため、
本 Codex パッケージでは意図的に非アクティブになっています。
アップストリームスクリプトを Codex CI に組み込む前に、
`skills/academic-research-suite/manifest.json` の
`inactive_upstream_scripts` を確認してください。

## 貢献者と謝辞

**Cheng-I Wu** — ARS スイートおよび本 Codex 兄弟ディストリビューションのメンテナ。

**Codex** — メンテナの指示のもと、Codex アダプタパッケージング、ルーターポリシーの強化、
テスト修正、およびリリース準備レビューを支援。

ベンダリングされたアップストリーム ARS の貢献者は
[`skills/academic-research-suite/ars/README.md`](skills/academic-research-suite/ars/README.md#contributors)
に記載されています。

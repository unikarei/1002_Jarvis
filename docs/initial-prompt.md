# Prj.JARVIS 開発初期プロンプト

あなたは、個人AI秘書システム「Prj.JARVIS」の主任ソフトウェアアーキテクト兼開発者です。以下の構想とルールに基づき、仕様駆動開発（SDD: Specification-Driven Development）でプロジェクトを開始してください。

## 1. プロジェクトの目的

Prj.JARVISは、ユーザーに直接仕える個人AI秘書であり、システム全体の最上位司令塔です。

音声・チャットを統一窓口として、以下を扱います。

- 予定・タスク管理
- 個人の長期記憶
- Windows PC操作
- 外部サービス連携
- ユーザーへの確認・承認
- 専門業務のMiTiR-Baseへの委託
- 実行状況、結果、履歴の管理

JARVIS自身がすべての専門処理を抱えるのではなく、ユーザーの依頼を理解・分類し、JARVISの個人機能で処理するか、MiTiR-Baseへ委託するかを判断します。

## 2. MiTiR-Baseとの関係

Prj.JARVISとMiTiR-Baseは、別プロジェクト・別リポジトリとして開発します。

- Prj.JARVIS：個人AI秘書、ユーザー窓口、承認管理、最上位司令塔
- MiTiR-Base：専門エージェント、サービス、解析アプリを統括する専門業務の実行基盤

JARVISからMiTiRのコードを直接importしてはいけません。Tailscale内のREST APIで疎結合に接続し、将来的にMCPまたはA2Aへ拡張できる構成にしてください。

両者の接続仕様はOpenAPIで管理し、APIのバージョン、認証、承認、タイムアウト、再試行、冪等性、重複実行防止、エラー形式を定義してください。

## 3. Gitリポジトリと相互参照ルール

対象リポジトリは以下です。

- Prj.JARVIS（本プロジェクト、読み書き可能）：https://github.com/unikarei/1002_Jarvis.git
- MiTiR-Base（相手プロジェクト、原則読み取り専用）：https://github.com/unikarei/MiTiR-BASE.git

両プロジェクトは、互いのGitリポジトリを参照し、仕様、API契約、進捗、テスト条件を確認できるようにします。ただし、所有権と責務境界を守るため、次の書き込み制限を厳守してください。

### JARVIS側のエージェント

- `1002_Jarvis` は本プロジェクトとして通常どおり読み書き可能です。
- `MiTiR-BASE` は原則として読み取り専用です。
- MiTiR側へ要望や伝達事項を残す場合に限り、MiTiRリポジトリの `docs/from-Jarvis.md` だけを書き込み可能とします。
- MiTiR側のソースコード、設定、その他の文書を直接変更してはいけません。

### MiTiR側のエージェント

- `MiTiR-BASE` はMiTiR側の本プロジェクトとして通常どおり読み書き可能です。
- `1002_Jarvis` は原則として読み取り専用です。
- JARVIS側へ要望や伝達事項を残す場合に限り、JARVISリポジトリの `docs/from-MiTiR.md` だけを書き込み可能とします。
- JARVIS側のソースコード、設定、その他の文書を直接変更してはいけません。

`docs/from-Jarvis.md` と `docs/from-MiTiR.md` には、希望仕様、API変更要求、確認事項、決定事項、未解決事項、互換性への影響、必要期限を記録します。相手側の変更を勝手に実装済みと仮定せず、合意されるまでは未確定事項として扱ってください。

## 4. SDDによる協調開発方針

コードを先に書かず、要求、仕様、API契約、受入条件、設計判断、作業計画を文書化してから実装してください。仕様変更時も、関連文書とAPI契約を先に更新します。

### JARVIS側の責務

- MiTiRへ送る依頼形式の設計
- MiTiR APIクライアントの実装
- Tailscale経由の接続
- 認証、ユーザー承認、タイムアウト、再試行の実装
- 実行状況と結果の受信
- エラー、取消、部分成功の表示と記録
- 両プロジェクト間の契約テストおよび結合テスト

### MiTiR側に要求する責務

- `GET /health`：稼働確認
- `GET /capabilities`：利用可能な機能一覧
- `POST /tasks`：タスクの受付
- `GET /tasks/{id}`：進捗・結果確認
- `POST /tasks/{id}/cancel`：タスク取消
- 統一されたエラー情報、実行状態、結果情報の返却

MiTiR側の実装変更が必要な場合、JARVIS側でMiTiRの内部実装を推測して変更せず、`MiTiR変更要求` としてJARVIS側文書へ記録し、必要に応じてMiTiR側の `docs/from-Jarvis.md` へ伝達してください。

## 5. 稼働環境

### Prj.JARVIS

- WindowsノートPC
- メモリ32GB
- VS Code＋Codex
- Pythonを中心とした構成
- クラウドLLMを主に利用
- 必要に応じてWindowsローカル機能を使用

### MiTiR-Base

- Mac mini M4 Pro
- メモリ48GB
- Ollama／ローカルLLM
- 専門エージェントとバックグラウンド処理
- Tailscale経由でJARVISから接続
- 一般インターネットには直接公開しない

環境依存値、APIキー、Tailscaleホスト名などはコードに直接記述せず、環境変数と設定ファイルで管理してください。

## 6. 技術方針

以下を第一候補としますが、着手前に妥当性を検討し、採用・不採用の理由をADRへ記録してください。

- Backend：Python 3.12＋FastAPI
- データモデル：Pydantic
- 永続化：SQLite
- マイグレーション：Alembic
- HTTP通信：httpx
- 設定管理：pydantic-settings
- テスト：pytest
- API仕様：OpenAPI
- ログ：構造化ログ
- 個人記憶：SQLite＋Markdown
- 将来のObsidian連携
- Windows操作：PowerShell、Playwrightを優先
- LLM：OpenAI、Claude、Gemini、Ollamaを交換可能にする
- UI：初期段階は最小限のWeb UI
- 音声機能：後続フェーズで追加

特定のLLMやエージェントフレームワークへ中核ロジックを密結合させないでください。LLMプロバイダー、MiTiR接続、記憶、外部ツールはインターフェースで交換可能にします。

## 7. セキュリティと承認

以下は、必ずユーザー承認を必要とする操作として設計してください。

- ファイルの削除・上書き
- メールやメッセージの送信
- 予定の登録・変更・削除
- 外部サービスへの書き込み
- プログラムのインストール
- システム設定の変更
- MiTiRで費用や長時間処理を伴うタスクの実行

LLMが生成した命令を、そのままOSコマンドとして実行してはいけません。許可された操作だけを型付きツールとして公開し、引数検証、承認、監査ログを通してください。

APIキー、パスワード、トークン、個人情報をログやGitへ保存しないでください。Tailscaleによるネットワーク制限だけに依存せず、アプリケーションレベルの認証も設計してください。

## 8. SDD文書

実装前に、両リポジトリと既存文書を確認したうえで次の文書を作成してください。

- `AGENTS.md`：開発原則、作業手順、禁止事項、完了条件
- `README.md`：概要、構成、セットアップ、起動方法
- `docs/vision.md`：目的、利用者、将来像、対象外
- `docs/spec.md`：機能要件、非機能要件、受入条件
- `docs/architecture.md`：システム構成、責務、データフロー
- `docs/security.md`：権限、承認、秘密情報、監査方針
- `docs/mitir-integration.md`：MiTiRとの責務境界と接続仕様
- `docs/api/mitir-openapi.yaml`：MiTiR連携API契約
- `docs/adr/`：主要な設計判断
- `docs/from-MiTiR.md`：MiTiR側からJARVIS側への連絡窓口
- `tasks.md`：フェーズ別タスク、状態、完了条件
- `.env.example`：秘密情報を含まない設定例

不明点を勝手に確定せず、`Assumptions`、`Open Questions`、`Out of Scope`として文書に明記してください。

## 9. Phase 1の実装範囲

最初の実装は、JARVISとMiTiRの接続基盤だけに限定します。

1. JARVISバックエンドの起動
2. `GET /health`によるJARVIS自身の状態確認
3. MiTiR APIクライアントの実装
4. MiTiRの`GET /health`および`GET /capabilities`呼び出し
5. MiTiRが停止している場合の適切なエラー表示
6. MiTiRのモックサーバーまたはモッククライアント
7. 接続設定の環境変数化
8. 認証、タイムアウト、限定的な再試行
9. 構造化ログ、相関ID、監査情報
10. 単体テスト、API契約テスト、両プロジェクト間の結合テスト
11. Windows PowerShellでの起動・確認手順

Phase 1では、音声、予定、メール、PC自動操作、長期記憶、複数エージェント制御を本実装しないでください。これらはインターフェースとロードマップだけを定義します。

## 10. 推奨ディレクトリ構成

以下を参考にし、より適切な構成があれば理由を示して調整してください。

```text
1002_Jarvis/
├─ AGENTS.md
├─ README.md
├─ tasks.md
├─ pyproject.toml
├─ .env.example
├─ docs/
│  ├─ initial-prompt.md
│  ├─ vision.md
│  ├─ spec.md
│  ├─ architecture.md
│  ├─ security.md
│  ├─ mitir-integration.md
│  ├─ from-MiTiR.md
│  ├─ api/
│  │  └─ mitir-openapi.yaml
│  └─ adr/
├─ src/
│  └─ jarvis/
│     ├─ api/
│     ├─ application/
│     ├─ domain/
│     ├─ integrations/
│     │  └─ mitir/
│     ├─ infrastructure/
│     └─ main.py
└─ tests/
   ├─ unit/
   ├─ integration/
   └─ contract/
```

## 11. 開発ルール

- 既存ファイル、Git状態、ブランチ、リモートを最初に確認する
- JARVISとMiTiR双方の関連仕様を確認する
- ユーザーや相手プロジェクトの既存変更を無断で削除・上書きしない
- 小さな単位で仕様化、実装、検証する
- 型ヒントを付ける
- 外部I/Oとドメインロジックを分離する
- Windowsで再現できるコマンドを提示する
- テスト、Lint、型チェックを実行する
- 実行していない検証を「成功」と報告しない
- 仕様変更時は、コードより先に関連文書とAPI契約を更新する
- API契約の後方互換性を維持する
- API契約変更は両プロジェクトへ伝達し、合意状態を記録する
- 相手プロジェクトへの書き込み制限を厳守する
- Gitへのcommit、push、PR作成はユーザーの明示的な指示があるまで行わない

## 12. 最初に行う作業

次の順番で進めてください。

1. 現在のJARVISリポジトリ、ファイル、Git状態、利用可能な実行環境を調査
2. MiTiRリポジトリを読み取り専用で調査し、既存API、文書、未解決事項を確認
3. 不足情報と重要な設計判断を整理
4. SDD文書とPhase 1の実装計画を作成
5. JARVIS／MiTiR間の責務、API契約、受入条件を定義
6. 重大な選択肢だけをユーザーへ確認
7. 合意後、Phase 1を実装
8. 単体テスト、契約テスト、結合テスト、接続確認を実施
9. 変更ファイル、テスト結果、残課題、MiTiR側への要求を報告

最初の応答では、いきなり全機能を実装せず、調査結果、推奨アーキテクチャ、Phase 1の作業計画、JARVISとMiTiRの連携上の確認事項を簡潔に提示してください。

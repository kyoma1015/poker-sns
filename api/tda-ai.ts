import OpenAI from "openai";
import { createClient } from "@supabase/supabase-js";

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

const supabaseUrl = process.env.VITE_SUPABASE_URL;
const supabaseAnonKey = process.env.VITE_SUPABASE_ANON_KEY;

type TdaRule = {
  rule_number: number;
  title_ja: string | null;
  conclusion_ja: string | null;
  explanation_ja: string | null;
  keywords_ja: string[] | null;
  examples_ja: string[] | null;
  cautions_ja: string[] | null;
  related_rules: number[] | null;
  title_en: string | null;
  body_en: string | null;
};

type SearchAnalysis = {
  queries?: string[];
};

export default async function handler(req: any, res: any) {
  if (req.method !== "POST") {
    return res.status(405).json({
      error: "POSTのみ利用できます。",
    });
  }

  if (!process.env.OPENAI_API_KEY) {
    return res.status(500).json({
      error: "OPENAI_API_KEYが設定されていません。",
    });
  }

  if (!supabaseUrl || !supabaseAnonKey) {
    return res.status(500).json({
      error: "Supabaseの環境変数が設定されていません。",
    });
  }

  const question =
    typeof req.body?.question === "string"
      ? req.body.question.trim()
      : "";

  if (!question) {
    return res.status(400).json({
      error: "質問を入力してください。",
    });
  }

  if (question.length > 1000) {
    return res.status(400).json({
      error: "質問は1000文字以内で入力してください。",
    });
  }

  try {
    const supabase = createClient(supabaseUrl, supabaseAnonKey);

    /*
     * STEP 1
     * ユーザーの自然文から「検索用の論点・用語」だけを抽出する。
     *
     * このAIには裁定をさせない。
     * あくまでDB検索の補助だけ。
     */
    const searchAnalysisResponse = await openai.responses.create({
      model: "gpt-5-mini",

      instructions: `
あなたはPoker TDAルールデータベースの検索補助AIです。

仕事は「裁定を答えること」ではありません。
ユーザーの質問から、関連するTDAルールを検索するための日本語キーワード・ポーカー用語・論点を抽出することだけです。

重要:
- 裁定結果を回答してはいけません。
- Rule番号を推測してはいけません。
- TDAルールの内容を作ってはいけません。
- 質問に書かれていない状況を勝手に追加してはいけません。
- 一般的な表現と専門用語の両方を検索候補にしてください。
- 数字そのものより、ルール上の論点を優先してください。
- 検索語は短くしてください。
- 最大8個までにしてください。

例:
「少ない額のオールインが何人か続いて、最初にベットした人はまたレイズできる？」
なら検索候補として
「オールイン」
「ショートオールイン」
「レイズ」
「リオープン」
「ベッティングのリオープン」
「フルレイズ」
などを考えます。

必ず次のJSONだけを返してください。

{
  "queries": ["検索語1", "検索語2"]
}
`.trim(),

      input: question,
    });

    let searchQueries: string[] = [];

    try {
      const raw = searchAnalysisResponse.output_text?.trim() ?? "";

      const cleaned = raw
        .replace(/^```json\s*/i, "")
        .replace(/^```\s*/i, "")
        .replace(/\s*```$/i, "");

      const parsed = JSON.parse(cleaned) as SearchAnalysis;

      if (Array.isArray(parsed.queries)) {
        searchQueries = parsed.queries
          .filter(
            (value): value is string =>
              typeof value === "string" && value.trim().length > 0,
          )
          .map((value) => value.trim())
          .slice(0, 8);
      }
    } catch (error) {
      console.error("TDA search analysis parse error:", error);
    }

    /*
     * 元の質問も必ず検索する。
     * AIが検索語抽出に失敗しても、従来の検索経路を残す。
     */
    const allSearchTexts = Array.from(
      new Set([question, ...searchQueries]),
    );
    console.log("TDA AI search queries:", allSearchTexts);

    /*
     * STEP 2
     * Poker IDの検証済みTDA DBを検索。
     *
     * 複数の検索語で検索して結果を統合する。
     */
    const ruleMap = new Map<number, TdaRule>();

    for (const searchText of allSearchTexts) {
      const { data, error } = await supabase.rpc("search_tda_rules", {
        search_text: searchText,
      });

      if (error) {
        console.error("TDA search error:", {
          searchText,
          error,
        });

        continue;
      }

      const foundRules = (data ?? []) as TdaRule[];

      for (const rule of foundRules) {
        if (
          typeof rule.rule_number === "number" &&
          !ruleMap.has(rule.rule_number)
        ) {
          ruleMap.set(rule.rule_number, rule);
        }
      }
    }

    /*
     * 最大12件までAIへ渡す。
     * 同じRuleはMapで重複排除済み。
     */
    const rules = Array.from(ruleMap.values()).slice(0, 12);

    /*
     * DBから根拠候補を1件も取得できなかった場合、
     * AIに裁定させない。
     */
    if (rules.length === 0) {
      return res.status(200).json({
        answer:
          "この質問に対して、Poker IDに登録されている検証済みTDAルールから十分な根拠を特定できませんでした。状況をもう少し具体的に入力してください。",
        rules: [],
        grounded: false,
      });
    }

    /*
     * STEP 3
     * DBから取得できた検証済みRuleだけを
     * 最終回答AIへ渡す。
     */
    const ruleContext = rules
      .map((rule) => {
        return `
【TDA Rule ${rule.rule_number}】

日本語タイトル:
${rule.title_ja ?? ""}

結論:
${rule.conclusion_ja ?? ""}

解説:
${rule.explanation_ja ?? ""}

検索キーワード:
${(rule.keywords_ja ?? []).join(" / ")}

具体例:
${(rule.examples_ja ?? []).join("\n")}

注意点:
${(rule.cautions_ja ?? []).join("\n")}

関連ルール:
${(rule.related_rules ?? []).join(", ")}

公式英語タイトル:
${rule.title_en ?? ""}

公式英語本文:
${rule.body_en ?? ""}
`.trim();
      })
      .join("\n\n--------------------\n\n");

    /*
     * STEP 4
     * 最終裁定。
     *
     * ここではDBから取得したRule以外を
     * 根拠として使わせない。
     */
    const response = await openai.responses.create({
      model: "gpt-5-mini",

      instructions: `
あなたはPoker IDのTDAルール解説AIです。

あなたの仕事は、ユーザーから提示されたポーカーの状況について、
提供された検証済みPoker TDAルールだけを根拠に説明することです。

【絶対に守ること】

1.
回答の裁定根拠として使用できるのは、
このリクエスト内で提供されたTDAルールだけです。

2.
あなた自身の記憶、学習済み知識、一般的なポーカールール、
ハウスルール、過去バージョンのTDAルールを
裁定根拠として使用してはいけません。

3.
提供されたRuleから確実に判断できない場合は、
推測してはいけません。

その場合は、
「この情報だけでは確定できません」
と明示してください。

4.
ユーザーの状況説明に、
裁定を決めるために必要な情報が不足している場合は、
勝手に条件を仮定しないでください。

何の情報が必要なのかを具体的に質問してください。

5.
提供された日本語説明と公式英語本文に
意味上の矛盾がある場合は、
公式英語本文を優先してください。

6.
提供されていないRule番号を
絶対に根拠として挙げないでください。

7.
「関連していそう」というだけのRuleを
根拠として列挙しないでください。
実際に裁定・説明に使用したRuleだけを示してください。

【回答形式】

最初に結論を書いてください。

その後、
なぜそうなるのかを初心者にも分かる自然な日本語で説明してください。

金額・チップ量が重要な場合は、
ユーザーが提示した数字を使って具体的に説明してください。

判断に条件分岐がある場合は、
「○○なら〜、△△なら〜」
のように明確に分けてください。

最後に必ず、

根拠: TDA Rule 49

のような形式で、
実際に使用したRule番号だけを書いてください。

複数ある場合は、

根拠: TDA Rule 49, Rule 51

の形式にしてください。
`.trim(),

      input: `
【ユーザーの質問】

${question}

【Poker IDのデータベースから取得した検証済みTDAルール】

${ruleContext}

上記のルールだけを根拠として回答してください。
`.trim(),
    });

    const answer = response.output_text?.trim();

    if (!answer) {
      return res.status(500).json({
        error: "AIから回答を取得できませんでした。",
      });
    }

    return res.status(200).json({
      answer,
      grounded: true,

      /*
       * 現段階では検索で取得した候補Ruleを返す。
       * 後で「AIが実際に使用したRuleだけ」に
       * 厳密化することも可能。
       */
      rules: rules.map((rule) => ({
        rule_number: rule.rule_number,
        title_ja: rule.title_ja,
      })),
    });
  } catch (error) {
    console.error("TDA AI error:", error);

    return res.status(500).json({
      error: "AI回答の生成中にエラーが発生しました。",
    });
  }
}
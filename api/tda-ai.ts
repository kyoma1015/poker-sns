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

    // 既存のTDA検索RPCを使用。
    // AIが自分の記憶だけでルールを選ばないよう、
    // まずPoker IDの検証済みTDAデータから関連ルールを取得する。
    const { data, error } = await supabase.rpc("search_tda_rules", {
      search_text: question,
    });

    if (error) {
      console.error("TDA search error:", error);

      return res.status(500).json({
        error: "TDAルールの検索に失敗しました。",
      });
    }

    const rules = ((data ?? []) as TdaRule[]).slice(0, 8);

    // 根拠となるルールを取得できない場合は、
    // OpenAIへ質問自体を送らない。
    if (rules.length === 0) {
      return res.status(200).json({
        answer:
          "この質問に対して、Poker IDに登録されている検証済みTDAルールから十分な根拠を特定できませんでした。状況をもう少し具体的に入力してください。",
        rules: [],
        grounded: false,
      });
    }

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

具体例:
${(rule.examples_ja ?? []).join("\n")}

注意点:
${(rule.cautions_ja ?? []).join("\n")}

公式英語タイトル:
${rule.title_en ?? ""}

公式英語本文:
${rule.body_en ?? ""}
`.trim();
      })
      .join("\n\n--------------------\n\n");

    const response = await openai.responses.create({
      model: "gpt-5-mini",
      instructions: `
あなたはPoker IDのTDAルール解説AIです。

最重要ルール:
- 回答の裁定根拠として使用できるのは、提供されたTDAルールだけです。
- 自分の記憶や一般的なポーカールールを根拠に裁定を作ってはいけません。
- 提供されたTDAルールから確実に判断できない場合は、推測せず「この情報だけでは確定できません」と回答してください。
- ハウスルールをTDAルールとして扱ってはいけません。
- ユーザーの質問に不足情報がある場合は、必要な追加情報を具体的に質問してください。
- 日本語で回答してください。
- 初心者にも分かる自然な日本語を使ってください。
- 結論を先に書いてください。
- 回答の最後に必ず「根拠: TDA Rule ○○」の形式で、実際に回答根拠として使用したRule番号だけを書いてください。
- 提供されていないRule番号を根拠として挙げてはいけません。
- 提供された日本語説明と公式英語本文に矛盾がある場合は、公式英語本文を優先してください。
`.trim(),

      input: `
ユーザーの質問:
${question}

以下はPoker IDのデータベースから取得した検証済みTDAルールです。
この情報だけを裁定根拠として回答してください。

${ruleContext}
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
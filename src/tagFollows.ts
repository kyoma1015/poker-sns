import { supabase } from './supabase'

export const SUGGESTED_TAGS = ['MIX', 'JOPT', 'TDA', 'ハンド相談'] as const

export function normalizeTag(value: string): string {
  return value.trim().replace(/^#+/, '').normalize('NFKC').toLocaleUpperCase('ja-JP')
}

export function extractTags(content: string): string[] {
  const tags = new Set<string>()
  for (const match of content.matchAll(/(?:^|\s)[#＃]([^\s#＃.,!?。、！？]+)/gu)) {
    const tag = normalizeTag(match[1])
    if (tag && tag.length <= 40) tags.add(tag)
  }
  return [...tags]
}

export async function getMyFollowedTags(userId: string): Promise<string[]> {
  const { data, error } = await supabase.from('tag_follows')
    .select('tag').eq('user_id', userId).order('tag')
  if (error) throw error
  return (data ?? []).map(row => String(row.tag))
}

export async function setTagFollow(userId: string, rawTag: string, following: boolean): Promise<void> {
  const tag = normalizeTag(rawTag)
  if (!tag || tag.length > 40 || /\s/.test(tag)) throw new Error('タグは1〜40文字で指定してください')
  const query = supabase.from('tag_follows')
  const { error } = following
    ? await query.upsert({ user_id: userId, tag }, { onConflict: 'user_id,tag' })
    : await query.delete().eq('user_id', userId).eq('tag', tag)
  if (error) throw error
}

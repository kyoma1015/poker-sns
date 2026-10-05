import {
  useEffect,
  useRef,
  useState,
} from 'react'
import {
  useNavigate,
  useParams,
} from 'react-router-dom'
import { supabase } from './supabase'

type DirectMessage = {
  id: string
  sender_id: string
  receiver_id: string
  content: string
  created_at: string
  read_at: string | null
}

function DirectMessageChat() {
  const { userId } = useParams()
  const navigate = useNavigate()

  const [currentUserId, setCurrentUserId] =
    useState('')

  const [playerName, setPlayerName] =
    useState('')

  const [pokerId, setPokerId] =
    useState('')

  const [avatarUrl, setAvatarUrl] =
    useState<string | null>(null)

  const [messages, setMessages] =
    useState<DirectMessage[]>([])

  const [input, setInput] =
    useState('')

  const [
    statusMessage,
    setStatusMessage,
  ] = useState('読み込み中...')

  const [isSending, setIsSending] =
    useState(false)

  const bottomRef =
    useRef<HTMLDivElement | null>(null)

  const scrollToBottom = (
    behavior: ScrollBehavior = 'smooth'
  ) => {
    setTimeout(() => {
      bottomRef.current?.scrollIntoView({
        behavior,
      })
    }, 50)
  }

  const markMessagesAsRead = async (
    myUserId: string,
    otherUserId: string
  ) => {
    const { error } = await supabase
      .from('direct_messages')
      .update({
        read_at:
          new Date().toISOString(),
      })
      .eq(
        'sender_id',
        otherUserId
      )
      .eq(
        'receiver_id',
        myUserId
      )
      .is('read_at', null)

    if (error) {
      console.error(
        '既読更新エラー:',
        error
      )
    }
  }

  const loadMessages = async () => {
    if (!userId) {
      setStatusMessage(
        '相手が見つかりませんでした。'
      )
      return
    }

    const {
      data: { user },
    } = await supabase.auth.getUser()

    if (!user) {
      navigate('/login')
      return
    }

    setCurrentUserId(user.id)

    if (user.id === userId) {
      setStatusMessage(
        '自分自身にはDMできません。'
      )
      return
    }

    const {
      data: profile,
      error: profileError,
    } = await supabase
      .from('profiles')
      .select(
        'display_name, poker_id, avatar_url'
      )
      .eq('id', userId)
      .maybeSingle()

    if (profileError) {
      console.error(profileError)

      setStatusMessage(
        `プロフィールの取得に失敗しました：${profileError.message}`
      )

      return
    }

    if (!profile) {
      setStatusMessage(
        '相手が見つかりませんでした。'
      )
      return
    }

    setPlayerName(
      profile.display_name
    )

    setPokerId(
      profile.poker_id
    )

    setAvatarUrl(
      profile.avatar_url || null
    )

    await markMessagesAsRead(
      user.id,
      userId
    )

    const {
      data: dmData,
      error: dmError,
    } = await supabase
      .from('direct_messages')
      .select('*')
      .or(
        `and(sender_id.eq.${user.id},receiver_id.eq.${userId}),and(sender_id.eq.${userId},receiver_id.eq.${user.id})`
      )
      .order('created_at', {
        ascending: true,
      })

    if (dmError) {
      console.error(dmError)

      setStatusMessage(
        `DMの取得に失敗しました：${dmError.message}`
      )

      return
    }

    setMessages(dmData || [])
    setStatusMessage('')

    scrollToBottom('auto')
  }

  useEffect(() => {
    loadMessages()
  }, [userId])

  useEffect(() => {
    if (
      !currentUserId ||
      !userId
    ) {
      return
    }

    const channel = supabase
      .channel(
        `dm-${currentUserId}-${userId}`
      )
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table:
            'direct_messages',
        },
        async (payload) => {
          if (
            payload.eventType ===
            'INSERT'
          ) {
            const newMessage =
              payload.new as DirectMessage

            const belongsToConversation =
              (newMessage.sender_id ===
                currentUserId &&
                newMessage.receiver_id ===
                  userId) ||
              (newMessage.sender_id ===
                userId &&
                newMessage.receiver_id ===
                  currentUserId)

            if (
              !belongsToConversation
            ) {
              return
            }

            if (
              newMessage.sender_id ===
                userId &&
              newMessage.receiver_id ===
                currentUserId
            ) {
              await markMessagesAsRead(
                currentUserId,
                userId
              )
            }

            await loadMessages()

            scrollToBottom()
          }

          if (
            payload.eventType ===
            'UPDATE'
          ) {
            const updatedMessage =
              payload.new as DirectMessage

            const belongsToConversation =
              (updatedMessage.sender_id ===
                currentUserId &&
                updatedMessage.receiver_id ===
                  userId) ||
              (updatedMessage.sender_id ===
                userId &&
                updatedMessage.receiver_id ===
                  currentUserId)

            if (
              !belongsToConversation
            ) {
              return
            }

            setMessages(
              (
                previousMessages
              ) =>
                previousMessages.map(
                  (message) =>
                    message.id ===
                    updatedMessage.id
                      ? updatedMessage
                      : message
                )
            )
          }
        }
      )
      .subscribe()

    return () => {
      supabase.removeChannel(
        channel
      )
    }
  }, [
    currentUserId,
    userId,
  ])

  useEffect(() => {
    if (messages.length > 0) {
      scrollToBottom()
    }
  }, [messages.length])

  const handleSend = async () => {
    const trimmedInput =
      input.trim()

    if (!trimmedInput) {
      return
    }

    if (
      !currentUserId ||
      !userId
    ) {
      setStatusMessage(
        '送信先を確認できませんでした。'
      )
      return
    }

    if (
      currentUserId === userId
    ) {
      setStatusMessage(
        '自分自身にはDMできません。'
      )
      return
    }

    setIsSending(true)

    const { error } =
      await supabase
        .from(
          'direct_messages'
        )
        .insert({
          sender_id:
            currentUserId,
          receiver_id: userId,
          content:
            trimmedInput,
        })

    if (error) {
      console.error(error)

      setStatusMessage(
        `DMを送信できませんでした：${error.message}`
      )

      setIsSending(false)
      return
    }

    setInput('')
    setStatusMessage('')
    setIsSending(false)

    await loadMessages()

    scrollToBottom()
  }

  const handleKeyDown = (
    event: React.KeyboardEvent<HTMLInputElement>
  ) => {
    if (
      event.key === 'Enter' &&
      !event.nativeEvent.isComposing
    ) {
      event.preventDefault()
      handleSend()
    }
  }

  const handlePlayerProfile =
    () => {
      if (!userId) return

      navigate(
        `/player/${userId}`
      )
    }

  const formatTime = (
    createdAt: string
  ) => {
    return new Date(
      createdAt
    ).toLocaleTimeString(
      'ja-JP',
      {
        hour: '2-digit',
        minute: '2-digit',
      }
    )
  }

  const formatDate = (
    createdAt: string
  ) => {
    const date =
      new Date(createdAt)

    const today = new Date()

    const yesterday =
      new Date()

    yesterday.setDate(
      today.getDate() - 1
    )

    if (
      date.toDateString() ===
      today.toDateString()
    ) {
      return '今日'
    }

    if (
      date.toDateString() ===
      yesterday.toDateString()
    ) {
      return '昨日'
    }

    return date.toLocaleDateString(
      'ja-JP',
      {
        month: 'numeric',
        day: 'numeric',
      }
    )
  }

  const shouldShowDate = (
    index: number
  ) => {
    if (index === 0) {
      return true
    }

    const current =
      new Date(
        messages[index].created_at
      )

    const previous =
      new Date(
        messages[
          index - 1
        ].created_at
      )

    return (
      current.toDateString() !==
      previous.toDateString()
    )
  }

  return (
    <main className="app">
      <div
        className="card"
        style={{
          paddingTop: 0,
          paddingBottom: '155px',
        }}
      >
        {/* 固定ヘッダー */}
        <header
          style={{
            position: 'sticky',
            top: 0,
            zIndex: 30,
            margin: '0 -20px',
            padding: '10px 16px',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            background:
              'rgba(0, 0, 0, 0.96)',
            borderBottom:
              '1px solid #242424',
            backdropFilter:
              'blur(14px)',
            WebkitBackdropFilter:
              'blur(14px)',
          }}
        >
          <button
            onClick={() =>
              navigate('/dm')
            }
            aria-label="DM一覧へ戻る"
            style={{
              width: '36px',
              height: '36px',
              padding: 0,
              flexShrink: 0,
              display: 'flex',
              alignItems:
                'center',
              justifyContent:
                'center',
              background:
                'transparent',
              color: '#fff',
              borderRadius: '50%',
              fontSize: '27px',
              fontWeight: 300,
            }}
          >
            ‹
          </button>

          {playerName ? (
            <div
              onClick={
                handlePlayerProfile
              }
              style={{
                flex: 1,
                minWidth: 0,
                display: 'flex',
                alignItems:
                  'center',
                gap: '10px',
                cursor: 'pointer',
              }}
            >
              {avatarUrl ? (
                <img
                  src={avatarUrl}
                  alt={`${playerName}のプロフィール画像`}
                  style={{
                    width: '40px',
                    height: '40px',
                    borderRadius:
                      '50%',
                    objectFit:
                      'cover',
                    border:
                      '1px solid #333',
                    flexShrink: 0,
                  }}
                />
              ) : (
                <div
                  style={{
                    width: '40px',
                    height: '40px',
                    flexShrink: 0,
                    display:
                      'flex',
                    alignItems:
                      'center',
                    justifyContent:
                      'center',
                    background:
                      '#171717',
                    border:
                      '1px solid #333',
                    borderRadius:
                      '50%',
                    fontSize:
                      '18px',
                  }}
                >
                  ♠
                </div>
              )}

              <div
                style={{
                  minWidth: 0,
                }}
              >
                <div
                  style={{
                    overflow:
                      'hidden',
                    textOverflow:
                      'ellipsis',
                    whiteSpace:
                      'nowrap',
                    color: '#fff',
                    fontSize:
                      '14px',
                    fontWeight:
                      800,
                  }}
                >
                  {playerName}
                </div>

                <div
                  style={{
                    marginTop:
                      '1px',
                    overflow:
                      'hidden',
                    textOverflow:
                      'ellipsis',
                    whiteSpace:
                      'nowrap',
                    color: '#777',
                    fontSize:
                      '11px',
                  }}
                >
                  @{pokerId}
                </div>
              </div>
            </div>
          ) : (
            <div
              style={{
                fontSize: '16px',
                fontWeight: 800,
              }}
            >
              メッセージ
            </div>
          )}
        </header>

        {/* ステータス */}
        {statusMessage && (
          <div
            style={{
              padding: '18px 0',
              color: '#777',
              fontSize: '12px',
              textAlign: 'center',
            }}
          >
            {statusMessage}
          </div>
        )}

        {/* メッセージなし */}
        {messages.length === 0 &&
          !statusMessage &&
          playerName && (
            <div
              style={{
                padding:
                  '55px 20px 30px',
                textAlign:
                  'center',
              }}
            >
              {avatarUrl ? (
                <img
                  src={avatarUrl}
                  alt={`${playerName}のプロフィール画像`}
                  onClick={
                    handlePlayerProfile
                  }
                  style={{
                    width: '72px',
                    height: '72px',
                    borderRadius:
                      '50%',
                    objectFit:
                      'cover',
                    border:
                      '1px solid #333',
                    cursor:
                      'pointer',
                  }}
                />
              ) : (
                <div
                  onClick={
                    handlePlayerProfile
                  }
                  style={{
                    width: '72px',
                    height: '72px',
                    margin:
                      '0 auto',
                    display:
                      'flex',
                    alignItems:
                      'center',
                    justifyContent:
                      'center',
                    background:
                      '#171717',
                    border:
                      '1px solid #333',
                    borderRadius:
                      '50%',
                    fontSize:
                      '28px',
                    cursor:
                      'pointer',
                  }}
                >
                  ♠
                </div>
              )}

              <div
                style={{
                  marginTop:
                    '13px',
                  fontSize:
                    '16px',
                  fontWeight:
                    800,
                }}
              >
                {playerName}
              </div>

              <div
                style={{
                  marginTop:
                    '3px',
                  color: '#777',
                  fontSize:
                    '12px',
                }}
              >
                @{pokerId}
              </div>

              <div
                style={{
                  marginTop:
                    '17px',
                  color: '#666',
                  fontSize:
                    '12px',
                }}
              >
                メッセージを送って
                会話を始めましょう
              </div>
            </div>
          )}

        {/* メッセージ */}
        <div
          style={{
            paddingTop: '18px',
          }}
        >
          {messages.map(
            (dm, index) => {
              const isMine =
                dm.sender_id ===
                currentUserId

              return (
                <div
                  key={dm.id}
                >
                  {shouldShowDate(
                    index
                  ) && (
                    <div
                      style={{
                        margin:
                          '13px 0 20px',
                        color:
                          '#666',
                        fontSize:
                          '11px',
                        textAlign:
                          'center',
                      }}
                    >
                      {formatDate(
                        dm.created_at
                      )}
                    </div>
                  )}

                  <div
                    style={{
                      display:
                        'flex',
                      justifyContent:
                        isMine
                          ? 'flex-end'
                          : 'flex-start',
                      marginBottom:
                        '7px',
                    }}
                  >
                    <div
                      style={{
                        maxWidth:
                          '78%',
                      }}
                    >
                      <div
                        style={{
                          padding:
                            '10px 13px',
                          background:
                            isMine
                              ? '#fff'
                              : '#1c1c1c',
                          color:
                            isMine
                              ? '#000'
                              : '#f5f5f5',
                          border:
                            isMine
                              ? '1px solid #fff'
                              : '1px solid #292929',
                          borderRadius:
                            isMine
                              ? '18px 18px 4px 18px'
                              : '18px 18px 18px 4px',
                          fontSize:
                            '14px',
                          lineHeight:
                            1.5,
                          whiteSpace:
                            'pre-wrap',
                          wordBreak:
                            'break-word',
                        }}
                      >
                        {dm.content}
                      </div>

                      <div
                        style={{
                          display:
                            'flex',
                          justifyContent:
                            isMine
                              ? 'flex-end'
                              : 'flex-start',
                          gap: '5px',
                          marginTop:
                            '4px',
                          padding:
                            '0 4px',
                          color:
                            '#555',
                          fontSize:
                            '10px',
                        }}
                      >
                        {isMine &&
                          dm.read_at && (
                            <span>
                              既読
                            </span>
                          )}

                        <span>
                          {formatTime(
                            dm.created_at
                          )}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              )
            }
          )}

          <div ref={bottomRef} />
        </div>

        {/* 送信欄 */}
        <div
          style={{
            position: 'fixed',
            left: '50%',
            bottom: '68px',
            transform:
              'translateX(-50%)',
            zIndex: 40,
            width: '100%',
            maxWidth: '600px',
            padding:
              '10px 14px',
            background:
              'rgba(0, 0, 0, 0.96)',
            borderTop:
              '1px solid #242424',
            borderLeft:
              '1px solid #242424',
            borderRight:
              '1px solid #242424',
            backdropFilter:
              'blur(14px)',
            WebkitBackdropFilter:
              'blur(14px)',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems:
                'center',
              gap: '8px',
            }}
          >
            <input
              type="text"
              placeholder="メッセージ..."
              value={input}
              onChange={(e) =>
                setInput(
                  e.target.value
                )
              }
              onKeyDown={
                handleKeyDown
              }
              maxLength={1000}
              style={{
                flex: 1,
                minWidth: 0,
                height: '42px',
                padding:
                  '0 15px',
                background:
                  '#151515',
                border:
                  '1px solid #2d2d2d',
                borderRadius:
                  '999px',
                fontSize:
                  '14px',
              }}
            />

            <button
              onClick={handleSend}
              disabled={
                isSending ||
                !input.trim()
              }
              aria-label="送信"
              style={{
                width: '42px',
                height: '42px',
                padding: 0,
                flexShrink: 0,
                display: 'flex',
                alignItems:
                  'center',
                justifyContent:
                  'center',
                background:
                  input.trim()
                    ? '#fff'
                    : '#222',
                color:
                  input.trim()
                    ? '#000'
                    : '#666',
                borderRadius:
                  '50%',
                fontSize:
                  '20px',
                fontWeight: 800,
              }}
            >
              ↑
            </button>
          </div>
        </div>
      </div>
    </main>
  )
}

export default DirectMessageChat
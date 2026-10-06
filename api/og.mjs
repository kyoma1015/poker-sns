export async function GET(request) {
  const url = new URL(request.url)

  return new Response(
    `OG function alive

type=${url.searchParams.get('type')}
id=${url.searchParams.get('id')}`,
    {
      status: 200,
      headers: {
        'Content-Type': 'text/plain; charset=utf-8',
      },
    },
  )
}
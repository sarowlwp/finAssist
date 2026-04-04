import { NextRequest, NextResponse } from 'next/server'

// 设置最大执行时间为 300 秒（Next.js App Router 支持）
export const maxDuration = 300

export async function POST(
  request: NextRequest,
  { params }: { params: { agentName: string } }
) {
  const { agentName } = params
  const body = await request.json()

  try {
    const backendResponse = await fetch(
      `http://localhost:8001/api/agents/${agentName}/chat`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
        // Node.js fetch 不受浏览器超时限制，这里依赖 maxDuration
      }
    )

    const data = await backendResponse.json()

    if (!backendResponse.ok) {
      return NextResponse.json(data, { status: backendResponse.status })
    }

    return NextResponse.json(data)
  } catch (error) {
    console.error(`[API Route] Agent chat failed:`, error)
    return NextResponse.json(
      { detail: `请求失败: ${error instanceof Error ? error.message : String(error)}` },
      { status: 500 }
    )
  }
}
